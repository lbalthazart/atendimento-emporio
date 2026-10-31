import base64
import json
import logging
from typing import Any, Dict, List, Optional
import httpx

from src.config import settings

logger = logging.getLogger(__name__)

class OpenRouterClient:
    """Cliente assíncrono para a API unificada do OpenRouter."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None
    ):
        self.api_key = api_key or settings.OPENROUTER_API_KEY
        self.base_url = (base_url or settings.OPENROUTER_BASE_URL).rstrip("/")
        self.default_model = default_model or settings.LLM_MODEL

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/lbalthazart/atendimento-emporio",
            "X-Title": "Emporio da Musica - Atendimento",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Executa chamada de chat completion com suporte a Function Calling / Tool Use.
        Retorna o dicionário com a mensagem de resposta da LLM.
        """
        if not self.api_key:
            # Fallback amigável caso o usuário ainda não tenha configurado a chave
            return {
                "role": "assistant",
                "content": (
                    "⚠️ [Modo de Demonstração]: A chave `OPENROUTER_API_KEY` ainda não foi configurada no `.env`. "
                    "Por favor, configure sua chave do OpenRouter para ativar as respostas dinâmicas com IA."
                )
            }

        payload: Dict[str, Any] = {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature if temperature is not None else settings.LLM_TEMPERATURE
        }

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        url = f"{self.base_url}/chat/completions"

        async with httpx.AsyncClient(timeout=45.0) as client:
            try:
                response = await client.post(url, json=payload, headers=self._get_headers())
                response.raise_for_status()
                data = response.json()
                choice = data["choices"][0]
                return choice["message"]
            except httpx.HTTPStatusError as e:
                logger.error(f"Erro HTTP do OpenRouter: {e.response.status_code} - {e.response.text}")
                error_detail = e.response.text
                return {
                    "role": "assistant",
                    "content": f"Desculpe, ocorreu uma instabilidade na comunicação com o provedor de IA ({e.response.status_code}). Detalhes: {error_detail}"
                }
            except Exception as e:
                logger.error(f"Exceção ao chamar OpenRouter: {str(e)}")
                return {
                    "role": "assistant",
                    "content": f"Desculpe, não consegui processar sua solicitação no momento. Erro interno: {str(e)}"
                }

    async def analyze_image(self, image_bytes: bytes, mime_type: str = "image/jpeg", prompt: str = "Descreva este instrumento musical em detalhes para o atendimento ao cliente.") -> str:
        """Analisa uma imagem de instrumento musical enviada pelo cliente usando visão computacional."""
        if not self.api_key:
            return "Imagem recebida (análise visual desabilitada sem OPENROUTER_API_KEY)."

        b64 = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:{mime_type};base64,{b64}"

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}}
                ]
            }
        ]

        payload = {
            "model": settings.VISION_MODEL,
            "messages": messages,
            "temperature": 0.2
        }

        url = f"{self.base_url}/chat/completions"

        async with httpx.AsyncClient(timeout=45.0) as client:
            try:
                response = await client.post(url, json=payload, headers=self._get_headers())
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except Exception as e:
                logger.error(f"Erro na análise de imagem: {str(e)}")
                return f"Não foi possível analisar a imagem: {str(e)}"

_default_client: Optional[OpenRouterClient] = None

def get_openrouter_client() -> OpenRouterClient:
    """Retorna singleton do cliente OpenRouter."""
    global _default_client
    if _default_client is None:
        _default_client = OpenRouterClient()
    return _default_client
