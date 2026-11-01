import json
import logging
import re
from typing import Any, Dict, List, Optional

from src.agent.openrouter_client import OpenRouterClient, get_openrouter_client
from src.agent.prompts import SYSTEM_PROMPT
from src.agent.tools import TOOL_DEFINITIONS, execute_tool
from src.config import settings
from src.memory.session_store import SessionStore, get_session_store

logger = logging.getLogger(__name__)

EN_WORDS = {
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "i", "it", "for", "not", "on", "with", "he",
    "as", "you", "do", "at", "this", "but", "his", "by", "from", "they", "we", "say", "her", "she", "or",
    "an", "will", "my", "one", "all", "would", "there", "their", "what", "so", "up", "out", "if", "about",
    "who", "get", "which", "go", "me", "when", "make", "can", "like", "time", "no", "just", "him", "know",
    "take", "into", "your", "good", "some", "could", "them", "see", "other", "than", "then", "now", "look",
    "only", "come", "its", "over", "think", "also", "back", "after", "use", "how", "our", "work", "well",
    "way", "even", "new", "want", "because", "any", "these", "give", "most", "us", "is", "are", "am",
    "was", "were", "been", "being", "has", "had", "did", "does", "having", "hi", "hello", "hey", "please",
    "thank", "thanks", "price", "cost", "buy", "guitar", "guitars", "drum", "drums", "bass", "acoustic",
    "electric", "store", "shop", "address", "ship", "shipping", "delivery", "order", "return", "refund",
    "discount", "promotion", "promotions", "clearance", "stock", "available", "cheapest", "expensive", "best",
    "tell", "find", "show", "much", "many", "cheap"
}

PT_WORDS = {
    "o", "a", "os", "as", "um", "uma", "uns", "umas", "de", "da", "do", "das", "dos", "em", "na", "no",
    "nas", "nos", "por", "para", "com", "sem", "sob", "sobre", "e", "ou", "mas", "que", "se", "como",
    "quando", "onde", "quem", "qual", "quais", "quanto", "quanta", "quantos", "quantas", "você", "voce",
    "vocês", "voces", "ele", "ela", "eles", "elas", "nós", "nos", "eu", "meu", "minha", "meus", "minhas",
    "seu", "sua", "seus", "suas", "nosso", "nossa", "é", "e", "são", "sao", "era", "eram", "foi", "foram",
    "ser", "estar", "está", "esta", "estão", "estao", "ter", "tem", "têm", "tinha", "haver", "há", "ha",
    "loja", "violão", "violao", "violões", "violoes", "guitarra", "guitarras", "bateria", "baterias",
    "teclado", "teclados", "instrumento", "instrumentos", "preço", "preco", "promoção", "promocao",
    "promoções", "promocoes", "desconto", "frete", "entrega", "devolução", "devolucao", "pedido",
    "rastreio", "estoque", "parcelamento", "cartão", "cartao", "pix", "boleto", "gostaria", "quero",
    "ajuda", "favor", "obrigado", "obrigada", "olá", "ola", "oi", "opa", "bom", "boa", "tarde", "noite",
    "dia", "mais", "menos", "barato", "caro"
}

def get_language_directive(text: str) -> str:
    """
    Detecta se o usuário está se comunicando em inglês ou espanhol para aplicar
    Language Mirroring estrito, garantindo respostas no idioma do interlocutor.
    """
    clean_text = text.strip().lower()
    if "pergunta do cliente:" in clean_text:
        clean_text = clean_text.split("pergunta do cliente:")[-1].strip()
    if clean_text in {"hi", "hello", "hey", "good morning", "good afternoon"}:
        return (
            "\n\n======================================================\n"
            "CRITICAL OVERRIDE: THE CURRENT USER IS SPEAKING IN ENGLISH!\n"
            "- You MUST formulate your entire response in 100% natural, fluent English.\n"
            "- Even if previous messages in the conversation history were in Portuguese, SWITCH TO ENGLISH NOW.\n"
            "- Even if database tool results are in Portuguese, translate everything into English.\n"
            "- Keep Brazilian Real currency (R$), store policies, and official contact phone numbers intact.\n"
            "======================================================\n"
        )

    words = set(re.findall(r"\b[a-zA-ZáéíóúâêîôûãõçÁÉÍÓÚÂÊÎÔÛÃÕÇ]+\b", clean_text))
    en_score = len(words & EN_WORDS)
    pt_score = len(words & PT_WORDS)

    if en_score > pt_score or any(clean_text.startswith(p) for p in ["hello", "hi ", "hey "]):
        return (
            "\n\n======================================================\n"
            "CRITICAL OVERRIDE: THE CURRENT USER IS SPEAKING IN ENGLISH!\n"
            "- You MUST formulate your entire response in 100% natural, fluent English.\n"
            "- Even if previous messages in the conversation history were in Portuguese, SWITCH TO ENGLISH NOW.\n"
            "- Even if database tool results are in Portuguese, translate everything into English.\n"
            "- Keep Brazilian Real currency (R$), store policies, and official contact phone numbers intact.\n"
            "======================================================\n"
        )
        
    es_markers = {"hola", "buenos dias", "buenas tardes", "precio", "tienen", "guitarra", "guitarras", "envio", "cuanto", "donde"}
    if len(words & es_markers) >= 2 or clean_text.startswith("hola"):
        return (
            "\n\n======================================================\n"
            "CRITICAL OVERRIDE: THE CURRENT USER IS SPEAKING IN SPANISH!\n"
            "- El cliente se está comunicando en ESPAÑOL. Toda tu resposta DEBE formularse en español fluido y natural.\n"
            "- Traduce descripciones del catálogo y detalles de la tienda al español, manteniendo los precios en Reales (R$).\n"
            "======================================================\n"
        )

    return ""

def sanitize_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Higieniza a sequencia de mensagens para conformidade com regras da OpenAI/OpenRouter
    e suporta multiplas tool_calls em paralelo na mesma rodada ReAct.
    """
    sanitized: List[Dict[str, Any]] = []
    
    for msg in messages:
        role = msg.get("role")
        
        if role == "tool":
            if not sanitized:
                logger.warning("Descartando mensagem tool no inicio do historico.")
                continue

            originating_assistant = None
            for prev_msg in reversed(sanitized):
                if prev_msg.get("role") == "assistant":
                    originating_assistant = prev_msg
                    break
                elif prev_msg.get("role") != "tool":
                    break

            if not originating_assistant or not originating_assistant.get("tool_calls"):
                logger.warning(f"Descartando mensagem tool orfa: {msg}")
                continue

            valid_ids = [tc.get("id") for tc in originating_assistant.get("tool_calls", [])]
            if msg.get("tool_call_id") not in valid_ids:
                logger.warning(f"Descartando mensagem tool com call_id invalido: {msg.get('tool_call_id')}")
                continue

        sanitized.append(msg)
        
    return sanitized

class Agent:
    """
    Agente Autônomo de Atendimento da Empório da Música.
    
    Gerencia o ciclo de raciocínio ReAct / Function Calling:
    1. Recupera histórico recente de diálogo (mantendo apenas mensagens de texto limpas).
    2. Envia para a LLM junto com as ferramentas disponíveis.
    3. Executa as chamadas de ferramentas solicitadas (consulta SQL / políticas).
    4. Devolve o contexto para a LLM sintetizar a resposta final natural.
    5. Possui tolerância a falhas e fallbacks automáticos se o provedor oscilar.
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

        # 3. Prepara histórico limpo de conversação (apenas user e assistant final)
        history = self.session_store.get_messages(session_id, max_history=12, include_tools=False)
        lang_directive = get_language_directive(user_message)
        messages: List[Dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT + lang_directive}] + history

        tools_used: List[str] = []
        handoff_required = False
        support_note = None

        # 4. Loop de Execução de Ferramentas (ReAct / Tool Calling)
        for iteration in range(self.max_iterations):
            # Higienização de mensagens para prevenir erros 400 da API
            clean_messages = sanitize_messages(messages)

            response_msg = await self.client.chat_completion(
                messages=clean_messages,
                tools=TOOL_DEFINITIONS
            )

            tool_calls = response_msg.get("tool_calls")
            content = response_msg.get("content")

            # Se a LLM respondeu com a mensagem de contingência/indisponibilidade
            if content == settings.DEFAULT_UNAVAILABLE_MESSAGE:
                return {
                    "session_id": session_id,
                    "reply": content,
                    "tools_used": list(set(tools_used)),
                    "handoff_required": True,
                    "support_message": "Instabilidade técnica em todos os provedores de IA."
                }

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

            # A LLM solicitou a execução de uma ou mais ferramentas na rodada atual
            messages.append(response_msg)

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

        # Se ultrapassou o limite de iterações sem resposta final
        fallback_reply = (
            "Consultei os dados necessários aqui na loja, mas demorou um pouco para consolidar a resposta. "
            "Poderia me dizer especificamente qual modelo ou dúvida você gostaria de ver agora? 🎸"
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
