"""Tests transverses d'instrumentation (Story 9.7 T14 — AC1, AC4, AC6, AC7).

Couvre :
- Sentinelle ``_is_wrapped_by_with_retry`` posée sur les 36 tools.
- Aucun ``@tool`` ne peut échapper au registre (protection anti-régression Epic 10).
- Journalisation par module sur **les vrais tools de production** (D2 Option B du
  review 9.7) : 9 classes ``TestXxxProdInstrumentation`` qui invoquent
  ``XXX_TOOLS[0]`` avec un service métier mocké pour valider la chaîne
  ``@tool → with_retry → service → tool_call_logs``.
- Smoke tests sur stubs synthétiques (9 classes ``TestXxxInstrumentationSmoke``)
  pour valider le wrapper ``with_retry`` générique indépendamment des
  contraintes métier spécifiques.

Les tests utilisent une session SQLAlchemy réelle (SQLite in-memory via
``conftest.py``) pour observer les écritures dans ``tool_call_logs``.
"""

from __future__ import annotations

import asyncio
import importlib
import inspect
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool, tool as tool_decorator
from sqlalchemy import select

from app.graph.tools import INSTRUMENTED_TOOLS
from app.graph.tools import common as common_mod
from app.graph.tools.common import _reset_breaker_state_for_tests, with_retry
from app.models.tool_call_log import ToolCallLog


# ---------------------------------------------------------------------------
# Fixtures partagées
# ---------------------------------------------------------------------------


@pytest.fixture
def reset_breaker():
    _reset_breaker_state_for_tests()
    yield
    _reset_breaker_state_for_tests()


@pytest.fixture
def mock_sleep(monkeypatch):
    """Évite les pauses réelles pendant les retries."""
    sleep_mock = AsyncMock()
    monkeypatch.setattr(common_mod.asyncio, "sleep", sleep_mock)
    return sleep_mock


@pytest.fixture
async def logging_config(db_session):
    """RunnableConfig avec session DB réelle + user/conversation préinsérés."""
    from app.models.conversation import Conversation
    from app.models.user import User

    user = User(
        id=uuid.uuid4(),
        email=f"test-{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="test",
        full_name="Test User",
        company_name="Test Co",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    conversation = Conversation(
        id=uuid.uuid4(),
        user_id=user.id,
        title="Test conv",
    )
    db_session.add(conversation)
    await db_session.flush()

    return {
        "configurable": {
            "db": db_session,
            "user_id": user.id,
            "conversation_id": conversation.id,
            "thread_id": str(conversation.id),
            "active_module": "chat",
        },
    }


async def _invoke(tool: BaseTool, args: dict, config):
    """Invoque un tool LangChain via son interface async."""
    return await tool.ainvoke(args, config=config)


async def _fetch_logs(db_session, tool_name: str) -> list[ToolCallLog]:
    """Récupère toutes les lignes de journalisation pour un tool donné."""
    rows = await db_session.execute(
        select(ToolCallLog).where(ToolCallLog.tool_name == tool_name)
    )
    return list(rows.scalars().all())


def _assert_12_columns_populated(log: ToolCallLog, *, logging_config, node_name: str) -> None:
    """Valide AC4 : les 12 colonnes sont correctement renseignées."""
    assert log.id is not None
    assert log.user_id == logging_config["configurable"]["user_id"]
    assert log.conversation_id == logging_config["configurable"]["conversation_id"]
    assert log.node_name == node_name
    assert log.tool_name is not None
    assert isinstance(log.tool_args, dict)
    assert "_input_size_bytes" in log.tool_args
    assert isinstance(log.tool_result, dict)
    assert "_output_size_bytes" in log.tool_result
    assert log.duration_ms is not None
    assert log.status == "success"
    assert log.error_message is None
    assert log.retry_count == 0
    assert log.created_at is not None


# ---------------------------------------------------------------------------
# AC1 + AC7 — sentinelle + garde anti-régression
# ---------------------------------------------------------------------------


class TestAllToolsWrapped:
    """AC1 + AC7 : 100% des tools exposés sont wrappés."""

    def test_all_tools_are_wrapped(self):
        """Chaque tool du registre agrégé porte la sentinelle."""
        assert len(INSTRUMENTED_TOOLS) >= 34
        not_wrapped = [
            t for t in INSTRUMENTED_TOOLS
            if not getattr(t, "_is_wrapped_by_with_retry", False)
        ]
        assert not not_wrapped, (
            f"Tools sans sentinelle _is_wrapped_by_with_retry: "
            f"{[t.name for t in not_wrapped]}"
        )

    def test_no_tool_escapes_wrapping(self):
        """Scan dynamique : tout @tool dans *_tools.py doit figurer dans le registre.

        Protection anti-régression pour Epic 10 : si un nouveau module
        déclare un @tool sans le wrapper et l'oublier dans INSTRUMENTED_TOOLS,
        ce test échoue.
        """
        module_paths = [
            "app.graph.tools.profiling_tools",
            "app.graph.tools.projects_tools",
            "app.graph.tools.maturity_tools",  # Story 10.3 — defense anti-regression
            "app.graph.tools.esg_tools",
            "app.graph.tools.carbon_tools",
            "app.graph.tools.financing_tools",
            "app.graph.tools.credit_tools",
            "app.graph.tools.application_tools",
            "app.graph.tools.document_tools",
            "app.graph.tools.action_plan_tools",
            "app.graph.tools.chat_tools",
            "app.graph.tools.interactive_tools",
            "app.graph.tools.guided_tour_tools",
        ]

        declared_tool_names: set[str] = set()
        for mod_path in module_paths:
            mod = importlib.import_module(mod_path)
            for _, obj in inspect.getmembers(mod):
                if isinstance(obj, BaseTool):
                    declared_tool_names.add(obj.name)

        registered_names = {t.name for t in INSTRUMENTED_TOOLS}

        missing = declared_tool_names - registered_names
        assert not missing, (
            f"Tools @tool déclarés mais absents de INSTRUMENTED_TOOLS : {missing}"
        )


# ---------------------------------------------------------------------------
# AC4 — validation exhaustive des 12 colonnes journalisées (stub)
# ---------------------------------------------------------------------------


class TestLogToolCallPopulatesAllColumns:
    """AC4 : les 12 colonnes du modèle ``ToolCallLog`` sont renseignées."""

    @pytest.mark.asyncio
    async def test_success_populates_all_12_columns(
        self, logging_config, db_session, reset_breaker
    ):
        @tool_decorator
        async def ac4_sample_tool(
            criterion_id: str, config: RunnableConfig = None
        ) -> str:
            """Test tool — valide la population des 12 colonnes."""
            return "dashboard summary"

        wrapped = with_retry(ac4_sample_tool, max_retries=2, node_name="chat")
        await _invoke(wrapped, {"criterion_id": "E01"}, logging_config)

        await db_session.flush()
        rows = await db_session.execute(
            select(ToolCallLog).where(ToolCallLog.tool_name == "ac4_sample_tool")
        )
        log = rows.scalars().first()
        assert log is not None

        # Les 12 colonnes
        assert log.id is not None
        assert log.user_id == logging_config["configurable"]["user_id"]
        assert log.conversation_id == logging_config["configurable"]["conversation_id"]
        assert log.node_name == "chat"
        assert log.tool_name == "ac4_sample_tool"
        assert isinstance(log.tool_args, dict)
        assert log.tool_args.get("criterion_id") == "E01"
        assert "_input_size_bytes" in log.tool_args
        assert isinstance(log.tool_result, dict)
        assert "_output_size_bytes" in log.tool_result
        assert log.duration_ms is not None
        assert log.status == "success"
        assert log.error_message is None
        assert log.retry_count == 0
        assert log.created_at is not None


# ---------------------------------------------------------------------------
# Smoke tests par module (stubs synthétiques) : 9 × 3 = 27 tests
#
# D2 Option B du review 9.7 : on conserve les stubs pour valider le
# comportement du wrapper ``with_retry`` indépendamment des services métier.
# ---------------------------------------------------------------------------


class _BaseModuleInstrumentationSmoke:
    """Squelette pour les tests smoke par module.

    Crée un tool de test local wrappé avec ``with_retry(node_name=<module>)``
    pour valider la chaîne wrapper → log sans dépendre des services métier.
    Vérifie que le comportement (success, error, retry) est reproductible
    indépendamment du tool de production.
    """

    MODULE_NAME: str = ""

    def _build_success_tool(self):
        @tool_decorator
        async def test_success_tool(config: RunnableConfig = None) -> str:  # noqa: D401
            """Stub de succès."""
            return "OK"

        return with_retry(test_success_tool, max_retries=2, node_name=self.MODULE_NAME)

    def _build_error_tool(self):
        @tool_decorator
        async def test_error_tool(config: RunnableConfig = None) -> str:  # noqa: D401
            """Stub d'erreur non-transient."""
            raise ValueError("deterministic failure")

        return with_retry(test_error_tool, max_retries=2, node_name=self.MODULE_NAME)

    def _build_flaky_tool(self, counter: dict):
        @tool_decorator
        async def test_flaky_tool(config: RunnableConfig = None) -> str:  # noqa: D401
            """Stub transient qui réussit au 2e essai."""
            counter["n"] += 1
            if counter["n"] == 1:
                raise asyncio.TimeoutError("transient")
            return "RECOVERED"

        return with_retry(test_flaky_tool, max_retries=2, node_name=self.MODULE_NAME)

    @pytest.mark.asyncio
    async def test_logs_success(self, logging_config, db_session, reset_breaker):
        tool = self._build_success_tool()
        result = await _invoke(tool, {}, logging_config)
        await db_session.flush()

        assert result == "OK"
        logs = await _fetch_logs(db_session, tool.name)
        assert any(log.status == "success" and log.retry_count == 0 for log in logs)
        assert logs[0].node_name == self.MODULE_NAME

    @pytest.mark.asyncio
    async def test_logs_error(
        self, logging_config, db_session, reset_breaker, mock_sleep
    ):
        tool = self._build_error_tool()
        result = await _invoke(tool, {}, logging_config)
        await db_session.flush()

        assert "Erreur" in result
        logs = await _fetch_logs(db_session, tool.name)
        assert any(log.status == "error" and log.retry_count == 0 for log in logs)
        assert logs[0].node_name == self.MODULE_NAME

    @pytest.mark.asyncio
    async def test_retries_on_transient(
        self, logging_config, db_session, reset_breaker, mock_sleep
    ):
        counter = {"n": 0}
        tool = self._build_flaky_tool(counter)
        result = await _invoke(tool, {}, logging_config)
        await db_session.flush()

        assert result == "RECOVERED"
        assert counter["n"] == 2

        logs = await _fetch_logs(db_session, tool.name)
        statuses = {log.status for log in logs}
        assert "error" in statuses
        assert "retry_success" in statuses


class TestProfilingInstrumentationSmoke(_BaseModuleInstrumentationSmoke):
    MODULE_NAME = "profiling"


class TestEsgInstrumentationSmoke(_BaseModuleInstrumentationSmoke):
    MODULE_NAME = "esg_scoring"


class TestCarbonInstrumentationSmoke(_BaseModuleInstrumentationSmoke):
    MODULE_NAME = "carbon"


class TestFinancingInstrumentationSmoke(_BaseModuleInstrumentationSmoke):
    MODULE_NAME = "financing"


class TestCreditInstrumentationSmoke(_BaseModuleInstrumentationSmoke):
    MODULE_NAME = "credit"


class TestApplicationInstrumentationSmoke(_BaseModuleInstrumentationSmoke):
    MODULE_NAME = "application"


class TestDocumentInstrumentationSmoke(_BaseModuleInstrumentationSmoke):
    MODULE_NAME = "document"


class TestActionPlanInstrumentationSmoke(_BaseModuleInstrumentationSmoke):
    MODULE_NAME = "action_plan"


class TestChatInstrumentationSmoke(_BaseModuleInstrumentationSmoke):
    MODULE_NAME = "chat"


# ---------------------------------------------------------------------------
# Tests prod par module (D2 Option B) : 9 modules × 2 tests = 18 tests
#
# Chaque test invoque le VRAI tool de prod (XXX_TOOLS[0]) avec le service
# métier mocké via monkeypatch. Valide la chaîne réelle @tool → with_retry →
# service → tool_call_logs.
# ---------------------------------------------------------------------------


# --- Profiling -------------------------------------------------------------


class TestProfilingProdInstrumentation:
    """AC1+AC2+AC4 : instrumentation du vrai tool ``update_company_profile``."""

    @pytest.mark.asyncio
    async def test_profiling_prod_logs_success(
        self, logging_config, db_session, reset_breaker, monkeypatch
    ):
        from app.graph.tools.profiling_tools import PROFILING_TOOLS

        tool = PROFILING_TOOLS[0]  # update_company_profile wrappé
        assert tool.name == "update_company_profile"

        mock_profile = MagicMock()
        monkeypatch.setattr(
            "app.modules.company.service.get_or_create_profile",
            AsyncMock(return_value=mock_profile),
        )
        monkeypatch.setattr(
            "app.modules.company.service.update_profile",
            AsyncMock(
                return_value=(
                    mock_profile,
                    [{"field": "company_name", "value": "EcoAfrik", "label": "Nom de l'entreprise"}],
                    [],
                )
            ),
        )
        monkeypatch.setattr(
            "app.graph.tools.profiling_tools.compute_completion",
            lambda _p: MagicMock(
                identity_completion=25.0,
                esg_completion=0.0,
                overall_completion=12.5,
            ),
        )

        result = await tool.ainvoke({"company_name": "EcoAfrik"}, config=logging_config)
        assert "EcoAfrik" in result or "Profil mis à jour" in result

        await db_session.flush()
        logs = await _fetch_logs(db_session, tool.name)
        assert len(logs) >= 1
        success_log = next(log for log in logs if log.status == "success")
        _assert_12_columns_populated(
            success_log, logging_config=logging_config, node_name="profiling"
        )

    @pytest.mark.asyncio
    async def test_profiling_prod_retries_on_transient(
        self, logging_config, db_session, reset_breaker, mock_sleep, monkeypatch
    ):
        from app.graph.tools.profiling_tools import PROFILING_TOOLS

        tool = PROFILING_TOOLS[0]
        mock_profile = MagicMock()

        counter = {"n": 0}

        async def flaky_get_or_create(*_a, **_kw):
            counter["n"] += 1
            if counter["n"] == 1:
                raise asyncio.TimeoutError("transient DB timeout")
            return mock_profile

        monkeypatch.setattr(
            "app.modules.company.service.get_or_create_profile", flaky_get_or_create
        )
        monkeypatch.setattr(
            "app.modules.company.service.update_profile",
            AsyncMock(
                return_value=(
                    mock_profile,
                    [{"field": "company_name", "value": "X", "label": "Nom"}],
                    [],
                )
            ),
        )
        monkeypatch.setattr(
            "app.graph.tools.profiling_tools.compute_completion",
            lambda _p: MagicMock(
                identity_completion=12.5, esg_completion=0.0, overall_completion=6.2
            ),
        )

        await tool.ainvoke({"company_name": "X"}, config=logging_config)
        await db_session.flush()

        assert counter["n"] == 2
        logs = await _fetch_logs(db_session, tool.name)
        statuses = {log.status for log in logs}
        assert "error" in statuses
        assert "retry_success" in statuses


# --- ESG Scoring -----------------------------------------------------------


class TestEsgProdInstrumentation:
    """AC1+AC2+AC4 : instrumentation du vrai tool ``create_esg_assessment``."""

    @pytest.mark.asyncio
    async def test_esg_prod_logs_success(
        self, logging_config, db_session, reset_breaker, monkeypatch
    ):
        from app.graph.tools.esg_tools import ESG_TOOLS

        tool = ESG_TOOLS[0]  # create_esg_assessment
        assert tool.name == "create_esg_assessment"

        mock_assessment = MagicMock()
        mock_assessment.id = uuid.uuid4()
        mock_assessment.sector = "services"
        status_enum = MagicMock()
        status_enum.value = "draft"
        mock_assessment.status = status_enum

        monkeypatch.setattr(
            "app.modules.esg.service.create_assessment",
            AsyncMock(return_value=mock_assessment),
        )

        result = await tool.ainvoke({}, config=logging_config)
        assert "creee avec succes" in result or "draft" in result

        await db_session.flush()
        logs = await _fetch_logs(db_session, tool.name)
        success_log = next(log for log in logs if log.status == "success")
        _assert_12_columns_populated(
            success_log, logging_config=logging_config, node_name="esg_scoring"
        )

    @pytest.mark.asyncio
    async def test_esg_prod_retries_on_transient(
        self, logging_config, db_session, reset_breaker, mock_sleep, monkeypatch
    ):
        from app.graph.tools.esg_tools import ESG_TOOLS

        tool = ESG_TOOLS[0]

        counter = {"n": 0}
        mock_assessment = MagicMock()
        mock_assessment.id = uuid.uuid4()
        mock_assessment.sector = "services"
        status_enum = MagicMock()
        status_enum.value = "draft"
        mock_assessment.status = status_enum

        async def flaky_create(*_a, **_kw):
            counter["n"] += 1
            if counter["n"] == 1:
                raise asyncio.TimeoutError("transient")
            return mock_assessment

        monkeypatch.setattr(
            "app.modules.esg.service.create_assessment", flaky_create
        )

        await tool.ainvoke({}, config=logging_config)
        await db_session.flush()

        assert counter["n"] == 2
        logs = await _fetch_logs(db_session, tool.name)
        statuses = {log.status for log in logs}
        assert "error" in statuses
        assert "retry_success" in statuses


# --- Carbon ----------------------------------------------------------------


class TestCarbonProdInstrumentation:
    """AC1+AC2+AC4 : instrumentation du vrai tool ``create_carbon_assessment``."""

    @pytest.mark.asyncio
    async def test_carbon_prod_logs_success(
        self, logging_config, db_session, reset_breaker, monkeypatch
    ):
        from app.graph.tools.carbon_tools import CARBON_TOOLS

        tool = CARBON_TOOLS[0]  # create_carbon_assessment
        assert tool.name == "create_carbon_assessment"

        mock_assessment = MagicMock()
        mock_assessment.id = uuid.uuid4()
        mock_assessment.year = 2025
        mock_assessment.sector = "agriculture"

        mock_profile = MagicMock()
        mock_profile.sector = "agriculture"

        monkeypatch.setattr(
            "app.modules.carbon.service.create_assessment",
            AsyncMock(return_value=mock_assessment),
        )
        monkeypatch.setattr(
            "app.modules.company.service.get_profile",
            AsyncMock(return_value=mock_profile),
        )

        result = await tool.ainvoke({"year": 2025}, config=logging_config)
        assert "success" in result

        await db_session.flush()
        logs = await _fetch_logs(db_session, tool.name)
        success_log = next(log for log in logs if log.status == "success")
        _assert_12_columns_populated(
            success_log, logging_config=logging_config, node_name="carbon"
        )

    @pytest.mark.asyncio
    async def test_carbon_prod_retries_on_transient(
        self, logging_config, db_session, reset_breaker, mock_sleep, monkeypatch
    ):
        from app.graph.tools.carbon_tools import CARBON_TOOLS

        tool = CARBON_TOOLS[0]

        counter = {"n": 0}
        mock_assessment = MagicMock()
        mock_assessment.id = uuid.uuid4()
        mock_assessment.year = 2025
        mock_assessment.sector = "agriculture"

        async def flaky_create(*_a, **_kw):
            counter["n"] += 1
            if counter["n"] == 1:
                raise asyncio.TimeoutError("transient")
            return mock_assessment

        monkeypatch.setattr(
            "app.modules.carbon.service.create_assessment", flaky_create
        )
        monkeypatch.setattr(
            "app.modules.company.service.get_profile",
            AsyncMock(return_value=None),
        )

        await tool.ainvoke({"year": 2025}, config=logging_config)
        await db_session.flush()

        assert counter["n"] == 2
        logs = await _fetch_logs(db_session, tool.name)
        statuses = {log.status for log in logs}
        assert "error" in statuses
        assert "retry_success" in statuses


# --- Financing -------------------------------------------------------------


class TestFinancingProdInstrumentation:
    """AC1+AC2+AC4 : instrumentation du vrai tool ``search_compatible_funds``."""

    @pytest.mark.asyncio
    async def test_financing_prod_logs_success(
        self, logging_config, db_session, reset_breaker, monkeypatch
    ):
        from app.graph.tools.financing_tools import FINANCING_TOOLS

        tool = FINANCING_TOOLS[0]  # search_compatible_funds
        assert tool.name == "search_compatible_funds"

        monkeypatch.setattr(
            "app.modules.company.service.get_profile",
            AsyncMock(return_value=None),
        )
        monkeypatch.setattr(
            "app.modules.financing.service.get_fund_matches",
            AsyncMock(return_value=[]),
        )

        result = await tool.ainvoke({}, config=logging_config)
        assert "Aucun" in result or "compatibles" in result

        await db_session.flush()
        logs = await _fetch_logs(db_session, tool.name)
        success_log = next(log for log in logs if log.status == "success")
        _assert_12_columns_populated(
            success_log, logging_config=logging_config, node_name="financing"
        )

    @pytest.mark.asyncio
    async def test_financing_prod_retries_on_transient(
        self, logging_config, db_session, reset_breaker, mock_sleep, monkeypatch
    ):
        from app.graph.tools.financing_tools import FINANCING_TOOLS

        tool = FINANCING_TOOLS[0]

        counter = {"n": 0}

        async def flaky_matches(*_a, **_kw):
            counter["n"] += 1
            if counter["n"] == 1:
                raise asyncio.TimeoutError("transient")
            return []

        monkeypatch.setattr(
            "app.modules.company.service.get_profile",
            AsyncMock(return_value=None),
        )
        monkeypatch.setattr(
            "app.modules.financing.service.get_fund_matches", flaky_matches
        )

        await tool.ainvoke({}, config=logging_config)
        await db_session.flush()

        assert counter["n"] == 2
        logs = await _fetch_logs(db_session, tool.name)
        statuses = {log.status for log in logs}
        assert "error" in statuses
        assert "retry_success" in statuses


# --- Credit ----------------------------------------------------------------


class TestCreditProdInstrumentation:
    """AC1+AC2+AC4 : instrumentation du vrai tool ``generate_credit_score``."""

    @pytest.mark.asyncio
    async def test_credit_prod_logs_success(
        self, logging_config, db_session, reset_breaker, monkeypatch
    ):
        from app.graph.tools.credit_tools import CREDIT_TOOLS

        tool = CREDIT_TOOLS[0]  # generate_credit_score
        assert tool.name == "generate_credit_score"

        mock_score = MagicMock(
            combined_score=72,
            solvability_score=68,
            green_impact_score=76,
            risk_level="moyen",
            version=1,
        )
        monkeypatch.setattr(
            "app.modules.credit.service.generate_credit_score",
            AsyncMock(return_value=mock_score),
        )

        result = await tool.ainvoke({}, config=logging_config)
        assert "72" in result

        await db_session.flush()
        logs = await _fetch_logs(db_session, tool.name)
        success_log = next(log for log in logs if log.status == "success")
        _assert_12_columns_populated(
            success_log, logging_config=logging_config, node_name="credit"
        )

    @pytest.mark.asyncio
    async def test_credit_prod_retries_on_transient(
        self, logging_config, db_session, reset_breaker, mock_sleep, monkeypatch
    ):
        from app.graph.tools.credit_tools import CREDIT_TOOLS

        tool = CREDIT_TOOLS[0]

        counter = {"n": 0}
        mock_score = MagicMock(
            combined_score=72,
            solvability_score=68,
            green_impact_score=76,
            risk_level="moyen",
            version=1,
        )

        async def flaky_gen(*_a, **_kw):
            counter["n"] += 1
            if counter["n"] == 1:
                raise asyncio.TimeoutError("transient")
            return mock_score

        monkeypatch.setattr(
            "app.modules.credit.service.generate_credit_score", flaky_gen
        )

        await tool.ainvoke({}, config=logging_config)
        await db_session.flush()

        assert counter["n"] == 2
        logs = await _fetch_logs(db_session, tool.name)
        statuses = {log.status for log in logs}
        assert "error" in statuses
        assert "retry_success" in statuses


# --- Application -----------------------------------------------------------


class TestApplicationProdInstrumentation:
    """AC1+AC2+AC4 : instrumentation du vrai tool ``submit_fund_application_draft``."""

    @pytest.mark.asyncio
    async def test_application_prod_logs_success(
        self, logging_config, db_session, reset_breaker, monkeypatch
    ):
        from app.graph.tools.application_tools import APPLICATION_TOOLS

        tool = APPLICATION_TOOLS[0]  # submit_fund_application_draft
        assert tool.name == "submit_fund_application_draft"

        mock_application = MagicMock()
        mock_application.id = uuid.uuid4()
        mock_application.status = "draft"
        mock_application.fund_id = uuid.uuid4()

        monkeypatch.setattr(
            "app.modules.applications.service.create_application",
            AsyncMock(return_value=mock_application),
        )

        fund_id = str(uuid.uuid4())
        result = await tool.ainvoke({"fund_id": fund_id}, config=logging_config)
        assert "cree avec succes" in result or "draft" in result

        await db_session.flush()
        logs = await _fetch_logs(db_session, tool.name)
        success_log = next(log for log in logs if log.status == "success")
        _assert_12_columns_populated(
            success_log, logging_config=logging_config, node_name="application"
        )

    @pytest.mark.asyncio
    async def test_application_prod_retries_on_transient(
        self, logging_config, db_session, reset_breaker, mock_sleep, monkeypatch
    ):
        from app.graph.tools.application_tools import APPLICATION_TOOLS

        tool = APPLICATION_TOOLS[0]

        counter = {"n": 0}
        mock_application = MagicMock()
        mock_application.id = uuid.uuid4()
        mock_application.status = "draft"
        mock_application.fund_id = uuid.uuid4()

        async def flaky_create(*_a, **_kw):
            counter["n"] += 1
            if counter["n"] == 1:
                raise asyncio.TimeoutError("transient")
            return mock_application

        monkeypatch.setattr(
            "app.modules.applications.service.create_application", flaky_create
        )

        fund_id = str(uuid.uuid4())
        await tool.ainvoke({"fund_id": fund_id}, config=logging_config)
        await db_session.flush()

        assert counter["n"] == 2
        logs = await _fetch_logs(db_session, tool.name)
        statuses = {log.status for log in logs}
        assert "error" in statuses
        assert "retry_success" in statuses


# --- Document --------------------------------------------------------------


class TestDocumentProdInstrumentation:
    """AC1+AC2+AC4 : instrumentation du vrai tool ``analyze_uploaded_document``."""

    @pytest.mark.asyncio
    async def test_document_prod_logs_success(
        self, logging_config, db_session, reset_breaker, monkeypatch
    ):
        from app.graph.tools.document_tools import DOCUMENT_TOOLS

        tool = DOCUMENT_TOOLS[0]  # analyze_uploaded_document
        assert tool.name == "analyze_uploaded_document"

        mock_document = MagicMock()
        mock_document.id = uuid.uuid4()
        mock_document.filename = "rapport-esg.pdf"

        mock_analysis = MagicMock()
        mock_analysis.document_type = "esg_report"
        mock_analysis.summary = "Rapport ESG EcoAfrik"
        mock_analysis.key_findings = ["Score E: 72"]
        mock_analysis.confidence_score = 0.85

        monkeypatch.setattr(
            "app.modules.documents.service.get_document",
            AsyncMock(return_value=mock_document),
        )
        monkeypatch.setattr(
            "app.modules.documents.service.analyze_document",
            AsyncMock(return_value=mock_analysis),
        )

        doc_id = str(mock_document.id)
        result = await tool.ainvoke({"document_id": doc_id}, config=logging_config)
        assert "rapport" in result.lower() or "Analyse" in result

        await db_session.flush()
        logs = await _fetch_logs(db_session, tool.name)
        success_log = next(log for log in logs if log.status == "success")
        _assert_12_columns_populated(
            success_log, logging_config=logging_config, node_name="document"
        )

    @pytest.mark.asyncio
    async def test_document_prod_retries_on_transient(
        self, logging_config, db_session, reset_breaker, mock_sleep, monkeypatch
    ):
        from app.graph.tools.document_tools import DOCUMENT_TOOLS

        tool = DOCUMENT_TOOLS[0]

        mock_document = MagicMock()
        mock_document.id = uuid.uuid4()
        mock_document.filename = "doc.pdf"

        mock_analysis = MagicMock()
        mock_analysis.document_type = "other"
        mock_analysis.summary = "Résumé"
        mock_analysis.key_findings = []
        mock_analysis.confidence_score = 0.5

        counter = {"n": 0}

        async def flaky_get_doc(*_a, **_kw):
            counter["n"] += 1
            if counter["n"] == 1:
                raise asyncio.TimeoutError("transient")
            return mock_document

        monkeypatch.setattr(
            "app.modules.documents.service.get_document", flaky_get_doc
        )
        monkeypatch.setattr(
            "app.modules.documents.service.analyze_document",
            AsyncMock(return_value=mock_analysis),
        )

        await tool.ainvoke(
            {"document_id": str(uuid.uuid4())}, config=logging_config
        )
        await db_session.flush()

        assert counter["n"] == 2
        logs = await _fetch_logs(db_session, tool.name)
        statuses = {log.status for log in logs}
        assert "error" in statuses
        assert "retry_success" in statuses


# --- Action Plan -----------------------------------------------------------


class TestActionPlanProdInstrumentation:
    """AC1+AC2+AC4 : instrumentation du vrai tool ``generate_action_plan``."""

    @pytest.mark.asyncio
    async def test_action_plan_prod_logs_success(
        self, logging_config, db_session, reset_breaker, monkeypatch
    ):
        from app.graph.tools.action_plan_tools import ACTION_PLAN_TOOLS

        tool = ACTION_PLAN_TOOLS[0]  # generate_action_plan
        assert tool.name == "generate_action_plan"

        mock_plan = MagicMock()
        mock_plan.title = "Plan ESG 12 mois"
        mock_plan.timeframe = 12
        mock_plan.total_actions = 10
        mock_plan.items = []

        monkeypatch.setattr(
            "app.modules.action_plan.service.generate_action_plan",
            AsyncMock(return_value=mock_plan),
        )

        result = await tool.ainvoke({"timeframe": 12}, config=logging_config)
        assert "Plan" in result or "12" in result

        await db_session.flush()
        logs = await _fetch_logs(db_session, tool.name)
        success_log = next(log for log in logs if log.status == "success")
        _assert_12_columns_populated(
            success_log, logging_config=logging_config, node_name="action_plan"
        )

    @pytest.mark.asyncio
    async def test_action_plan_prod_retries_on_transient(
        self, logging_config, db_session, reset_breaker, mock_sleep, monkeypatch
    ):
        from app.graph.tools.action_plan_tools import ACTION_PLAN_TOOLS

        tool = ACTION_PLAN_TOOLS[0]

        counter = {"n": 0}
        mock_plan = MagicMock()
        mock_plan.title = "Plan"
        mock_plan.timeframe = 12
        mock_plan.total_actions = 5
        mock_plan.items = []

        async def flaky_gen(*_a, **_kw):
            counter["n"] += 1
            if counter["n"] == 1:
                raise asyncio.TimeoutError("transient")
            return mock_plan

        monkeypatch.setattr(
            "app.modules.action_plan.service.generate_action_plan", flaky_gen
        )

        await tool.ainvoke({"timeframe": 12}, config=logging_config)
        await db_session.flush()

        assert counter["n"] == 2
        logs = await _fetch_logs(db_session, tool.name)
        statuses = {log.status for log in logs}
        assert "error" in statuses
        assert "retry_success" in statuses


# --- Chat ------------------------------------------------------------------


class TestChatProdInstrumentation:
    """AC1+AC2+AC4 : instrumentation du vrai tool ``get_user_dashboard_summary``."""

    @pytest.mark.asyncio
    async def test_chat_prod_logs_success(
        self, logging_config, db_session, reset_breaker, monkeypatch
    ):
        from app.graph.tools.chat_tools import CHAT_TOOLS

        tool = CHAT_TOOLS[0]  # get_user_dashboard_summary
        assert tool.name == "get_user_dashboard_summary"

        monkeypatch.setattr(
            "app.modules.dashboard.service.get_dashboard_summary",
            AsyncMock(
                return_value={
                    "esg": {
                        "overall_score": 65,
                        "environment_score": 70,
                        "social_score": 60,
                        "governance_score": 65,
                    },
                    "carbon": {"total_emissions_tco2e": 12.5, "year": 2025},
                    "credit": {"combined_score": 72, "risk_level": "moyen"},
                    "financing": {"matched_funds": 3, "interested_funds": 1},
                }
            ),
        )

        result = await tool.ainvoke({}, config=logging_config)
        assert "65" in result or "ESG" in result

        await db_session.flush()
        logs = await _fetch_logs(db_session, tool.name)
        success_log = next(log for log in logs if log.status == "success")
        _assert_12_columns_populated(
            success_log, logging_config=logging_config, node_name="chat"
        )

    @pytest.mark.asyncio
    async def test_chat_prod_retries_on_transient(
        self, logging_config, db_session, reset_breaker, mock_sleep, monkeypatch
    ):
        from app.graph.tools.chat_tools import CHAT_TOOLS

        tool = CHAT_TOOLS[0]

        counter = {"n": 0}

        async def flaky_summary(*_a, **_kw):
            counter["n"] += 1
            if counter["n"] == 1:
                raise asyncio.TimeoutError("transient")
            return {
                "esg": None,
                "carbon": None,
                "credit": None,
                "financing": {"matched_funds": 0, "interested_funds": 0},
            }

        monkeypatch.setattr(
            "app.modules.dashboard.service.get_dashboard_summary", flaky_summary
        )

        await tool.ainvoke({}, config=logging_config)
        await db_session.flush()

        assert counter["n"] == 2
        logs = await _fetch_logs(db_session, tool.name)
        statuses = {log.status for log in logs}
        assert "error" in statuses
        assert "retry_success" in statuses
