"""Módulo de gestão de sessões, memória e conformidade com a LGPD."""

from src.memory.session_store import SessionStore, get_session_store

__all__ = ["SessionStore", "get_session_store"]
