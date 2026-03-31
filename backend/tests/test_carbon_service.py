"""Tests unitaires du service carbone (T013).

Verifie le calcul des emissions, la validation, le CRUD des bilans,
les equivalences parlantes et les benchmarks.
"""

import uuid

import pytest

from app.modules.carbon.emission_factors import (
    EMISSION_FACTORS,
    compute_emissions_tco2e,
    compute_equivalences,
    get_applicable_categories,
    get_emission_factor,
)
from app.modules.carbon.benchmarks import (
    compute_benchmark_position,
    get_sector_benchmark,
)


class TestEmissionFactors:
    """Tests des facteurs d'emission et calculs."""

    def test_get_emission_factor_valid(self) -> None:
        """T013-01 : Facteur d'emission valide pour electricite CI."""
        factor = get_emission_factor("electricity_ci")
        assert factor == 0.41

    def test_get_emission_factor_invalid(self) -> None:
        """T013-02 : Erreur pour facteur inconnu."""
        with pytest.raises(ValueError, match="Facteur d'emission inconnu"):
            get_emission_factor("unknown_source")

    def test_compute_emissions_tco2e(self) -> None:
        """T013-03 : Calcul correct kgCO2e → tCO2e."""
        # 5000 kWh * 0.41 kgCO2e/kWh = 2050 kgCO2e = 2.05 tCO2e
        result = compute_emissions_tco2e(5000, 0.41)
        assert result == 2.05

    def test_compute_emissions_small_quantity(self) -> None:
        """T013-04 : Calcul pour petites quantites."""
        result = compute_emissions_tco2e(10, 0.41)
        assert result == 0.0041

    def test_compute_equivalences(self) -> None:
        """T013-05 : Equivalences parlantes correctes."""
        equivalences = compute_equivalences(12.0)
        assert len(equivalences) == 3
        labels = [e["label"] for e in equivalences]
        assert "vols Paris-Dakar" in labels
        assert "annees de conduite moyenne" in labels
        # 12.0 / 1.2 = 10.0 vols
        flight_equiv = next(e for e in equivalences if e["label"] == "vols Paris-Dakar")
        assert flight_equiv["value"] == 10.0

    def test_compute_equivalences_zero(self) -> None:
        """T013-06 : Equivalences pour zero emissions."""
        equivalences = compute_equivalences(0.0)
        for e in equivalences:
            assert e["value"] == 0.0

    def test_get_applicable_categories_services(self) -> None:
        """T013-07 : Categories applicables pour services = 3 obligatoires."""
        cats = get_applicable_categories("services")
        assert cats == ["energy", "transport", "waste"]

    def test_get_applicable_categories_agriculture(self) -> None:
        """T013-08 : Categories applicables pour agriculture inclut agriculture."""
        cats = get_applicable_categories("agriculture")
        assert "agriculture" in cats
        assert "energy" in cats

    def test_get_applicable_categories_manufacturing(self) -> None:
        """T013-09 : Categories applicables pour manufacturing inclut industrial."""
        cats = get_applicable_categories("manufacturing")
        assert "industrial" in cats

    def test_all_emission_factors_have_required_fields(self) -> None:
        """T013-10 : Tous les facteurs ont les champs requis."""
        for key, data in EMISSION_FACTORS.items():
            assert "factor" in data, f"{key} manque 'factor'"
            assert "unit" in data, f"{key} manque 'unit'"
            assert "label" in data, f"{key} manque 'label'"
            assert "category" in data, f"{key} manque 'category'"
            assert data["factor"] > 0, f"{key} facteur <= 0"


class TestBenchmarks:
    """Tests des benchmarks sectoriels."""

    def test_get_benchmark_valid_sector(self) -> None:
        """T013-11 : Benchmark disponible pour agriculture."""
        benchmark = get_sector_benchmark("agriculture")
        assert benchmark is not None
        assert benchmark["average_emissions_tco2e"] == 18.0

    def test_get_benchmark_unknown_sector(self) -> None:
        """T013-12 : None pour secteur totalement inconnu."""
        benchmark = get_sector_benchmark("espace_spatial")
        assert benchmark is None

    def test_get_benchmark_fallback(self) -> None:
        """T013-13 : Fallback vers secteur similaire."""
        benchmark = get_sector_benchmark("mining")
        assert benchmark is not None
        # mining fallback vers construction
        assert benchmark.get("sector") == "construction"

    def test_benchmark_position_below_average(self) -> None:
        """T013-14 : Position en-dessous de la moyenne."""
        result = compute_benchmark_position(10.0, "agriculture")
        assert result["position"] in ("below_average", "well_below_average")

    def test_benchmark_position_above_average(self) -> None:
        """T013-15 : Position au-dessus de la moyenne."""
        result = compute_benchmark_position(25.0, "agriculture")
        assert result["position"] in ("above_average", "well_above_average")

    def test_benchmark_position_unknown_sector(self) -> None:
        """T013-16 : Position inconnue pour secteur sans benchmark."""
        result = compute_benchmark_position(10.0, "espace_spatial")
        assert result["position"] == "unknown"


class TestCarbonServiceCRUD:
    """Tests CRUD du service carbone (avec base de donnees)."""

    @pytest.fixture
    def user_id(self) -> uuid.UUID:
        return uuid.uuid4()

    async def test_create_assessment(self, db_session, user_id: uuid.UUID) -> None:
        """T013-17 : Creation d'un bilan carbone."""
        from app.modules.carbon.service import create_assessment

        assessment = await create_assessment(
            db=db_session, user_id=user_id, year=2026, sector="agriculture",
        )
        assert assessment.user_id == user_id
        assert assessment.year == 2026
        assert assessment.status.value == "in_progress"
        assert assessment.total_emissions_tco2e is None

    async def test_create_assessment_duplicate_year(self, db_session, user_id: uuid.UUID) -> None:
        """T013-18 : Erreur si bilan existe deja pour cette annee."""
        from app.modules.carbon.service import create_assessment

        await create_assessment(db=db_session, user_id=user_id, year=2026)
        await db_session.flush()

        with pytest.raises(ValueError, match="existe deja"):
            await create_assessment(db=db_session, user_id=user_id, year=2026)

    async def test_get_assessment(self, db_session, user_id: uuid.UUID) -> None:
        """T013-19 : Recuperation d'un bilan par ID."""
        from app.modules.carbon.service import create_assessment, get_assessment

        created = await create_assessment(db=db_session, user_id=user_id, year=2026)
        await db_session.flush()

        found = await get_assessment(db=db_session, assessment_id=created.id, user_id=user_id)
        assert found is not None
        assert found.id == created.id

    async def test_get_assessment_wrong_user(self, db_session, user_id: uuid.UUID) -> None:
        """T013-20 : Bilan inaccessible par un autre utilisateur."""
        from app.modules.carbon.service import create_assessment, get_assessment

        created = await create_assessment(db=db_session, user_id=user_id, year=2026)
        await db_session.flush()

        other = uuid.uuid4()
        found = await get_assessment(db=db_session, assessment_id=created.id, user_id=other)
        assert found is None

    async def test_list_assessments(self, db_session, user_id: uuid.UUID) -> None:
        """T013-21 : Liste paginee des bilans."""
        from app.modules.carbon.service import create_assessment, list_assessments

        for year in (2024, 2025, 2026):
            await create_assessment(db=db_session, user_id=user_id, year=year)
        await db_session.flush()

        assessments, total = await list_assessments(db=db_session, user_id=user_id)
        assert total == 3
        assert len(assessments) == 3

    async def test_add_entries(self, db_session, user_id: uuid.UUID) -> None:
        """T013-22 : Ajout d'entrees d'emissions."""
        from app.modules.carbon.service import add_entries, create_assessment

        assessment = await create_assessment(db=db_session, user_id=user_id, year=2026)
        await db_session.flush()

        entries_data = [{
            "category": "energy",
            "subcategory": "electricity_ci",
            "quantity": 5000,
            "unit": "kWh",
            "emission_factor": 0.41,
            "emissions_tco2e": 2.05,
        }]

        added, total, completed = await add_entries(
            db=db_session, assessment=assessment, entries_data=entries_data,
            mark_category_complete="energy",
        )
        assert added == 1
        assert total == 2.05
        assert "energy" in completed

    async def test_add_entries_to_completed_assessment_fails(self, db_session, user_id: uuid.UUID) -> None:
        """T013-23 : Erreur si bilan deja finalise."""
        from app.modules.carbon.service import add_entries, complete_assessment, create_assessment

        assessment = await create_assessment(db=db_session, user_id=user_id, year=2026)
        await db_session.flush()
        await complete_assessment(db=db_session, assessment=assessment)
        await db_session.flush()

        with pytest.raises(ValueError, match="deja finalise"):
            await add_entries(db=db_session, assessment=assessment, entries_data=[{
                "category": "energy", "subcategory": "electricity_ci",
                "quantity": 100, "unit": "kWh",
                "emission_factor": 0.41, "emissions_tco2e": 0.041,
            }])

    async def test_complete_assessment(self, db_session, user_id: uuid.UUID) -> None:
        """T013-24 : Finalisation d'un bilan."""
        from app.modules.carbon.service import add_entries, complete_assessment, create_assessment

        assessment = await create_assessment(db=db_session, user_id=user_id, year=2026)
        await db_session.flush()

        await add_entries(db=db_session, assessment=assessment, entries_data=[{
            "category": "energy", "subcategory": "electricity_ci",
            "quantity": 5000, "unit": "kWh",
            "emission_factor": 0.41, "emissions_tco2e": 2.05,
        }])
        await db_session.flush()

        result = await complete_assessment(db=db_session, assessment=assessment)
        assert result.status.value == "completed"
        assert result.total_emissions_tco2e == 2.05

    async def test_get_resumable_assessment(self, db_session, user_id: uuid.UUID) -> None:
        """T013-25 : Trouver un bilan en cours pour reprise."""
        from app.modules.carbon.service import create_assessment, get_resumable_assessment

        await create_assessment(db=db_session, user_id=user_id, year=2026)
        await db_session.flush()

        resumable = await get_resumable_assessment(db=db_session, user_id=user_id)
        assert resumable is not None
        assert resumable.year == 2026

    async def test_get_assessment_summary(self, db_session, user_id: uuid.UUID) -> None:
        """T013-26 : Resume complet d'un bilan."""
        from app.modules.carbon.service import (
            add_entries,
            complete_assessment,
            create_assessment,
            get_assessment_summary,
        )

        assessment = await create_assessment(
            db=db_session, user_id=user_id, year=2026, sector="agriculture",
        )
        await db_session.flush()

        await add_entries(db=db_session, assessment=assessment, entries_data=[
            {"category": "energy", "subcategory": "electricity_ci",
             "quantity": 5000, "unit": "kWh", "emission_factor": 0.41, "emissions_tco2e": 2.05},
            {"category": "transport", "subcategory": "gasoline",
             "quantity": 1000, "unit": "L", "emission_factor": 2.31, "emissions_tco2e": 2.31},
        ], mark_category_complete="energy")
        await db_session.flush()

        await complete_assessment(db=db_session, assessment=assessment)
        await db_session.flush()

        summary = await get_assessment_summary(db=db_session, assessment=assessment)
        assert summary["total_emissions_tco2e"] == pytest.approx(4.36, rel=0.01)
        assert "energy" in summary["by_category"]
        assert "transport" in summary["by_category"]
        assert len(summary["equivalences"]) == 3
        assert summary["sector_benchmark"] is not None


class TestCarbonServiceHelpers:
    """Tests des helpers du service carbone."""

    def test_build_initial_carbon_state(self) -> None:
        """T013-27 : Etat initial du carbon_data."""
        from app.modules.carbon.service import build_initial_carbon_state

        state = build_initial_carbon_state("test-id", sector="agriculture")
        assert state["assessment_id"] == "test-id"
        assert state["status"] == "in_progress"
        assert state["current_category"] == "energy"
        assert "agriculture" in state["applicable_categories"]

    def test_get_next_category(self) -> None:
        """T013-28 : Progression entre categories."""
        from app.modules.carbon.service import get_next_category

        applicable = ["energy", "transport", "waste"]
        assert get_next_category("energy", applicable) == "transport"
        assert get_next_category("transport", applicable) == "waste"
        assert get_next_category("waste", applicable) is None

    def test_compute_category_label(self) -> None:
        """T013-29 : Labels francais des categories."""
        from app.modules.carbon.service import compute_category_label

        assert compute_category_label("energy") == "Energie"
        assert compute_category_label("transport") == "Transport"
        assert compute_category_label("waste") == "Dechets"
