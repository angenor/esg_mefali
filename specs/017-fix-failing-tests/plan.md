# Implementation Plan: Correction des 34 tests en échec

**Branch**: `017-fix-failing-tests` | **Date**: 2026-04-02 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/017-fix-failing-tests/spec.md`

## Summary

Corriger 34 tests pré-existants en échec répartis en 5 causes racines distinctes (auth 401, state incomplet, Form/JSON mismatch, mock type incorrect, WeasyPrint lib système absente). Approche : fixtures partagés dans conftest.py + corrections ciblées par fichier. Zéro modification du code de production.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: FastAPI, pytest, pytest-asyncio, LangChain, LangGraph
**Storage**: PostgreSQL + pgvector (SQLite in-memory pour tests)
**Testing**: pytest + pytest-asyncio + AsyncClient
**Target Platform**: Linux server / macOS dev
**Project Type**: Web service (backend API)
**Performance Goals**: N/A (correction tests uniquement)
**Constraints**: Zéro régression sur les 867 tests existants
**Scale/Scope**: 9 fichiers de test, 34 corrections

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principe | Statut | Justification |
|----------|--------|---------------|
| I. Francophone-First | PASS | Commentaires en français, aucun changement UI |
| II. Architecture Modulaire | PASS | Aucun changement d'architecture, corrections tests seulement |
| III. Conversation-Driven | N/A | Pas de changement UX |
| IV. Test-First | PASS | Feature entièrement dédiée à la correction de tests |
| V. Sécurité | PASS | Aucun secret exposé, auth correctement mockée |
| VI. Inclusivité | N/A | Pas de changement UI |
| VII. Simplicité & YAGNI | PASS | Fixtures partagés = réduction de duplication, pas d'abstraction excessive |

**Post-Phase 1 re-check**: PASS — Aucun artefact de design ne viole la constitution.

## Project Structure

### Documentation (this feature)

```text
specs/017-fix-failing-tests/
├── plan.md              # Ce fichier
├── research.md          # Recherche Phase 0
├── data-model.md        # Modèle de données (lecture seule)
├── quickstart.md        # Guide démarrage rapide
├── contracts/           # Contrats fixtures
│   └── test-fixtures-contract.md
└── tasks.md             # Phase 2 (à générer via /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── api/deps.py              # get_current_user (lecture seule)
│   ├── api/chat.py              # send_message endpoint (lecture seule)
│   ├── graph/state.py           # ConversationState (lecture seule)
│   └── modules/reports/service.py  # WeasyPrint usage (lecture seule)
└── tests/
    ├── conftest.py              # MODIFIER: ajouter fixtures partagés
    ├── test_financing_status.py       # MODIFIER: utiliser override_auth
    ├── test_financing_intermediaries.py # MODIFIER: utiliser override_auth
    ├── test_financing_preparation.py   # MODIFIER: utiliser override_auth
    ├── test_financing_node.py          # MODIFIER: make_conversation_state
    ├── test_credit/test_node.py        # MODIFIER: make_conversation_state
    ├── test_chat.py                    # MODIFIER: data= au lieu de json=
    ├── test_applications/test_node.py  # MODIFIER: AIMessage + AsyncMock
    ├── test_report_router.py           # MODIFIER: mock WeasyPrint
    └── test_report_service.py          # MODIFIER: mock WeasyPrint
```

**Structure Decision**: Aucun nouveau fichier de production. Modifications limitées aux fichiers de test existants + conftest.py.

## Complexity Tracking

Aucune violation de constitution. Pas de complexité ajoutée.

## Phases d'implémentation

### Phase 1 — Fixtures partagés (impact maximal: 22 tests)

1. Ajouter dans `conftest.py`:
   - Fixture `override_auth` avec `dependency_overrides`
   - Helper `make_conversation_state(**overrides)` avec les 27 clés par défaut

2. Mettre à jour les 3 fichiers financing (15 tests):
   - Supprimer les `@patch` auth locaux
   - Ajouter `@pytest.mark.usefixtures("override_auth")`

3. Mettre à jour financing_node + credit node (7 tests):
   - Remplacer les state dicts partiels par `make_conversation_state(...)`

### Phase 2 — Corrections ciblées (12 tests)

4. `test_chat.py` (3 tests):
   - Remplacer `json={"content": "..."}` par `data={"content": "..."}`

5. `test_applications/test_node.py` (1 test):
   - Remplacer `MagicMock` par `AIMessage` + `AsyncMock` chain

6. `test_report_router.py` + `test_report_service.py` (6 tests):
   - Mock WeasyPrint via `patch.dict(sys.modules, {"weasyprint": mock})`

### Phase 3 — Validation

7. Lancer les 34 tests ciblés → 0 échec
8. Lancer la suite complète → 901/901 pass
9. Vérifier zéro régression
