import pytest
from unittest.mock import AsyncMock, MagicMock
from src.agent.agent import Agent
from src.agent.tools import TOOL_DEFINITIONS, execute_tool
from src.memory.session_store import SessionStore

def test_tool_definitions_validity():
    assert len(TOOL_DEFINITIONS) == 6
    names = [t["function"]["name"] for t in TOOL_DEFINITIONS]
    assert "consultar_catalogo" in names
    assert "consultar_promocoes_ativas" in names
    assert "consultar_detalhes_produto" in names
    assert "consultar_status_pedido" in names
    assert "consultar_politicas" in names
    assert "solicitar_atendimento_humano" in names

def test_execute_tool_promocoes():
    res = execute_tool("consultar_promocoes_ativas", {})
    assert res["total_promocoes"] >= 1
    promo = res["promocoes"][0]
    assert "promo_description" in promo
    assert "discount_percent" in promo
    assert promo["discounted_price"] < promo["price_brl"]

def test_execute_tool_pedido_sem_id_bloqueado():
    res = execute_tool("consultar_status_pedido", {"identificador_cliente": "Ana Carolina"})
    assert res["found"] is False
    assert "obrigatório" in res["message"]

def test_execute_tool_catalogo():
    res = execute_tool("consultar_catalogo", {"termo": "Yamaha C40", "preco_maximo": 1000.0})
    assert res["total_encontrado"] >= 1
    prod = res["produtos"][0]
    assert "Yamaha" in prod["name"]
    assert prod["price_brl"] <= 1000.0

def test_execute_tool_politicas():
    res = execute_tool("consultar_politicas", {"topico": "devolução arrependimento"})
    assert "resultado_politica" in res
    assert "7 (SETE) DIAS CORRIDOS" in res["resultado_politica"]

def test_execute_tool_pedido():
    res = execute_tool("consultar_status_pedido", {"id_pedido": 1})
    assert res["found"] is True
    assert res["order_id"] == 1
    assert "status" in res

def test_execute_tool_transbordo():
    res = execute_tool("solicitar_atendimento_humano", {"motivo": "cliente_irritado", "resumo": "Deseja cancelamento urgente"})
    assert res["transbordo_acionado"] is True

@pytest.mark.asyncio
async def test_agent_tool_calling_loop():
    session_store = SessionStore(ttl_days=7)
    mock_client = MagicMock()

    # Simula primeira resposta da LLM chamando a ferramenta 'consultar_catalogo'
    # e na segunda resposta trazendo o texto final formatado
    mock_client.chat_completion = AsyncMock(side_effect=[
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_123",
                    "function": {
                        "name": "consultar_catalogo",
                        "arguments": '{"termo": "Takamine GD20"}'
                    }
                }
            ]
        },
        {
            "role": "assistant",
            "content": "O Takamine GD20 custa R$ 2.199,00 e no PIX sai por R$ 2.089,05 com 5% de desconto!",
            "tool_calls": None
        }
    ])

    agent = Agent(client=mock_client, session_store=session_store)
    result = await agent.process_message(
        session_id="session_test_agent",
        user_message="Quanto custa o Takamine GD20?"
    )

    assert result["session_id"] == "session_test_agent"
    assert "Takamine GD20 custa R$ 2.199,00" in result["reply"]
    assert "consultar_catalogo" in result["tools_used"]
    assert result["handoff_required"] is False
    assert mock_client.chat_completion.call_count == 2


def test_sanitize_messages_removes_orphan_tools():
    from src.agent.agent import sanitize_messages
    
    dirty_messages = [
        {"role": "system", "content": "Prompt do sistema"},
        {"role": "tool", "content": "resultado órfão", "tool_call_id": "call_orphan"},  # Órfã -> deve ser removida
        {"role": "user", "content": "Olá"},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [{"id": "call_valid", "function": {"name": "test"}}]
        },
        {"role": "tool", "content": "resultado válido", "tool_call_id": "call_valid"},  # Válida -> deve ser mantida
        {"role": "assistant", "content": "Resposta final"}
    ]
    
    clean = sanitize_messages(dirty_messages)
    assert len(clean) == 5
    assert clean[0]["role"] == "system"
    assert clean[1]["role"] == "user"
    assert clean[2]["role"] == "assistant"
    assert clean[3]["role"] == "tool"
    assert clean[4]["role"] == "assistant"

@pytest.mark.asyncio
async def test_openrouter_fallback_on_error():
    from src.agent.openrouter_client import OpenRouterClient
    from unittest.mock import patch, MagicMock
    import httpx

    client = OpenRouterClient(api_key="test_key")

    # Simula primeira chamada falhando com HTTPStatusError e segunda tendo sucesso
    with patch("httpx.AsyncClient.post") as mock_post:
        resp_fail = MagicMock()
        resp_fail.raise_for_status.side_effect = httpx.HTTPStatusError("Erro 400", request=MagicMock(), response=MagicMock(status_code=400, text="Invalid param"))

        resp_ok = MagicMock()
        resp_ok.raise_for_status.return_value = None
        resp_ok.json.return_value = {
            "choices": [{"message": {"role": "assistant", "content": "Resposta do modelo de contingência!"}}]
        }

        mock_post.side_effect = [resp_fail, resp_ok]

        res = await client.chat_completion(messages=[{"role": "user", "content": "Teste"}])
        assert res["content"] == "Resposta do modelo de contingência!"
        assert mock_post.call_count == 2
