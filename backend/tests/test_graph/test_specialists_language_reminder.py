"""Tests d'invariant structurel pour DEF-BUG-V2-001-1.

Garantit que les 6 noeuds specialistes (esg_scoring, carbon, financing,
application, credit, action_plan) appendent « RAPPEL FINAL — » + LANGUAGE_INSTRUCTION
en queue de `full_prompt`, comme cela est deja fait dans `chat_node`.

Le pattern protege contre la regression chinois MiniMax post-tool-calling
observee en Vague 2 (scenarios T-ESG-01, T-CARBON-01, T-FIN-09, T-APP-02,
T-CREDIT-02, T-PLAN-02).

Ces tests sont statiques (inspection du code source) pour eviter l'overhead
de mocker l'ensemble des dependances DB + LLM de chaque noeud.
"""

from pathlib import Path

import pytest

NODES_FILE = Path(__file__).resolve().parents[2] / "app" / "graph" / "nodes.py"

SPECIALIST_NODES = [
    "esg_scoring_node",
    "carbon_node",
    "financing_node",
    "credit_node",
    "application_node",
    "action_plan_node",
]


@pytest.fixture(scope="module")
def nodes_source() -> str:
    return NODES_FILE.read_text(encoding="utf-8")


def test_nodes_file_exists(nodes_source: str) -> None:
    assert "RAPPEL FINAL" in nodes_source, (
        "Le token sentinel « RAPPEL FINAL » doit exister dans nodes.py"
    )


def test_rappel_final_count_covers_chat_plus_specialists(nodes_source: str) -> None:
    """chat_node (1) + 6 specialistes = au moins 7 occurrences."""
    count = nodes_source.count('"\\n\\nRAPPEL FINAL — " + LANGUAGE_INSTRUCTION')
    assert count >= 7, (
        f"Attendu >= 7 occurrences (chat_node + 6 specialistes), trouve {count}. "
        "Verifier que chaque noeud append LANGUAGE_INSTRUCTION en queue de full_prompt."
    )


@pytest.mark.parametrize("node_name", SPECIALIST_NODES)
def test_specialist_node_contains_language_reminder(
    nodes_source: str, node_name: str
) -> None:
    """Chaque noeud specialiste doit contenir le pattern RAPPEL FINAL dans son corps."""
    start = nodes_source.find(f"async def {node_name}(")
    assert start != -1, f"Definition {node_name} introuvable dans nodes.py"

    # Cherche la fin du corps : prochaine definition de niveau module
    next_def = nodes_source.find("\nasync def ", start + 1)
    if next_def == -1:
        next_def = nodes_source.find("\ndef ", start + 1)
    body = nodes_source[start: next_def if next_def != -1 else None]

    assert 'RAPPEL FINAL' in body, (
        f"Le noeud {node_name} doit contenir le rappel RAPPEL FINAL + LANGUAGE_INSTRUCTION "
        "en queue de full_prompt (DEF-BUG-V2-001-1)."
    )
    assert 'LANGUAGE_INSTRUCTION' in body, (
        f"Le noeud {node_name} doit importer et utiliser LANGUAGE_INSTRUCTION."
    )
