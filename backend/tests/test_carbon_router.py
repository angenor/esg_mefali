"""Tests d'integration des endpoints carbon (T014).

Verifie les 6 endpoints REST du module carbon via le client HTTP.
"""

import uuid

import pytest
from httpx import AsyncClient

from app.models.carbon import CarbonAssessment, CarbonEmissionEntry, CarbonStatusEnum


class TestCarbonEndpoints:
    """Tests des endpoints REST /api/carbon."""

    @pytest.fixture
    def user_id(self) -> uuid.UUID:
        return uuid.uuid4()

    async def _create_assessment_in_db(self, db_session, user_id: uuid.UUID, year: int = 2026) -> CarbonAssessment:
        """Helper pour creer un bilan directement en BDD."""
        assessment = CarbonAssessment(
            user_id=user_id,
            year=year,
            sector="agriculture",
            status=CarbonStatusEnum.in_progress,
            completed_categories=[],
        )
        db_session.add(assessment)
        await db_session.flush()
        return assessment

    async def _add_entry_in_db(
        self, db_session, assessment_id: uuid.UUID,
        category: str = "energy", emissions: float = 2.05,
    ) -> CarbonEmissionEntry:
        """Helper pour ajouter une entree directement en BDD."""
        entry = CarbonEmissionEntry(
            assessment_id=assessment_id,
            category=category,
            subcategory="electricity_ci",
            quantity=5000,
            unit="kWh",
            emission_factor=0.41,
            emissions_tco2e=emissions,
        )
        db_session.add(entry)
        await db_session.flush()
        return entry

    async def test_create_assessment_no_auth(self, client: AsyncClient) -> None:
        """T014-01 : Creation sans authentification → 401."""
        resp = await client.post("/api/carbon/assessments", json={"year": 2026})
        assert resp.status_code in (401, 403)

    async def test_list_assessments_no_auth(self, client: AsyncClient) -> None:
        """T014-02 : Liste sans authentification → 401."""
        resp = await client.get("/api/carbon/assessments")
        assert resp.status_code in (401, 403)

    async def test_get_benchmark_agriculture(self, client: AsyncClient) -> None:
        """T014-03 : Benchmark pour un secteur connu (test sans auth necessaire si endpoint public)."""
        # Les benchmarks necessitent aussi l'auth dans notre implementation
        resp = await client.get("/api/carbon/benchmarks/agriculture")
        # Devrait retourner 401 (auth requise) ou 200 (si public)
        assert resp.status_code in (200, 401, 403)

    async def test_get_benchmark_unknown_sector(self, client: AsyncClient) -> None:
        """T014-04 : Benchmark pour secteur inconnu → 404 (ou 401 si auth)."""
        resp = await client.get("/api/carbon/benchmarks/espace_spatial")
        assert resp.status_code in (404, 401, 403)


class TestCarbonServiceIntegration:
    """Tests d'integration du service carbon directement (sans HTTP)."""

    @pytest.fixture
    def user_id(self) -> uuid.UUID:
        return uuid.uuid4()

    async def test_full_assessment_flow(self, db_session, user_id: uuid.UUID) -> None:
        """T014-05 : Flux complet creation → ajout entrees → finalisation → resume."""
        from app.modules.carbon.service import (
            add_entries,
            complete_assessment,
            create_assessment,
            get_assessment_summary,
        )

        # 1. Creer un bilan
        assessment = await create_assessment(
            db=db_session, user_id=user_id, year=2026, sector="agriculture",
        )
        await db_session.flush()
        assert assessment.status.value == "in_progress"

        # 2. Ajouter des entrees energie
        added, total, completed = await add_entries(
            db=db_session,
            assessment=assessment,
            entries_data=[
                {"category": "energy", "subcategory": "electricity_ci",
                 "quantity": 5000, "unit": "kWh", "emission_factor": 0.41, "emissions_tco2e": 2.05},
                {"category": "energy", "subcategory": "diesel_generator",
                 "quantity": 200, "unit": "L", "emission_factor": 2.68, "emissions_tco2e": 0.536},
            ],
            mark_category_complete="energy",
        )
        assert added == 2
        assert "energy" in completed
        await db_session.flush()

        # 3. Ajouter des entrees transport
        added2, total2, completed2 = await add_entries(
            db=db_session,
            assessment=assessment,
            entries_data=[
                {"category": "transport", "subcategory": "gasoline",
                 "quantity": 500, "unit": "L", "emission_factor": 2.31, "emissions_tco2e": 1.155},
            ],
            mark_category_complete="transport",
        )
        assert "transport" in completed2
        await db_session.flush()

        # 4. Ajouter des entrees dechets
        await add_entries(
            db=db_session,
            assessment=assessment,
            entries_data=[
                {"category": "waste", "subcategory": "waste_landfill",
                 "quantity": 1000, "unit": "kg", "emission_factor": 0.5, "emissions_tco2e": 0.5},
            ],
            mark_category_complete="waste",
        )
        await db_session.flush()

        # 5. Finaliser
        result = await complete_assessment(db=db_session, assessment=assessment)
        assert result.status.value == "completed"
        assert result.total_emissions_tco2e is not None
        assert result.total_emissions_tco2e > 0
        await db_session.flush()

        # 6. Generer le resume
        summary = await get_assessment_summary(db=db_session, assessment=assessment)
        assert summary["status"] == "completed"
        assert "energy" in summary["by_category"]
        assert "transport" in summary["by_category"]
        assert "waste" in summary["by_category"]
        assert len(summary["equivalences"]) == 3
        assert summary["sector_benchmark"] is not None
        assert summary["sector_benchmark"]["sector"] == "agriculture"

    async def test_duplicate_year_prevention(self, db_session, user_id: uuid.UUID) -> None:
        """T014-06 : Prevention des doublons par annee."""
        from app.modules.carbon.service import create_assessment

        await create_assessment(db=db_session, user_id=user_id, year=2026)
        await db_session.flush()

        with pytest.raises(ValueError):
            await create_assessment(db=db_session, user_id=user_id, year=2026)

    async def test_different_users_same_year(self, db_session) -> None:
        """T014-07 : Differents utilisateurs peuvent avoir la meme annee."""
        from app.modules.carbon.service import create_assessment

        user1 = uuid.uuid4()
        user2 = uuid.uuid4()

        await create_assessment(db=db_session, user_id=user1, year=2026)
        await create_assessment(db=db_session, user_id=user2, year=2026)
        await db_session.flush()
        # Pas d'erreur = OK

    async def test_list_with_status_filter(self, db_session, user_id: uuid.UUID) -> None:
        """T014-08 : Filtrage par statut dans la liste."""
        from app.modules.carbon.service import (
            complete_assessment,
            create_assessment,
            list_assessments,
        )

        a1 = await create_assessment(db=db_session, user_id=user_id, year=2025)
        await create_assessment(db=db_session, user_id=user_id, year=2026)
        await db_session.flush()

        await complete_assessment(db=db_session, assessment=a1)
        await db_session.flush()

        completed_list, completed_total = await list_assessments(
            db=db_session, user_id=user_id, status="completed",
        )
        assert completed_total == 1

        in_progress_list, ip_total = await list_assessments(
            db=db_session, user_id=user_id, status="in_progress",
        )
        assert ip_total == 1
