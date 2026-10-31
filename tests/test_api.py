import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["store"] == "Empório da Música"
    assert data["database_ready"] is True

def test_home_page_renders_html():
    response = client.get("/")
    assert response.status_code == 200
    assert "Empório da Música" in response.text
    assert "LGPD" in response.text

@patch("src.agent.agent.OpenRouterClient.chat_completion")
def test_chat_endpoint_success(mock_chat):
    mock_chat.return_value = {
        "role": "assistant",
        "content": "Olá! Temos violões Yamaha a partir de R$ 599,90. Posso te ajudar com algum modelo específico?",
        "tool_calls": None
    }

    payload = {
        "session_id": "test_api_session",
        "message": "Quais violões vocês têm?"
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test_api_session"
    assert "violões Yamaha" in data["reply"]
    assert data["handoff_required"] is False

def test_chat_endpoint_empty_message():
    response = client.post("/api/chat", json={"session_id": "s1", "message": "   "})
    assert response.status_code == 400

def test_history_and_delete_lgpd():
    session_id = "test_history_lgpd"
    
    # Adiciona mensagem direta no session store
    from src.memory.session_store import get_session_store
    store = get_session_store()
    store.add_message(session_id, "user", "Mensagem de teste")
    
    # Consulta histórico
    get_res = client.get(f"/api/history/{session_id}")
    assert get_res.status_code == 200
    assert get_res.json()["total_messages"] >= 1
    
    # Exclui via LGPD (Direito ao esquecimento)
    del_res = client.delete(f"/api/history/{session_id}")
    assert del_res.status_code == 200
    assert del_res.json()["deleted"] is True
    
    # Confirma que foi excluído
    get_res2 = client.get(f"/api/history/{session_id}")
    assert get_res2.json()["total_messages"] == 0
