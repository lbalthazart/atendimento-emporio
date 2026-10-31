import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from src.agent.agent import get_agent
from src.agent.openrouter_client import get_openrouter_client
from src.config import BASE_DIR, settings
from src.database.loader import init_database
from src.memory.session_store import get_session_store
from src.security import verify_api_security, create_access_token

# Configuração de logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("emporio_api")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa banco SQLite e recursos na inicialização do servidor."""
    logger.info("Iniciando Empório da Música - Agente de Atendimento...")
    init_database()
    logger.info("Banco de dados SQLite verificado e pronto.")
    yield
    logger.info("Encerrando aplicação.")

app = FastAPI(
    title="Empório da Música - API de Atendimento Inteligente",
    description="API RESTful e Agente de Atendimento ao Cliente para a loja Empório da Música (Campo Grande/MS).",
    version="1.0.0",
    lifespan=lifespan
)

# CORS liberado para permitir conexões de frontends externos, widgets e webhooks
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware de Cabeçalhos de Segurança (OWASP)
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# Templates
templates_dir = BASE_DIR / "src" / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Schemas Pydantic
class ChatRequest(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Identificador da sessão ou telefone do cliente")
    message: str = Field(..., description="Texto da mensagem enviada pelo cliente")
    debounce: bool = Field(default=False, description="Se ativo, aguarda janela de agrupamento de mensagens rápidas (3s)")

class ChatResponse(BaseModel):
    session_id: str
    reply: str
    tools_used: List[str]
    handoff_required: bool
    support_message: Optional[str] = None

# --- ROTAS PRINCIPAIS ---

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Interface Web de Atendimento ao Cliente embutida."""
    return templates.TemplateResponse(request=request, name="index.html")

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest, _authorized: bool = Depends(verify_api_security)):
    """
    Endpoint principal de envio de mensagens para o Agente.
    Compatível com integrações de sites, WhatsApp (Evolution API, Z-API) e bots omnichannel.
    """
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="A mensagem não pode estar vazia.")

    agent = get_agent()
    store = get_session_store()
    target_text = payload.message

    # Agrupamento de mensagens (Debounce) opcional
    if payload.debounce:
        buffered = await store.buffer_message(payload.session_id, payload.message, buffer_seconds=settings.MESSAGE_BUFFER_SECONDS)
        if not buffered:
            # Mensagem ainda aguardando a janela de debounce consolidar
            return ChatResponse(
                session_id=payload.session_id,
                reply="...",
                tools_used=[],
                handoff_required=False,
                support_message="Mensagem em buffer aguardando consolidação."
            )
        target_text = buffered

    result = await agent.process_message(
        session_id=payload.session_id,
        user_message=target_text
    )

    return ChatResponse(
        session_id=result["session_id"],
        reply=result["reply"],
        tools_used=result["tools_used"],
        handoff_required=result["handoff_required"],
        support_message=result.get("support_message")
    )

@app.post("/api/media", response_model=ChatResponse)
async def media_endpoint(
    file: UploadFile = File(...),
    session_id: str = Form(default_factory=lambda: str(uuid.uuid4())),
    message: Optional[str] = Form(None)
):
    """
    Endpoint multimodal para envio de fotos de instrumentos ou mensagens de voz.
    - Imagens: são analisadas visualmente com LLM de visão (OpenRouter Vision).
    - Áudios: são encaminhados com prompt contextualizado.
    """
    content = await file.read()
    client = get_openrouter_client()
    agent = get_agent()

    if file.content_type and file.content_type.startswith("image/"):
        logger.info(f"Processando imagem ({file.filename}) para a sessão {session_id}...")
        image_analysis = await client.analyze_image(
            image_bytes=content,
            mime_type=file.content_type,
            prompt="Identifique o instrumento musical da foto, marca visível, tipo de cordas e condição aparente para atendimento."
        )
        combined_text = f"[Foto do instrumento anexada: {image_analysis}]"
        if message and message.strip():
            combined_text += f"\nPergunta do cliente: {message.strip()}"
        else:
            combined_text += "\nPergunta do cliente: Vocês vendem ou têm disponível instrumentos desse modelo ou similares no catálogo?"

        result = await agent.process_message(session_id=session_id, user_message=combined_text)
        return ChatResponse(
            session_id=result["session_id"],
            reply=result["reply"],
            tools_used=result["tools_used"],
            handoff_required=result["handoff_required"],
            support_message=result.get("support_message")
        )

    else:
        # Formato de arquivo genérico ou áudio
        text_prompt = message or f"[Arquivo de mídia recebido: {file.filename}]"
        result = await agent.process_message(session_id=session_id, user_message=text_prompt)
        return ChatResponse(
            session_id=result["session_id"],
            reply=result["reply"],
            tools_used=result["tools_used"],
            handoff_required=result["handoff_required"],
            support_message=result.get("support_message")
        )

@app.get("/api/history/{session_id}")
async def get_history(session_id: str):
    """Recupera histórico da conversa do cliente respeitando a política de retenção de 7 dias (LGPD)."""
    store = get_session_store()
    messages = store.get_messages(session_id)
    return {
        "session_id": session_id,
        "total_messages": len(messages),
        "history": messages
    }

@app.delete("/api/history/{session_id}")
async def delete_history(session_id: str):
    """Exclui imediatamente todos os dados da sessão (Direito ao Esquecimento - Art. 18 LGPD)."""
    store = get_session_store()
    deleted = store.delete_session(session_id)
    return {
        "session_id": session_id,
        "deleted": deleted,
        "message": "Dados de atendimento expurgados com sucesso conforme a LGPD." if deleted else "Sessão não encontrada ou já expirada."
    }

class TokenRequest(BaseModel):
    client_id: str = Field(..., description="ID da aplicação, bot do WhatsApp ou sessão")
    secret_key: Optional[str] = Field(None, description="Chave mestra da API (se configurada no servidor)")

@app.post("/api/auth/token")
async def issue_token(payload: TokenRequest):
    """Emite um token JWT de segurança para bots de mensageria e integrações externas."""
    if settings.API_SECRET_KEY and payload.secret_key != settings.API_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Chave secreta de autenticação inválida.")
    token = create_access_token(data={"sub": payload.client_id})
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in_hours": settings.JWT_EXPIRATION_HOURS
    }

@app.get("/api/security/policies")
async def security_policies():
    """Declaração pública de conformidade LGPD, segurança e política de cookies."""
    return {
        "lgpd_compliance": True,
        "data_retention_ttl_days": settings.HISTORY_TTL_DAYS,
        "right_to_be_forgotten": True,
        "rate_limit_per_minute": settings.RATE_LIMIT_PER_MINUTE,
        "cookie_policy": {
            "essential_storage_only": True,
            "tracking_cookies": False,
            "storage_type": "localStorage (apenas session_id e consentimento)"
        },
        "store_info": {
            "name": "Empório da Música",
            "city": "Campo Grande - MS",
            "address": "Rua 14 de Maio, 3200",
            "phone": "(67) 3341-4444",
            "whatsapp": "(67) 3321-4500"
        }
    }

@app.get("/health")
async def health_check():
    """Checagem de integridade do serviço e configuração."""
    has_api_key = bool(settings.OPENROUTER_API_KEY)
    db_ok = settings.DATABASE_PATH.exists()
    return {
        "status": "healthy",
        "store": "Empório da Música",
        "openrouter_configured": has_api_key,
        "model": settings.LLM_MODEL,
        "database_ready": db_ok,
        "lgpd_ttl_days": settings.HISTORY_TTL_DAYS
    }
