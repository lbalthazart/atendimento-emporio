import json
import logging
from typing import Any, Dict, List, Optional

from src.agent.openrouter_client import OpenRouterClient, get_openrouter_client
from src.agent.prompts import SYSTEM_PROMPT
from src.agent.tools import TOOL_DEFINITIONS, execute_tool
from src.memory.session_store import SessionStore, get_session_store

logger = logging.getLogger(__name__)

class Agent:
    """
    Agente Autônomo de Atendimento da Empório da Música.
    
    Gerencia o ciclo de raciocínio ReAct / Function Calling:
    1. Recupera histórico recente da sessão (respeitando LGPD e TTL de 7 dias).
    2. Envia para a LLM junto com as ferramentas disponíveis.
    3. Executa as chamadas de ferramentas solicitadas (consulta SQL / políticas).
    4. Devolve o contexto para a LLM sintetizar a resposta final natural.
    5. Identifica necessidade de transbordo para atendimento humano.
    """

    def __init__(
        self,
        client: Optional[OpenRouterClient] = None,
        session_store: Optional[SessionStore] = None,
        max_iterations: int = 5
    ):
        self.client = client or get_openrouter_client()
        self.session_store = session_store or get_session_store()
        self.max_iterations = max_iterations

    async def process_message(
        self,
        session_id: str,
        user_message: str
    ) -> Dict[str, Any]:
        """Processa a mensagem do usuário e retorna a resposta gerada pelo agente."""
        
        # 1. Verifica se o atendimento automático está em pausa (transbordo humano ativo)
        if self.session_store.is_paused(session_id):
            return {
                "session_id": session_id,
                "reply": "Seu atendimento foi transferido para um de nossos atendentes humanos da Empório da Música. Em instantes um operador continuará a conversa com você!",
                "tools_used": [],
                "handoff_required": True,
                "support_message": "Sessão sob atendimento humano (IA pausada)."
            }

        # 2. Registra a mensagem do usuário no histórico
        self.session_store.add_message(session_id, role="user", content=user_message)

        # 3. Prepara a lista de mensagens para envio à LLM
        history = self.session_store.get_messages(session_id, max_history=15)
        messages: List[Dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}] + history

        tools_used: List[str] = []
        handoff_required = False
        support_note = None

        # 4. Loop de Execução de Ferramentas (ReAct / Tool Calling)
        for iteration in range(self.max_iterations):
            response_msg = await self.client.chat_completion(
                messages=messages,
                tools=TOOL_DEFINITIONS
            )

            tool_calls = response_msg.get("tool_calls")
            content = response_msg.get("content")

            # Se a LLM não solicitou ferramentas, chegamos na resposta final
            if not tool_calls:
                final_reply = content or "Desculpe, como posso ajudar você com os instrumentos da Empório da Música?"
                self.session_store.add_message(session_id, role="assistant", content=final_reply)
                return {
                    "session_id": session_id,
                    "reply": final_reply,
                    "tools_used": list(set(tools_used)),
                    "handoff_required": handoff_required,
                    "support_message": support_note
                }

            # A LLM solicitou a execução de uma ou mais ferramentas
            messages.append(response_msg)
            # Salva no histórico a intenção de chamada de ferramenta
            self.session_store.add_message(
                session_id,
                role="assistant",
                content=content or "",
                tool_calls=tool_calls
            )

            for tc in tool_calls:
                fn_name = tc.get("function", {}).get("name")
                call_id = tc.get("id", "call_default")
                args_raw = tc.get("function", {}).get("arguments", "{}")

                try:
                    args = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
                except Exception:
                    args = {}

                tools_used.append(fn_name)
                logger.info(f"Executando ferramenta '{fn_name}' com argumentos: {args}")

                # Execução da ferramenta
                tool_result = execute_tool(fn_name, args)

                # Detecção de transbordo humano
                if fn_name == "solicitar_atendimento_humano":
                    handoff_required = True
                    support_note = f"Transbordo acionado: {args.get('motivo')} - {args.get('resumo')}"
                    self.session_store.pause_ia(session_id, duration_seconds=600)

                result_str = json.dumps(tool_result, ensure_ascii=False)
                tool_msg = {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "name": fn_name,
                    "content": result_str
                }
                messages.append(tool_msg)
                self.session_store.add_message(
                    session_id,
                    role="tool",
                    content=result_str,
                    tool_call_id=call_id,
                    name=fn_name
                )

        # Se ultrapassou o limite de iterações sem resposta final
        fallback_reply = (
            "Consultei os dados necessários, mas o sistema demorou a sintetizar a resposta. "
            "Poderia repetir a pergunta de forma mais específica?"
        )
        self.session_store.add_message(session_id, role="assistant", content=fallback_reply)
        return {
            "session_id": session_id,
            "reply": fallback_reply,
            "tools_used": list(set(tools_used)),
            "handoff_required": handoff_required,
            "support_message": support_note
        }

_global_agent: Optional[Agent] = None

def get_agent() -> Agent:
    """Retorna singleton do agente."""
    global _global_agent
    if _global_agent is None:
        _global_agent = Agent()
    return _global_agent
