import base64
import json
import logging
from typing import Any, Dict, List, Optional
import httpx

from src.config import settings

logger = logging.getLogger(__name__)

class OpenRouterClient:
    """Cliente assíncrono para a API unificada do OpenRouter com tolerância a falhas e fallbacks automáticos."""

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
        Possui fallback automático para modelos secundários se o provedor primário falhar.
        Se todos falharem, retorna uma mensagem padrão educada e amigável.
        """
        if not self.api_key:
            return {
                "role": "assistant",
                "content": (
                    "⚠️ [Modo de Demonstração]: A chave `OPENROUTER_API_KEY` ainda não foi configurada no `.env`. "
                    "Por favor, configure sua chave do OpenRouter para ativar as respostas dinâmicas com IA."
                )
            }

        # Lista ordenada de modelos a tentar (Primário -> Fallbacks)
        primary_model = model or self.default_model
        candidate_models = [primary_model]
        for fb in settings.FALLBACK_MODELS:
            if fb not in candidate_models:
                candidate_models.append(fb)

        url = f"{self.base_url}/chat/completions"
        temp = temperature if temperature is not None else settings.LLM_TEMPERATURE

        async with httpx.AsyncClient(timeout=40.0) as client:
            for candidate in candidate_models:
                payload: Dict[str, Any] = {
                    "model": candidate,
                    "messages": messages,
                    "temperature": temp
                }
                if tools:
                    payload["tools"] = tools
                    payload["tool_choice"] = "auto"

                try:
                    logger.info(f"Tentando requisição com modelo: {candidate}")
                    response = await client.post(url, json=payload, headers=self._get_headers())
                    response.raise_for_status()
                    data = response.json()
                    choice = data["choices"][0]
                    return choice["message"]
                except httpx.HTTPStatusError as e:
                    logger.warning(
                        f"Provedor falhou para o modelo {candidate} (HTTP {e.response.status_code}): {e.response.text[:200]}. "
                        "Tentando modelo de contingência..."
                    )
                except Exception as e:
                    logger.warning(f"Exceção ao chamar modelo {candidate}: {str(e)}. Tentando contingência...")

        # Se todos os modelos da cadeia falharam, retorna a mensagem padrão humanizada
        logger.error("Todos os modelos de IA e contingências falharam.")
        return {
            "role": "assistant",
            "content": settings.DEFAULT_UNAVAILABLE_MESSAGE
        }

    async def analyze_image(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        prompt: str = "Descreva este instrumento musical em detalhes para o atendimento ao cliente."
    ) -> str:
        """Analisa imagem com fallback automático para modelo secundário de visão."""
        if not self.api_key:
            return "Imagem recebida (análise visual desabilitada sem OPENROUTER_API_KEY)."

        candidate_vision_models = [settings.VISION_MODEL]
        for fb in settings.VISION_FALLBACK_MODELS:
            if fb not in candidate_vision_models:
                candidate_vision_models.append(fb)

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

        url = f"{self.base_url}/chat/completions"

        async with httpx.AsyncClient(timeout=40.0) as client:
            for candidate in candidate_vision_models:
                payload = {
                    "model": candidate,
                    "messages": messages,
                    "temperature": 0.2
                }
                try:
                    response = await client.post(url, json=payload, headers=self._get_headers())
                    response.raise_for_status()
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                except Exception as e:
                    logger.warning(f"Falha na análise de imagem com modelo {candidate}: {e}. Tentando fallback...")

        return "Não foi possível analisar a imagem no momento. Por favor, descreva o instrumento em texto ou tente enviar novamente."

_default_client: Optional[OpenRouterClient] = None

def get_openrouter_client() -> OpenRouterClient:
    """Retorna singleton do cliente OpenRouter."""
    global _default_client
    if _default_client is None:
        _default_client = OpenRouterClient()
    return _default_client
