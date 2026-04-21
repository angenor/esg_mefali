"""Configuration de l'application via variables d'environnement."""

from pydantic import Field, field_validator, model_validator
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

# Environnements autorisés NFR73 — ségrégation stricte (Story 10.7 AC1).
# Pattern miroir `ALLOWED_EU_REGIONS` + `field_validator` fail-fast boot.
ALLOWED_ENV_NAMES: frozenset[str] = frozenset({"dev", "staging", "prod"})


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

    # --- Environnement (Story 10.7 AC1) ---
    # dev (local docker-compose), staging (AWS minimal), prod (AWS full).
    # Fail-fast au boot si valeur hors whitelist (NFR73 isolation).
    env_name: str = Field(
        default="dev",
        description="Environnement courant (dev/staging/prod) — NFR73",
    )
    # Namespace AWS Secrets Manager (vide en DEV, "mefali/staging" ou
    # "mefali/prod" en AWS). Défense en profondeur contre fuite cross-env.
    aws_secrets_manager_namespace: str = ""

    @field_validator("env_name")
    @classmethod
    def _validate_env_name(cls, v: str) -> str:
        """NFR73 — fail-fast si ENV_NAME non reconnu (empêche boot accidentel
        avec secrets génériques). Aligné pattern `aws_region` (Story 10.6)."""
        if v not in ALLOWED_ENV_NAMES:
            raise ValueError(
                f"env_name must be one of {sorted(ALLOWED_ENV_NAMES)} "
                f"(NFR73 isolation). Got: {v!r}"
            )
        return v

    def is_production(self) -> bool:
        """True uniquement si `env_name == "prod"`. Consommé par code qui
        doit se comporter différemment en PROD (guards MFA, no debug, etc.)."""
        return self.env_name == "prod"

    @model_validator(mode="after")
    def _forbid_debug_in_production(self) -> "Settings":
        """Garde-fou boot : PROD avec debug=True interdit (fuite traces stack,
        leak secrets dans logs, timing attacks exposées). NFR73."""
        if self.env_name == "prod" and self.debug:
            raise ValueError(
                "Production cannot run with debug=True (NFR73 isolation). "
                "Set DEBUG=false or change ENV_NAME."
            )
        return self

    # --- Feature flag Phase 1 Cluster A (Story 10.9) ---
    # Bascule modèle Company × Project (Clarification 5 architecture, NFR63).
    # Champ informationnel : le runtime lit `os.environ` dynamiquement via
    # `app.core.feature_flags.is_project_model_enabled()` pour le toggle live
    # DEV (monkeypatch.setenv). Ce champ sert la self-documentation du schéma
    # Settings + la coercion bool au boot (rejette "garbage").
    # Retrait fin Phase 1 via migration 027 (Story 20.1).
    enable_project_model: bool = Field(
        default=False,
        description=(
            "Feature flag Phase 1 Cluster A — bascule Company × Project "
            "(NFR63). Lu dynamiquement par `is_project_model_enabled()` au "
            "runtime ; le champ Settings est informationnel."
        ),
    )

    # --- Worker Outbox (Story 10.10) ---
    # Kill-switch + intervalle batch APScheduler (architecture.md §D11).
    # Lu au startup uniquement (pas de toggle live runtime — APScheduler
    # peut pause_job mais cela complique le shutdown ; kill-switch = redéploy).
    domain_events_worker_enabled: bool = Field(
        default=True,
        description=(
            "Kill-switch worker Outbox APScheduler (architecture.md §D11). "
            "Désactiver en DEV pour debug handler — les events s'accumulent "
            "en 'pending' mais ne sont jamais consommés. Lu au startup."
        ),
    )
    domain_events_worker_interval_s: int = Field(
        default=30,
        ge=5,
        le=3600,
        description=(
            "Intervalle batch Outbox en secondes (architecture.md §D11 "
            "défaut 30 s). Borné 5-3600 : évite hot-loop (ge=5) et worker "
            "dormant 1 jour (le=3600) qui masquerait la latence métier."
        ),
    )

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

    # --- Embeddings (Story 10.13) ---
    # Provider : "voyage" (MVP default, voyage-3 1024 dim) ou "openai" (legacy
    # fallback text-embedding-3-small 1536 dim). Coexistence v1+v2 via
    # migration 031 — Q2 parallel strategy.
    embedding_provider: str = Field(default="voyage", pattern="^(voyage|openai)$")
    voyage_api_key: str = ""
    voyage_model: str = Field(default="voyage-3")

    @field_validator("voyage_model")
    @classmethod
    def _validate_voyage_model(cls, v: str) -> str:
        """Q1 whitelist — fail-fast boot si typo modèle Voyage."""
        allowed = {"voyage-3", "voyage-3-large", "voyage-code-3", "voyage-3-lite"}
        if v not in allowed:
            raise ValueError(
                f"voyage_model must be one of {sorted(allowed)}. Got: {v!r}"
            )
        return v

    # --- Anthropic direct (Story 10.13 bench Livrable B) ---
    anthropic_api_key: str = ""
    anthropic_base_url: str = Field(default="https://api.anthropic.com/v1")

    # --- LLM Provider abstraction (Story 10.13 AC10) ---
    # Default MVP avant-bench = ``openrouter`` (comportement historique).
    # Post-bench R-04-1, le winner sera hardcodé ici (voir docs/bench-...).
    llm_provider: str = Field(
        default="openrouter", pattern="^(openrouter|anthropic_direct)$"
    )
    llm_fallback_provider: str = Field(
        default="openrouter", pattern="^(openrouter|anthropic_direct)$"
    )

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
