"""Tests d'invariant structurel pour BUG-V5-001.

Garantit que :
1. Le prompt `ESG_SCORING_PROMPT` contient une section « FINALISATION — TOOL CALL
   OBLIGATOIRE » forçant l'appel au tool `finalize_esg_assessment` apres les
   30 criteres + confirmation utilisateur.
2. Le noeud `esg_scoring_node` injecte `assessment_id` dans le bloc
   `ETAT DE L'EVALUATION EN COURS` afin que le LLM dispose de l'UUID a passer
   au tool.

Tests statiques (inspection source) — pas d'overhead DB/LLM.
"""

import re
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[2]
ESG_PROMPT_FILE = BACKEND_ROOT / "app" / "prompts" / "esg_scoring.py"
NODES_FILE = BACKEND_ROOT / "app" / "graph" / "nodes.py"


@pytest.fixture(scope="module")
def esg_prompt_source() -> str:
    return ESG_PROMPT_FILE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def nodes_source() -> str:
    return NODES_FILE.read_text(encoding="utf-8")


def test_esg_prompt_has_finalisation_tool_call_section(esg_prompt_source: str) -> None:
    """La section FINALISATION doit etre explicitement marquee TOOL CALL OBLIGATOIRE.

    Regex tolerant aux variations de separateur (em-dash U+2014, en-dash U+2013, hyphen).
    """
    pattern = re.compile(
        r"FINALISATION\s*[—–\-]\s*TOOL CALL OBLIGATOIRE",
        re.IGNORECASE,
    )
    assert pattern.search(esg_prompt_source), (
        "Section « FINALISATION — TOOL CALL OBLIGATOIRE » manquante dans "
        "ESG_SCORING_PROMPT — regression BUG-V5-001."
    )


def test_esg_prompt_mentions_finalize_tool(esg_prompt_source: str) -> None:
    """Le prompt doit nommer le tool `finalize_esg_assessment` dans sa section finalisation."""
    assert "finalize_esg_assessment" in esg_prompt_source, (
        "Le prompt ESG doit nommer finalize_esg_assessment pour que le LLM "
        "sache quel tool appeler."
    )


def test_esg_prompt_forbids_textual_score_without_tool(esg_prompt_source: str) -> None:
    """Le prompt doit interdire explicitement les scores textuels sans tool call."""
    # On cherche des mots-cles attestant l'interdiction (le wording peut evoluer).
    source_lower = esg_prompt_source.lower()
    assert "regle absolue" in source_lower, (
        "Le marqueur « REGLE ABSOLUE » doit exister pour signaler l'interdiction "
        "d'un score sans tool call (BUG-V5-001)."
    )
    assert "interdit" in source_lower or "jamais" in source_lower, (
        "Le prompt doit contenir une interdiction explicite de communiquer un "
        "score sans avoir appele le tool de finalisation."
    )


def test_esg_node_injects_assessment_id_in_state_context(nodes_source: str) -> None:
    """esg_scoring_node doit exposer assessment_id dans ETAT DE L'EVALUATION EN COURS."""
    # Localiser le bloc esg_state_context
    start = nodes_source.find("esg_state_context")
    assert start != -1, "Bloc esg_state_context introuvable dans nodes.py."

    # Prendre une fenetre suffisamment large pour couvrir la f-string
    window = nodes_source[start : start + 600]

    assert "assessment_id" in window, (
        "Le bloc esg_state_context doit injecter assessment_id (BUG-V5-001) — "
        "sans cet UUID, le LLM ne peut pas appeler finalize_esg_assessment."
    )
    assert "ETAT DE L'EVALUATION EN COURS" in window, (
        "En-tete ETAT DE L'EVALUATION EN COURS manquante dans le bloc."
    )
