from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

class Settings(BaseSettings):
    """Configurações centrais da aplicação."""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Provedor e Chaves
    LLM_PROVIDER: str = "openrouter"
    OPENROUTER_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # Modelos
    LLM_MODEL: str = "openai/gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.2
    VISION_MODEL: str = "openai/gpt-4o-mini"

    # Base URL
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    # LGPD e Memória
    HISTORY_TTL_DAYS: int = 7
    MESSAGE_BUFFER_SECONDS: float = 3.0

    # Banco de Dados
    DATABASE_PATH: Path = BASE_DIR / "data" / "emporio.sqlite3"

    # Servidor
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False

settings = Settings()
