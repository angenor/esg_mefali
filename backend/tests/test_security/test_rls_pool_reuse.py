"""AC5 — apply/reset RLS context : pool asyncpg safe, pas de fuite cross-requête.

Vérifie que ``reset_rls_context`` vide bien les settings PostgreSQL et
qu'une 2ᵉ session successive ne hérite pas du contexte de la 1ʳᵉ.

PostgreSQL-only — marker ``@pytest.mark.postgres``. Skippé si
``TEST_ALEMBIC_URL`` n'est pas positionné.
"""
from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest
from alembic import command
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.rls import apply_rls_context, reset_rls_context


pytestmark = pytest.mark.postgres


@pytest.fixture(autouse=True)
def _apply_head(alembic_config):
    command.upgrade(alembic_config, "head")
    yield


def _to_async_url(url: str) -> str:
    """Normalise toute URL PostgreSQL sync vers asyncpg pour les tests async."""
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
async def async_factory(alembic_postgres_url):
    """async_sessionmaker isolé pour ces tests (petit pool)."""
    if not alembic_postgres_url:
        pytest.skip("TEST_ALEMBIC_URL requis")
    engine = create_async_engine(
        _to_async_url(alembic_postgres_url),
        pool_size=2,
        max_overflow=0,
        pool_pre_ping=True,
    )
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        yield factory
    finally:
        await engine.dispose()


def _fake_user(uid: uuid.UUID, email: str = "test@example.com"):
    return SimpleNamespace(id=uid, email=email)


async def test_session_reset_clears_rls_context(async_factory, monkeypatch):
    """apply → check → reset → check empty."""
    monkeypatch.setenv("ADMIN_MEFALI_EMAILS", "")
    monkeypatch.setenv("ADMIN_SUPER_EMAILS", "")
    user_a_id = uuid.uuid4()

    async with async_factory() as session:
        await apply_rls_context(session, _fake_user(user_a_id))
        row = (
            await session.execute(
                text("SELECT current_setting('app.current_user_id', true)")
            )
        ).fetchone()
        assert row[0] == str(user_a_id)

        await reset_rls_context(session)
        row = (
            await session.execute(
                text("SELECT current_setting('app.current_user_id', true)")
            )
        ).fetchone()
        role_row = (
            await session.execute(
                text("SELECT current_setting('app.user_role', true)")
            )
        ).fetchone()
        # Postgres retourne '' pour une variable vide (missing_ok=true).
        assert row[0] == ""
        assert role_row[0] == ""


async def test_sequential_requests_isolation(async_factory, monkeypatch):
    """2 sessions successives : la 2ᵉ ne voit pas le contexte de la 1ʳᵉ
    après reset (simule le pattern get_db avec reset en finally)."""
    monkeypatch.setenv("ADMIN_MEFALI_EMAILS", "")
    monkeypatch.setenv("ADMIN_SUPER_EMAILS", "")
    user_a_id = uuid.uuid4()
    user_b_id = uuid.uuid4()

    # 1ʳᵉ "requête"
    async with async_factory() as session1:
        await apply_rls_context(session1, _fake_user(user_a_id))
        row = (
            await session1.execute(
                text("SELECT current_setting('app.current_user_id', true)")
            )
        ).fetchone()
        assert row[0] == str(user_a_id)
        # Simule la fin de get_db : reset défensif dans finally.
        await reset_rls_context(session1)

    # 2ᵉ "requête" — potentiellement la même connexion physique via pool.
    async with async_factory() as session2:
        # Avant apply, le contexte doit être vide (pas de fuite).
        row = (
            await session2.execute(
                text("SELECT current_setting('app.current_user_id', true)")
            )
        ).fetchone()
        assert row[0] == "", (
            f"Fuite cross-requête détectée : app.current_user_id={row[0]!r}"
        )
        await apply_rls_context(session2, _fake_user(user_b_id))
        row = (
            await session2.execute(
                text("SELECT current_setting('app.current_user_id', true)")
            )
        ).fetchone()
        assert row[0] == str(user_b_id)
        await reset_rls_context(session2)


async def test_apply_with_none_user_sets_empty_context(async_factory):
    """apply_rls_context(None) → anonyme explicite."""
    async with async_factory() as session:
        await apply_rls_context(session, None)
        uid = (
            await session.execute(
                text("SELECT current_setting('app.current_user_id', true)")
            )
        ).fetchone()[0]
        role = (
            await session.execute(
                text("SELECT current_setting('app.user_role', true)")
            )
        ).fetchone()[0]
        assert uid == ""
        assert role == ""
