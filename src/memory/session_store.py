import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.config import settings

@dataclass
class Message:
    role: str
    content: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None

@dataclass
class Session:
    session_id: str
    messages: List[Message] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    is_human_paused: bool = False
    paused_until: float = 0.0
    buffer: List[str] = field(default_factory=list)
    last_message_time: float = 0.0

class SessionStore:
    """
    Gerenciador de sessões e memória de atendimento com conformidade à LGPD.
    
    Características:
    - Retenção estrita por 7 dias (expira sessões inativas automaticamente).
    - Direito ao esquecimento (exclusão sob demanda via DELETE).
    - Mecanismo de Buffer/Debounce para mensagens rápidas sequenciais.
    - Suporte a pausa temporária de IA (Transbordo Humano).
    """

    def __init__(self, ttl_days: int = 7):
        self.ttl_seconds = ttl_days * 86400
        self._sessions: Dict[str, Session] = {}
        self._lock = asyncio.Lock()

    def _is_expired(self, session: Session) -> bool:
        """Verifica se a sessão ultrapassou o período de retenção da LGPD."""
        return (time.time() - session.updated_at) > self.ttl_seconds

    def purge_expired(self) -> int:
        """Varre e remove todas as sessões expiradas conforme a regra de 7 dias."""
        now = time.time()
        expired_keys = [
            sid for sid, s in self._sessions.items()
            if (now - s.updated_at) > self.ttl_seconds
        ]
        for sid in expired_keys:
            del self._sessions[sid]
        return len(expired_keys)

    def get_or_create_session(self, session_id: str) -> Session:
        """Obtém sessão ativa ou cria uma nova, expurgando dados expirados se houver."""
        self.purge_expired()
        session = self._sessions.get(session_id)
        if session is None or self._is_expired(session):
            session = Session(session_id=session_id)
            self._sessions[session_id] = session
        return session

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        tool_call_id: Optional[str] = None,
        name: Optional[str] = None
    ) -> Message:
        """Adiciona uma mensagem ao histórico da sessão e atualiza o timestamp."""
        session = self.get_or_create_session(session_id)
        msg = Message(
            role=role,
            content=content,
            tool_calls=tool_calls,
            tool_call_id=tool_call_id,
            name=name
        )
        session.messages.append(msg)
        session.updated_at = time.time()
        return msg

    def get_messages(self, session_id: str, max_history: int = 20, include_tools: bool = False) -> List[Dict[str, Any]]:
        """
        Retorna histórico recente formatado para consumo pela LLM.
        Por padrão, filtra mensagens intermediárias de ferramentas para manter o histórico
        limpo, fluido e livre de erros de validação de mensagens 'tool' órfãs.
        """
        session = self.get_or_create_session(session_id)
        
        if include_tools:
            source = session.messages
        else:
            # Mantém apenas as mensagens de diálogo final (user e assistant com conteúdo de texto)
            source = [m for m in session.messages if m.role in ("user", "system") or (m.role == "assistant" and m.content)]

        recent = source[-max_history:] if len(source) > max_history else source
        output = []
        for m in recent:
            item: Dict[str, Any] = {"role": m.role, "content": m.content}
            if include_tools and m.tool_calls:
                item["tool_calls"] = m.tool_calls
            if include_tools and m.tool_call_id:
                item["tool_call_id"] = m.tool_call_id
            if include_tools and m.name:
                item["name"] = m.name
            output.append(item)
        return output

    def delete_session(self, session_id: str) -> bool:
        """Remove imediatamente todos os dados da sessão (Direito ao Esquecimento - LGPD)."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def pause_ia(self, session_id: str, duration_seconds: int = 600) -> None:
        """Pausa o atendimento da IA para permitir transbordo a atendente humano."""
        session = self.get_or_create_session(session_id)
        session.is_human_paused = True
        session.paused_until = time.time() + duration_seconds

    def is_paused(self, session_id: str) -> bool:
        """Verifica se a IA está pausada para esta sessão."""
        session = self._sessions.get(session_id)
        if not session or not session.is_human_paused:
            return False
        if time.time() > session.paused_until:
            session.is_human_paused = False
            return False
        return True

    def unpause_ia(self, session_id: str) -> None:
        """Despausa a IA permitindo que retome o atendimento."""
        session = self.get_or_create_session(session_id)
        session.is_human_paused = False
        session.paused_until = 0.0

    async def buffer_message(self, session_id: str, text: str, buffer_seconds: float = 3.0) -> Optional[str]:
        """
        Acumula mensagens enviadas rapidamente em sequência (Debounce).
        Retorna a mensagem unificada apenas quando a janela de tempo expirar.
        """
        async with self._lock:
            session = self.get_or_create_session(session_id)
            session.buffer.append(text.strip())
            session.last_message_time = time.time()

        await asyncio.sleep(buffer_seconds)

        async with self._lock:
            session = self._sessions.get(session_id)
            if not session or not session.buffer:
                return None
            
            # Se uma nova mensagem chegou durante o sleep, deixa a última rodada consolidar
            if (time.time() - session.last_message_time) < (buffer_seconds - 0.2):
                return None

            merged_text = " ".join(session.buffer)
            session.buffer.clear()
            return merged_text

# Singleton global de sessão
_global_store: Optional[SessionStore] = None

def get_session_store() -> SessionStore:
    """Retorna instância singleton do SessionStore."""
    global _global_store
    if _global_store is None:
        _global_store = SessionStore(ttl_days=settings.HISTORY_TTL_DAYS)
    return _global_store
