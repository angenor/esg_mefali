"""Tests pour les templates de sections par target_type (US4 agence + US5 carbone)."""

import pytest

from app.models.application import TargetType
from app.modules.applications.templates import (
    CHECKLISTS,
    GENERIC_TEMPLATE,
    SECTION_TEMPLATES,
    get_checklist_for_target,
    get_template_for_target,
    initialize_sections,
)
from app.modules.applications.service import build_section_prompt


# =====================================================================
# TESTS TEMPLATES AGENCE (US4 — T038)
# =====================================================================


class TestIntermediaryAgencyTemplate:
    """Tests pour le template intermediary_agency (5 sections developpement)."""

    def test_agency_template_has_5_sections(self) -> None:
        """Le template agence contient exactement 5 sections."""
        template = get_template_for_target(TargetType.intermediary_agency)
        assert len(template) == 5

    def test_agency_template_section_keys(self) -> None:
        """Les cles des sections agence correspondent au data-model."""
        template = get_template_for_target(TargetType.intermediary_agency)
        keys = [s["key"] for s in template]
        expected = [
            "project_holder_id",
            "national_alignment",
            "technical_description",
            "budget_cofinancing",
            "impact_indicators",
        ]
        assert keys == expected

    def test_agency_template_has_development_tone(self) -> None:
        """Chaque section agence contient des instructions de ton orientees developpement."""
        template = get_template_for_target(TargetType.intermediary_agency)
        for section in template:
            assert "tone" in section
            assert len(section["tone"]) > 10

    def test_agency_template_project_holder_tone(self) -> None:
        """La section project_holder_id a un ton 'Developpement'."""
        template = get_template_for_target(TargetType.intermediary_agency)
        holder = next(s for s in template if s["key"] == "project_holder_id")
        assert "veloppement" in holder["tone"].lower() or "local" in holder["tone"].lower()

    def test_agency_template_national_alignment_tone(self) -> None:
        """La section national_alignment a un ton strategique."""
        template = get_template_for_target(TargetType.intermediary_agency)
        alignment = next(s for s in template if s["key"] == "national_alignment")
        assert "strat" in alignment["tone"].lower()

    def test_agency_template_impact_indicators_tone(self) -> None:
        """La section impact_indicators a un ton rigoureux/mesurable."""
        template = get_template_for_target(TargetType.intermediary_agency)
        indicators = next(s for s in template if s["key"] == "impact_indicators")
        tone_lower = indicators["tone"].lower()
        assert "mesur" in tone_lower or "rigoureux" in tone_lower

    def test_agency_checklist_exists(self) -> None:
        """La checklist agence existe et contient des documents pertinents."""
        checklist = get_checklist_for_target(TargetType.intermediary_agency)
        assert len(checklist) >= 4
        keys = [item["key"] for item in checklist]
        assert "project_proposal" in keys
        assert "results_framework" in keys

    def test_initialize_sections_agency(self) -> None:
        """initialize_sections retourne 5 sections a not_generated pour agence."""
        sections = initialize_sections(TargetType.intermediary_agency)
        assert len(sections) == 5
        for key, section in sections.items():
            assert section["status"] == "not_generated"
            assert section["content"] is None
            assert "title" in section


class TestAgencySectionPrompt:
    """Tests pour le prompt de generation de sections agence."""

    def test_build_section_prompt_agency_includes_target_type(self) -> None:
        """Le prompt inclut le target_type intermediary_agency."""
        template = get_template_for_target(TargetType.intermediary_agency)
        section_config = template[0]
        prompt = build_section_prompt(
            target_type="intermediary_agency",
            section_key=section_config["key"],
            section_config=section_config,
            company_context="Entreprise test",
            fund_context="Fonds FEM",
        )
        assert "intermediary_agency" in prompt

    def test_build_section_prompt_agency_includes_tone(self) -> None:
        """Le prompt inclut les instructions de ton de la section."""
        template = get_template_for_target(TargetType.intermediary_agency)
        section_config = template[0]
        prompt = build_section_prompt(
            target_type="intermediary_agency",
            section_key=section_config["key"],
            section_config=section_config,
            company_context="Entreprise test",
            fund_context="Fonds FEM",
        )
        assert section_config["tone"] in prompt

    def test_build_section_prompt_agency_with_rag(self) -> None:
        """Le prompt inclut le contexte RAG quand fourni."""
        template = get_template_for_target(TargetType.intermediary_agency)
        section_config = template[0]
        prompt = build_section_prompt(
            target_type="intermediary_agency",
            section_key=section_config["key"],
            section_config=section_config,
            company_context="Entreprise test",
            fund_context="Fonds FEM",
            rag_context="Contexte RAG supplementaire",
        )
        assert "Contexte RAG supplementaire" in prompt


# =====================================================================
# TESTS TEMPLATES CARBONE (US5 — T041)
# =====================================================================


class TestIntermediaryDeveloperTemplate:
    """Tests pour le template intermediary_developer (5 sections techniques carbone)."""

    def test_developer_template_has_5_sections(self) -> None:
        """Le template carbone contient exactement 5 sections."""
        template = get_template_for_target(TargetType.intermediary_developer)
        assert len(template) == 5

    def test_developer_template_section_keys(self) -> None:
        """Les cles des sections carbone correspondent au data-model."""
        template = get_template_for_target(TargetType.intermediary_developer)
        keys = [s["key"] for s in template]
        expected = [
            "project_methodology",
            "emission_reductions",
            "monitoring_plan",
            "additionality_analysis",
            "co_benefits",
        ]
        assert keys == expected

    def test_developer_template_has_technical_tone(self) -> None:
        """Chaque section carbone contient des instructions de ton technique."""
        template = get_template_for_target(TargetType.intermediary_developer)
        for section in template:
            assert "tone" in section
            assert len(section["tone"]) > 10

    def test_developer_template_methodology_tone(self) -> None:
        """La section project_methodology a un ton technique/methodologique."""
        template = get_template_for_target(TargetType.intermediary_developer)
        methodology = next(s for s in template if s["key"] == "project_methodology")
        tone_lower = methodology["tone"].lower()
        assert "technique" in tone_lower or "m\u00e9thodolog" in tone_lower

    def test_developer_template_emission_reductions_tone(self) -> None:
        """La section emission_reductions a un ton scientifique/quantifie."""
        template = get_template_for_target(TargetType.intermediary_developer)
        emissions = next(s for s in template if s["key"] == "emission_reductions")
        tone_lower = emissions["tone"].lower()
        assert "scientif" in tone_lower or "quantif" in tone_lower

    def test_developer_template_additionality_tone(self) -> None:
        """La section additionality_analysis a un ton analytique."""
        template = get_template_for_target(TargetType.intermediary_developer)
        add = next(s for s in template if s["key"] == "additionality_analysis")
        assert "analytique" in add["tone"].lower()

    def test_developer_checklist_exists(self) -> None:
        """La checklist carbone existe et contient les documents pertinents."""
        checklist = get_checklist_for_target(TargetType.intermediary_developer)
        assert len(checklist) >= 4
        keys = [item["key"] for item in checklist]
        assert "project_design_doc" in keys
        assert "baseline_study" in keys
        assert "monitoring_methodology" in keys

    def test_initialize_sections_developer(self) -> None:
        """initialize_sections retourne 5 sections a not_generated pour carbone."""
        sections = initialize_sections(TargetType.intermediary_developer)
        assert len(sections) == 5
        for key, section in sections.items():
            assert section["status"] == "not_generated"
            assert section["content"] is None
            assert "title" in section


class TestDeveloperSectionPrompt:
    """Tests pour le prompt de generation de sections carbone."""

    def test_build_section_prompt_developer_includes_target_type(self) -> None:
        """Le prompt inclut le target_type intermediary_developer."""
        template = get_template_for_target(TargetType.intermediary_developer)
        section_config = template[0]
        prompt = build_section_prompt(
            target_type="intermediary_developer",
            section_key=section_config["key"],
            section_config=section_config,
            company_context="Entreprise test",
            fund_context="Gold Standard",
        )
        assert "intermediary_developer" in prompt

    def test_build_section_prompt_developer_includes_tone(self) -> None:
        """Le prompt inclut les instructions de ton de la section."""
        template = get_template_for_target(TargetType.intermediary_developer)
        section_config = template[0]
        prompt = build_section_prompt(
            target_type="intermediary_developer",
            section_key=section_config["key"],
            section_config=section_config,
            company_context="Entreprise test",
            fund_context="Gold Standard",
        )
        assert section_config["tone"] in prompt


# =====================================================================
# TESTS GENERIQUES TEMPLATES
# =====================================================================


class TestGenericTemplate:
    """Tests pour le template generique (fallback)."""

    def test_generic_template_has_5_sections(self) -> None:
        """Le template generique contient 5 sections."""
        assert len(GENERIC_TEMPLATE) == 5

    def test_unknown_target_type_returns_generic(self) -> None:
        """Un target_type inconnu retourne le template generique."""
        template = get_template_for_target("unknown_type")
        assert template == GENERIC_TEMPLATE


class TestAllTemplates:
    """Tests transversaux sur tous les templates."""

    @pytest.mark.parametrize("target_type", [
        TargetType.fund_direct,
        TargetType.intermediary_bank,
        TargetType.intermediary_agency,
        TargetType.intermediary_developer,
    ])
    def test_all_templates_have_required_fields(self, target_type: str) -> None:
        """Chaque section de chaque template a les champs requis."""
        template = get_template_for_target(target_type)
        for section in template:
            assert "key" in section
            assert "title" in section
            assert "description" in section
            assert "tone" in section

    @pytest.mark.parametrize("target_type", [
        TargetType.fund_direct,
        TargetType.intermediary_bank,
        TargetType.intermediary_agency,
        TargetType.intermediary_developer,
    ])
    def test_all_templates_have_matching_checklists(self, target_type: str) -> None:
        """Chaque target_type a une checklist associee."""
        checklist = get_checklist_for_target(target_type)
        assert len(checklist) >= 4
        for item in checklist:
            assert "key" in item
            assert "name" in item
            assert "status" in item
            assert item["status"] == "missing"
