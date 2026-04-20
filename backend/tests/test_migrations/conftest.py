"""Fixtures pour tester les migrations Alembic 020-027 (Story 10.1).

Les tests de migrations Alembic nécessitent un PostgreSQL réel : les
migrations 001 (pgvector), 163318558259 (HNSW) et 024 (RLS) ne sont pas
exécutables sur SQLite. Les tests sont donc marqués @pytest.mark.postgres
et skippés si TEST_ALEMBIC_URL n'est pas configuré.

Pattern conforme à CLAUDE.md §Phase 4 : tests prod véritables, vraie
Alembic env + vrais modèles (pas de stubs).
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine


def _backend_root() -> Path:
    """Racine backend/ (pour localiser alembic.ini)."""
    return Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def alembic_postgres_url() -> str | None:
    """URL PostgreSQL synchrone pour les commandes Alembic.

    Renvoie None si non configurée — les tests sont alors skip.
    """
    return os.environ.get("TEST_ALEMBIC_URL")


@pytest.fixture
def alembic_config(alembic_postgres_url):
    """Configuration Alembic pour une DB PostgreSQL de test isolée."""
    if not alembic_postgres_url:
        pytest.skip("TEST_ALEMBIC_URL non configuré (PostgreSQL requis)")

    cfg = Config(str(_backend_root() / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", alembic_postgres_url)
    return cfg


def _to_sync_url(url: str) -> str:
    """Normalise toute URL PostgreSQL vers un driver sync (psycopg2).

    Aligné sur ``scripts/validate_schema.py`` et le workflow CI qui utilisent
    tous ``postgresql+psycopg2://``. Le driver psycopg2-binary est listé dans
    ``requirements-dev.txt``.
    """
    # Si déjà un driver sync explicite, laisser tel quel.
    if url.startswith("postgresql+psycopg2://") or url.startswith(
        "postgresql+psycopg://"
    ):
        return url
    if url.startswith("postgresql+asyncpg://"):
        return "postgresql+psycopg2://" + url[len("postgresql+asyncpg://") :]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg2://" + url[len("postgresql://") :]
    return url


@pytest.fixture(autouse=True)
def _reset_schema_before_each_test(alembic_postgres_url):
    """Nettoie le schéma public avant chaque test (round-trip deterministic)."""
    if not alembic_postgres_url:
        yield
        return
    from sqlalchemy import text as _text

    engine = create_engine(_to_sync_url(alembic_postgres_url))
    try:
        with engine.begin() as conn:
            conn.execute(_text("DROP SCHEMA IF EXISTS public CASCADE"))
            conn.execute(_text("CREATE SCHEMA public"))
            conn.execute(_text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
            conn.execute(_text("CREATE EXTENSION IF NOT EXISTS vector"))
    finally:
        engine.dispose()
    yield


@pytest.fixture
def sync_engine(alembic_postgres_url):
    """Engine SQLAlchemy synchrone pour l'introspection du schéma."""
    if not alembic_postgres_url:
        pytest.skip("TEST_ALEMBIC_URL non configuré (PostgreSQL requis)")
    engine = create_engine(_to_sync_url(alembic_postgres_url))
    yield engine
    engine.dispose()


def needs_postgres():
    """Décorateur rapide pour skip si pas de PostgreSQL."""
    return pytest.mark.skipif(
        not os.environ.get("TEST_ALEMBIC_URL"),
        reason="TEST_ALEMBIC_URL non configuré — tests migrations PG-only",
    )
