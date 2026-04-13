"""Tests pour GUIDED_TOUR_INSTRUCTION et son injection dans les 6 noeuds LangGraph.

Story 6.2 — branche le tool `trigger_guided_tour` (story 6.1) cote LLM
via un prompt module-level concatene dans 6 builders de prompts et binde
dans 6 noeuds LangGraph.
"""

from pathlib import Path

import pytest

from app.prompts.action_plan import build_action_plan_prompt
from app.prompts.application import build_application_prompt
from app.prompts.carbon import build_carbon_prompt
from app.prompts.credit import build_credit_prompt
from app.prompts.esg_scoring import build_esg_prompt
from app.prompts.financing import build_financing_prompt
from app.prompts.guided_tour import GUIDED_TOUR_INSTRUCTION
from app.prompts.system import build_system_prompt


# --- AC1 : Contenu du prompt GUIDED_TOUR_INSTRUCTION ---


EXPECTED_TOUR_IDS = [
    "show_esg_results",
    "show_carbon_results",
    "show_financing_catalog",
    "show_credit_score",
    "show_action_plan",
    "show_dashboard_overview",
]


def test_instruction_contains_all_six_tour_ids():
    """T1 — GUIDED_TOUR_INSTRUCTION declare les 6 tour_id exacts."""
    for tour_id in EXPECTED_TOUR_IDS:
        assert tour_id in GUIDED_TOUR_INSTRUCTION, (
            f"tour_id manquant dans GUIDED_TOUR_INSTRUCTION : {tour_id}"
        )


def test_instruction_contains_trigger_keywords():
    """T2 — GUIDED_TOUR_INSTRUCTION mentionne les regles de declenchement.

    On verifie la presence des mots-cles critiques : conditions de proposition
    (completion / demande explicite), outil interactif pour consentement.
    """
    text = GUIDED_TOUR_INSTRUCTION.lower()
    assert "completion" in text or "complet" in text
    assert "demande explicite" in text
    assert "ask_interactive_question" in text
    assert "consentement" in text


def test_instruction_mentions_trigger_tool_name():
    """T3 — Le prompt nomme explicitement le tool trigger_guided_tour."""
    assert "trigger_guided_tour" in GUIDED_TOUR_INSTRUCTION


def test_instruction_mentions_security_context_rule():
    """T4 — Le prompt rappelle la regle NFR10 sur le champ `context`."""
    text = GUIDED_TOUR_INSTRUCTION.lower()
    # Rappel securite : pas d'IDs / tokens / emails / PII dans context
    assert "context" in text
    assert "id" in text or "token" in text or "pii" in text or "email" in text


# --- AC2 : Injection dans les 6 builders autorises ---


@pytest.mark.parametrize(
    "name,builder",
    [
        ("esg", build_esg_prompt),
        ("carbon", build_carbon_prompt),
        ("financing", build_financing_prompt),
        ("credit", build_credit_prompt),
        ("action_plan", build_action_plan_prompt),
    ],
)
def test_guided_tour_injected_in_specialized_prompt(name, builder):
    """T5 — GUIDED_TOUR_INSTRUCTION est injecte dans les 5 prompts specialises."""
    prompt = builder()
    assert GUIDED_TOUR_INSTRUCTION in prompt, (
        f"GUIDED_TOUR_INSTRUCTION absent dans build_{name}_prompt()"
    )


def test_guided_tour_injected_in_system_prompt_with_profile():
    """T6 — build_system_prompt() injecte GUIDED_TOUR_INSTRUCTION post-onboarding."""
    profile = {"sector": "recyclage", "city": "Abidjan"}
    prompt = build_system_prompt(user_profile=profile)
    assert GUIDED_TOUR_INSTRUCTION in prompt


# --- AC3 : Non-injection dans les noeuds exclus ---


def test_guided_tour_not_injected_in_application_prompt():
    """T7 — build_application_prompt() ne contient PAS GUIDED_TOUR_INSTRUCTION."""
    prompt = build_application_prompt()
    assert GUIDED_TOUR_INSTRUCTION not in prompt


def test_guided_tour_absent_in_system_prompt_without_profile():
    """T8 — build_system_prompt() sans profil n'injecte PAS le guidage.

    Meme logique que pour STYLE_INSTRUCTION : un utilisateur non onboarde
    n'a aucun resultat a visiter.
    """
    prompt = build_system_prompt()
    assert GUIDED_TOUR_INSTRUCTION not in prompt


def test_guided_tour_absent_in_system_prompt_minimal_profile():
    """T9 — build_system_prompt() avec profil < 2 champs n'injecte PAS."""
    profile = {"sector": "recyclage"}
    prompt = build_system_prompt(user_profile=profile)
    assert GUIDED_TOUR_INSTRUCTION not in prompt


# --- AC4 : Binding de GUIDED_TOUR_TOOLS dans les 6 noeuds ---


def test_guided_tour_tools_export_shape():
    """T10 — Le module guided_tour_tools expose trigger_guided_tour et GUIDED_TOUR_TOOLS."""
    from app.graph.tools.guided_tour_tools import (
        GUIDED_TOUR_TOOLS,
        trigger_guided_tour,
    )

    assert isinstance(GUIDED_TOUR_TOOLS, list)
    assert trigger_guided_tour in GUIDED_TOUR_TOOLS
    assert len(GUIDED_TOUR_TOOLS) >= 1


def test_guided_tour_tools_bound_in_all_six_nodes():
    """T11 — graph/nodes.py importe et binde GUIDED_TOUR_TOOLS dans les 6 noeuds.

    Smoke test textuel : on verifie que le symbole est importe et reference
    dans le fichier source de nodes.py. On s'appuie sur le fait que les
    noeuds concernes (esg, carbon, financing, credit, chat, action_plan)
    sont clairement identifiables dans un module mono-fichier.
    """
    nodes_path = (
        Path(__file__).resolve().parent.parent.parent
        / "app"
        / "graph"
        / "nodes.py"
    )
    source = nodes_path.read_text(encoding="utf-8")

    assert "from app.graph.tools.guided_tour_tools import GUIDED_TOUR_TOOLS" in source, (
        "Import GUIDED_TOUR_TOOLS absent de graph/nodes.py"
    )
    # Le symbole doit etre reference plusieurs fois (1 import + 6 bindings minimum)
    assert source.count("GUIDED_TOUR_TOOLS") >= 7, (
        "GUIDED_TOUR_TOOLS doit etre binde dans les 6 noeuds en plus de l'import"
    )


def test_guided_tour_tools_not_bound_in_excluded_nodes():
    """T12 — application_node / document_node / profiling_node / router_node n'importent pas GUIDED_TOUR_TOOLS.

    On isole la zone de chaque noeud exclu par recherche textuelle de
    l'entete `async def <node>_node(` jusqu'au prochain `async def`.
    """
    nodes_path = (
        Path(__file__).resolve().parent.parent.parent
        / "app"
        / "graph"
        / "nodes.py"
    )
    source = nodes_path.read_text(encoding="utf-8")

    excluded = ["application_node", "document_node", "profiling_node", "router_node"]
    for node in excluded:
        header = f"async def {node}("
        start = source.find(header)
        if start == -1:
            # certains noeuds peuvent etre synchrones ou absents -> skip silencieux
            continue
        # Chercher le debut du prochain noeud pour delimiter le corps
        next_def = source.find("\nasync def ", start + 1)
        body = source[start:next_def] if next_def != -1 else source[start:]
        assert "GUIDED_TOUR_TOOLS" not in body, (
            f"GUIDED_TOUR_TOOLS ne doit PAS apparaitre dans le noeud exclu {node}"
        )
