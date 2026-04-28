"""Tests V8-AXE2 — validation runtime relachee + fallback template (Lecon 40 §4decies).

Couvre :
- json_repair (3 cas : trailing comma, single quotes, unquoted keys)
- generate_fallback_actions (substitution placeholders)
- persist_fallback_plan (declenchement apres LLMGuardError + persistance 10 actions)
- generate_action_plan tool (mode batch incremental >=5 actions)

Reference ARCHIVE V7.1 : tests-manuels-vague-7-2026-04-28.md.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.llm_guards import LLMGuardError
from app.graph.tools.action_plan_tools import generate_action_plan
from app.services.action_plan_fallback import (
    generate_fallback_actions,
    persist_fallback_plan,
)
from app.services.json_repair import repair_json


# === Helpers ===


def _make_action_item(**overrides):
    item = MagicMock()
    defaults = {
        "id": uuid.uuid4(),
        "title": "Action test",
        "category": "environment",
        "priority": "high",
        "status": MagicMock(value="todo"),
        "completion_percentage": 0,
    }
    defaults.update(overrides)
    for k, v in defaults.items():
        setattr(item, k, v)
    return item


def _make_action_plan(item_count: int = 10, **overrides):
    plan = MagicMock()
    defaults = {
        "id": uuid.uuid4(),
        "title": "Plan d'action ESG 12 mois",
        "timeframe": 12,
        "total_actions": item_count,
        "completed_actions": 0,
        "items": [_make_action_item() for _ in range(item_count)],
    }
    defaults.update(overrides)
    for k, v in defaults.items():
        setattr(plan, k, v)
    return plan


# === json_repair ===


class TestJsonRepair:
    def test_action_plan_json_repair_trailing_comma(self):
        """JSON malformé avec trailing comma est réparé."""
        malformed = '[{"title": "a", "category": "environment",},]'
        result = repair_json(malformed)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["title"] == "a"

    def test_action_plan_json_repair_unquoted_keys(self):
        """JSON avec cles non quotees est repare."""
        malformed = '[{title: "a", category: "social"}]'
        result = repair_json(malformed)
        assert isinstance(result, list)
        assert result[0]["category"] == "social"

    def test_action_plan_json_repair_returns_none_on_unrecoverable(self):
        """JSON irreparable retourne None."""
        garbage = "<html>not json at all</html>"
        assert repair_json(garbage) is None


# === generate_fallback_actions ===


class TestFallbackTemplate:
    def test_action_plan_template_substitution(self):
        """Template substitue {{sector}} {{employee_count}} {{country}}."""
        profile = {
            "sector": "agriculture",
            "employee_count": 25,
            "country": "Senegal",
        }
        actions = generate_fallback_actions(profile, timeframe=12)

        assert len(actions) == 10
        # Au moins une action doit contenir le secteur substitue
        sector_present = any("agriculture" in a["title"] or "agriculture" in a["description"] for a in actions)
        assert sector_present, "Le placeholder {{sector}} n'a pas ete substitue"

        # Au moins une action doit contenir le nombre d'employes
        emp_present = any("25" in a["description"] for a in actions)
        assert emp_present, "Le placeholder {{employee_count}} n'a pas ete substitue"

        # Aucune action ne doit conserver de placeholder non substitue
        for a in actions:
            assert "{{" not in a["title"], f"Placeholder restant : {a['title']}"
            assert "{{" not in a["description"], f"Placeholder restant : {a['description']}"

    def test_action_plan_fallback_categories_distribution(self):
        """Le template respecte la repartition cible : 3 env / 2 soc / 2 gov / 2 fin / 1 carbon."""
        profile = {"sector": "energy", "employee_count": 50, "country": "Mali"}
        actions = generate_fallback_actions(profile, timeframe=12)

        from collections import Counter

        counts = Counter(a["category"] for a in actions)
        assert counts["environment"] == 3
        assert counts["social"] == 2
        assert counts["governance"] == 2
        assert counts["financing"] == 2
        assert counts["carbon"] == 1


# === persist_fallback_plan + tool integration ===


class TestActionPlanFallbackPersistence:
    @pytest.mark.asyncio
    async def test_action_plan_fallback_persists_10_actions(self, db_session):
        """Fallback persiste effectivement 10 actions en BDD."""
        from sqlalchemy import select

        from app.models.action_plan import ActionItem, ActionPlan
        from app.models.company import CompanyProfile

        user_id = uuid.uuid4()

        # Pre-requis : creer un profil entreprise
        profile = CompanyProfile(
            user_id=user_id,
            company_name="AgriVert SARL",
            employee_count=15,
            country="Senegal",
        )
        db_session.add(profile)
        await db_session.commit()

        # Declencher le fallback
        plan = await persist_fallback_plan(db=db_session, user_id=user_id, timeframe=12)

        assert plan is not None
        assert plan.total_actions == 10

        # Verifier en BDD
        items_result = await db_session.execute(
            select(ActionItem).where(ActionItem.plan_id == plan.id)
        )
        items = list(items_result.scalars().all())
        assert len(items) == 10

        plan_result = await db_session.execute(
            select(ActionPlan).where(ActionPlan.user_id == user_id)
        )
        persisted = plan_result.scalar_one()
        assert "fallback" in persisted.title.lower()


class TestGenerateActionPlanToolFallback:
    @pytest.mark.asyncio
    @patch(
        "app.services.action_plan_fallback.persist_fallback_plan",
        new_callable=AsyncMock,
    )
    @patch(
        "app.modules.action_plan.service.generate_action_plan",
        new_callable=AsyncMock,
        side_effect=LLMGuardError("count_below_min", "action_plan", {"count": 0}),
    )
    async def test_action_plan_fallback_template_after_llm_guard_error(
        self, mock_gen, mock_fallback, mock_config
    ):
        """Si LLMGuardError leve apres 3 retries, fallback template declenche."""
        fallback_plan = _make_action_plan(item_count=10)
        fallback_plan.title = "Plan d'action ESG 12 mois — AgriVert (fallback)"
        mock_fallback.return_value = fallback_plan

        result = await generate_action_plan.ainvoke(
            {"timeframe": 12}, config=mock_config
        )

        mock_fallback.assert_awaited_once()
        assert "fallback" in result.lower()
        assert "ERREUR" not in result

    @pytest.mark.asyncio
    @patch(
        "app.services.action_plan_fallback.persist_fallback_plan",
        new_callable=AsyncMock,
    )
    @patch(
        "app.modules.action_plan.service.generate_action_plan",
        new_callable=AsyncMock,
    )
    async def test_action_plan_validation_relaxed_5_actions_succeeds(
        self, mock_gen, mock_fallback, mock_config
    ):
        """Tool accepte batch >=5 actions (mode incremental, pas de fallback)."""
        plan = _make_action_plan(item_count=5)
        mock_gen.return_value = plan

        result = await generate_action_plan.ainvoke(
            {"timeframe": 12}, config=mock_config
        )

        # Pas de fallback declenche
        mock_fallback.assert_not_awaited()

        assert "ERREUR" not in result
        assert "5/10" in result
        assert "incremental" in result.lower() or "incrémental" in result.lower()
        # Le message doit inviter a continuer
        assert "manque 5" in result.lower() or "manque" in result.lower()

    @pytest.mark.asyncio
    @patch(
        "app.services.action_plan_fallback.persist_fallback_plan",
        new_callable=AsyncMock,
    )
    @patch(
        "app.modules.action_plan.service.generate_action_plan",
        new_callable=AsyncMock,
    )
    async def test_action_plan_incremental_batch_message_format(
        self, mock_gen, mock_fallback, mock_config
    ):
        """Tool retourne explicitement X actions sauvegardees, manque Y pour cible 10."""
        plan = _make_action_plan(item_count=7)
        mock_gen.return_value = plan

        result = await generate_action_plan.ainvoke(
            {"timeframe": 12}, config=mock_config
        )

        mock_fallback.assert_not_awaited()
        assert "7/10" in result
        # 10 - 7 = 3 manquantes
        assert "manque 3" in result.lower()

    @pytest.mark.asyncio
    @patch(
        "app.services.action_plan_fallback.persist_fallback_plan",
        new_callable=AsyncMock,
    )
    @patch(
        "app.modules.action_plan.service.generate_action_plan",
        new_callable=AsyncMock,
    )
    async def test_action_plan_count_below_min_triggers_fallback(
        self, mock_gen, mock_fallback, mock_config
    ):
        """Review finding #4 : count=4 (sans LLMGuardError) -> fallback path step-3.

        Verifie la branche distincte de declenchement par `count_below_min`,
        avec la bonne raison passee a persist_fallback_plan.
        """
        partial_plan = _make_action_plan(item_count=4)
        mock_gen.return_value = partial_plan

        fallback_plan = _make_action_plan(item_count=10)
        fallback_plan.title = "Plan d'action ESG 12 mois — Test (fallback)"
        mock_fallback.return_value = fallback_plan

        result = await generate_action_plan.ainvoke(
            {"timeframe": 12}, config=mock_config
        )

        mock_fallback.assert_awaited_once()
        call_kwargs = mock_fallback.await_args.kwargs
        assert call_kwargs.get("reason") == "count_below_min"
        assert "fallback" in result.lower()


class TestFallbackTemplateError:
    """Review finding #5 : template introuvable / corrompu doit lever
    FallbackTemplateError (et non FileNotFoundError / JSONDecodeError nu)."""

    def test_action_plan_fallback_raises_on_missing_template(self, monkeypatch):
        from pathlib import Path

        from app.services import action_plan_fallback as mod

        monkeypatch.setattr(mod, "_TEMPLATE_PATH", Path("/non/existant.json"))

        with pytest.raises(mod.FallbackTemplateError):
            mod._load_template()

    def test_action_plan_fallback_raises_on_corrupt_template(self, tmp_path, monkeypatch):
        from app.services import action_plan_fallback as mod

        bad = tmp_path / "bad.json"
        bad.write_text("{not: valid json,,,", encoding="utf-8")
        monkeypatch.setattr(mod, "_TEMPLATE_PATH", bad)

        with pytest.raises(mod.FallbackTemplateError):
            mod._load_template()
