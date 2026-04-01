"""Tests des endpoints REST Plan d'Action (T027)."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


# --- Helpers ---


def _make_mock_plan(
    timeframe: int = 12,
    total: int = 4,
    completed: int = 0,
) -> MagicMock:
    """Créer un mock ActionPlan pour les tests du router."""
    from app.models.action_plan import PlanStatus

    plan = MagicMock()
    plan.id = uuid.uuid4()
    plan.user_id = uuid.uuid4()
    plan.title = f"Plan d'action {timeframe} mois"
    plan.timeframe = timeframe
    plan.status = PlanStatus.active
    plan.total_actions = total
    plan.completed_actions = completed
    plan.items = []
    plan.created_at = datetime.now(tz=timezone.utc)
    plan.updated_at = datetime.now(tz=timezone.utc)
    return plan


def _make_mock_item(
    category: str = "environment",
    status: str = "todo",
    completion_percentage: int = 0,
) -> MagicMock:
    """Créer un mock ActionItem pour les tests du router.

    Utilise des valeurs string directes pour les enums Pydantic.
    """
    from app.models.action_plan import ActionItemCategory, ActionItemPriority, ActionItemStatus

    item = MagicMock()
    item.id = uuid.uuid4()
    item.plan_id = uuid.uuid4()
    item.title = f"Action {category}"
    item.description = "Description test"
    item.category = ActionItemCategory(category)
    item.priority = ActionItemPriority.medium
    item.status = ActionItemStatus(status)
    item.due_date = None
    item.estimated_cost_xof = None
    item.estimated_benefit = None
    item.completion_percentage = completion_percentage
    item.related_fund_id = None
    item.related_intermediary_id = None
    item.intermediary_name = None
    item.intermediary_address = None
    item.intermediary_phone = None
    item.intermediary_email = None
    item.sort_order = 0
    item.created_at = datetime.now(tz=timezone.utc)
    item.updated_at = datetime.now(tz=timezone.utc)
    return item


def _make_mock_db() -> AsyncMock:
    """Créer un mock de session BDD."""
    return AsyncMock()


def _make_mock_user() -> MagicMock:
    """Créer un mock d'utilisateur authentifié."""
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = "test@example.com"
    return user


# --- Tests POST /api/action-plan/generate (T027) ---


class TestGenerateEndpoint:
    """Tests de l'endpoint POST /api/action-plan/generate."""

    @pytest.mark.asyncio
    async def test_generate_201_success(self):
        """T027-01 : Génération réussie retourne un plan."""
        from app.modules.action_plan.router import generate_plan
        from app.modules.action_plan.schemas import ActionPlanCreate

        mock_db = _make_mock_db()
        mock_user = _make_mock_user()
        mock_plan = _make_mock_plan(timeframe=12, total=4)

        with patch(
            "app.modules.action_plan.router.generate_action_plan",
            new=AsyncMock(return_value=mock_plan),
        ):
            payload = ActionPlanCreate(timeframe=12)
            result = await generate_plan(
                payload=payload,
                db=mock_db,
                current_user=mock_user,
            )

        assert result.timeframe == 12
        assert result.total_actions == 4

    @pytest.mark.asyncio
    async def test_generate_428_no_profile(self):
        """T027-02 : 428 si le profil est incomplet."""
        from app.modules.action_plan.router import generate_plan
        from app.modules.action_plan.schemas import ActionPlanCreate

        mock_db = _make_mock_db()
        mock_user = _make_mock_user()

        with patch(
            "app.modules.action_plan.router.generate_action_plan",
            new=AsyncMock(
                side_effect=HTTPException(status_code=428, detail="Profil entreprise requis.")
            ),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await generate_plan(
                    payload=ActionPlanCreate(timeframe=12),
                    db=mock_db,
                    current_user=mock_user,
                )
        assert exc_info.value.status_code == 428

    @pytest.mark.asyncio
    async def test_generate_401_without_auth(self, client):
        """T027-03 : 401 sans authentification."""
        resp = await client.post(
            "/api/action-plan/generate",
            json={"timeframe": 12},
        )
        assert resp.status_code == 401


# --- Tests GET /api/action-plan/ (T027) ---


class TestGetActivePlanEndpoint:
    """Tests de l'endpoint GET /api/action-plan/."""

    @pytest.mark.asyncio
    async def test_get_active_plan_200(self):
        """T027-04 : Plan actif retourné avec succès."""
        from app.modules.action_plan.router import get_active_plan_endpoint

        mock_db = _make_mock_db()
        mock_user = _make_mock_user()
        mock_plan = _make_mock_plan()

        with patch(
            "app.modules.action_plan.router.get_active_plan",
            new=AsyncMock(return_value=mock_plan),
        ):
            result = await get_active_plan_endpoint(db=mock_db, current_user=mock_user)

        assert result.timeframe == 12

    @pytest.mark.asyncio
    async def test_get_active_plan_404_no_plan(self):
        """T027-05 : 404 si aucun plan actif."""
        from app.modules.action_plan.router import get_active_plan_endpoint

        mock_db = _make_mock_db()
        mock_user = _make_mock_user()

        with patch(
            "app.modules.action_plan.router.get_active_plan",
            new=AsyncMock(return_value=None),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_active_plan_endpoint(db=mock_db, current_user=mock_user)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_active_plan_401_without_auth(self, client):
        """T027-06 : 401 sans authentification."""
        resp = await client.get("/api/action-plan/")
        assert resp.status_code == 401


# --- Tests GET /api/action-plan/{id}/items (T027) ---


class TestListPlanItemsEndpoint:
    """Tests de l'endpoint GET /api/action-plan/{id}/items."""

    @pytest.mark.asyncio
    async def test_list_items_200(self):
        """T027-07 : Liste des items retournée."""
        from app.modules.action_plan.router import list_plan_items

        mock_db = _make_mock_db()
        mock_user = _make_mock_user()
        plan_id = str(uuid.uuid4())
        items = [_make_mock_item("environment"), _make_mock_item("social")]
        progress = {"global_percentage": 0}

        with patch(
            "app.modules.action_plan.router.get_plan_items",
            new=AsyncMock(return_value=(items, 2, progress)),
        ):
            result = await list_plan_items(
                plan_id=plan_id,
                category=None,
                status=None,
                page=1,
                limit=20,
                db=mock_db,
                current_user=mock_user,
            )

        assert result.total == 2
        assert len(result.items) == 2

    @pytest.mark.asyncio
    async def test_list_items_with_category_filter(self):
        """T027-08 : Filtre par catégorie transmis au service."""
        from app.modules.action_plan.router import list_plan_items

        mock_db = _make_mock_db()
        mock_user = _make_mock_user()
        plan_id = str(uuid.uuid4())
        items = [_make_mock_item("environment")]
        progress = {"global_percentage": 0}
        captured = {}

        async def mock_service(db, plan_id, user_id, **kwargs):
            captured.update(kwargs)
            return items, 1, progress

        with patch("app.modules.action_plan.router.get_plan_items", new=mock_service):
            await list_plan_items(
                plan_id=plan_id,
                category="environment",
                status=None,
                page=1,
                limit=20,
                db=mock_db,
                current_user=mock_user,
            )

        assert captured.get("category") == "environment"

    @pytest.mark.asyncio
    async def test_list_items_404_from_service(self):
        """T027-09 : 404 si le plan n'appartient pas à l'utilisateur."""
        from app.modules.action_plan.router import list_plan_items

        mock_db = _make_mock_db()
        mock_user = _make_mock_user()
        plan_id = str(uuid.uuid4())

        with patch(
            "app.modules.action_plan.router.get_plan_items",
            new=AsyncMock(
                side_effect=HTTPException(status_code=404, detail="Plan introuvable.")
            ),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await list_plan_items(
                    plan_id=plan_id,
                    category=None,
                    status=None,
                    page=1,
                    limit=20,
                    db=mock_db,
                    current_user=mock_user,
                )
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_list_items_401_without_auth(self, client):
        """T027-10 : 401 sans authentification."""
        plan_id = str(uuid.uuid4())
        resp = await client.get(f"/api/action-plan/{plan_id}/items")
        assert resp.status_code == 401


# --- Tests PATCH /api/action-plan/items/{id} (T027) ---


class TestUpdateItemEndpoint:
    """Tests de l'endpoint PATCH /api/action-plan/items/{id}."""

    @pytest.mark.asyncio
    async def test_update_item_200_success(self):
        """T027-11 : Mise à jour réussie."""
        from app.modules.action_plan.router import update_item
        from app.modules.action_plan.schemas import ActionItemUpdate

        mock_db = _make_mock_db()
        mock_user = _make_mock_user()
        item_id = str(uuid.uuid4())
        mock_item = _make_mock_item("environment", "in_progress", 50)

        with patch(
            "app.modules.action_plan.router.update_action_item",
            new=AsyncMock(return_value=mock_item),
        ):
            result = await update_item(
                item_id=item_id,
                payload=ActionItemUpdate(status="in_progress"),
                db=mock_db,
                current_user=mock_user,
            )

        assert result.status.value == "in_progress"

    @pytest.mark.asyncio
    async def test_update_item_400_invalid_transition(self):
        """T027-12 : 400 pour une transition de statut invalide."""
        from app.modules.action_plan.router import update_item
        from app.modules.action_plan.schemas import ActionItemUpdate

        mock_db = _make_mock_db()
        mock_user = _make_mock_user()
        item_id = str(uuid.uuid4())

        with patch(
            "app.modules.action_plan.router.update_action_item",
            new=AsyncMock(
                side_effect=HTTPException(
                    status_code=400,
                    detail="Transition de statut invalide : todo → completed.",
                )
            ),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await update_item(
                    item_id=item_id,
                    payload=ActionItemUpdate(status="completed"),
                    db=mock_db,
                    current_user=mock_user,
                )
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_update_item_401_without_auth(self, client):
        """T027-13 : 401 sans authentification."""
        item_id = str(uuid.uuid4())
        resp = await client.patch(
            f"/api/action-plan/items/{item_id}",
            json={"status": "in_progress"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_update_item_404_not_found(self):
        """T027-14 : 404 si l'action n'appartient pas à l'utilisateur."""
        from app.modules.action_plan.router import update_item
        from app.modules.action_plan.schemas import ActionItemUpdate

        mock_db = _make_mock_db()
        mock_user = _make_mock_user()
        item_id = str(uuid.uuid4())

        with patch(
            "app.modules.action_plan.router.update_action_item",
            new=AsyncMock(
                side_effect=HTTPException(
                    status_code=404,
                    detail="Action introuvable.",
                )
            ),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await update_item(
                    item_id=item_id,
                    payload=ActionItemUpdate(status="in_progress"),
                    db=mock_db,
                    current_user=mock_user,
                )
        assert exc_info.value.status_code == 404
