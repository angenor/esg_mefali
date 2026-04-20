"""Modèles SQLAlchemy — importer tous les modèles pour Alembic."""

from app.models.base import Base  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.conversation import Conversation  # noqa: F401
from app.models.message import Message  # noqa: F401
from app.models.company import CompanyProfile  # noqa: F401
from app.models.document import Document, DocumentAnalysis, DocumentChunk  # noqa: F401
from app.models.esg import ESGAssessment  # noqa: F401
from app.models.report import Report  # noqa: F401
from app.models.carbon import CarbonAssessment, CarbonEmissionEntry  # noqa: F401
from app.models.financing import (  # noqa: F401
    FinancingChunk,
    Fund,
    FundIntermediary,
    FundMatch,
    Intermediary,
)
from app.models.application import FundApplication  # noqa: F401
from app.models.credit import CreditDataPoint, CreditScore  # noqa: F401
from app.models.action_plan import (  # noqa: F401
    ActionItem,
    ActionPlan,
    Badge,
    Reminder,
)
from app.models.tool_call_log import ToolCallLog  # noqa: F401
from app.models.interactive_question import (  # noqa: F401
    InteractiveQuestion,
    InteractiveQuestionState,
    InteractiveQuestionType,
)

# Story 10.2 — Module projects squelette : enregistrement SQLAlchemy metadata
from app.modules.projects.models import (  # noqa: F401
    BeneficiaryProfile,
    Company,
    CompanyProjection,
    Project,
    ProjectMembership,
    ProjectRolePermission,
    ProjectSnapshot,
)

# Story 10.3 — Module maturity squelette : enregistrement SQLAlchemy metadata
from app.modules.maturity.models import (  # noqa: F401
    AdminMaturityLevel,
    AdminMaturityRequirement,
    FormalizationPlan,
)

# Story 10.4 — Module admin_catalogue squelette : enregistrement SQLAlchemy metadata
from app.modules.admin_catalogue.models import (  # noqa: F401
    AdminCatalogueAuditTrail,
    Criterion,
    CriterionDerivationRule,
    Pack,
    Referential,
)
