"""Fixtures E2E postgres Outbox (Story 10.10 AC7).

Skip auto si ``TEST_ALEMBIC_URL`` non configuré — ``SELECT FOR UPDATE SKIP
LOCKED`` n'est pas supporté par SQLite (leçon Story 10.1).
"""

from __future__ import annotations

import os
import uuid
from collections.abc import AsyncGenerator

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from app.models.base import Base
from app.models.domain_event import DomainEvent  # noqa: F401  # register mapping


def _to_async_url(url: str) -> str:
    if url.startswith("postgresql+asyncpg://"):
        return url
    if url.startswith("postgresql+psycopg2://"):
        return "postgresql+asyncpg://" + url[len("postgresql+psycopg2://") :]
    if url.startswith("postgresql+psycopg://"):
        return "postgresql+asyncpg://" + url[len("postgresql+psycopg://") :]
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url[len("postgresql://") :]
    return url


@pytest.fixture
async def postgres_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Engine async PostgreSQL avec schéma ``domain_events`` + ``prefill_drafts``.

    Crée les tables minimales requises via ``Base.metadata.create_all``
    (pas d'Alembic — on teste le worker, pas les migrations).
    """
    url = os.environ.get("TEST_ALEMBIC_URL")
    if not url:
        pytest.skip("TEST_ALEMBIC_URL non configuré — test postgres-only")

    async_url = _to_async_url(url)
    engine = create_async_engine(async_url, echo=False, future=True)

    async with engine.begin() as conn:
        # Nettoyage schéma public (cohérence avec test_migrations/conftest).
        await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))

        # Table minimale `users` (FK prefill_drafts.user_id).
        await conn.execute(text(
            """
            CREATE TABLE users (
                id UUID PRIMARY KEY,
                email VARCHAR(255) NOT NULL UNIQUE,
                hashed_password VARCHAR(255) NOT NULL,
                full_name VARCHAR(255),
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        ))
        # Table domain_events (matchant migration 027 + 029).
        await conn.execute(text(
            """
            CREATE TABLE domain_events (
                id UUID PRIMARY KEY,
                event_type VARCHAR(64) NOT NULL,
                aggregate_type VARCHAR(64) NOT NULL,
                aggregate_id UUID NOT NULL,
                payload JSONB NOT NULL,
                status VARCHAR(16) NOT NULL DEFAULT 'pending',
                retry_count INTEGER NOT NULL DEFAULT 0,
                error_message TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                processed_at TIMESTAMPTZ,
                next_retry_at TIMESTAMPTZ,
                CONSTRAINT ck_domain_events_retry_cap CHECK (retry_count <= 5)
            )
            """
        ))
        # Table prefill_drafts (matchant migration 027).
        await conn.execute(text(
            """
            CREATE TABLE prefill_drafts (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                payload JSONB NOT NULL,
                expires_at TIMESTAMPTZ NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        ))

    yield engine

    await engine.dispose()


@pytest.fixture
async def insert_test_user(postgres_engine: AsyncEngine) -> uuid.UUID:
    """Insère un utilisateur test et renvoie son UUID (FK prefill_drafts)."""
    user_id = uuid.uuid4()
    async with AsyncSession(postgres_engine) as db:
        await db.execute(
            text(
                "INSERT INTO users (id, email, hashed_password) "
                "VALUES (:id, :email, :pwd)"
            ),
            {"id": user_id, "email": f"test-{user_id}@mefali.test", "pwd": "x"},
        )
        await db.commit()
    return user_id
