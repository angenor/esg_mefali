"""Tests du prompt dynamique (US2)."""

import pytest

from app.prompts.system import build_system_prompt


class TestBuildSystemPrompt:
    """Tests de la construction dynamique du prompt système."""

    def test_prompt_contains_profile_when_present(self) -> None:
        """Le prompt contient les infos du profil quand user_profile est fourni."""
        profile = {
            "company_name": "EcoPlast SARL",
            "sector": "recyclage",
            "city": "Abidjan",
            "country": "Côte d'Ivoire",
            "employee_count": 15,
        }
        prompt = build_system_prompt(user_profile=profile)

        assert "EcoPlast SARL" in prompt
        assert "recyclage" in prompt
        assert "Abidjan" in prompt
        assert "15" in prompt
        assert "Ne repose JAMAIS une question" in prompt

    def test_prompt_without_profile(self) -> None:
        """Le prompt ne contient pas de section profil quand vide."""
        prompt = build_system_prompt(user_profile=None)

        assert "Profil de l'entreprise" not in prompt
        assert "Ne repose JAMAIS une question" not in prompt

    def test_prompt_with_empty_profile(self) -> None:
        """Un profil vide (dict sans valeurs) n'ajoute pas de section."""
        prompt = build_system_prompt(user_profile={})

        assert "Profil de l'entreprise" not in prompt

    def test_prompt_excludes_none_and_empty(self) -> None:
        """Les champs None et chaînes vides ne sont pas inclus."""
        profile = {
            "company_name": "Test",
            "sector": None,
            "city": "",
            "country": "Mali",
        }
        prompt = build_system_prompt(user_profile=profile)

        assert "Test" in prompt
        assert "Mali" in prompt
        assert "sector" not in prompt.split("Profil de l'entreprise")[1].split("IMPORTANT")[0].lower()

    def test_prompt_with_context_memory(self) -> None:
        """Le prompt contient les résumés des conversations précédentes."""
        summaries = [
            "Discussion sur le scoring ESG de l'entreprise",
            "Analyse des fonds GCF disponibles au Mali",
        ]
        prompt = build_system_prompt(context_memory=summaries)

        assert "Résumés des conversations précédentes" in prompt
        assert "scoring ESG" in prompt
        assert "fonds GCF" in prompt
        assert "continuité" in prompt

    def test_prompt_with_profile_and_memory(self) -> None:
        """Le prompt combine profil et mémoire contextuelle."""
        profile = {"company_name": "AgriSol", "sector": "agriculture"}
        memory = ["Premier échange sur les certifications bio"]

        prompt = build_system_prompt(
            user_profile=profile, context_memory=memory
        )

        assert "AgriSol" in prompt
        assert "certifications bio" in prompt

    def test_boolean_true_displayed_as_oui(self) -> None:
        """Les booléens True sont affichés comme 'Oui'."""
        profile = {"has_waste_management": True}
        prompt = build_system_prompt(user_profile=profile)

        assert "Oui" in prompt

    def test_boolean_false_excluded(self) -> None:
        """Les booléens False ne sont pas affichés (considérés comme négatifs)."""
        profile = {"has_energy_policy": False}
        prompt = build_system_prompt(user_profile=profile)

        # False est exclu car il n'apporte pas d'info utile au prompt
        assert "Politique énergétique" not in prompt

    def test_empty_memory_no_section(self) -> None:
        """Une liste vide de résumés n'ajoute pas de section."""
        prompt = build_system_prompt(context_memory=[])

        assert "Résumés des conversations" not in prompt
