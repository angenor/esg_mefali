# Implementation Plan: Style de communication concis

**Branch**: `014-concise-chat-style` | **Date**: 2026-04-02 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/014-concise-chat-style/spec.md`

## Summary

Ajouter une instruction de style concis (`STYLE_INSTRUCTION`) dans le prompt systeme de tous les noeuds LangGraph. L'instruction interdit la redondance texte/visuels, les formules de politesse, les recapitulatifs, et impose max 2-3 phrases par bloc visuel. Exception pour l'onboarding (utilisateur sans profil).

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: FastAPI, LangGraph, LangChain, langchain-openai
**Storage**: N/A (pas de changement BDD)
**Testing**: pytest
**Target Platform**: Linux server (backend API)
**Project Type**: web-service (monolithe modulaire)
**Performance Goals**: N/A (changement de prompt uniquement, aucun impact perf)
**Constraints**: L'instruction doit rester sous ~800 tokens pour ne pas surcharger le contexte LLM
**Scale/Scope**: 7 fichiers de prompt a modifier, 1 constante a definir

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principe | Statut | Note |
|----------|--------|------|
| I. Francophone-First | PASS | L'instruction est en francais, cible les PME africaines |
| II. Architecture Modulaire | PASS | Constante centralisee, importee par chaque module |
| III. Conversation-Driven UX | PASS | Ameliore l'UX conversationnelle (reponses plus utiles) |
| IV. Test-First | PASS | Tests a ecrire pour verifier injection/condition onboarding |
| V. Securite & Donnees | PASS | Pas de donnees sensibles impliquees |
| VI. Inclusivite | PASS | Exception onboarding preserve le mode guide |
| VII. Simplicite & YAGNI | PASS | Ajout d'une constante + imports, pas d'abstraction |

**Post-Phase 1 re-check** : Identique — aucune complexite ajoutee au-dela d'une constante et de son injection.

## Project Structure

### Documentation (this feature)

```text
specs/014-concise-chat-style/
├── plan.md              # Ce fichier
├── research.md          # Strategie d'injection
├── data-model.md        # Points d'injection
├── quickstart.md        # Verification rapide
└── tasks.md             # (genere par /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   └── prompts/
│       ├── system.py          # STYLE_INSTRUCTION + build_system_prompt() modifie
│       ├── esg_scoring.py     # build_esg_prompt() + import STYLE_INSTRUCTION
│       ├── carbon.py          # build_carbon_prompt() + import
│       ├── financing.py       # build_financing_prompt() + import
│       ├── credit.py          # build_credit_prompt() + import
│       ├── application.py     # build_application_prompt() + import
│       └── action_plan.py     # build_action_plan_prompt() + import
└── tests/
    └── test_prompts/
        └── test_style_instruction.py  # Tests injection + onboarding
```

**Structure Decision**: Modification de fichiers existants uniquement. Un seul fichier de test ajoute.

## Design

### Constante STYLE_INSTRUCTION

Definie dans `backend/app/prompts/system.py` apres `DOCUMENT_VISUAL_INSTRUCTIONS`. Contient :

1. Regles de concision (FR-001 a FR-006, FR-009)
2. Exemples BON/MAUVAIS (FR-008)
3. Regle "chaque mot = info nouvelle ou action concrete" (FR-009)

### Injection dans build_system_prompt() (chat_node)

```python
def build_system_prompt(user_profile=None, ...):
    sections = [BASE_PROMPT]

    # ... sections existantes (profil, memoire, documents, profilage) ...

    # Injecter STYLE_INSTRUCTION uniquement post-onboarding
    if user_profile and _has_minimum_profile(user_profile):
        sections.append(STYLE_INSTRUCTION)

    return "\n\n".join(sections)

def _has_minimum_profile(profile: dict) -> bool:
    """Verifie que le profil a au moins 2 champs renseignes (post-onboarding)."""
    filled = sum(1 for v in profile.values() if v is not None and v != "" and v is not False)
    return filled >= 2
```

### Injection dans les prompts specialises

Chaque `build_*_prompt()` concatene `STYLE_INSTRUCTION` en fin de prompt :

```python
from app.prompts.system import STYLE_INSTRUCTION

def build_esg_prompt(company_context=..., document_context=...) -> str:
    return ESG_SCORING_PROMPT.format(...) + "\n\n" + STYLE_INSTRUCTION
```

Pattern identique pour les 6 modules.

### Tests

Fichier `backend/tests/test_prompts/test_style_instruction.py` :

- `test_style_instruction_present_with_profile` — verifie injection quand profil renseigne
- `test_style_instruction_absent_without_profile` — verifie absence en onboarding
- `test_style_instruction_absent_minimal_profile` — verifie absence avec profil <2 champs
- `test_style_instruction_in_esg_prompt` — verifie presence dans build_esg_prompt()
- `test_style_instruction_in_carbon_prompt` — idem carbone
- `test_style_instruction_in_all_specialized_prompts` — verifie les 6 modules
- `test_style_instruction_contains_examples` — verifie presence exemples BON/MAUVAIS
- `test_style_instruction_contains_rules` — verifie presence des regles cles

## Complexity Tracking

Aucune violation de constitution a justifier. Complexite minimale : 1 constante + 7 modifications de fonctions existantes.
