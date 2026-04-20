"""Configuration SQLAlchemy async engine et session factory."""

import contextlib
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.rls import reset_rls_context

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dépendance FastAPI pour obtenir une session de base de données.

    Story 10.5 — le ``finally`` appelle ``reset_rls_context`` avant que la
    session ne soit retournée au pool asyncpg, pour éviter toute fuite
    cross-requête (``set_config(..., false)`` persiste jusqu'à fermeture
    de la connexion physique).
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            # Story 10.5 — reset défensif du contexte RLS.
            # Dérogation C1 (leçon 9.7) justifiée : si la session est déjà
            # invalide (rollback sur erreur métier), propager l'exception
            # de reset masquerait l'erreur réelle ; le reset n'a que
            # valeur défensive (belt-and-braces).
            #
            # NOTE SÉCURITÉ (fix review 10.5 MEDIUM-10.5-2) :
            # ``pool_pre_ping=True`` NE protège PAS contre un contexte RLS
            # résiduel — il ne fait qu'un ``SELECT 1`` pour vérifier que
            # la connexion TCP est vivante, pas que ses settings de
            # session (``app.current_user_id``, ``app.user_role``) sont
            # propres. La vraie garantie anti-fuite cross-requête est
            # qu'``apply_rls_context`` écrase systématiquement les
            # settings au début de chaque requête authentifiée (cf.
            # ``app.api.deps.get_current_user``). Le reset ici est un
            # filet de sécurité additionnel.
            with contextlib.suppress(Exception):
                await reset_rls_context(session)
