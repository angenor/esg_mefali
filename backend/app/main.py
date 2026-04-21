"""Point d'entrée FastAPI avec lifespan, CORS et routers."""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.admin_audit_listener import register_admin_access_listener
from app.core.config import settings
from app.core.database import engine as _db_engine
from app.core.outbox.worker import (
    start_outbox_scheduler,
    stop_outbox_scheduler,
)
from app.core.rate_limit import limiter

logger = logging.getLogger(__name__)

# Référence globale au graphe compilé LangGraph
compiled_graph = None

# Référence globale au scheduler Outbox (Story 10.10)
outbox_scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Cycle de vie de l'application : initialisation et nettoyage."""
    global compiled_graph, outbox_scheduler

    # Story 10.5 — attacher le listener before_flush qui log les bypass
    # admin dans admin_access_audit (architecture.md §D7). Idempotent.
    register_admin_access_listener(_db_engine)

    # Story 10.10 — démarrer le worker Outbox APScheduler (batch 30 s +
    # purge prefill_drafts 1 h). Skippé si DOMAIN_EVENTS_WORKER_ENABLED=false.
    outbox_scheduler = start_outbox_scheduler(_db_engine)

    # Démarrage : initialiser le graphe LangGraph
    if settings.openrouter_api_key:
        try:
            from app.graph.graph import create_compiled_graph

            compiled_graph = await create_compiled_graph()
            logger.info("Graphe LangGraph initialisé avec succès")
        except Exception as e:
            logger.warning("Impossible d'initialiser le graphe LangGraph : %s", e)
            compiled_graph = None
    else:
        logger.warning("OPENROUTER_API_KEY non configurée — graphe LangGraph désactivé")

    # Validation OCR bilingue (dette P1 #8 — story 9.4)
    # Log WARNING si la traineddata anglaise (ou francaise) est absente, pour
    # rendre le diagnostic visible au startup plutot qu'au premier upload.
    # Non bloquant : en dev, un contributeur peut demarrer sans eng installe
    # (seuls les appels OCR sur documents anglophones echoueront, comportement
    # identique a aujourd'hui — on rend juste le diagnostic visible).
    try:
        import pytesseract

        languages = set(pytesseract.get_languages(config=""))
        missing = {"fra", "eng"} - languages
        if missing:
            logger.warning(
                "Tesseract OCR : langue(s) %s absente(s) — l'OCR bilingue "
                "(fra+eng) echouera sur les documents concernes. "
                "Installez les paquets : %s.",
                sorted(missing),
                ", ".join(f"tesseract-ocr-{lang}" for lang in sorted(missing)),
            )
        else:
            logger.info("Tesseract OCR : langues fra+eng disponibles")
    except ImportError:
        logger.warning(
            "pytesseract non installe — OCR indisponible (echec au 1er upload image/PDF scanne). "
            "Installez pytesseract + tesseract-ocr + tesseract-ocr-fra "
            "+ tesseract-ocr-eng pour activer l'extraction de documents scannes."
        )
    except Exception as exc:  # pytesseract.TesseractNotFoundError et autres
        logger.warning(
            "Tesseract OCR introuvable ou non fonctionnel (%s) — installez "
            "tesseract-ocr + tesseract-ocr-fra + tesseract-ocr-eng pour "
            "activer l'extraction de documents scannes.",
            exc,
        )

    yield

    # Arrêt — stopper le scheduler AVANT la libération du pool de connexions
    # (évite les jobs en vol quand la pool ferme).
    await stop_outbox_scheduler(outbox_scheduler)
    compiled_graph = None


app = FastAPI(
    title="ESG Mefali API",
    description="Plateforme conversationnelle IA pour la finance durable des PME africaines",
    version=settings.app_version,
    lifespan=lifespan,
)

# Rate limiting SlowAPI — FR-013 : 30 msg/min/user sur l'endpoint chat
# Le limiter est applique via decorateur cible dans app/api/chat.py (pas de middleware global)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routers
from app.api.auth import router as auth_router  # noqa: E402
from app.api.chat import router as chat_router  # noqa: E402
from app.api.health import router as health_router  # noqa: E402
from app.modules.company.router import router as company_router  # noqa: E402
from app.modules.documents.router import router as documents_router  # noqa: E402
from app.modules.esg.router import router as esg_router  # noqa: E402
from app.modules.projects.router import router as projects_router  # noqa: E402
from app.modules.maturity.router import router as maturity_router  # noqa: E402
from app.modules.admin_catalogue.router import router as admin_catalogue_router  # noqa: E402
from app.modules.reports.router import router as reports_router  # noqa: E402
from app.modules.carbon.router import router as carbon_router  # noqa: E402
from app.modules.financing.router import router as financing_router  # noqa: E402
from app.modules.applications.router import router as applications_router  # noqa: E402
from app.modules.credit.router import router as credit_router  # noqa: E402
from app.modules.dashboard.router import router as dashboard_router  # noqa: E402
from app.modules.action_plan.router import router as action_plan_router  # noqa: E402

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
app.include_router(company_router, prefix="/api/company", tags=["company"])
app.include_router(documents_router, prefix="/api/documents", tags=["documents"])
app.include_router(esg_router, prefix="/api/esg", tags=["esg"])
app.include_router(projects_router, prefix="/api/projects", tags=["projects"])
app.include_router(maturity_router, prefix="/api/maturity", tags=["maturity"])
app.include_router(admin_catalogue_router, prefix="/api/admin/catalogue", tags=["admin-catalogue"])
app.include_router(reports_router, prefix="/api/reports", tags=["reports"])
app.include_router(carbon_router, prefix="/api/carbon", tags=["carbon"])
app.include_router(financing_router, prefix="/api/financing", tags=["financing"])
app.include_router(applications_router, prefix="/api/applications", tags=["applications"])
app.include_router(credit_router, prefix="/api/credit", tags=["credit"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(action_plan_router, prefix="/api/action-plan", tags=["action-plan"])
app.include_router(health_router, prefix="/api", tags=["health"])
