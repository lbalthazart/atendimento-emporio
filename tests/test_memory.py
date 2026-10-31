import asyncio
import time
import pytest
from src.memory.session_store import SessionStore

def test_session_message_flow():
    store = SessionStore(ttl_days=7)
    session_id = "test_user_1"
    
    store.add_message(session_id, "user", "Olá!")
    store.add_message(session_id, "assistant", "Olá! Como posso ajudar você hoje?")
    
    msgs = store.get_messages(session_id)
    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"
    assert msgs[0]["content"] == "Olá!"
    assert msgs[1]["role"] == "assistant"

def test_lgpd_ttl_expiration():
    # Testa com TTL de 1 segundo para validar a expiração
    store = SessionStore(ttl_days=0)
    store.ttl_seconds = 1  # 1 segundo para teste rápido
    
    session_id = "test_expire"
    store.add_message(session_id, "user", "Mensagem que deve expirar")
    
    assert len(store.get_messages(session_id)) == 1
    
    # Aguarda 1.2 segundos para ultrapassar o TTL
    time.sleep(1.2)
    purged = store.purge_expired()
    assert purged >= 1
    
    # Ao consultar novamente, nova sessão limpa é gerada sem o histórico expirado
    msgs = store.get_messages(session_id)
    assert len(msgs) == 0

def test_lgpd_right_to_be_forgotten():
    store = SessionStore(ttl_days=7)
    session_id = "test_forget"
    store.add_message(session_id, "user", "Meus dados")
    
    assert store.delete_session(session_id) is True
    assert len(store.get_messages(session_id)) == 0

def test_pause_ia_handoff():
    store = SessionStore(ttl_days=7)
    session_id = "test_handoff"
    
    assert store.is_paused(session_id) is False
    
    # Pausa por 10 segundos
    store.pause_ia(session_id, duration_seconds=10)
    assert store.is_paused(session_id) is True
    
    # Despausa manualmente
    store.unpause_ia(session_id)
    assert store.is_paused(session_id) is False

@pytest.mark.asyncio
async def test_message_debouncing():
    store = SessionStore(ttl_days=7)
    session_id = "test_debounce"
    
    # Simula envio de duas mensagens rápidas com janela de 0.2s
    task1 = asyncio.create_task(store.buffer_message(session_id, "Oi,", buffer_seconds=0.2))
    await asyncio.sleep(0.05)
    task2 = asyncio.create_task(store.buffer_message(session_id, "tudo bem?", buffer_seconds=0.2))
    
    res1, res2 = await asyncio.gather(task1, task2)
    # Apenas a última tarefa consolida o texto unificado
    consolidated = res1 or res2
    assert consolidated == "Oi, tudo bem?"
