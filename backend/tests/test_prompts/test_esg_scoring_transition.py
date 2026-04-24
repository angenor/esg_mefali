"""BUG-V4-001 — Garde-fou : le prompt ESG force l'appel `ask_interactive_question` a chaque transition de pilier.

Sans cette regle, le LLM bascule d'un pilier a l'autre en texte libre apres
`batch_save_esg_criteria`, laissant l'utilisateur sans widget a cliquer et
bloquant toute la progression ESG en cascade (voir tests-manuels-vague-4).
"""

from app.prompts.esg_scoring import ESG_SCORING_PROMPT, build_esg_prompt


def test_esg_prompt_contains_transition_tool_rule():
    """Le prompt contient la section TRANSITION PILIER — TOOL CALL OBLIGATOIRE."""
    prompt = build_esg_prompt()
    assert "TRANSITION PILIER" in prompt, (
        "La regle de transition pilier est absente — risque que le LLM "
        "bascule d'un pilier a l'autre sans nouveau widget (BUG-V4-001)."
    )


def test_esg_prompt_transition_mentions_ask_interactive_question():
    """La regle de transition cite explicitement `ask_interactive_question`."""
    prompt = build_esg_prompt()
    # La section TRANSITION PILIER doit citer le tool a appeler.
    transition_idx = prompt.find("TRANSITION PILIER")
    assert transition_idx >= 0
    transition_section = prompt[transition_idx : transition_idx + 1200]
    assert "ask_interactive_question" in transition_section, (
        "La section TRANSITION PILIER doit citer `ask_interactive_question` "
        "comme tool a appeler au tour suivant batch_save_esg_criteria."
    )


def test_esg_prompt_transition_forbids_text_only():
    """La regle interdit un message texte seul entre deux piliers."""
    prompt = build_esg_prompt()
    transition_idx = prompt.find("TRANSITION PILIER")
    assert transition_idx >= 0
    transition_section = prompt[transition_idx : transition_idx + 1200]
    # Mots-cles qui traduisent l'interdiction en francais.
    assert "INTERDIT" in transition_section or "JAMAIS" in transition_section, (
        "La section TRANSITION PILIER doit interdire explicitement les "
        "messages texte seuls entre piliers (sinon le LLM ignore la regle)."
    )


def test_esg_prompt_transition_lists_full_sequence():
    """La sequence E -> S -> G -> finalize est explicitement documentee."""
    prompt = ESG_SCORING_PROMPT
    transition_idx = prompt.find("TRANSITION PILIER")
    assert transition_idx >= 0
    section = prompt[transition_idx : transition_idx + 1200]
    # Chaque pilier est nomme dans la sequence (ordre d'evaluation).
    assert "Social" in section
    assert "Gouvernance" in section
    assert "finalize_esg_assessment" in section
