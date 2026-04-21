"""Registre central des instructions transverses injectees dans les prompts LLM.

CCC-9 (Story 10.8) — framework d'injection unifie. Consolide les 3 instructions
transverses (style concis spec 014, widgets interactifs spec 018, guidage
visuel spec 019) jusqu'ici dupliquees manuellement dans chacun des 7 modules
metier (chat, esg_scoring, carbon, financing, application, credit, action_plan).

Apres ce refactor, ajouter une 4e instruction transverse = 1 bloc
`InstructionEntry(...)` dans INSTRUCTION_REGISTRY. Aucun module metier a editer.

Contraintes techniques (Q tranchees) :
- Q1 : INSTRUCTION_REGISTRY est un `tuple[InstructionEntry, ...]` frozen.
- Q2 : InstructionEntry est un `@dataclass(frozen=True)` stdlib (pas Pydantic).
- Q3 : ordre d'injection = (priority ASC, name ASC) — tie-break explicite.
- Q4 : substitution via `string.Template.substitute` (strict, fail-fast).

Erreurs :
- `UnknownPromptModuleError` : module inconnu (pas dans SUPPORTED_MODULES).
- `UnboundPromptVariableError` : variable requise absente de `variables`.
Toutes deux heritent de `PromptRegistryError(ValueError)` — C1 9.7 : aucun
`try/except Exception` catch-all dans ce module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from string import Template
from typing import Final, Mapping

from app.prompts.guided_tour import GUIDED_TOUR_INSTRUCTION as _GUIDED_TOUR_TEMPLATE
from app.prompts.system import STYLE_INSTRUCTION as _STYLE_TEMPLATE
from app.prompts.widget import WIDGET_INSTRUCTION as _WIDGET_TEMPLATE


class PromptRegistryError(ValueError):
    """Erreur de base du registre (NFR60 fail-fast)."""


class UnknownPromptModuleError(PromptRegistryError):
    """Module absent du registre — evite les prompts vides silencieux."""


class UnboundPromptVariableError(PromptRegistryError):
    """Variable referencee par une instruction mais absente de `variables`."""


@dataclass(frozen=True)
class InstructionEntry:
    """Entree immutable du registre d'instructions transverses.

    Attributes:
        name: identifiant stable (cle de log, snapshot, debug).
        applies_to: tuple des modules qui consomment cette instruction
            (ex. ("chat", "esg_scoring", "carbon")).
        priority: ordre d'injection (ASC). Ex. 10 = style (tot), 50 = widget,
            90 = guided_tour (plus tard).
        template: texte d'instruction (peut contenir ${variables}).
        required_vars: variables obligatoires (fail-fast si absentes).
    """

    name: str
    applies_to: tuple[str, ...]
    priority: int
    template: str
    required_vars: tuple[str, ...] = field(default_factory=tuple)


# Modules metier supportes — fail-fast si build_prompt recoit autre chose.
# "chat" correspond a build_system_prompt (prompt principal du noeud chat).
SUPPORTED_MODULES: Final[frozenset[str]] = frozenset({
    "chat",
    "esg_scoring",
    "carbon",
    "financing",
    "application",
    "credit",
    "action_plan",
})


# Tuple frozen (immutable). Ajouter une 4e instruction = 1 bloc ici.
# Les templates sont importes depuis leurs modules d'origine pour preserver
# la retro-compatibilite (tests existants qui importent directement les
# constantes STYLE_INSTRUCTION / WIDGET_INSTRUCTION / GUIDED_TOUR_INSTRUCTION).
INSTRUCTION_REGISTRY: Final[tuple[InstructionEntry, ...]] = (
    InstructionEntry(
        name="style",
        applies_to=(
            "chat", "esg_scoring", "carbon", "financing",
            "application", "credit", "action_plan",
        ),
        priority=10,
        template=_STYLE_TEMPLATE,
    ),
    InstructionEntry(
        name="widget",
        applies_to=(
            "chat", "esg_scoring", "carbon", "financing",
            "application", "credit", "action_plan",
        ),
        priority=50,
        template=_WIDGET_TEMPLATE,
    ),
    InstructionEntry(
        name="guided_tour",
        # Note : "application" exclu pour parite historique — les dossiers
        # de candidature sont une phase de saisie, pas un terminal de resultats
        # a guider.
        applies_to=(
            "chat", "esg_scoring", "carbon", "financing",
            "credit", "action_plan",
        ),
        priority=90,
        template=_GUIDED_TOUR_TEMPLATE,
    ),
)


def build_prompt(
    module: str,
    variables: Mapping[str, str] | None = None,
    base: str = "",
) -> str:
    """Construire un prompt composite a partir du registre d'instructions.

    Flow :
        1. Valide module ∈ SUPPORTED_MODULES (sinon UnknownPromptModuleError).
        2. Filtre INSTRUCTION_REGISTRY par `applies_to` contient `module`.
        3. Trie par (priority ASC, name ASC) — stable et deterministe.
        4. Pour chaque entree : verifie required_vars, substitue ${var}
           via string.Template.substitute (strict) → UnboundPromptVariableError
           si variable manquante (ou KeyError re-levee explicitement).
        5. Concatene base + "\\n\\n" + "\\n\\n".join(rendered).

    Args:
        module: identifiant du module metier (cle de SUPPORTED_MODULES).
        variables: mapping des variables de substitution (optionnel).
        base: prefixe concatene en tete du prompt (optionnel).

    Returns:
        Le prompt composite final, pret a injection LLM.

    Raises:
        UnknownPromptModuleError: si module n'est pas dans SUPPORTED_MODULES.
        UnboundPromptVariableError: si une required_var manque dans variables
            ou si une variable referencee par le template n'est pas fournie.
    """
    if module not in SUPPORTED_MODULES:
        raise UnknownPromptModuleError(
            f"Unknown prompt module: {module!r}. "
            f"Supported: {sorted(SUPPORTED_MODULES)}"
        )

    vars_map: dict[str, str] = dict(variables or {})

    applicable = sorted(
        (e for e in INSTRUCTION_REGISTRY if module in e.applies_to),
        key=lambda e: (e.priority, e.name),
    )

    rendered: list[str] = []
    for entry in applicable:
        missing = [v for v in entry.required_vars if v not in vars_map]
        if missing:
            raise UnboundPromptVariableError(
                f"Instruction {entry.name!r} requires variables {missing} "
                f"for module {module!r} — got {sorted(vars_map.keys())}"
            )
        try:
            rendered.append(Template(entry.template).substitute(vars_map))
        except KeyError as exc:
            # Variable referencee par le template mais absente de variables :
            # on remonte explicitement plutot que silencieusement (fail-fast).
            raise UnboundPromptVariableError(
                f"Template variable {exc.args[0]!r} referenced by instruction "
                f"{entry.name!r} but not provided for module {module!r}"
            ) from exc

    parts = [p for p in [base.strip(), *rendered] if p]
    return "\n\n".join(parts)
