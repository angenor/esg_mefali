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
    """T4 — Le prompt rappelle la regle NFR10 sur le champ `context`.

    Verifie que la regle securite est documentee via des mots-cles pleins
    (non sous-chaines — « id » matche « aide », « guide », « vide »).
    Au moins 2 occurrences PII distinctes doivent etre presentes pour
    garantir un rappel explicite et non accidentel.
    """
    text = GUIDED_TOUR_INSTRUCTION.lower()
    assert "context" in text

    pii_keywords = [
        "user_id",
        "conversation_id",
        "token",
        "email",
        "pii",
        "mot de passe",
        "password",
    ]
    mentions = [kw for kw in pii_keywords if kw in text]
    assert len(mentions) >= 2, (
        f"NFR10 insuffisamment documente : au moins 2 mots-cles PII requis, "
        f"trouve {mentions}"
    )


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


def test_guided_tour_present_in_system_prompt_without_profile():
    """T8 — build_system_prompt() sans profil injecte GUIDED_TOUR_INSTRUCTION.

    Le tool `trigger_guided_tour` est binde sans condition dans `chat_node`,
    donc les regles d'usage (6 tour_id autorises, consentement, NFR10 sur
    `context`) doivent toujours accompagner le tool cote LLM — meme pour
    un utilisateur non onboarde. Defense en profondeur (review story 6.2).
    """
    prompt = build_system_prompt()
    assert GUIDED_TOUR_INSTRUCTION in prompt


def test_guided_tour_present_in_system_prompt_minimal_profile():
    """T9 — build_system_prompt() avec profil < 2 champs injecte aussi le guidage."""
    profile = {"sector": "recyclage"}
    prompt = build_system_prompt(user_profile=profile)
    assert GUIDED_TOUR_INSTRUCTION in prompt


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

    Chaque noeud cible (esg, carbon, financing, credit, chat, action_plan)
    reference le symbole 2 fois : 1 import local + 1 ajout a bind_tools.
    Le plancher attendu est donc 6 * 2 = 12 occurrences. On exige >= 12
    pour qu'une regression sur un seul nœud (perte de binding) soit detectee.
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
    occurrences = source.count("GUIDED_TOUR_TOOLS")
    assert occurrences >= 12, (
        f"GUIDED_TOUR_TOOLS doit etre importe + binde dans les 6 noeuds "
        f"(>= 12 occurrences attendues), trouve {occurrences}"
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
        assert start != -1, (
            f"En-tete `async def {node}(` introuvable dans graph/nodes.py : "
            f"le noeud a ete renomme, supprime ou rendu synchrone. "
            f"Mettre a jour la liste `excluded` si ce changement est volontaire."
        )
        # Chercher le debut du prochain noeud pour delimiter le corps
        next_def = source.find("\nasync def ", start + 1)
        body = source[start:next_def] if next_def != -1 else source[start:]
        assert "GUIDED_TOUR_TOOLS" not in body, (
            f"GUIDED_TOUR_TOOLS ne doit PAS apparaitre dans le noeud exclu {node}"
        )
