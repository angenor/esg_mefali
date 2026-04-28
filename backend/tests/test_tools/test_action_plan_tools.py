"""Tests unitaires pour les tools plan d'action."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.graph.tools.action_plan_tools import (
    ACTION_PLAN_TOOLS,
    generate_action_plan,
    get_action_plan,
    update_action_item,
)


def _make_action_item(**overrides):
    """Creer un mock d'ActionItem."""
    item = MagicMock()
    defaults = {
        "id": uuid.uuid4(),
        "title": "Realiser un audit energetique",
        "category": "environment",
        "priority": "high",
        "status": MagicMock(value="pending"),
        "deadline_months": 3,
        "completion_percentage": 0,
    }
    defaults.update(overrides)
    for key, value in defaults.items():
        setattr(item, key, value)
    return item


def _make_action_plan(**overrides):
    """Creer un mock d'ActionPlan.

    Defaut a 10 items pour respecter la garde runtime BUG-V6-005
    (`generate_action_plan` exige >= 10 actions). Les tests qui veulent
    un plan plus court doivent override `items` explicitement.
    """
    plan = MagicMock()
    defaults = {
        "id": uuid.uuid4(),
        "title": "Plan d'action ESG 12 mois",
        "timeframe": 12,
        "total_actions": 10,
        "completed_actions": 2,
        "items": [_make_action_item() for _ in range(10)],
    }
    defaults.update(overrides)
    for key, value in defaults.items():
        setattr(plan, key, value)
    return plan


class TestGenerateActionPlan:
    """Tests pour generate_action_plan."""

    @pytest.mark.asyncio
    @patch("app.modules.action_plan.service.generate_action_plan", new_callable=AsyncMock)
    async def test_generate_success(self, mock_generate, mock_config):
        """Generation d'un plan retourne le resume avec nombre d'actions."""
        plan = _make_action_plan()
        mock_generate.return_value = plan

        result = await generate_action_plan.ainvoke(
            {"timeframe": 12},
            config=mock_config,
        )

        assert "12" in result
        assert "10" in result or "actions" in result.lower()
        mock_generate.assert_awaited_once()

    @pytest.mark.asyncio
    @patch(
        "app.modules.action_plan.service.generate_action_plan",
        new_callable=AsyncMock,
        side_effect=Exception("LLM timeout"),
    )
    async def test_generate_handles_error(self, mock_generate, mock_config):
        """Erreur retourne un message lisible."""
        result = await generate_action_plan.ainvoke(
            {"timeframe": 12},
            config=mock_config,
        )

        assert "Erreur" in result


class TestUpdateActionItem:
    """Tests pour update_action_item."""

    @pytest.mark.asyncio
    @patch("app.modules.action_plan.service.update_action_item", new_callable=AsyncMock)
    async def test_update_status(self, mock_update, mock_config):
        """Mise a jour du statut retourne la confirmation."""
        item = _make_action_item(status=MagicMock(value="in_progress"))
        mock_update.return_value = item

        action_id = str(uuid.uuid4())
        result = await update_action_item.ainvoke(
            {"action_id": action_id, "status": "in_progress"},
            config=mock_config,
        )

        assert "in_progress" in result or "mise" in result.lower() or "jour" in result.lower()
        mock_update.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.modules.action_plan.service.update_action_item", new_callable=AsyncMock)
    async def test_update_completion(self, mock_update, mock_config):
        """Mise a jour du pourcentage de completion."""
        item = _make_action_item(completion_percentage=75)
        mock_update.return_value = item

        action_id = str(uuid.uuid4())
        result = await update_action_item.ainvoke(
            {"action_id": action_id, "completion_percentage": 75},
            config=mock_config,
        )

        assert "75" in result
        mock_update.assert_awaited_once()

    @pytest.mark.asyncio
    @patch(
        "app.modules.action_plan.service.update_action_item",
        new_callable=AsyncMock,
        side_effect=Exception("Not found"),
    )
    async def test_update_handles_error(self, mock_update, mock_config):
        """Erreur retourne un message lisible."""
        result = await update_action_item.ainvoke(
            {"action_id": str(uuid.uuid4()), "status": "completed"},
            config=mock_config,
        )

        assert "Erreur" in result


class TestGetActionPlan:
    """Tests pour get_action_plan."""

    @pytest.mark.asyncio
    @patch("app.modules.action_plan.service.get_active_plan", new_callable=AsyncMock)
    async def test_active_plan_found(self, mock_get_plan, mock_config):
        """Plan actif retourne le resume avec progression."""
        plan = _make_action_plan()
        mock_get_plan.return_value = plan

        result = await get_action_plan.ainvoke({}, config=mock_config)

        assert "12" in result or "mois" in result.lower()
        assert "10" in result or "actions" in result.lower()
        mock_get_plan.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.modules.action_plan.service.get_active_plan", new_callable=AsyncMock)
    async def test_no_active_plan(self, mock_get_plan, mock_config):
        """Pas de plan actif retourne un message invitant a en creer un."""
        mock_get_plan.return_value = None

        result = await get_action_plan.ainvoke({}, config=mock_config)

        assert "Aucun" in result or "aucun" in result

    @pytest.mark.asyncio
    @patch(
        "app.modules.action_plan.service.get_active_plan",
        new_callable=AsyncMock,
        side_effect=Exception("DB error"),
    )
    async def test_get_handles_error(self, mock_get_plan, mock_config):
        """Erreur retourne un message lisible."""
        result = await get_action_plan.ainvoke({}, config=mock_config)

        assert "Erreur" in result


class TestGenerateActionPlanRuntimeGuard:
    """BUG-V6-005 : garde runtime exige >= 5 actions (mode batch §4decies) et champs requis."""

    @pytest.mark.asyncio
    @patch("app.modules.action_plan.service.generate_action_plan", new_callable=AsyncMock)
    async def test_accepts_partial_batch_with_incremental_message(
        self, mock_generate, mock_config
    ):
        """V8-AXE2 §4decies : plan service avec 5 actions -> succes mode batch incremental.

        Remplace l'ancien comportement strict (ERREUR < 10) par l'acceptation
        d'un plan partiel >= 5 actions avec message invitant le LLM a
        completer via un nouvel appel.
        """
        plan = _make_action_plan(
            items=[_make_action_item() for _ in range(5)],
            total_actions=5,
        )
        mock_generate.return_value = plan

        result = await generate_action_plan.ainvoke({"timeframe": 12}, config=mock_config)

        assert "ERREUR" not in result
        assert "5/10" in result
        assert "incremental" in result.lower() or "incrémental" in result.lower()
        assert "manque 5" in result.lower()

    @pytest.mark.asyncio
    @patch("app.modules.action_plan.service.generate_action_plan", new_callable=AsyncMock)
    async def test_rejects_action_missing_required_fields(self, mock_generate, mock_config):
        """Action sans title -> ERREUR listant le champ manquant."""
        items = [_make_action_item() for _ in range(10)]
        items[3] = _make_action_item(title="", category=None)
        plan = _make_action_plan(items=items)
        mock_generate.return_value = plan

        result = await generate_action_plan.ainvoke({"timeframe": 12}, config=mock_config)

        assert "ERREUR" in result
        assert "action #4" in result
        assert "title" in result
        assert "category" in result

    @pytest.mark.asyncio
    @patch("app.modules.action_plan.service.generate_action_plan", new_callable=AsyncMock)
    async def test_succeeds_with_complete_plan(self, mock_generate, mock_config):
        """Plan avec 10 actions valides -> succes (pas d'ERREUR)."""
        plan = _make_action_plan()  # 10 items par defaut
        mock_generate.return_value = plan

        result = await generate_action_plan.ainvoke({"timeframe": 12}, config=mock_config)

        assert "ERREUR" not in result
        assert "succes" in result.lower()

    @pytest.mark.asyncio
    @patch("app.modules.action_plan.service.generate_action_plan", new_callable=AsyncMock)
    async def test_rejects_whitespace_only_title(self, mock_generate, mock_config):
        """Action avec title whitespace-only -> ERREUR (defense en profondeur)."""
        items = [_make_action_item() for _ in range(10)]
        items[7].title = "   "
        plan = _make_action_plan(items=items)
        mock_generate.return_value = plan

        result = await generate_action_plan.ainvoke({"timeframe": 12}, config=mock_config)

        assert "ERREUR" in result
        assert "action #8" in result


class TestActionPlanToolsExport:
    """Tests pour l'export du module."""

    def test_tools_list_count(self):
        """ACTION_PLAN_TOOLS contient 3 tools."""
        assert len(ACTION_PLAN_TOOLS) == 3

    def test_tool_names(self):
        """Les tools ont les bons noms."""
        names = {t.name for t in ACTION_PLAN_TOOLS}
        assert names == {"generate_action_plan", "update_action_item", "get_action_plan"}

    def test_tools_have_french_descriptions(self):
        """Les descriptions des tools sont en francais."""
        for t in ACTION_PLAN_TOOLS:
            assert any(
                word in t.description.lower()
                for word in ["plan", "action", "utilise", "outil"]
            ), f"Description manque de termes francais : {t.description}"
