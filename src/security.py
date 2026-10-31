import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import jwt
from fastapi import Header, HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.config import settings

security_scheme = HTTPBearer(auto_error=False)

# In-memory sliding window rate limiter
_request_history: Dict[str, List[float]] = defaultdict(list)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Gera um token JWT assinado para autenticação de clientes ou canais."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    secret = settings.API_SECRET_KEY or settings.JWT_SECRET_KEY
    return jwt.encode(to_encode, secret, algorithm=settings.JWT_ALGORITHM)

def decode_access_token(token: str) -> Optional[dict]:
    """Decodifica e valida o token JWT."""
    try:
        secret = settings.API_SECRET_KEY or settings.JWT_SECRET_KEY
        payload = jwt.decode(token, secret, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except (jwt.PyJWTError, Exception):
        return None

def check_rate_limit(client_id: str, limit_per_minute: int = 60) -> None:
    """Verifica se o cliente ultrapassou o limite de requisições por minuto."""
    now = time.time()
    one_minute_ago = now - 60.0

    # Purga timestamps antigos
    history = [t for t in _request_history[client_id] if t > one_minute_ago]
    history.append(now)
    _request_history[client_id] = history

    if len(history) > limit_per_minute:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                "Limite de requisições excedido. Para proteger a estabilidade do serviço, "
                "por favor aguarde alguns instantes antes de enviar novas mensagens."
            )
        )

async def verify_api_security(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> bool:
    """
    Middleware/Dependência de verificação de autenticação:
    - Se API_SECRET_KEY não estiver configurada no .env: modo de desenvolvimento livre (acesso permitido).
    - Se API_SECRET_KEY estiver configurada: exige X-API-Key válido ou Bearer JWT válido.
    """
    # 1. Verifica Rate Limiter por IP / Session
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(client_ip, limit_per_minute=settings.RATE_LIMIT_PER_MINUTE)

    # 2. Se não há chave secreta configurada no servidor, opera em modo público/aberto
    if not settings.API_SECRET_KEY:
        return True

    # 3. Validação por X-API-Key direto
    if x_api_key and x_api_key == settings.API_SECRET_KEY:
        return True

    # 4. Validação por Bearer Token (JWT ou Secret)
    if credentials and credentials.scheme.lower() == "bearer":
        token = credentials.credentials
        if token == settings.API_SECRET_KEY:
            return True
        payload = decode_access_token(token)
        if payload is not None:
            return True

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Acesso não autorizado. Informe um cabeçalho 'X-API-Key' válido ou token 'Authorization: Bearer <token>'.",
        headers={"WWW-Authenticate": "Bearer"}
    )
