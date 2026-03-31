"""Tests unitaires des criteres et ponderations ESG (T011).

Verifie la validite des 30 criteres, la coherence des poids sectoriels,
et le bon fonctionnement des fonctions utilitaires.
"""

import pytest

from app.modules.esg.criteria import (
    ALL_CRITERIA,
    CRITERIA_BY_CODE,
    ENVIRONMENT_CRITERIA,
    GOVERNANCE_CRITERIA,
    PILLAR_CRITERIA,
    PILLAR_ORDER,
    SOCIAL_CRITERIA,
    TOTAL_CRITERIA,
)
from app.modules.esg.weights import (
    DEFAULT_WEIGHT,
    SECTOR_BENCHMARKS,
    SECTOR_WEIGHTS,
    get_criterion_weight,
    get_sector_benchmark,
)


class TestESGCriteria:
    """Tests de la definition des 30 criteres ESG."""

    def test_total_criteria_count(self) -> None:
        """T011-01 : 30 criteres au total."""
        assert TOTAL_CRITERIA == 30
        assert len(ALL_CRITERIA) == 30

    def test_environment_criteria_count(self) -> None:
        """T011-02 : 10 criteres Environnement (E1-E10)."""
        assert len(ENVIRONMENT_CRITERIA) == 10
        codes = [c.code for c in ENVIRONMENT_CRITERIA]
        assert codes == [f"E{i}" for i in range(1, 11)]

    def test_social_criteria_count(self) -> None:
        """T011-03 : 10 criteres Social (S1-S10)."""
        assert len(SOCIAL_CRITERIA) == 10
        codes = [c.code for c in SOCIAL_CRITERIA]
        assert codes == [f"S{i}" for i in range(1, 11)]

    def test_governance_criteria_count(self) -> None:
        """T011-04 : 10 criteres Gouvernance (G1-G10)."""
        assert len(GOVERNANCE_CRITERIA) == 10
        codes = [c.code for c in GOVERNANCE_CRITERIA]
        assert codes == [f"G{i}" for i in range(1, 11)]

    def test_criteria_by_code_lookup(self) -> None:
        """T011-05 : Acces aux criteres par code."""
        assert len(CRITERIA_BY_CODE) == 30
        assert CRITERIA_BY_CODE["E1"].label == "Gestion des dechets"
        assert CRITERIA_BY_CODE["S1"].pillar == "social"
        assert CRITERIA_BY_CODE["G10"].pillar == "governance"

    def test_each_criterion_has_required_fields(self) -> None:
        """T011-06 : Chaque critere a code, pillar, label, description, question."""
        for c in ALL_CRITERIA:
            assert c.code, f"Critere sans code"
            assert c.pillar in ("environment", "social", "governance"), f"{c.code}: pilier invalide"
            assert len(c.label) > 0, f"{c.code}: label vide"
            assert len(c.description) > 0, f"{c.code}: description vide"
            assert len(c.question) > 0, f"{c.code}: question vide"

    def test_unique_codes(self) -> None:
        """T011-07 : Tous les codes sont uniques."""
        codes = [c.code for c in ALL_CRITERIA]
        assert len(codes) == len(set(codes))

    def test_pillar_criteria_mapping(self) -> None:
        """T011-08 : Le mapping PILLAR_CRITERIA est coherent."""
        assert set(PILLAR_CRITERIA.keys()) == {"environment", "social", "governance"}
        assert PILLAR_CRITERIA["environment"] == ENVIRONMENT_CRITERIA

    def test_pillar_order(self) -> None:
        """T011-09 : L'ordre des piliers est E, S, G."""
        assert PILLAR_ORDER == ["environment", "social", "governance"]

    def test_criteria_are_frozen(self) -> None:
        """T011-10 : Les criteres sont immutables (frozen dataclass)."""
        with pytest.raises(AttributeError):
            ALL_CRITERIA[0].code = "X99"


class TestSectorWeights:
    """Tests des ponderations sectorielles."""

    def test_all_sectors_defined(self) -> None:
        """T011-11 : 10 secteurs avec ponderations."""
        expected = {
            "agriculture", "energie", "recyclage", "transport", "construction",
            "textile", "agroalimentaire", "services", "commerce", "artisanat",
        }
        assert set(SECTOR_WEIGHTS.keys()) == expected

    def test_weights_are_positive(self) -> None:
        """T011-12 : Tous les poids sont positifs (> 0)."""
        for sector, weights in SECTOR_WEIGHTS.items():
            for code, weight in weights.items():
                assert weight > 0, f"{sector}/{code}: poids negatif ou nul"

    def test_weights_reference_valid_criteria(self) -> None:
        """T011-13 : Les poids referent des codes criteres valides."""
        valid_codes = {c.code for c in ALL_CRITERIA}
        for sector, weights in SECTOR_WEIGHTS.items():
            for code in weights:
                assert code in valid_codes, f"{sector}: code {code} invalide"

    def test_get_criterion_weight_known(self) -> None:
        """T011-14 : get_criterion_weight retourne le poids sectoriel."""
        weight = get_criterion_weight("agriculture", "E6")
        assert weight == 1.5

    def test_get_criterion_weight_default(self) -> None:
        """T011-15 : get_criterion_weight retourne 1.0 par defaut."""
        weight = get_criterion_weight("agriculture", "G10")
        assert weight == DEFAULT_WEIGHT

    def test_get_criterion_weight_unknown_sector(self) -> None:
        """T011-16 : Secteur inconnu retourne poids par defaut."""
        weight = get_criterion_weight("inconnu", "E1")
        assert weight == DEFAULT_WEIGHT


class TestSectorBenchmarks:
    """Tests des benchmarks sectoriels."""

    def test_all_sectors_have_benchmarks(self) -> None:
        """T011-17 : 10 secteurs avec benchmarks."""
        assert set(SECTOR_BENCHMARKS.keys()) == set(SECTOR_WEIGHTS.keys())

    def test_benchmark_structure(self) -> None:
        """T011-18 : Chaque benchmark a la bonne structure."""
        for sector, bench in SECTOR_BENCHMARKS.items():
            assert "sector_label" in bench, f"{sector}: sector_label manquant"
            assert "averages" in bench, f"{sector}: averages manquant"
            averages = bench["averages"]
            assert isinstance(averages, dict)
            for key in ("environment", "social", "governance", "overall"):
                assert key in averages, f"{sector}: {key} manquant dans averages"

    def test_benchmark_averages_in_range(self) -> None:
        """T011-19 : Les moyennes sont entre 0 et 100."""
        for sector, bench in SECTOR_BENCHMARKS.items():
            for key, value in bench["averages"].items():
                assert 0 <= value <= 100, f"{sector}/{key}: moyenne hors limites"

    def test_get_sector_benchmark_known(self) -> None:
        """T011-20 : get_sector_benchmark retourne le benchmark."""
        bench = get_sector_benchmark("agriculture")
        assert bench is not None
        assert bench["sector"] == "agriculture"
        assert bench["sector_label"] == "Agriculture"

    def test_get_sector_benchmark_unknown(self) -> None:
        """T011-21 : get_sector_benchmark retourne None pour secteur inconnu."""
        assert get_sector_benchmark("inconnu") is None
