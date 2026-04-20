"""Configuration de l'application via variables d'environnement."""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Zones UE/UK autorisées NFR24 — data residency Mefali (Story 10.6 post-review
# MEDIUM-10.6-2). Le default `eu-west-3` Paris reste la cible tranchée ; les
# autres régions UE sont admises pour couvrir les plans de contingence
# documentés §D8 architecture (EU-Central/EU-North pour DR hors zone Paris).
ALLOWED_EU_REGIONS: frozenset[str] = frozenset({
    "eu-west-1",    # Irlande
    "eu-west-2",    # Londres
    "eu-west-3",    # Paris (NFR24 default)
    "eu-central-1", # Francfort
    "eu-central-2", # Zurich
    "eu-south-1",   # Milan
    "eu-south-2",   # Espagne
    "eu-north-1",   # Stockholm
})


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

    # --- Stockage fichiers (Story 10.6) ---
    # Provider : "local" (MVP default) ou "s3" (Phase Growth EU-West-3)
    storage_provider: str = Field(default="local", pattern="^(local|s3)$")
    # Si local : chemin relatif (depuis backend/) ou absolu
    storage_local_path: str = Field(default="uploads")
    # Si s3 : bucket + région (NFR24 data residency AWS EU-West-3 Paris)
    aws_s3_bucket: str = ""
    aws_region: str = Field(default="eu-west-3")

    @field_validator("aws_region")
    @classmethod
    def _validate_eu_region(cls, v: str) -> str:
        """NFR24 data residency — fail-fast si région hors UE.

        Story 10.6 post-review MEDIUM-10.6-2 : bloque au boot toute valeur
        `AWS_REGION` qui violerait la résidence européenne (bascule accidentelle
        `us-east-1`, `ap-south-1` dans un `.env` STAGING, etc.). Les plans de
        contingence documentés §D8 architecture (DR inter-UE) restent couverts.
        """
        if v not in ALLOWED_EU_REGIONS:
            raise ValueError(
                f"aws_region must be a UE region (NFR24 data residency). "
                f"Got: {v!r}. Allowed: {sorted(ALLOWED_EU_REGIONS)}"
            )
        return v


settings = Settings()
