"""Configuration de l'application via variables d'environnement."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Base de données
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/esg_mefali"

    # Sécurité JWT
    secret_key: str = "changez-cette-cle-en-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30

    # OpenRouter / LLM
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "anthropic/claude-sonnet-4-20250514"

    # Application
    app_version: str = "0.1.0"
    debug: bool = False


settings = Settings()
