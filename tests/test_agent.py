import pytest
from unittest.mock import AsyncMock, MagicMock
from src.agent.agent import Agent
from src.agent.tools import TOOL_DEFINITIONS, execute_tool
from src.memory.session_store import SessionStore

def test_tool_definitions_validity():
    assert len(TOOL_DEFINITIONS) == 5
    names = [t["function"]["name"] for t in TOOL_DEFINITIONS]
    assert "consultar_catalogo" in names
    assert "consultar_detalhes_produto" in names
    assert "consultar_status_pedido" in names
    assert "consultar_politicas" in names
    assert "solicitar_atendimento_humano" in names

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
