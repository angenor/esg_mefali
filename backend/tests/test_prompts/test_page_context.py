"""Tests Story 3.2 : build_page_context_instruction et integration dans les prompts."""

import pytest

from app.prompts.system import (
    PAGE_DESCRIPTIONS,
    build_page_context_instruction,
    build_system_prompt,
)


class TestBuildPageContextInstruction:
    """Task 4 — Tests unitaires pour build_page_context_instruction."""

    def test_none_returns_empty(self):
        """AC3 — current_page=None retourne une chaine vide."""
        assert build_page_context_instruction(None) == ""

    def test_empty_string_returns_empty(self):
        """AC3 — current_page="" retourne une chaine vide."""
        assert build_page_context_instruction("") == ""

    def test_known_page_includes_description(self):
        """AC1 — Une page connue retourne un contexte avec la description."""
        result = build_page_context_instruction("/carbon/results")
        assert "/carbon/results" in result
        assert "CONTEXTE DE NAVIGATION" in result
        assert "bilan carbone" in result

    def test_dashboard_includes_guidance_suggestion(self):
        """AC2/FR13 — /dashboard contient une proposition de guidage."""
        result = build_page_context_instruction("/dashboard")
        assert "proposer" in result.lower() or "accompagner" in result.lower()

    def test_esg_results_includes_guidance_suggestion(self):
        """AC2/FR13 — /esg/results contient une proposition de guidage."""
        result = build_page_context_instruction("/esg/results")
        assert "accompagner" in result.lower() or "proposer" in result.lower()

    def test_carbon_results_includes_guidance_suggestion(self):
        """AC2/FR13 — /carbon/results contient une proposition de guidage."""
        result = build_page_context_instruction("/carbon/results")
        assert "accompagner" in result.lower() or "proposer" in result.lower()

    def test_action_plan_includes_guidance_suggestion(self):
        """AC2/FR13 — /action-plan contient une proposition de guidage."""
        result = build_page_context_instruction("/action-plan")
        assert "accompagner" in result.lower() or "proposer" in result.lower()

    def test_unknown_page_returns_generic_context(self):
        """AC1 — Une page inconnue retourne un contexte generique."""
        result = build_page_context_instruction("/unknown-page")
        assert "/unknown-page" in result
        assert "CONTEXTE DE NAVIGATION" in result

    def test_known_page_no_guidance_for_non_result_pages(self):
        """Les pages non-resultats n'incluent pas la proposition de guidage FR13."""
        result = build_page_context_instruction("/esg")
        assert "accompagner" not in result.lower()

    def test_all_page_descriptions_produce_nonempty(self):
        """Chaque page du mapping PAGE_DESCRIPTIONS produit un resultat non-vide."""
        for page in PAGE_DESCRIPTIONS:
            result = build_page_context_instruction(page)
            assert result, f"Page {page} devrait produire un resultat non-vide"
            assert "CONTEXTE DE NAVIGATION" in result


class TestBuildSystemPromptWithCurrentPage:
    """Task 5 — Tests d'integration de current_page dans build_system_prompt."""

    def test_current_page_included_in_prompt(self):
        """AC1 — build_system_prompt avec current_page inclut le contexte de page."""
        result = build_system_prompt(current_page="/esg")
        assert "CONTEXTE DE NAVIGATION" in result
        assert "/esg" in result

    def test_current_page_none_no_page_context(self):
        """AC3 — build_system_prompt sans current_page n'inclut pas de bloc PAGE_CONTEXT."""
        result = build_system_prompt(current_page=None)
        assert "CONTEXTE DE NAVIGATION" not in result

    def test_current_page_empty_no_page_context(self):
        """AC3 — build_system_prompt avec current_page="" n'inclut pas de bloc PAGE_CONTEXT."""
        result = build_system_prompt(current_page="")
        assert "CONTEXTE DE NAVIGATION" not in result

    def test_current_page_default_no_page_context(self):
        """AC3 — build_system_prompt sans parametre current_page n'inclut pas de bloc PAGE_CONTEXT."""
        result = build_system_prompt()
        assert "CONTEXTE DE NAVIGATION" not in result


class TestBuildSpecialistPromptsWithCurrentPage:
    """Task 5 — Tests d'integration de current_page dans les build_*_prompt specialistes."""

    def test_esg_prompt_with_current_page(self):
        """AC5 — build_esg_prompt avec current_page inclut le contexte."""
        from app.prompts.esg_scoring import build_esg_prompt

        result = build_esg_prompt(current_page="/dashboard")
        assert "CONTEXTE DE NAVIGATION" in result
        assert "/dashboard" in result

    def test_esg_prompt_without_current_page(self):
        """AC3 — build_esg_prompt sans current_page n'inclut pas le contexte."""
        from app.prompts.esg_scoring import build_esg_prompt

        result = build_esg_prompt(current_page=None)
        assert "CONTEXTE DE NAVIGATION" not in result

    def test_carbon_prompt_with_current_page(self):
        """AC5 — build_carbon_prompt avec current_page inclut le contexte."""
        from app.prompts.carbon import build_carbon_prompt

        result = build_carbon_prompt(current_page="/carbon/results")
        assert "CONTEXTE DE NAVIGATION" in result

    def test_carbon_prompt_without_current_page(self):
        from app.prompts.carbon import build_carbon_prompt

        result = build_carbon_prompt(current_page=None)
        assert "CONTEXTE DE NAVIGATION" not in result

    def test_financing_prompt_with_current_page(self):
        """AC5 — build_financing_prompt avec current_page inclut le contexte."""
        from app.prompts.financing import build_financing_prompt

        result = build_financing_prompt(current_page="/financing")
        assert "CONTEXTE DE NAVIGATION" in result

    def test_financing_prompt_without_current_page(self):
        from app.prompts.financing import build_financing_prompt

        result = build_financing_prompt(current_page=None)
        assert "CONTEXTE DE NAVIGATION" not in result

    def test_application_prompt_with_current_page(self):
        """AC5 — build_application_prompt avec current_page inclut le contexte."""
        from app.prompts.application import build_application_prompt

        result = build_application_prompt(current_page="/dashboard")
        assert "CONTEXTE DE NAVIGATION" in result

    def test_application_prompt_without_current_page(self):
        from app.prompts.application import build_application_prompt

        result = build_application_prompt(current_page=None)
        assert "CONTEXTE DE NAVIGATION" not in result

    def test_credit_prompt_with_current_page(self):
        """AC5 — build_credit_prompt avec current_page inclut le contexte."""
        from app.prompts.credit import build_credit_prompt

        result = build_credit_prompt(current_page="/credit-score")
        assert "CONTEXTE DE NAVIGATION" in result

    def test_credit_prompt_without_current_page(self):
        from app.prompts.credit import build_credit_prompt

        result = build_credit_prompt(current_page=None)
        assert "CONTEXTE DE NAVIGATION" not in result

    def test_action_plan_prompt_with_current_page(self):
        """AC5 — build_action_plan_prompt avec current_page inclut le contexte."""
        from app.prompts.action_plan import build_action_plan_prompt

        result = build_action_plan_prompt(current_page="/action-plan")
        assert "CONTEXTE DE NAVIGATION" in result

    def test_action_plan_prompt_without_current_page(self):
        from app.prompts.action_plan import build_action_plan_prompt

        result = build_action_plan_prompt(current_page=None)
        assert "CONTEXTE DE NAVIGATION" not in result
