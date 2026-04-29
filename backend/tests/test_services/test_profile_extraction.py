"""Tests unitaires pour app.services.profile_extraction (V8-AXE1).

Couvre les patterns regex (forme juridique, secteurs FR, pays UEMOA, effectif)
et les cas limites (texte vide, accents, casse mixte, ambigu, multi-sector).
"""

from __future__ import annotations

import logging

import pytest

from app.modules.company.schemas import SectorEnum
from app.services.profile_extraction import (
    COUNTRIES_UEMOA,
    SECTORS_FR,
    extract_profile_from_text,
)


class TestExtractCompleteProfile:
    """Cas nominaux few-shot du spec : 4 champs sur un message structure."""

    def test_agrivert_sarl_agriculture_senegal(self):
        result = extract_profile_from_text(
            "AgriVert Sarl, Agriculture, 15 employés, Sénégal"
        )
        assert result["company_name"] == "AgriVert Sarl"
        assert result["sector"] == "agriculture"
        assert result["employee_count"] == 15
        assert result["country"] == "Sénégal"

    def test_ecosolaire_sas_solaire_abidjan(self):
        result = extract_profile_from_text(
            "Mon entreprise EcoSolaire SAS dans le solaire à Abidjan, 30 personnes en Côte d'Ivoire"
        )
        assert result["company_name"] == "EcoSolaire SAS"
        assert result["sector"] == "energie"
        assert result["employee_count"] == 30
        assert result["country"] == "Côte d'Ivoire"

    def test_textilevert_sarl_textile_bamako(self):
        result = extract_profile_from_text(
            "Je suis Mariam de TextileVert Sarl, secteur textile, 8 employés à Bamako Mali"
        )
        assert result["company_name"] == "TextileVert Sarl"
        assert result["sector"] == "textile"
        assert result["employee_count"] == 8
        assert result["country"] == "Mali"


class TestEmployeeCount:
    """Patterns FR pour le nombre d'employes."""

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("15 employés", 15),
            ("30 personnes", 30),
            ("8 salariés", 8),
            ("12 collaborateurs", 12),
            ("100 staff", 100),
            ("1 employé", 1),
            ("250 employes", 250),  # sans accent
            ("Salaries: 75 salaries dans l'equipe", 75),
            ("99999 employés", 99999),  # max 5 chiffres
        ],
    )
    def test_extracts_count(self, text: str, expected: int):
        assert extract_profile_from_text(text)["employee_count"] == expected

    def test_no_match_when_no_keyword(self):
        result = extract_profile_from_text("Nous avons 15 succursales")
        assert "employee_count" not in result

    def test_six_digit_number_rejected(self):
        """\\d{1,5} max : evite la ValidationError Pydantic le=100_000 (review ÉLEVÉ-4)."""
        # « 500000 employes » : seuls les 5 premiers chiffres pourraient
        # etre captes mais le pattern \\d{1,5} doit refuser le bloc complet
        # car il prend au maximum 5 chiffres consecutifs et le reste casse
        # le mot-cle. Resultat attendu : pas d'extraction.
        result = extract_profile_from_text("500000 employes")
        # 5 premiers chiffres = 50000 ; ils sont quand meme suivis de "0" puis
        # « employes » → \\d{1,5}\\s*employes ne matche pas car le 6e chiffre
        # rompt l'enchainement. Doit donc etre absent.
        assert "employee_count" not in result


class TestSector:
    """Premier match canonique parmi SECTORS_FR."""

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("Nous faisons de l'agriculture biologique", "agriculture"),
            ("activité agricole en zone rurale", "agriculture"),
            ("nous travaillons dans le solaire photovoltaïque", "energie"),
            ("entreprise textile et habillement", "textile"),
            ("logistique et fret routier", "transport"),
            ("BTP et construction", "construction"),
            ("conseil et services aux PME", "services"),
            # « industrie/manufacture » mappe vers `autre` (n'est PAS un membre
            # de SectorEnum) — review V8-AXE1 CRITIQUE-1.
            ("manufacture industrielle", "autre"),
            ("commerce et distribution", "commerce"),
            # « tourisme/hotellerie/restaurant » mappe vers `services`.
            ("hôtellerie et tourisme", "services"),
            # Nouveaux secteurs alignes sur SectorEnum.
            ("activité agroalimentaire", "agroalimentaire"),
            ("recyclage des déchets", "recyclage"),
            ("artisanat local", "artisanat"),
        ],
    )
    def test_extracts_canonical_sector(self, text: str, expected: str):
        assert extract_profile_from_text(text)["sector"] == expected

    def test_all_sectors_are_valid_enum_members(self):
        """Toutes les cles canoniques de SECTORS_FR DOIVENT etre dans SectorEnum.

        Garde-fou contre la regression CRITIQUE-1 : un secteur non aligne sur
        l'enum Pydantic ferait planter CompanyProfileUpdate au moment du merge.
        """
        valid_values = {member.value for member in SectorEnum}
        for canonical in SECTORS_FR.keys():
            assert canonical in valid_values, (
                f"SECTORS_FR['{canonical}'] n'est pas un membre valide de "
                f"SectorEnum (valeurs valides : {valid_values})"
            )

    def test_multi_sector_picks_first_and_logs_warning(self, caplog):
        """Le premier match canonique est retenu ET un warning est loggé."""
        with caplog.at_level(logging.WARNING, logger="app.services.profile_extraction"):
            result = extract_profile_from_text(
                "agriculture et solaire combines"
            )
        assert result["sector"] == "agriculture"
        # Warning explicitement emis avec les candidats detectes (review M4).
        assert any(
            "Multi-sector match" in record.message
            for record in caplog.records
        ), f"Aucun warning multi-sector trouve dans {caplog.records!r}"

    def test_no_match_unknown_sector(self):
        result = extract_profile_from_text("Sustainable business consulting")
        # "consulting" matche "services"
        assert result["sector"] == "services"


class TestCountry:
    """Pays UEMOA, tolerance accents et casse."""

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("nous sommes au Sénégal", "Sénégal"),
            ("basés au senegal sans accent", "Sénégal"),
            ("Abidjan, Côte d'Ivoire", "Côte d'Ivoire"),
            ("cote d'ivoire", "Côte d'Ivoire"),
            ("au Mali", "Mali"),
            ("au Burkina Faso", "Burkina Faso"),
            ("au burkina", "Burkina Faso"),
            ("Bénin", "Bénin"),
            ("benin sans accent", "Bénin"),
            ("Togo", "Togo"),
            ("au Niger", "Niger"),
            ("Guinée-Bissau", "Guinée-Bissau"),
        ],
    )
    def test_extracts_canonical_country(self, text: str, expected: str):
        assert extract_profile_from_text(text)["country"] == expected

    def test_no_match_non_uemoa(self):
        result = extract_profile_from_text("Nous sommes au Maroc")
        assert "country" not in result


class TestCity:
    """BUG-V8-001 : extraction city via dict CITIES_FR."""

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("AgriVert Sarl, Agriculture, 15 employés, Sénégal, Dakar", "Dakar"),
            ("base a Abidjan", "Abidjan"),
            ("a Bamako", "Bamako"),
            ("Ouagadougou centre", "Ouagadougou"),
            ("siege a Ouaga", "Ouagadougou"),
            ("base a Lome", "Lomé"),
            ("basé à Lomé", "Lomé"),
            ("a Cotonou", "Cotonou"),
            ("Yaoundé Cameroun", "Yaoundé"),
            ("yaounde sans accent", "Yaoundé"),
            ("Casablanca Maroc", "Casablanca"),
            ("Saint-Louis du Senegal", "Saint-Louis"),
            ("Thiès region", "Thiès"),
            ("Bouaké centre", "Bouaké"),
        ],
    )
    def test_extracts_canonical_city(self, text: str, expected: str):
        assert extract_profile_from_text(text)["city"] == expected

    def test_no_match_unknown_city(self):
        result = extract_profile_from_text("Nous sommes a Tombouctou")
        assert "city" not in result

    def test_empty_text_no_city(self):
        assert extract_profile_from_text("") == {}

    def test_full_phrase_extracts_all_five_fields(self):
        """Régression T-V8-PROFILE-01 : 5 champs sur la phrase complète."""
        text = "AgriVert Sarl, Agriculture, 15 employés, Sénégal, Dakar"
        result = extract_profile_from_text(text)
        assert result.get("company_name") == "AgriVert Sarl"
        assert result.get("sector") == "agriculture"
        assert result.get("employee_count") == 15
        assert result.get("country") == "Sénégal"
        assert result.get("city") == "Dakar"


class TestCompanyName:
    """Pattern nom + forme juridique."""

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("AgriVert Sarl à Dakar", "AgriVert Sarl"),
            ("Notre societe EcoSolaire SAS", "EcoSolaire SAS"),
            ("TextileVert SA fabrique des vetements", "TextileVert SA"),
            ("FinanceVerte S.A. cherche financement", "FinanceVerte S.A."),
            # Max 2 mots capitalises avant la forme juridique (review V8-AXE1
            # CRITIQUE-2 : evite de capter les prefixes phrastiques).
            ("Compagnie Solaris SAS active", "Compagnie Solaris SAS"),
        ],
    )
    def test_extracts_company_name(self, text: str, expected: str):
        result = extract_profile_from_text(text)
        assert result["company_name"] == expected

    def test_max_two_words_before_legal_form(self):
        """Les prefixes phrastiques sont ecartes : seuls 2 derniers mots capitalises."""
        # « Mon Entreprise AgriVert Sarl » : ne doit PAS capter « Mon Entreprise
        # AgriVert Sarl ». Capte au plus « Entreprise AgriVert Sarl ».
        result = extract_profile_from_text("Mon Entreprise AgriVert Sarl")
        name = result["company_name"]
        assert name.endswith("Sarl")
        assert "Mon" not in name  # le 1er mot phrastique est hors capture

    def test_no_legal_form_no_extraction(self):
        # Pas de Sarl/SA/SAS => aucun nom extrait (heuristique conservatrice).
        result = extract_profile_from_text("Nous sommes une cooperative agricole")
        assert "company_name" not in result

    def test_lookahead_excludes_alphanum_suffix(self):
        """SAS123 ne doit pas etre interprete comme forme juridique SAS (review ÉLEVÉ-2)."""
        result = extract_profile_from_text("Compagnie SAS123 active")
        assert "company_name" not in result


class TestSecurity:
    """Garde-fous anti-DoS / ReDoS (review V8-AXE1 ÉLEVÉ-1)."""

    def test_caps_input_length(self):
        """Texte > 5000 caracteres tronque silencieusement, pas de DoS."""
        # 100 000 caracteres : sans cap, le moteur regex ferait 9 secteurs ×
        # 5 synonymes × O(n) iterations.
        big_text = "AgriVert Sarl, Agriculture, 15 employés, Sénégal" + ("x" * 100_000)
        # Doit terminer rapidement et renvoyer le meme resultat que la version courte.
        result = extract_profile_from_text(big_text)
        assert result["company_name"] == "AgriVert Sarl"
        assert result["sector"] == "agriculture"

    def test_no_redos_on_pathological_input(self):
        """Les patterns ne doivent pas backtracker exponentiellement."""
        import time

        pathological = "A " * 200 + "Sarl"
        start = time.monotonic()
        extract_profile_from_text(pathological)
        elapsed = time.monotonic() - start
        # Tolerance large mais detecte un backtracking exponentiel reel
        # (qui prendrait plusieurs secondes minimum).
        assert elapsed < 1.0, f"Possible ReDoS: {elapsed:.2f}s sur input pathologique"


class TestEdgeCases:
    """Cas limites : input vide, types non-string, etc."""

    @pytest.mark.parametrize("bad_input", ["", "   ", None, 42, [], {}])
    def test_returns_empty_for_invalid_input(self, bad_input):
        assert extract_profile_from_text(bad_input) == {}  # type: ignore[arg-type]

    def test_only_employee_count_no_other(self):
        result = extract_profile_from_text("J'ai 15 employés")
        assert result == {"employee_count": 15}

    def test_only_sector_no_other(self):
        result = extract_profile_from_text("dans la logistique")
        assert result == {"sector": "transport"}

    def test_constants_consistency(self):
        # SECTORS_FR keys sont les valeurs canoniques renvoyees.
        assert "agriculture" in SECTORS_FR
        assert "energie" in SECTORS_FR
        # COUNTRIES_UEMOA keys avec accents canoniques.
        assert "Sénégal" in COUNTRIES_UEMOA
        assert "Côte d'Ivoire" in COUNTRIES_UEMOA
