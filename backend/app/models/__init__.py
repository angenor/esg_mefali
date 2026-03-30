"""Modèles SQLAlchemy — importer tous les modèles pour Alembic."""

from app.models.base import Base  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.conversation import Conversation  # noqa: F401
from app.models.message import Message  # noqa: F401
from app.models.company import CompanyProfile  # noqa: F401
