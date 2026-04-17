"""Configuration de l'application via variables d'environnement."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Base de données
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/esg_mefali"

    # Sécurité JWT
    secret_key: str = "changez-cette-cle-en-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    refresh_token_expire_days: int = 30

    # OpenRouter / LLM
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "anthropic/claude-sonnet-4-20250514"

    # Aliases pour compatibilite avec le .env existant
    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_model: str = ""

    def model_post_init(self, __context: object) -> None:
        """Mapper les variables LLM_* vers openrouter_* si non definies."""
        if not self.openrouter_api_key and self.llm_api_key:
            self.openrouter_api_key = self.llm_api_key
        if self.llm_base_url:
            self.openrouter_base_url = self.llm_base_url
        if self.llm_model:
            self.openrouter_model = self.llm_model

    # Application
    app_version: str = "0.1.0"
    debug: bool = False

    # Quotas utilisateur (dette spec 004 §3.2)
    # ge=1 : refuse 0 au boot pour éviter les sémantiques ambigues
    # (disabled vs unlimited) — cf. review D1.
    quota_bytes_per_user_mb: int = Field(default=100, ge=1)
    quota_docs_per_user: int = Field(default=50, ge=1)


settings = Settings()
