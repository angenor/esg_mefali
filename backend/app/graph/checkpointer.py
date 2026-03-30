"""Configuration du checkpointer PostgreSQL pour LangGraph."""

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.core.config import settings


def get_checkpointer_connection_string() -> str:
    """Retourner l'URL de connexion pour le checkpointer.

    Le checkpointer utilise psycopg (pas asyncpg), donc on convertit l'URL.
    """
    db_url = settings.database_url
    # Convertir postgresql+asyncpg:// en postgresql://
    return db_url.replace("postgresql+asyncpg://", "postgresql://")


async def create_checkpointer() -> AsyncPostgresSaver:
    """Créer et initialiser le checkpointer PostgreSQL."""
    conn_string = get_checkpointer_connection_string()
    checkpointer = AsyncPostgresSaver.from_conn_string(conn_string)
    await checkpointer.setup()
    return checkpointer
