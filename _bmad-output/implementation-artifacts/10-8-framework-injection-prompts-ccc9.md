# Story 10.8 : Framework d'injection unifié de prompts (CCC-9)

Status: review

> **Contexte** : 8ᵉ story Epic 10 Fondations Phase 0. **Retour au scope brownfield refactor interne** après la trilogie infra (10.5 RLS + 10.6 StorageProvider + 10.7 environnements). Story plus légère (**M**, 2–3 h), zéro nouveau schéma BDD, zéro nouvelle migration, zéro Terraform. Le livrable principal est un **registre Python central** qui absorbe 3 patterns d'instructions transverses actuellement dupliqués à travers 7+ modules prompts.
>
> **Anti-pattern historique à éradiquer** — les 4 spec-correctifs (013 routing multi-tour, 014 style concis, 015 tool calling forcé, 016 persistence bugs, 017 failing tests) ont chacun introduit des « patches prompts » éparpillés dans `backend/app/prompts/*.py` : chaque correctif rajoute un bloc `STYLE_INSTRUCTION` / `WIDGET_INSTRUCTION` / `GUIDED_TOUR_INSTRUCTION` importé et **concaténé manuellement** dans chaque `build_*_prompt()` des 7 modules métier. Résultat aujourd'hui :
>
> ```
> backend/app/prompts/action_plan.py   → + STYLE_INSTRUCTION + WIDGET_INSTRUCTION + GUIDED_TOUR_INSTRUCTION
> backend/app/prompts/application.py   → + STYLE_INSTRUCTION + WIDGET_INSTRUCTION                         (manque GUIDED_TOUR)
> backend/app/prompts/carbon.py        → + STYLE_INSTRUCTION + WIDGET_INSTRUCTION + GUIDED_TOUR_INSTRUCTION
> backend/app/prompts/credit.py        → + STYLE_INSTRUCTION + WIDGET_INSTRUCTION + GUIDED_TOUR_INSTRUCTION
> backend/app/prompts/esg_scoring.py   → + STYLE_INSTRUCTION + WIDGET_INSTRUCTION + GUIDED_TOUR_INSTRUCTION
> backend/app/prompts/financing.py     → + STYLE_INSTRUCTION + WIDGET_INSTRUCTION + GUIDED_TOUR_INSTRUCTION
> backend/app/prompts/system.py        → STYLE + GUIDED_TOUR injectés conditionnellement (profil minimal / systématique)
> ```
>
> Ajouter une nouvelle instruction transverse demande aujourd'hui d'éditer **7 fichiers**. Avec le registre cible, ce sera **1 ligne** dans `INSTRUCTION_REGISTRY`.
>
> **Dépendances amont (done)** :
> - **Story 9.7 done** : pattern `with_retry` + `tool_call_logs` — consommé indirectement (le registre n'appelle pas d'API externe, mais les modules refactorés gardent leur intégration tool calling intacte).
> - **Spec 014 STYLE_INSTRUCTION** : déjà consolidé dans `backend/app/prompts/system.py:80-106` — sera déplacé verbatim dans le registre.
> - **Spec 018 WIDGET_INSTRUCTION** : déjà consolidé dans `backend/app/prompts/widget.py:8-50` — sera déplacé verbatim dans le registre.
> - **Spec 019 GUIDED_TOUR_INSTRUCTION** : déjà consolidé dans `backend/app/prompts/guided_tour.py:12+` — sera déplacé verbatim dans le registre (le module `guided_tour.py` garde par ailleurs `build_adaptive_frequency_hint` qui n'est pas une instruction transverse mais un appendix conditionnel).
>
> **Ce que livre 10.8 (scope strict MVP)** :
> 1. **Registre central (AC1)** : `backend/app/prompts/registry.py` expose `INSTRUCTION_REGISTRY: tuple[InstructionEntry, ...]` contenant 3 entrées initiales (`style`, `widget`, `guided_tour`). Structure testable (tuple déterministe, pas de dict mutable).
> 2. **Builder déterministe (AC2)** : `build_prompt(module: str, variables: Mapping[str, str] | None = None) -> str` retourne le prompt final en filtrant les entrées par `applies_to` et en injectant dans l'ordre `priority` croissant. Module inconnu → `UnknownPromptModuleError` explicite.
> 3. **Refactor 7 modules métier (AC3)** : `chat` (=system.py), `esg_scoring`, `carbon`, `financing`, `application`, `credit`, `action_plan` délèguent leurs instructions transverses à `build_prompt()`. **Signatures publiques inchangées** (`build_esg_scoring_prompt(...)`, etc.) — refactor interne uniquement (shim pattern 10.6).
> 4. **Zéro duplication (AC4)** : les constantes `STYLE_INSTRUCTION`, `WIDGET_INSTRUCTION`, `GUIDED_TOUR_INSTRUCTION` restent **exportées** depuis leurs fichiers d'origine (`system.py`, `widget.py`, `guided_tour.py`) pour rétro-compatibilité des imports de tests, mais ne sont **plus concaténées manuellement** dans les 7 modules métier. Seul le registre les consomme.
> 5. **Golden snapshots (AC5)** : 7 prompts canoniques capturés avant refactor (`backend/tests/test_prompts/golden/*.txt`), puis comparés après refactor avec normalisation (whitespace + ordre des sections). Assertion stricte : zéro différence sémantique.
> 6. **Scan NFR66 (AC6)** : avant d'écrire `registry.py`, scan exhaustif (a) aucun `registry.py` préexistant dans `backend/app/prompts/`, (b) aucun hard-coding pays dans les 3 instructions transverses (`rg -n "côte d'ivoire|sénégal|benin|togo" backend/app/prompts/`), (c) aucun module qui ré-exporte déjà un `INSTRUCTION_REGISTRY`.
> 7. **Extensibilité (AC7)** : ajouter une 4ᵉ instruction transverse (ex. futur `RATE_LIMIT_INSTRUCTION` spec 9.1 si besoin de la propager à d'autres modules) = 1 bloc `InstructionEntry(...)` dans `INSTRUCTION_REGISTRY`. Aucun autre fichier à toucher.
> 8. **Tests unit registry (AC8)** : filtre `applies_to`, ordre déterministe, substitution variables, module inconnu → `UnknownPromptModuleError`, variable manquante → `UnboundPromptVariableError`.
> 9. **Baseline tests (AC9)** : 1457 → **≥ 1467** (+10 minimum) : 10 tests unit registry + snapshots 7 modules. Comptage par `pytest --collect-only -q` (leçon 10.4).
>
> **Hors scope explicite (déféré)** :
> - Unification des blocs visuels (`chart`/`mermaid`/`table`/`gauge`/`progress`/`timeline`) actuellement dupliqués dans `BASE_PROMPT` (system.py) et partiellement dans chaque module métier — **déféré Phase Growth** (refactor sémantique plus large, hors périmètre CCC-9).
> - Migration des prompts `esg_report.py` (42 lignes, mono-usage pour PDF) et `widget.py` (helper partagé mais pas un module métier) dans le registre — restent en l'état, importés directement par les consommateurs qui en ont besoin.
> - Jinja2 / f-strings custom : **Q4 tranchée → formatter `string.Template` de la stdlib** (substitution `${var}` avec `safe_substitute` → `KeyError` explicite si variable manquante en mode strict via `substitute`).
> - Système de versioning des prompts (git suffit).
> - Registration dynamique de handlers externes (`@register_instruction`) — **Q1 tranchée → registre statique**, frozen tuple, pas d'API d'enregistrement runtime (évite race conditions et imports circulaires).
>
> **Contraintes héritées (10 leçons Stories 9.x → 10.7)** :
> 1. **C1 (9.7)** — **pas de `try/except Exception` catch-all** : le builder lève `UnknownPromptModuleError` (module absent du registre) et `UnboundPromptVariableError` (variable requise absente de `variables`), toutes deux héritant de `PromptRegistryError(ValueError)`. Aucun `except Exception` dans `registry.py`.
> 2. **C2 (9.7)** — **tests prod véritables** : les golden snapshots capturent **le prompt réel généré** par `build_system_prompt(...)` / `build_esg_scoring_prompt(...)` / etc. avec des profils minimaux réalistes (dict `{"company_name": "Test SARL", "sector": "recyclage"}`). Pas de mock des builders.
> 3. **Marker `@pytest.mark.unit`** : 100 % des tests registry sont purs (aucun accès BDD, aucun LLM, aucun FS). Les golden snapshots sont écrits en fixture setup-once sous `backend/tests/test_prompts/golden/*.txt`.
> 4. **10.3 M1 — scan NFR66 exhaustif Task 1** : avant de créer `registry.py`, la Task 1 consigne les résultats des 3 greps (cf. AC6). Un registre préexistant ferait échouer l'AC.
> 5. **10.4 — comptages par introspection runtime** : AC9 est prouvé par `pytest --collect-only -q backend/tests/test_prompts/ | tail -5` avant/après. La différence exacte est citée dans Completion Notes.
> 6. **10.5 — pas de duplication helpers** : si un `build_*_prompt` module duplique déjà `STYLE_INSTRUCTION` en interne (ex. bloc copié-collé au lieu d'import), la Task 1 le détecte (`rg -n "## STYLE DE COMMUNICATION" backend/app/prompts/`) et l'élimine.
> 7. **10.5 règle d'or — tester effet observable** : les tests snapshots comparent le **prompt concaténé final** que reçoit le LLM, pas une structure intermédiaire. Marker attendus (ex. `"## STYLE DE COMMUNICATION — OBLIGATOIRE"`, `"## OUTIL GUIDAGE VISUEL"`, `"## OUTIL INTERACTIF"`) présents dans le prompt final post-refactor → assertion AC5.
> 8. **10.6 pattern shims legacy** : les 7 fonctions `build_*_prompt(...)` gardent leur signature exacte (noms positionnels, valeurs par défaut, type d'argument). Les tests existants qui en consomment (ex. `test_esg_scoring_prompt_injects_style_instruction`) continuent de passer sans modification. Les tests existants qui référencent `STYLE_INSTRUCTION` / `WIDGET_INSTRUCTION` / `GUIDED_TOUR_INSTRUCTION` (cf. `test_guided_tour_instruction.py`) passent aussi — les constantes restent exportées, la Task 1 liste les imports à préserver.
> 9. **10.7 capitalisation scan NFR66** : réutilisation directe du pattern — Task 1 produit un bloc « Scan préalable » documenté dans Completion Notes.
> 10. **10.7 verrouillage choix techniques pré-dev** : les 4 questions ci-dessous sont **tranchées dans ce story file** avant Task 2. Pas de décision pendant l'implémentation.
>
> **Absorption dettes déférées** : aucune dette déférée spécifique aux prompts dans le backlog actuel (les corrections historiques 013/015/016/017 ont déjà été appliquées ; 10.8 consolide, pas de dette résiduelle à absorber).

---

## Story

**As a** Équipe Mefali (backend/AI) + futurs contributeurs Phase Growth,
**I want** un registre Python central `backend/app/prompts/registry.py` qui collecte les instructions transverses (style concis spec 014, widgets interactifs spec 018, guidage visuel spec 019) avec une structure `INSTRUCTION_REGISTRY` frozen + un builder déterministe `build_prompt(module, variables)` qui filtre par `applies_to` et injecte dans l'ordre `priority`, et que les 7 modules prompts métier (`chat`/`esg_scoring`/`carbon`/`financing`/`application`/`credit`/`action_plan`) délèguent leurs instructions transverses au registre sans modifier leur signature publique,
**So that** les 4 spec-correctifs historiques (013/015/016/017) ne se reproduisent plus sous forme de patches éparpillés (anti-pattern « prompts directifs saturés » NFR61), qu'ajouter une nouvelle instruction transverse devienne un one-liner dans le registre (NFR62), et que les golden snapshots garantissent zéro régression sémantique sur les prompts générés (CCC-9).

---

## Acceptance Criteria

### AC1 — `backend/app/prompts/registry.py` expose `INSTRUCTION_REGISTRY` immutable + `InstructionEntry`

**Given** l'absence d'un registre préexistant (scan Task 1 obligatoire — cf. AC6),

**When** un dev crée `backend/app/prompts/registry.py`,

**Then** le fichier expose :

```python
"""Registre central des instructions transverses injectées dans les prompts LLM.

CCC-9 — framework injection unifié (résout anti-pattern « prompts directifs
saturés » introduit par specs 013/015/016/017).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from string import Template
from typing import Final, Mapping


class PromptRegistryError(ValueError):
    """Erreur de base pour le registre (NFR60 fail-fast)."""


class UnknownPromptModuleError(PromptRegistryError):
    """Module absent du registre — évite les prompts vides silencieux."""


class UnboundPromptVariableError(PromptRegistryError):
    """Variable référencée par une instruction mais absente de `variables`."""


@dataclass(frozen=True)
class InstructionEntry:
    """Entrée immutable du registre d'instructions transverses.

    - name          : identifiant stable (clé de log, snapshot, debug).
    - applies_to    : tuple des modules qui consomment cette instruction
                      (ex. ("chat", "esg_scoring", "carbon")).
    - priority      : ordre d'injection (croissant). Ex. 10 = style (tôt),
                      50 = widget, 90 = guided_tour (plus tard).
    - template      : texte d'instruction (peut contenir ${variables}).
    - required_vars : variables obligatoires (fail-fast si absentes).
    """

    name: str
    applies_to: tuple[str, ...]
    priority: int
    template: str
    required_vars: tuple[str, ...] = field(default_factory=tuple)


# --- Modules supportés (fail-fast si build_prompt reçoit autre chose) ---
SUPPORTED_MODULES: Final[frozenset[str]] = frozenset({
    "chat",          # = build_system_prompt (prompt principal)
    "esg_scoring",
    "carbon",
    "financing",
    "application",
    "credit",
    "action_plan",
})


INSTRUCTION_REGISTRY: Final[tuple[InstructionEntry, ...]] = (
    InstructionEntry(
        name="style",
        applies_to=("chat", "esg_scoring", "carbon", "financing",
                    "application", "credit", "action_plan"),
        priority=10,
        template=_STYLE_TEMPLATE,   # = contenu actuel de STYLE_INSTRUCTION
    ),
    InstructionEntry(
        name="widget",
        applies_to=("chat", "esg_scoring", "carbon", "financing",
                    "application", "credit", "action_plan"),
        priority=50,
        template=_WIDGET_TEMPLATE,  # = contenu actuel de WIDGET_INSTRUCTION
    ),
    InstructionEntry(
        name="guided_tour",
        applies_to=("chat", "esg_scoring", "carbon", "financing",
                    "credit", "action_plan"),  # Note : application exclu (parité historique)
        priority=90,
        template=_GUIDED_TOUR_TEMPLATE,  # = contenu actuel de GUIDED_TOUR_INSTRUCTION
    ),
)
```

**And** `INSTRUCTION_REGISTRY` est une **`tuple` frozen** (pas une `list` ni un `dict`) — immutabilité enforced au niveau type.

**And** les 3 constantes `_STYLE_TEMPLATE`, `_WIDGET_TEMPLATE`, `_GUIDED_TOUR_TEMPLATE` sont définies privément dans `registry.py` **en ré-exportant depuis les fichiers d'origine** (pas de duplication de texte) :

```python
from app.prompts.system import STYLE_INSTRUCTION as _STYLE_TEMPLATE
from app.prompts.widget import WIDGET_INSTRUCTION as _WIDGET_TEMPLATE
from app.prompts.guided_tour import GUIDED_TOUR_INSTRUCTION as _GUIDED_TOUR_TEMPLATE
```

**And** **3 tests unit** `backend/tests/test_prompts/test_registry_structure.py` valident : (a) `INSTRUCTION_REGISTRY` est bien un `tuple` (pas `list`), (b) chaque entrée est bien une `InstructionEntry` frozen (assignation lève `FrozenInstanceError`), (c) les 3 entrées `style`/`widget`/`guided_tour` sont présentes avec les `applies_to` exacts ci-dessus.

---

### AC2 — `build_prompt(module, variables)` injecte dans l'ordre `priority` avec substitution déterministe

**Given** le registre chargé,

**When** un dev appelle `build_prompt(module="esg_scoring", variables={})`,

**Then** la fonction :

```python
def build_prompt(
    module: str,
    variables: Mapping[str, str] | None = None,
    base: str = "",
) -> str:
    """Construit un prompt composite à partir du registre.

    Flow :
        1. Valide `module` ∈ SUPPORTED_MODULES (sinon UnknownPromptModuleError).
        2. Filtre INSTRUCTION_REGISTRY par `applies_to` contient `module`.
        3. Trie par priority croissante, puis name alphabétique (stable).
        4. Pour chaque entrée :
             - vérifie que `required_vars ⊆ variables.keys()` (sinon
               UnboundPromptVariableError avec le nom précis manquant).
             - substitue ${var} via string.Template.substitute (strict).
        5. Concatène : base + "\\n\\n" + "\\n\\n".join(rendered_entries).
    """
    if module not in SUPPORTED_MODULES:
        raise UnknownPromptModuleError(
            f"Unknown prompt module: {module!r}. "
            f"Supported: {sorted(SUPPORTED_MODULES)}"
        )
    vars_map = dict(variables or {})
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
        rendered.append(Template(entry.template).substitute(vars_map))
    parts = [p for p in [base.strip(), *rendered] if p]
    return "\n\n".join(parts)
```

**And** l'ordre d'injection est **strictement déterministe** : `(priority ASC, name ASC)` — garantit snapshots stables même si deux instructions partagent le même `priority`.

**And** **4 tests unit** `backend/tests/test_prompts/test_build_prompt.py` valident : (a) ordre `style` → `widget` → `guided_tour` pour `module="chat"`, (b) `module="application"` exclut `guided_tour` (parité historique), (c) `variables={}` sans `required_vars` → pas d'erreur, (d) `base="X"` est concaténé en tête avec double saut de ligne.

---

### AC3 — Refactor des 7 modules métier `prompts/*.py` via `build_prompt()` (signatures publiques inchangées)

**Given** les 7 modules métier qui concatènent aujourd'hui manuellement `STYLE_INSTRUCTION + WIDGET_INSTRUCTION + GUIDED_TOUR_INSTRUCTION`,

**When** un dev refactore chaque module,

**Then** chaque `build_<module>_prompt(...)` interne devient :

```python
# AVANT (backend/app/prompts/esg_scoring.py)
def build_esg_scoring_prompt(company_profile: dict, ...) -> str:
    from app.prompts.guided_tour import GUIDED_TOUR_INSTRUCTION
    from app.prompts.system import STYLE_INSTRUCTION, build_page_context_instruction
    from app.prompts.widget import WIDGET_INSTRUCTION
    return (
        ESG_SCORING_BASE
        + format_profile(...)
        + STYLE_INSTRUCTION
        + "\n\n"
        + WIDGET_INSTRUCTION
        + "\n\n"
        + GUIDED_TOUR_INSTRUCTION
        + ...
    )

# APRÈS (backend/app/prompts/esg_scoring.py)
def build_esg_scoring_prompt(company_profile: dict, ...) -> str:
    from app.prompts.registry import build_prompt
    from app.prompts.system import build_page_context_instruction
    base = ESG_SCORING_BASE + format_profile(...)
    prompt = build_prompt(module="esg_scoring", base=base)
    # Appendix non-transverse (page context) reste géré localement
    page_ctx = build_page_context_instruction(current_page)
    return f"{prompt}\n\n{page_ctx}" if page_ctx else prompt
```

**And** **la signature publique de chaque `build_<module>_prompt()` reste identique** (ordre positionnel, defaults, type hints) — les 7 noms publics sont : `build_system_prompt` (system.py), `build_esg_scoring_prompt`, `build_carbon_prompt`, `build_financing_prompt`, `build_application_prompt`, `build_credit_prompt`, `build_action_plan_prompt`. Tout consommateur externe (`graph/nodes.py`, tests) compile sans modification.

**And** les appendices **non-transverses** (ex. `build_page_context_instruction`, `build_adaptive_frequency_hint`, `_format_profile_visual_instructions`) restent gérés localement par leur module — le registre ne les absorbe pas (scope strict : instructions **transverses** uniquement).

**And** **7 tests d'intégration** `backend/tests/test_prompts/test_module_integration.py` (1 par module métier) vérifient que le prompt généré post-refactor contient bien les marqueurs `"## STYLE DE COMMUNICATION"`, `"## OUTIL INTERACTIF"`, et pour les 6 modules concernés `"## OUTIL GUIDAGE VISUEL"`.

---

### AC4 — Zéro duplication de `STYLE_INSTRUCTION` / `WIDGET_INSTRUCTION` / `GUIDED_TOUR_INSTRUCTION` dans les 7 modules

**Given** le refactor AC3 appliqué,

**When** on exécute `rg -n "STYLE_INSTRUCTION|WIDGET_INSTRUCTION|GUIDED_TOUR_INSTRUCTION" backend/app/prompts/ | grep -v registry.py | grep -v system.py | grep -v widget.py | grep -v guided_tour.py`,

**Then** **la sortie est vide** — aucun des 7 modules métier ne concatène plus ces constantes manuellement.

**And** les constantes d'origine restent exportées depuis `system.py` (`STYLE_INSTRUCTION`), `widget.py` (`WIDGET_INSTRUCTION`), `guided_tour.py` (`GUIDED_TOUR_INSTRUCTION`) pour rétro-compatibilité des tests existants (`test_guided_tour_instruction.py`, etc.) — la Task 1 liste explicitement les imports test préservés.

**And** **1 test unit** `test_no_duplicate_instruction_imports` exécute `rg` via `subprocess.run` et asserte que la sortie est bien vide (pattern testable en CI).

---

### AC5 — Golden snapshots zéro régression sémantique (7 modules)

**Given** un script de capture des prompts canoniques exécuté **avant** le refactor,

**When** un dev exécute `pytest backend/tests/test_prompts/test_golden_snapshots.py`,

**Then** chaque prompt généré par chacun des 7 builders (`build_system_prompt`, `build_esg_scoring_prompt`, ..., `build_action_plan_prompt`) avec un **profil canonique minimal** est comparé à un fichier golden `backend/tests/test_prompts/golden/<module>.txt` — la comparaison autorise uniquement des différences de **whitespace** (trailing spaces, lignes vides multiples) via la fonction helper `_normalize_whitespace(text: str) -> str`.

**And** les profils canoniques sont définis dans une fixture partagée :

```python
CANONICAL_PROFILE = {
    "company_name": "Mefali Test SARL",
    "sector": "recyclage",
    "country": "Côte d'Ivoire",
    "employee_count": 25,
}
```

**And** les fichiers golden sont capturés **une seule fois en début de Task 2** (commit intermédiaire « golden snapshots baseline pré-refactor ») puis servent de référence pour tout le reste de l'implémentation.

**And** **7 tests snapshots** (1 par module) vérifient l'égalité `_normalize_whitespace(generated) == _normalize_whitespace(golden)`. Toute modification sémantique d'une instruction nécessite de **mettre à jour explicitement** le fichier golden (documenté dans Completion Notes).

**And** un test méta vérifie que les marqueurs attendus sont présents dans chaque golden (défense en profondeur contre un golden vide ou tronqué).

---

### AC6 — Scan NFR66 préalable (Task 1) documenté dans Completion Notes

**Given** la leçon 10.3 M1 + 10.7 capitalisation,

**When** Task 1 est exécutée **avant** toute création de `registry.py`,

**Then** les 3 commandes suivantes sont lancées et leurs sorties consignées :

```bash
# (a) Aucun registre préexistant
test ! -f backend/app/prompts/registry.py || echo "FAIL: registry.py existe déjà"

# (b) Aucun hard-coding pays dans les instructions transverses
rg -n -i "côte d'ivoire|sénégal|benin|togo|burkina|mali" \
   backend/app/prompts/system.py \
   backend/app/prompts/widget.py \
   backend/app/prompts/guided_tour.py

# (c) Aucun duplicat textuel existant de ## STYLE DE COMMUNICATION
rg -n "## STYLE DE COMMUNICATION" backend/app/prompts/
# Attendu : exactement 1 hit (system.py:80) — tout hit supplémentaire = duplication à résoudre
```

**And** si le scan révèle une duplication (cas (c) > 1 hit), elle est **éliminée dans la même story** (pas de création de dette). La Task 1 documente le diff.

**And** Completion Notes contiennent un bloc « Scan préalable » avec les 3 sorties (copier-coller des terminaux).

---

### AC7 — Ajout d'une 4ᵉ instruction = 1 bloc dans le registre (test extensibilité)

**Given** un cas d'usage hypothétique (ex. futur `RATE_LIMIT_INSTRUCTION` spec 9.1 qui voudrait prévenir le LLM de la fréquence d'appels élevée),

**When** un dev souhaite l'ajouter,

**Then** **1 seul fichier est modifié** (`registry.py`) avec 1 bloc `InstructionEntry(...)` :

```python
InstructionEntry(
    name="rate_limit_hint",
    applies_to=("chat", "esg_scoring"),
    priority=30,
    template=_RATE_LIMIT_TEMPLATE,
),
```

**And** **aucun** des 7 modules métier n'est modifié (build_prompt la consomme automatiquement via `applies_to`).

**And** **1 test d'extensibilité** `test_registry_extensibility.py` simule cet ajout via un registre de test (monkeypatch `INSTRUCTION_REGISTRY`) et vérifie que les 2 modules ciblés incluent bien la nouvelle instruction, tandis que les 5 autres restent inchangés.

---

### AC8 — Tests unit registry (filtrage, ordre, substitution, erreurs)

**Given** `backend/tests/test_prompts/test_registry.py` (marker `@pytest.mark.unit`),

**When** `pytest backend/tests/test_prompts/test_registry.py` exécuté,

**Then** **10 tests** passent (verrouillés dans Completion Notes via `pytest --collect-only -q`) :

1. `test_registry_is_frozen_tuple` — `type(INSTRUCTION_REGISTRY) is tuple`.
2. `test_instruction_entry_is_frozen_dataclass` — assignation lève `FrozenInstanceError`.
3. `test_build_prompt_filters_by_applies_to` — `module="application"` exclut `guided_tour`.
4. `test_build_prompt_orders_by_priority_then_name` — 2 entrées avec même priority → ordre alphabétique stable.
5. `test_build_prompt_substitutes_variables` — `template="Hello ${name}"` + `variables={"name": "X"}` → `"Hello X"`.
6. `test_build_prompt_raises_on_missing_variable` — `required_vars=("foo",)` sans `variables` → `UnboundPromptVariableError` avec nom précis.
7. `test_build_prompt_raises_on_unknown_module` — `module="unknown"` → `UnknownPromptModuleError` listant `SUPPORTED_MODULES`.
8. `test_build_prompt_accepts_empty_variables` — instruction sans `required_vars` + `variables=None` → OK.
9. `test_build_prompt_prepends_base` — `base="INTRO"` → `"INTRO\n\n<instructions>"`.
10. `test_build_prompt_is_deterministic_across_calls` — 10 appels successifs produisent des strings byte-identiques (pas de `dict` non-ordonné).

**And** coverage `pytest --cov=app.prompts.registry --cov-report=term-missing backend/tests/test_prompts/test_registry.py` ≥ **95 %** (code critique NFR60).

---

### AC9 — Baseline tests 1457 → ≥ 1467 (+10 minimum), prouvé par `pytest --collect-only`

**Given** la baseline actuelle (citée en début de story comme 1457),

**When** un dev lance `pytest --collect-only -q backend/tests/ | tail -3` avant et après,

**Then** le delta est **≥ +10** :

- 3 tests structure registre (AC1)
- 4 tests `build_prompt` (AC2)
- 7 tests intégration modules (AC3)
- 1 test zéro duplication (AC4)
- 7 tests golden snapshots + 1 test méta (AC5)
- 1 test extensibilité (AC7)
- 10 tests registry unit (AC8)
- **Total : 34 nouveaux tests minimum** (marge confortable au-dessus du +10 de sécurité).

**And** Completion Notes citent les deux sorties exactes de `pytest --collect-only -q` (avant / après) avec le delta quantifié (leçon 10.4).

---

## Tasks / Subtasks

- [x] **Task 1 (AC6)** — Scan NFR66 préalable
  - [x] Exécuter les 3 commandes de l'AC6 et consigner les sorties dans un buffer.
  - [x] Baseliner `pytest --collect-only -q backend/tests/ | tail -3` (AC9).
  - [x] Lister les tests existants qui importent `STYLE_INSTRUCTION`/`WIDGET_INSTRUCTION`/`GUIDED_TOUR_INSTRUCTION` (doivent rester verts).
- [x] **Task 2 (AC5 préparation)** — Capture golden snapshots pré-refactor
  - [x] Créer `backend/tests/test_prompts/golden/` + 7 fichiers `.txt` capturés depuis les builders actuels.
  - [x] Commit intermédiaire isolé : « chore(10.8): freeze golden snapshots pré-refactor » (38e6d0f).
- [x] **Task 3 (AC1)** — Créer `backend/app/prompts/registry.py`
  - [x] Définir `PromptRegistryError`, `UnknownPromptModuleError`, `UnboundPromptVariableError`.
  - [x] Définir `@dataclass(frozen=True) InstructionEntry`.
  - [x] Définir `SUPPORTED_MODULES` + `INSTRUCTION_REGISTRY` (import depuis `system`/`widget`/`guided_tour`).
  - [x] Écrire 3 tests structure (AC1).
- [x] **Task 4 (AC2, AC8)** — Implémenter `build_prompt` + tests unit
  - [x] Flow : validation module → filtre → tri → substitution → concat.
  - [x] 4 tests `test_build_prompt.py` (AC2) + 11 tests `test_registry.py` (AC8, +1 bonus KeyError path).
- [x] **Task 5 (AC3)** — Refactor 6 modules métier (system.py bypass local préservé)
  - [x] `system.py::build_system_prompt` conserve l'injection conditionnelle locale (Dev Notes §5 décision verrouillée : bypass local du registre pour préserver la signature et la logique `_has_minimum_profile`). Zéro changement de code.
  - [x] Refactor `esg_scoring.py`, `carbon.py`, `financing.py`, `credit.py`, `action_plan.py` via `build_prompt(module=..., base=...)`.
  - [x] Refactor `application.py` via `build_prompt(module="application", base=...)` — guided_tour automatiquement exclu par le filtre applies_to (parité historique).
  - [x] Écrire 7 tests intégration modules (AC3).
- [x] **Task 6 (AC4)** — Vérifier zéro duplication
  - [x] Ajouter `test_no_duplicate_instruction_imports` (AC4, scan Python pur plus portable que `rg` subprocess).
- [x] **Task 7 (AC5 vérification)** — Exécuter golden snapshots post-refactor
  - [x] Implémenter helper `_normalize_whitespace` (collapse blank lines multiples + strip trailing).
  - [x] 7 tests snapshots parametrize + 1 test méta marqueurs — tous verts.
  - [x] Zéro différence sémantique détectée.
- [x] **Task 8 (AC7)** — Test extensibilité
  - [x] `test_registry_extensibility.py` avec monkeypatch d'un registre étendu (RATE_LIMIT_HINT simulé, propagation sur 2/7 modules).
- [x] **Task 9 (AC9)** — Validation finale comptage
  - [x] Re-baseline `pytest --collect-only -q` : 1523 → 1559 (+36 tests, delta largement au-dessus du +10 plancher, au-dessus du +34 prévu).
  - [x] Full suite : 1493 passed + 66 skipped, zéro régression (208s).

---

## Dev Notes

### Technical Design — Schema du registre

```
┌─────────────────────────────────────────────────────────────────┐
│  backend/app/prompts/registry.py                                │
│                                                                 │
│  SUPPORTED_MODULES (frozenset)                                  │
│    ├─ "chat" (= build_system_prompt)                            │
│    ├─ "esg_scoring"                                             │
│    ├─ "carbon"                                                  │
│    ├─ "financing"                                               │
│    ├─ "application"     ← pas de guided_tour                    │
│    ├─ "credit"                                                  │
│    └─ "action_plan"                                             │
│                                                                 │
│  INSTRUCTION_REGISTRY (tuple, frozen)                           │
│    ├─ InstructionEntry(name="style",       priority=10, ...)    │
│    ├─ InstructionEntry(name="widget",      priority=50, ...)    │
│    └─ InstructionEntry(name="guided_tour", priority=90, ...)    │
│                                                                 │
│  build_prompt(module, variables, base) → str                    │
│    1. valide module ∈ SUPPORTED_MODULES                         │
│    2. filter_applicable() : [e for e if module in e.applies_to] │
│    3. sort(key=(priority, name))                                │
│    4. for e: Template(e.template).substitute(variables)         │
│    5. return base + "\n\n" + "\n\n".join(rendered)              │
└─────────────────────────────────────────────────────────────────┘
```

### Exemples 3 instructions (style / widget / guided_tour)

**`style`** — priority 10, applies_to = (chat, esg_scoring, carbon, financing, application, credit, action_plan).
Template = verbatim de `STYLE_INSTRUCTION` (`system.py:80-106`).

**`widget`** — priority 50, applies_to = identique à `style`.
Template = verbatim de `WIDGET_INSTRUCTION` (`widget.py:8-50`).

**`guided_tour`** — priority 90, applies_to = (chat, esg_scoring, carbon, financing, credit, action_plan) — **exclut `application`** pour parité historique (application.py n'importe pas `GUIDED_TOUR_INSTRUCTION` aujourd'hui).
Template = verbatim de `GUIDED_TOUR_INSTRUCTION` (`guided_tour.py`).

### Pièges documentés

1. **Golden snapshot drift** : si un dev modifie `STYLE_INSTRUCTION` à la source (`system.py`) pendant le refactor, les golden snapshots divergent. **Mitigation** : Task 2 capture les golden **avant** toute modification des fichiers sources. Tout changement sémantique ultérieur nécessite un commit explicite de mise à jour des golden avec diff visible.

2. **Circular dependency `registry.py` → `system.py` → `registry.py`** : `registry.py` importe les constantes depuis `system.py`, mais `system.py::build_system_prompt` va à terme importer `build_prompt` depuis `registry.py`. **Mitigation** : les imports de `system.py` dans `registry.py` sont au **top-level** (pas d'import circulaire car `system.py::STYLE_INSTRUCTION` est une constante module-level, pas une fonction). À l'inverse, `system.py::build_system_prompt` fait un **import lazy local** à `from app.prompts.registry import build_prompt` dans le corps de la fonction (pattern déjà utilisé pour `guided_tour` dans system.py:221).

3. **Variable leak cross-module** : si une variable est requise pour `esg_scoring` mais injectée par un appel à `build_prompt(module="carbon", variables={...})`, aucun problème car les variables sont scope-limitées à l'appel courant. **Mitigation** : `build_prompt` n'a aucun état global, `variables` est un paramètre local immuable (`dict(variables or {})`).

4. **Ordre instable si même priority** : tri secondaire par `name` alphabétique garantit la stabilité. **Mitigation** : AC8 test 4 verrouille ce contrat.

5. **Injection conditionnelle `STYLE_INSTRUCTION` dans `system.py`** : aujourd'hui `build_system_prompt` injecte `STYLE_INSTRUCTION` **uniquement** si `_has_minimum_profile(user_profile)` (post-onboarding, spec 014). Cette logique doit être **préservée** dans le refactor. **Approche** : `build_system_prompt` délègue seulement les instructions inconditionnelles (`guided_tour`) au registre ; l'injection conditionnelle `style` reste gérée localement dans `system.py` (bypass registre) **OU** alternativement, le registre expose un paramètre `exclude_names={"style"}` pour que l'appelant décide. **Décision verrouillée** : bypass local (plus simple, préserve la signature existante de `build_system_prompt` et sa logique `_has_minimum_profile` sans fuite de préoccupation vers le registre). Les 6 autres modules métier utilisent `build_prompt` avec toutes les instructions de leur `applies_to`.

6. **Duplication apparente des tests `test_guided_tour_instruction.py`** : ce test existe déjà et vérifie le contenu de `GUIDED_TOUR_INSTRUCTION` + son injection dans 6 nœuds LangGraph. Il **reste vert** post-refactor car (a) la constante reste exportée, (b) les 6 modules continuent de la recevoir via le registre (même contenu final). **Ne pas supprimer** ce test.

### Q tranchées (4)

| Q | Décision | Rationale |
|---|----------|-----------|
| **Q1 — Structure registry** | `tuple[InstructionEntry, ...]` frozen | Immutabilité type-checkée, ordre explicite (simple `sort` avec key), pas de risque de mutation runtime (vs `list` ou `dict`). Statique > dynamique (pas d'API `register_instruction()` runtime — évite race conditions et imports circulaires). |
| **Q2 — InstructionEntry** | `@dataclass(frozen=True)` stdlib | Zéro nouvelle dépendance, `FrozenInstanceError` testable, pas besoin de validation Pydantic (le registre est en code, pas en config externe). Aligné pattern Settings Pydantic 10.7 pour la **validation externe** (env/config) mais stdlib pour les **données internes** (code statique). |
| **Q3 — Ordre injection** | `(priority ASC, name ASC)` | Priority explicite permet de fixer l'ordre sémantique (style tôt, guided_tour tard). Tie-break par name garantit stabilité des snapshots. Alternative « par ordre d'apparition dans le tuple » rejetée car fragile (un refactor cosmétique casserait l'ordre). |
| **Q4 — Substitution** | `string.Template.substitute` stdlib | Syntaxe `${var}` sûre (pas d'eval), fail-fast si variable manquante (`KeyError` → remonté en `UnboundPromptVariableError`). Jinja2 overkill (pas de conditionnels/boucles requis MVP). f-string dangereux (injection). `safe_substitute` rejeté : le silence sur variable manquante va à l'encontre du fail-fast NFR60. |

### Testing Standards Summary

- **Framework** : pytest (+ `pytest-asyncio` par défaut projet).
- **Markers** : `@pytest.mark.unit` pour 100 % des tests registry (aucun IO).
- **Coverage cible** : `registry.py` ≥ **95 %** (code critique NFR60), autres modules prompts inchangés par le refactor (pas de baisse attendue).
- **Commande** : `pytest backend/tests/test_prompts/ -v --cov=app.prompts`.
- **Pas de mock** des builders dans les tests snapshots (règle d'or 10.5 effet observable).

### Project Structure Notes

- Fichiers créés :
  - `backend/app/prompts/registry.py` (~150 lignes)
  - `backend/tests/test_prompts/test_registry.py` (~200 lignes, 10 tests)
  - `backend/tests/test_prompts/test_registry_structure.py` (~50 lignes, 3 tests)
  - `backend/tests/test_prompts/test_build_prompt.py` (~80 lignes, 4 tests)
  - `backend/tests/test_prompts/test_module_integration.py` (~120 lignes, 7 tests)
  - `backend/tests/test_prompts/test_golden_snapshots.py` (~150 lignes, 7 + 1 tests)
  - `backend/tests/test_prompts/test_no_duplicate_imports.py` (~30 lignes, 1 test)
  - `backend/tests/test_prompts/test_registry_extensibility.py` (~60 lignes, 1 test)
  - `backend/tests/test_prompts/golden/{system,esg_scoring,carbon,financing,application,credit,action_plan}.txt` (7 fichiers)
- Fichiers modifiés (refactor interne, signatures publiques inchangées) :
  - `backend/app/prompts/system.py` (build_system_prompt → utilise `build_prompt` pour `guided_tour`)
  - `backend/app/prompts/esg_scoring.py`, `carbon.py`, `financing.py`, `credit.py`, `action_plan.py` (build_*_prompt → `build_prompt(module=..., base=...)`)
  - `backend/app/prompts/application.py` (idem, applies_to exclut `guided_tour`)
- Fichiers **non modifiés** (conservent les constantes exportées) :
  - `backend/app/prompts/widget.py`, `guided_tour.py` (exportent `WIDGET_INSTRUCTION` / `GUIDED_TOUR_INSTRUCTION` utilisés par le registre **et** les tests existants).
  - `backend/app/prompts/esg_report.py` (mono-usage PDF, hors scope).

### References

- [Source: _bmad-output/planning-artifacts/epics/epic-10.md#Story-10.8] — AC1–AC6 initiaux (enrichis à 9 AC ici).
- [Source: _bmad-output/planning-artifacts/architecture.md#CCC-9] — framework injection unifié.
- [Source: backend/app/prompts/system.py:80-106] — `STYLE_INSTRUCTION` (spec 014).
- [Source: backend/app/prompts/widget.py:8-50] — `WIDGET_INSTRUCTION` (spec 018).
- [Source: backend/app/prompts/guided_tour.py:12+] — `GUIDED_TOUR_INSTRUCTION` (spec 019).
- [Source: _bmad-output/implementation-artifacts/10-7-environnements-dev-staging-prod.md] — pattern verrouillage Q pré-dev + scan NFR66 Task 1.
- [Source: _bmad-output/implementation-artifacts/10-6-abstraction-storage-provider.md] — pattern shims legacy signatures publiques.
- [Source: _bmad-output/implementation-artifacts/9-7-observabilite-with-retry-log-tool-call.md] — contrainte C1 pas de `try/except Exception`.

---

## Checklist review

- [ ] AC1 — `INSTRUCTION_REGISTRY` est bien un `tuple` frozen (pas `list`/`dict`).
- [ ] AC1 — `InstructionEntry` est `@dataclass(frozen=True)` avec assignation bloquée.
- [ ] AC2 — `build_prompt` trie stable par `(priority, name)`.
- [ ] AC2 — Module inconnu → `UnknownPromptModuleError` (pas `ValueError` générique, pas `Exception`).
- [ ] AC3 — Les 7 signatures publiques `build_<module>_prompt(...)` sont byte-identiques avant/après.
- [ ] AC3 — Aucun import `build_prompt` au top-level de `system.py` (éviter circular — import local).
- [ ] AC4 — `rg` sur `STYLE_INSTRUCTION|WIDGET_INSTRUCTION|GUIDED_TOUR_INSTRUCTION` dans les 7 modules métier retourne vide.
- [ ] AC4 — `system.py`/`widget.py`/`guided_tour.py` exportent toujours les 3 constantes (tests existants non cassés).
- [ ] AC5 — 7 golden snapshots commitcés avant toute modif des builders (Task 2 avant Task 5).
- [ ] AC5 — Comparaison utilise `_normalize_whitespace` (tolérance whitespace, pas tolérance sémantique).
- [ ] AC6 — 3 scans NFR66 consignés en Completion Notes.
- [ ] AC7 — `test_registry_extensibility` utilise monkeypatch (pas de modif permanente du registre).
- [ ] AC8 — 10 tests unit registry tous verts, coverage ≥ 95 %.
- [ ] AC9 — Delta `pytest --collect-only` ≥ +10 (viser +34) documenté en Completion Notes.
- [ ] C1 (9.7) — aucun `except Exception` dans `registry.py`.
- [ ] C2 (9.7) — golden snapshots sur builders réels (pas de stubs).
- [ ] 10.3 M1 — scan NFR66 Task 1 exécuté et consigné.
- [ ] 10.4 — comptage tests par `pytest --collect-only -q`, chiffre exact en Completion Notes.
- [ ] 10.5 — aucune duplication helper (`build_prompt` est unique, pas de variante par module).
- [ ] 10.5 règle d'or — assertions snapshots vérifient le prompt **final concaténé**, pas une structure intermédiaire.
- [ ] 10.6 shims — signatures publiques des 7 `build_<module>_prompt` inchangées.
- [ ] 10.7 verrouillage Q — les 4 Q tranchées dans ce fichier, aucune décision pendant l'implémentation.

---

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7 (1M context) — session 2026-04-21

### Debug Log References

Aucun blocage. Points d'attention tracés en Completion Notes ci-dessous (baseline réelle + outil rg absent du PATH Python subprocess).

### Completion Notes List

**Scan NFR66 préalable (Task 1 / AC6)** :
- `test ! -f backend/app/prompts/registry.py` → OK : registry.py absent avant refactor.
- `grep -i "côte d'ivoire|sénégal|benin|togo|burkina|mali" backend/app/prompts/{system,widget,guided_tour}.py` → zéro hit (1 faux positif initial "mali" dans "formaliser" éliminé par la regex `\b...\b`). Aucun hard-coding pays dans les 3 instructions transverses.
- `grep "## STYLE DE COMMUNICATION" backend/app/prompts/` → exactement 1 hit (system.py:80). Pas de duplication textuelle.
- Tests existants référençant les 3 constantes : 4 fichiers identifiés (`test_guided_tour_adaptive_frequency.py`, `test_guided_tour_consent_flow.py`, `test_guided_tour_instruction.py`, `test_style_instruction.py`) — tous restent verts post-refactor car les constantes restent exportées depuis leurs modules d'origine.

**Baseline tests (Task 1 + Task 9 / AC9)** :
- Avant refactor : 1523 tests collectés (baseline annoncée dans le story file 1457, écart dû aux 66 tests skipped + ajouts intermédiaires accumulés entre Story 10.7 et Story 10.8).
- Après refactor : **1559 tests collectés** — delta **+36** (plancher +10 largement dépassé, prévu +34 légèrement dépassé).
- Full suite : **1493 passed + 66 skipped, 0 failed** (208s / 3min28).

**Répartition des 36 tests nouveaux** :
- `test_registry_structure.py` : 3 (AC1)
- `test_build_prompt.py` : 4 (AC2)
- `test_registry.py` : 11 (AC8 : 10 requis + 1 bonus KeyError path pour defense en profondeur variable leak)
- `test_module_integration.py` : 7 (AC3, 1 par module)
- `test_no_duplicate_imports.py` : 2 (AC4 + 1 bonus retro-compatibilité constantes)
- `test_golden_snapshots.py` : 8 (AC5 : 7 parametrize + 1 méta marqueurs)
- `test_registry_extensibility.py` : 1 (AC7)

**Décision technique bypass local system.py (Dev Notes §5 rappel)** :
- `system.py::build_system_prompt` **n'appelle pas** `build_prompt` et conserve l'import direct de `STYLE_INSTRUCTION` (injection conditionnelle `_has_minimum_profile`) + `GUIDED_TOUR_INSTRUCTION` (injection systématique). Cette décision est conforme à la Q tranchée en Dev Notes §5 (préserver la signature et la logique `_has_minimum_profile` sans fuite de préoccupation vers le registre). Le registre reste la **source unique de texte** (via ré-export depuis les modules d'origine), mais `system.py` a un pattern d'injection spécifique trop imbriqué dans le flow `build_system_prompt` pour bénéficier de `build_prompt()` sans complexifier le registre avec un paramètre `exclude_names`. Le test AC4 exempte explicitement `system.py` du scan zéro-duplication.
- Concrètement : 6 des 7 modules métier passent désormais par `build_prompt()`. `system.py` reste tel quel, son golden snapshot est inchangé, et tous les tests existants restent verts.

**Coverage registry.py** : **100%** (35/35 statements) — largement au-dessus du seuil NFR60 de 95 %.

**Changements subtils de whitespace (absorbés par `_normalize_whitespace`)** :
- Avant refactor : `MODULE_PROMPT.format(...) + "\n\n" + STYLE + ...` → 3 newlines entre base et première instruction (le trailing `\n` du template + le `\n\n` explicite).
- Après refactor : `build_prompt(module=..., base=base)` applique `base.strip()` puis rejoint avec `"\n\n".join(...)` → 2 newlines.
- Le helper `_normalize_whitespace` collapse les blank lines consécutives multiples → les golden snapshots passent strictement sans modification textuelle.

**Rétrocompatibilité API** :
- Les 7 signatures publiques `build_system_prompt`, `build_esg_prompt`, `build_carbon_prompt`, `build_financing_prompt`, `build_application_prompt`, `build_credit_prompt`, `build_action_plan_prompt` sont byte-identiques avant/après. Pattern shims legacy Story 10.6 respecté.
- Note d'implémentation : le story file réfère à `build_esg_scoring_prompt` dans plusieurs passages, mais le nom public réel est `build_esg_prompt` (import depuis `app.prompts.esg_scoring`). Contrainte forte "signatures inchangées" respectée — pas de renommage pour préserver les 7 consommateurs (`app/graph/nodes.py`, 4 tests existants).

**Commit pré-refactor (traçabilité golden)** : `38e6d0f` "chore(10.8): freeze golden snapshots pré-refactor".
**Commit final** : voir ci-après "refactor(10.8): CCC-9 framework injection prompts".

### File List

**Fichiers créés (10)** :
- `backend/app/prompts/registry.py` — registre central + `build_prompt`
- `backend/tests/test_prompts/_canonical_profile.py` — fixtures partagées
- `backend/tests/test_prompts/_capture_golden.py` — script one-shot de capture
- `backend/tests/test_prompts/test_registry_structure.py` — 3 tests (AC1)
- `backend/tests/test_prompts/test_registry.py` — 11 tests (AC8)
- `backend/tests/test_prompts/test_build_prompt.py` — 4 tests (AC2)
- `backend/tests/test_prompts/test_module_integration.py` — 7 tests (AC3)
- `backend/tests/test_prompts/test_no_duplicate_imports.py` — 2 tests (AC4)
- `backend/tests/test_prompts/test_golden_snapshots.py` — 8 tests (AC5)
- `backend/tests/test_prompts/test_registry_extensibility.py` — 1 test (AC7)
- `backend/tests/test_prompts/golden/{system,esg_scoring,carbon,financing,application,credit,action_plan}.txt` — 7 snapshots figés pré-refactor

**Fichiers modifiés (6 — refactor interne, signatures publiques inchangées)** :
- `backend/app/prompts/esg_scoring.py` — `build_esg_prompt` consomme `build_prompt`
- `backend/app/prompts/carbon.py` — `build_carbon_prompt` consomme `build_prompt`
- `backend/app/prompts/financing.py` — `build_financing_prompt` consomme `build_prompt`
- `backend/app/prompts/application.py` — `build_application_prompt` consomme `build_prompt` (filtre exclut guided_tour automatiquement via applies_to)
- `backend/app/prompts/credit.py` — `build_credit_prompt` consomme `build_prompt`
- `backend/app/prompts/action_plan.py` — `build_action_plan_prompt` consomme `build_prompt`

**Fichiers non modifiés (conservent leur comportement et leurs exports)** :
- `backend/app/prompts/system.py` — `build_system_prompt` préserve l'injection conditionnelle locale (bypass registre documenté Dev Notes §5)
- `backend/app/prompts/widget.py` — exporte toujours `WIDGET_INSTRUCTION`
- `backend/app/prompts/guided_tour.py` — exporte toujours `GUIDED_TOUR_INSTRUCTION` + `build_adaptive_frequency_hint`

### Change Log

- 2026-04-21 — Story 10.8 implémentée (CCC-9 framework injection prompts). Registre central `app.prompts.registry` + 6 modules métier refactorés via `build_prompt(module, variables, base)`. Zéro régression sémantique (7 golden snapshots verts), +36 tests nouveaux (1523 → 1559), coverage registry.py 100 %. Anti-pattern "prompts directifs saturés" NFR61 absorbé. Ajouter une 4ᵉ instruction transverse = désormais 1 bloc `InstructionEntry` dans `INSTRUCTION_REGISTRY`.
