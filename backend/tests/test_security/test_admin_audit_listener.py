"""HIGH-10.5-1 (review fix) — tests E2E du listener ``admin_audit_listener``.

Objet : fermer la boucle AC4 contrat D7 « tout bypass admin doit être
logué » en vérifiant end-to-end la chaîne complète
``apply_rls_context → mutation ORM admin → before_flush → insertion
admin_access_audit``. Les tests matrice 4×4 livrés par Story 10.5
(``test_rls_enforcement.py``) prouvent le **bypass RLS** via raw SQL
mais n'exécutent **jamais** le listener ``before_flush`` (raw
``session.execute(text(...))`` ne déclenche pas ``before_flush`` —
limitation SQLAlchemy connue, documentée dans ``security-rls.md``).

Ce fichier comble cette lacune : chaque test charge le listener sur un
engine async réel, déclenche une mutation **via ORM** sous un rôle
admin (whitelist email), puis assert qu'une ligne
``admin_access_audit`` a bien été insérée avec le contexte correct.

Règle d'or (capitalisée Story 10.5 review) : toute story touchant
``event.listens_for`` ou un intercepteur SQLAlchemy DOIT avoir au moins
un test E2E qui (1) charge le listener sur un engine test réel,
(2) déclenche une mutation observable, (3) assert l'effet dans la table
cible — sans cela, le listener peut devenir muet silencieusement (cf.
leçon 9.7 C2 « tests prod véritables »).

PostgreSQL-only — marker ``@pytest.mark.postgres``. Skippé si
``TEST_ALEMBIC_URL`` n'est pas configuré.
"""
from __future__ import annotations

import uuid

import pytest
from alembic import command
from sqlalchemy import String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.admin_audit_listener import register_admin_access_listener
from app.core.rls import apply_rls_context
from app.models.application import ApplicationStatus, FundApplication, TargetType
from app.models.document import Document, DocumentStatus
from app.modules.projects.models import Company


pytestmark = pytest.mark.postgres


# Modèle ORM minimal pour ``facts`` : aucun modèle de production ne
# mappe cette table aujourd'hui (l'ORM métier est déféré Epic 13). On
# utilise un ``DeclarativeBase`` isolé pour éviter toute pollution du
# registre ``app.models.base.Base``. Le listener ne lit que
# ``__tablename__`` — n'importe quel mapped class convient.
class _FactTestBase(DeclarativeBase):
    pass


class _FactForTest(_FactTestBase):
    """Modèle de test pour ``facts`` (voir deferred-work Story 10.5)."""

    __tablename__ = "facts"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False
    )
    fact_type: Mapped[str] = mapped_column(String(64), nullable=False)
    value_json: Mapped[dict] = mapped_column(JSONB, nullable=False)


def _to_async_url(url: str) -> str:
    """Normalise toute URL PostgreSQL vers asyncpg."""
    if url.startswith("postgresql+asyncpg://"):
        return url
    if url.startswith("postgresql+psycopg2://"):
        return "postgresql+asyncpg://" + url[len("postgresql+psycopg2://") :]
    if url.startswith("postgresql+psycopg://"):
        return "postgresql+asyncpg://" + url[len("postgresql+psycopg://") :]
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url[len("postgresql://") :]
    return url


@pytest.fixture(autouse=True)
def _apply_head(alembic_config):
    """Applique toutes les migrations jusqu'à HEAD avant chaque test."""
    command.upgrade(alembic_config, "head")
    yield


@pytest.fixture
async def listener_engine(alembic_postgres_url):
    """Engine async avec listener ``before_flush`` enregistré.

    Pattern : chaque test crée son propre engine + factory pour isoler
    du reste de la suite (et garantir que le listener voit bien les
    mutations effectuées via l'async factory locale).
    """
    if not alembic_postgres_url:
        pytest.skip("TEST_ALEMBIC_URL requis (PostgreSQL)")
    engine = create_async_engine(_to_async_url(alembic_postgres_url))
    register_admin_access_listener(engine)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        yield factory
    finally:
        await engine.dispose()


async def _seed_admin_user(factory, email: str) -> uuid.UUID:
    """Insert un user admin whitelisté via raw SQL (listener inactif)."""
    user_id = uuid.uuid4()
    async with factory() as s:
        # Contexte admin_super pour bypass RLS sur users (pas RLS sur users
        # directement, mais cohérence avec les autres fixtures).
        await s.execute(
            text("SELECT set_config('app.user_role', 'admin_super', false)")
        )
        await s.execute(
            text(
                "INSERT INTO users (id, email, hashed_password, full_name, "
                "company_name, is_active) VALUES (:id, :em, 'h', 'U', 'C', true)"
            ),
            {"id": user_id, "em": email},
        )
        await s.commit()
    return user_id


async def _seed_company(factory, owner_user_id: uuid.UUID) -> uuid.UUID:
    """Insert une company via raw SQL (nécessaire FK pour facts)."""
    company_id = uuid.uuid4()
    async with factory() as s:
        await s.execute(
            text("SELECT set_config('app.user_role', 'admin_super', false)")
        )
        await s.execute(
            text(
                "INSERT INTO companies (id, owner_user_id, name) "
                "VALUES (:id, :u, :n)"
            ),
            {"id": company_id, "u": owner_user_id, "n": "Seed Co"},
        )
        await s.commit()
    return company_id


async def _seed_fund(factory) -> uuid.UUID:
    """Insert un fund via raw SQL (FK pour fund_applications)."""
    fund_id = uuid.uuid4()
    async with factory() as s:
        await s.execute(
            text("SELECT set_config('app.user_role', 'admin_super', false)")
        )
        await s.execute(
            text(
                "INSERT INTO funds "
                "(id, name, organization, fund_type, description, access_type, status) "
                "VALUES (:id, 'TestFund', 'TestOrg', 'international', 'd', 'direct', 'active')"
            ),
            {"id": fund_id},
        )
        await s.commit()
    return fund_id


class _FakeUser:
    """Shim ``User`` pour ``apply_rls_context`` (duck typing id + email)."""

    def __init__(self, uid: uuid.UUID, email: str) -> None:
        self.id = uid
        self.email = email


async def _count_audit_rows(
    factory, admin_id: uuid.UUID, table_accessed: str, admin_role: str
) -> int:
    """Compte les lignes admin_access_audit correspondant au contexte.

    Utilise un contexte admin_super pour lire (lecture sensitive =
    autorisée aux admins uniquement, cohérence D7).
    """
    async with factory() as s:
        await s.execute(
            text("SELECT set_config('app.user_role', 'admin_super', false)")
        )
        result = await s.execute(
            text(
                "SELECT COUNT(*) FROM admin_access_audit "
                "WHERE admin_user_id = :uid "
                "AND table_accessed = :t "
                "AND admin_role = :r"
            ),
            {"uid": admin_id, "t": table_accessed, "r": admin_role},
        )
        return int(result.scalar() or 0)


# --------------------------------------------------------------------
# Tests paramétrés — 4 scénarios (1 par table RLS) × rôle admin.
# --------------------------------------------------------------------

TABLE_SCENARIOS = [
    pytest.param(
        "admin_mefali", "ADMIN_MEFALI_EMAILS", "companies",
        id="companies",
    ),
    pytest.param(
        "admin_super", "ADMIN_SUPER_EMAILS", "fund_applications",
        id="fund_applications",
    ),
    pytest.param(
        "admin_super", "ADMIN_SUPER_EMAILS", "facts",
        id="facts",
    ),
    pytest.param(
        "admin_mefali", "ADMIN_MEFALI_EMAILS", "documents",
        id="documents",
    ),
]


@pytest.mark.parametrize("admin_role,env_var,table", TABLE_SCENARIOS)
async def test_listener_writes_audit_entry_on_admin_mutation(
    listener_engine, monkeypatch, admin_role, env_var, table
):
    """Chaîne end-to-end : apply_rls_context(admin) + ORM INSERT →
    ligne ``admin_access_audit`` écrite par le listener.

    Couvre AC4 contrat D7 matériellement pour les 4 tables RLS :
    - ``companies`` → ``Company`` (app.modules.projects.models)
    - ``fund_applications`` → ``FundApplication`` (app.models.application)
    - ``facts`` → ORM local ``_FactForTest`` (aucun modèle de prod, cf.
      deferred-work Story 10.5)
    - ``documents`` → ``Document`` (app.models.document)
    """
    factory = listener_engine
    admin_email = f"bypass-{uuid.uuid4().hex[:8]}@mefali.com"
    monkeypatch.setenv(env_var, admin_email)
    # Vider l'autre liste pour isoler le rôle (précédence admin_super).
    other_var = (
        "ADMIN_MEFALI_EMAILS"
        if env_var == "ADMIN_SUPER_EMAILS"
        else "ADMIN_SUPER_EMAILS"
    )
    monkeypatch.setenv(other_var, "")

    admin_id = await _seed_admin_user(factory, admin_email)

    # Contexte spécifique par table : on construit l'objet ORM à
    # muter. ``facts`` et ``fund_applications`` requièrent un seed
    # préalable (FK) ; ``companies`` et ``documents`` n'ont besoin
    # que de l'admin user comme propriétaire.
    if table == "companies":
        instance_factory = lambda: Company(  # noqa: E731
            id=uuid.uuid4(),
            owner_user_id=admin_id,
            name=f"OrmCo-{uuid.uuid4().hex[:6]}",
        )
    elif table == "fund_applications":
        fund_id = await _seed_fund(factory)
        instance_factory = lambda: FundApplication(  # noqa: E731
            id=uuid.uuid4(),
            user_id=admin_id,
            fund_id=fund_id,
            target_type=TargetType.fund_direct,
            status=ApplicationStatus.draft,
        )
    elif table == "facts":
        company_id = await _seed_company(factory, admin_id)
        instance_factory = lambda: _FactForTest(  # noqa: E731
            id=uuid.uuid4(),
            company_id=company_id,
            fact_type="esg_indicator",
            value_json={"k": "v"},
        )
    elif table == "documents":
        instance_factory = lambda: Document(  # noqa: E731
            id=uuid.uuid4(),
            user_id=admin_id,
            filename="t.pdf",
            original_filename="t.pdf",
            mime_type="application/pdf",
            file_size=1,
            storage_path=f"/tmp/t-{uuid.uuid4().hex[:6]}.pdf",
            status=DocumentStatus.uploaded,
        )
    else:
        raise AssertionError(f"Table inattendue : {table}")

    # Mutation ORM sous contexte admin : déclenche before_flush + listener.
    async with factory() as session:
        await apply_rls_context(session, _FakeUser(admin_id, admin_email))
        session.add(instance_factory())
        await session.commit()

    count = await _count_audit_rows(factory, admin_id, table, admin_role)
    assert count >= 1, (
        f"[table={table} role={admin_role}] attendu au moins 1 ligne "
        f"admin_access_audit — le listener n'a pas déclenché l'insertion "
        f"(régression D7 tout bypass admin doit être logué)."
    )
