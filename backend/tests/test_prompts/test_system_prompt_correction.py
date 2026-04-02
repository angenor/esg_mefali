"""Tests pour l'instruction de correction des données inexistantes (US5)."""

from app.prompts.system import build_system_prompt


def test_system_prompt_contains_correction_instruction():
    """T019 — Le prompt système avec profil contient l'instruction de correction."""
    profile = {
        "company_name": "EcoPlast SARL",
        "sector": "recyclage",
        "city": "Abidjan",
        "country": "Côte d'Ivoire",
    }
    prompt = build_system_prompt(user_profile=profile)
    assert "n'existe PAS" in prompt or "n'existe pas" in prompt.lower()
    assert "corrige" in prompt.lower()


def test_system_prompt_correction_mentions_profile_data():
    """T019 — L'instruction de correction référence les données du profil."""
    profile = {
        "company_name": "EcoPlast SARL",
        "city": "Abidjan",
    }
    prompt = build_system_prompt(user_profile=profile)
    # L'instruction doit mentionner de rediriger vers les données réelles du profil
    assert "profil" in prompt.lower()
    # L'instruction ne doit pas proposer d'ajouter sauf demande explicite
    assert "Ne propose PAS" in prompt or "ne propose pas" in prompt.lower()
