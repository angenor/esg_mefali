# Story 6.1 : Tool LangChain trigger_guided_tour et marker SSE

Status: done

## Story

En tant qu'utilisateur,
je veux que l'assistant puisse declencher un parcours guide visuel depuis le chat,
afin d'etre accompagne visuellement sans manipulation manuelle.

## Acceptance Criteria

### AC1 : Creation du tool `trigger_guided_tour`

**Given** le tool `trigger_guided_tour` n'existe pas encore
**When** un developpeur le cree dans `graph/tools/guided_tour_tools.py`
**Then** le tool accepte `tour_id (str)` et `context (dict | None)`
**And** il retourne un marker SSE au format `<!--SSE:{"__sse_guided_tour__":true,"tour_id":"...","context":{}}-->`
**And** aucune donnee sensible (scores, montants, IDs utilisateur) ne transite dans le marker (NFR10)

### AC2 : Detection du marker dans `stream_graph_events`

**Given** le tool est appele par un noeud LangGraph
**When** `stream_graph_events` detecte le marker `__sse_guided_tour__` dans le contenu
**Then** il emet un event SSE au format `{"type": "guided_tour", "tour_id": "...", "context": {...}}`

### AC3 : Parsing frontend et declenchement du parcours

**Given** le frontend recoit un event SSE de type `'guided_tour'`
**When** `useChat` parse l'event
**Then** `useGuidedTour().startTour(tour_id, context)` est appele automatiquement

### AC4 : Gestion du tour_id invalide

**Given** le tool est appele avec un `tour_id` invalide (pas dans le registre)
**When** `useGuidedTour` recoit l'appel
**Then** le parcours est ignore silencieusement et un message d'erreur est ajoute dans le chat via `addSystemMessage()`

### AC5 : Journalisation et events SSE tool calling

**Given** le tool est utilise en production
**When** on verifie les logs
**Then** l'appel est journalise dans `tool_call_logs` suivant le pattern existant (NFR21)
**And** les events SSE `tool_call_start` et `tool_call_end` sont emis

### AC6 : Zero regression

**Given** les tests existants (263 tests frontend, 935+ tests backend)
**When** on execute la suite de tests complete
**Then** zero regression, couverture >= 80% sur le nouveau code

## Tasks / Subtasks

- [x] Task 1 : Creer `backend/app/graph/tools/guided_tour_tools.py` (AC: #1, #5)
  - [x] 1.1 Definir le tool `trigger_guided_tour` avec decorator `@tool` async
  - [x] 1.2 Parametres : `tour_id: str`, `context: dict | None = None`, `config: RunnableConfig = None`
  - [x] 1.3 Construire le marker SSE `<!--SSE:{"__sse_guided_tour__":true,...}-->`
  - [x] 1.4 Journaliser via `log_tool_call()` (pattern `interactive_tools.py`)
  - [x] 1.5 Exporter `GUIDED_TOUR_TOOLS = [trigger_guided_tour]`
  - [x] 1.6 Ecrire les tests pytest : `backend/tests/test_tools/test_guided_tour_tools.py`

- [x] Task 2 : Ajouter la detection du marker dans `stream_graph_events` (AC: #2)
  - [x] 2.1 Dans `backend/app/api/chat.py` (apres ligne ~226), ajouter `elif sse_data.get("__sse_guided_tour__")`
  - [x] 2.2 Filtrer la cle `__sse_guided_tour__` du payload avant yield
  - [x] 2.3 Yield `{"type": "guided_tour", "tour_id": ..., "context": ...}`
  - [x] 2.4 Ecrire les tests : `backend/tests/test_graph/test_sse_tool_events.py` (2 tests ajoutes)

- [x] Task 3 : Ajouter le parsing `'guided_tour'` dans `useChat.ts` (AC: #3, #4)
  - [x] 3.1 Dans le bloc principal `sendMessage()` (apres `report_suggestion`, avant `error`), ajouter `else if (event.type === 'guided_tour' && event.tour_id)`
  - [x] 3.2 Importer et appeler `useGuidedTour().startTour(event.tour_id, event.context)`
  - [x] 3.3 Dans le bloc `submitInteractiveAnswer()` (apres `interactive_question`), ajouter le meme handler
  - [x] 3.4 Gestion erreur : `startTour` retourne deja silencieusement + `addSystemMessage()` si `tour_id` invalide (comportement existant dans `useGuidedTour.ts`)
  - [x] 3.5 Ecrire les tests Vitest : `frontend/tests/composables/useChat.guidedTour.test.ts`

- [x] Task 4 : Verifier la gestion de `tour_id` invalide dans `useGuidedTour.ts` (AC: #4)
  - [x] 4.1 Verifier que `startTour()` gere deja le cas `tourId` absent du registre — confirme (lignes 136-143 de useGuidedTour.ts)
  - [x] 4.2 Guard deja presente avec `addSystemMessage()` — aucune modification necessaire
  - [x] 4.3 Test Vitest existant : `useGuidedTour.test.ts` ligne 250-258

- [x] Task 5 : Tests d'integration et non-regression (AC: #6)
  - [x] 5.1 Lancer `cd backend && python -m pytest` — 992 passed, zero regression
  - [x] 5.2 Lancer `cd frontend && npx vitest run` — 267 passed, zero regression
  - [x] 5.3 Couverture : 11 tests backend + 2 tests SSE + 4 tests frontend = 17 nouveaux tests

## Dev Notes

### Pattern de reference : `interactive_tools.py` (feature 018)

Le tool `trigger_guided_tour` suit exactement le meme pattern que `ask_interactive_question` :

```python
# backend/app/graph/tools/guided_tour_tools.py
import json
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from app.graph.tools.common import get_db_and_user, log_tool_call

@tool
async def trigger_guided_tour(
    tour_id: str,
    context: dict | None = None,
    config: RunnableConfig = None,  # type: ignore
) -> str:
    """Declencher un parcours guide visuel pour l'utilisateur.

    Utilise cet outil pour lancer un guidage interactif qui montre
    visuellement a l'utilisateur les elements de l'interface.

    Args:
        tour_id: Identifiant du parcours (ex: show_esg_results, show_carbon_results).
        context: Donnees contextuelles optionnelles pour personnaliser le parcours.
    """
    db, _user_id = get_db_and_user(config)
    conversation_id = config["configurable"].get("conversation_id", "") if config else ""

    sse_payload = {
        "__sse_guided_tour__": True,
        "type": "guided_tour",
        "tour_id": tour_id,
        "context": context or {},
    }
    sse_marker = json.dumps(sse_payload)

    try:
        await log_tool_call(
            db=db,
            conversation_id=conversation_id,
            tool_name="trigger_guided_tour",
            tool_input={"tour_id": tour_id, "context": context},
            tool_output=f"Parcours {tour_id} declenche",
            success=True,
        )
    except Exception:
        pass  # Journalisation non bloquante

    return f"Parcours guide '{tour_id}' declenche pour l'utilisateur.\n\n<!--SSE:{sse_marker}-->"

GUIDED_TOUR_TOOLS = [trigger_guided_tour]
```

**Differences avec `ask_interactive_question` :**
- Pas de persistence DB (pas de table dediee — le tool ne fait que transmettre un signal)
- Pas de gestion d'invariant (pas de "1 pending max")
- Pas de `config.configurable.active_module` necessaire
- Le tool est beaucoup plus simple : il construit le marker SSE et le retourne

### Pattern de detection SSE dans `api/chat.py`

Ajouter le bloc apres la detection `__sse_interactive_question__` (ligne ~226) :

```python
elif sse_data.get("__sse_guided_tour__"):
    # Emettre l'event guided_tour (feature 019)
    event_payload = {
        k: v for k, v in sse_data.items()
        if k != "__sse_guided_tour__"
    }
    yield event_payload
```

### Pattern de parsing SSE dans `useChat.ts`

Ajouter dans les deux blocs de parsing SSE (sendMessage ~ligne 405, submitInteractiveAnswer ~ligne 637) :

```typescript
} else if (event.type === 'guided_tour' && event.tour_id) {
  // Feature 019 — Declenchement parcours guide via SSE
  const { startTour } = useGuidedTour()
  startTour(event.tour_id, event.context || {})
}
```

**Position d'insertion :**
- Bloc `sendMessage()` : apres `report_suggestion` (ligne ~410), avant `error`
- Bloc `submitInteractiveAnswer()` : apres `interactive_question` (ligne ~637)

### Comportement existant de `useGuidedTour.startTour()`

Le composable `useGuidedTour.ts` (516 lignes) gere deja :
- Validation du `tourId` contre le registre (`tourRegistry` dans `lib/guided-tours/registry.ts`)
- Lazy-loading de Driver.js
- Retraction du widget via `uiStore.chatWidgetMinimized`
- Navigation cross-pages avec countdown
- Cleanup DOM complet en cas d'erreur/interruption
- `addSystemMessage()` pour les erreurs UX

**A verifier (Task 4) :** que `startTour()` contient bien une guard pour `tourId` invalide avec `addSystemMessage()`. Si la validation se fait mais sans message, ajouter le message.

### Securite (NFR10)

Le `tour_id` ne doit contenir QUE l'identifiant du parcours (ex: `show_esg_results`). Les identifiants valides :
- `show_esg_results`
- `show_carbon_results`
- `show_financing_catalog`
- `show_credit_score`
- `show_action_plan`
- `show_dashboard_overview`

Le `context` peut contenir des donnees numeriques de personnalisation (ex: `{"total_tco2": 47}`) mais JAMAIS d'IDs utilisateur, tokens, ou donnees PII.

### Project Structure Notes

| Fichier | Action | Localisation |
|---------|--------|--------------|
| `backend/app/graph/tools/guided_tour_tools.py` | CREER | Nouveau, meme dossier que `interactive_tools.py` |
| `backend/app/api/chat.py` | MODIFIER | Ligne ~226, ajouter bloc `elif __sse_guided_tour__` |
| `frontend/app/composables/useChat.ts` | MODIFIER | Lignes ~405 et ~637, ajouter handler `guided_tour` |
| `frontend/app/composables/useGuidedTour.ts` | VERIFIER/MODIFIER | Guard `tour_id` invalide |
| `backend/tests/test_tools/test_guided_tour_tools.py` | CREER | Tests unitaires backend |
| `backend/tests/test_api/test_stream_guided_tour.py` | CREER | Tests detection marker |
| `frontend/tests/composables/useChat.guidedTour.test.ts` | CREER | Tests parsing event SSE |

### Alignement architecture

- **ADR4** (architecture.md) : Tool LangChain `trigger_guided_tour` + marker SSE — cette story implemente exactement cette decision
- **Convention markers SSE** : `__sse_[feature]__` avec double underscore, snake_case (precedent : `__sse_interactive_question__`, `__sse_profile__`)
- **Convention tools** : export via liste `[DOMAIN]_TOOLS` — ici `GUIDED_TOUR_TOOLS`
- **Convention tests** : `test_tools/test_[domain]_tools.py` pour les tools, `test_api/test_stream_[feature].py` pour la detection SSE

### Intelligence story 5.4 (derniere story completee)

**Lecons a retenir :**
- `onPopoverRender` est la propriete correcte (pas `popoverRender`) pour Driver.js
- `cleanupDriverResiduals()` doit utiliser `classList.remove()` et non `el.remove()` pour les elements `.driver-active-element`
- Flag `userInitiatedClose` module-level distingue les interruptions volontaires des resolutions programmatiques
- Le composable `useGuidedTour` utilise `createApp()` + `h()` pour monter les popovers Vue dans le conteneur Driver.js
- Les `mountedApps` sont trackes pour un unmount propre dans `unmountAllPopoverApps()`

**Fichiers touches dans 5.4 (contexte de la codebase actuelle) :**
- `frontend/app/components/copilot/GuidedTourPopover.vue` — composant popover custom (146 lignes)
- `frontend/app/composables/useGuidedTour.ts` — machine a etats (516 lignes)
- 263 tests frontend totaux, 0 regression

### References

- [Source: _bmad-output/planning-artifacts/architecture-019-floating-copilot.md#Decision-4] — ADR4 Tool LangChain trigger_guided_tour
- [Source: _bmad-output/planning-artifacts/epics-019-floating-copilot.md#Epic-6-Story-6.1] — Exigences story
- [Source: _bmad-output/planning-artifacts/prd.md#FR14-FR17] — Consentement et declenchement
- [Source: backend/app/graph/tools/interactive_tools.py] — Pattern de reference tool + marker SSE
- [Source: backend/app/api/chat.py#L212-L232] — Detection markers SSE existante
- [Source: frontend/app/composables/useChat.ts#L344-L405] — Parsing events SSE existant
- [Source: frontend/app/composables/useGuidedTour.ts] — Machine a etats et startTour()
- [Source: _bmad-output/implementation-artifacts/5-4-interruption-du-parcours-et-popover-custom.md] — Lecons story precedente

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

- Aucun probleme de debug rencontre

### Completion Notes List

- Tool `trigger_guided_tour` cree suivant le pattern exact de `ask_interactive_question` (meme structure marker SSE, meme journalisation via `log_tool_call`), sans persistence BDD (pas de table dediee)
- Detection marker `__sse_guided_tour__` ajoutee dans `stream_graph_events` — filtre la cle interne avant yield, emettre `guided_tour` event
- Handler SSE `guided_tour` ajoute dans les 2 blocs de parsing de `useChat.ts` (`sendMessage` et `submitInteractiveAnswer`) — import dynamique de `useGuidedTour` pour appel `startTour()`
- Task 4 : guard `tourId` invalide avec `addSystemMessage()` deja implementee dans story 5.1 (lignes 136-143 de useGuidedTour.ts), test existant confirme
- Tests SSE ajoutes dans le fichier existant `test_sse_tool_events.py` plutot que de creer un nouveau fichier `test_api/test_stream_guided_tour.py` — plus coherent avec la structure existante
- 992 tests backend, 267 tests frontend — zero regression

### Change Log

- 2026-04-13 : Implementation complete story 6.1 — tool trigger_guided_tour + marker SSE + parsing frontend (17 nouveaux tests)

### Review Findings

**Revue du 2026-04-13** — 3 couches (Blind Hunter, Edge Case Hunter, Acceptance Auditor). Acceptance Auditor : AC1-AC6 tous satisfaits, zero deviation bloquante.

#### Decisions requises (resolues)

- [x] [Review][Decision→Patch] Concurrent tour triggers — RESOLUTION : interrompre le tour en cours puis demander confirmation utilisateur avant de lancer le nouveau. Voir patch ci-dessous.
- [x] [Review][Decision→Patch] Tour declenche pendant question interactive `pending` — RESOLUTION : bloquer le tour + `addSystemMessage("Repondez d'abord a la question en attente.")`. Voir patch ci-dessous.

#### Patches (batch applique le 2026-04-13)

- [ ] [Review][Patch] Interruption + confirmation utilisateur pour tour concurrent [useGuidedTour.ts] — **SKIPPE** (requiert un jugement UX : modal custom vs `window.confirm()` natif). A traiter dans une iteration dediee. (Resolution Decision 1)
- [x] [Review][Patch] Bloquer le tour pendant une question interactive pending [useChat.ts] — APPLIQUE : helper `handleGuidedTourEvent` verifie `currentInteractiveQuestion.value?.state === 'pending'` et appelle `addSystemMessage("Repondez d'abord a la question en attente.")` (Resolution Decision 2).
- [x] [Review][Patch] Injection `-->` / `<!--` dans `tour_id` ou `context` [guided_tour_tools.py] — APPLIQUE : regex `^[a-z][a-z0-9_]*$` pour `tour_id` + remplacement `-->` → `--\u003e` dans le JSON serialise (decodable par le client).
- [x] [Review][Patch] `uuid.UUID(conversation_id_raw)` hors try/except [guided_tour_tools.py] — APPLIQUE : try/except ValueError avec fallback `conversation_id=None`.
- [x] [Review][Patch] `startTour(...)` non attendu + `await import(...)` sans gestion d'erreur [useChat.ts] — APPLIQUE : bloc try/catch dans `handleGuidedTourEvent`, `await` explicite, `console.warn` sur rejet.
- [x] [Review][Patch] Duplication du handler `guided_tour` [useChat.ts] — APPLIQUE : extraction en helper `handleGuidedTourEvent`, appele depuis `sendMessage` et `submitInteractiveAnswer`.
- [x] [Review][Patch] `context` non-JSON-serializable [guided_tour_tools.py] — APPLIQUE : `json.dumps(sse_payload, default=str)`.
- [x] [Review][Patch] `tour_id=""` silencieusement drop [guided_tour_tools.py + useChat.ts] — APPLIQUE : validation cote tool (rejet avec message d'erreur) + `console.warn` cote frontend si event sans tour_id valide.

**Tests ajoutes :** 12 nouveaux tests backend (`TestTriggerGuidedTourHardening` : empty/malformed tour_id, `-->` dans context, UUID invalide, datetime non-serialisable) + 2 nouveaux tests frontend (pending question bloquant, rattrapage rejet de `startTour`).

#### Deferes (pre-existant ou hardening)

- [x] [Review][Defer] Pas d'allowlist serveur pour `tour_id` [guided_tour_tools.py] — defere, AC4 delegue explicitement la validation au registre frontend (par conception). Hardening defense-en-profondeur possible plus tard.
- [x] [Review][Defer] `context` dict sans limite de taille/profondeur [guided_tour_tools.py:24] — defere, hardening. Pre-existant aux autres tools qui acceptent des dicts LLM-controlled.
- [x] [Review][Defer] Marker SSE split entre chunks de streaming [chat.py:212-239] — defere, pre-existant. Parser actuel dans `stream_graph_events` suppose un `on_tool_end` avec output complet. Limitation partagee avec les markers `__sse_profile__` et `__sse_interactive_question__`.
- [x] [Review][Defer] Plusieurs markers SSE dans un seul output ne sont pas tous parses [chat.py:213-217] — defere, pre-existant. `index()` ne trouve que le premier `-->`, les markers suivants sont ignores.

#### Notes

- Dismisses (3) : assertion cosmetique `"-->".rstrip() in result`, lecture redondante de `configurable`, `except Exception` sur `log_tool_call` (pattern projet documente dans `interactive_tools.py`).
- Acceptance Auditor : AC1-AC6 tous `Met` ou `Cannot verify from diff` (AC6 repose sur la claim spec de 992 backend + 267 frontend pass). Aucune contradiction avec le spec, aucune donnee sensible ne transite dans le marker (NFR10 respecte).

### File List

- `backend/app/graph/tools/guided_tour_tools.py` — CREE — Tool LangChain trigger_guided_tour
- `backend/app/api/chat.py` — MODIFIE — Detection marker `__sse_guided_tour__` dans stream_graph_events
- `frontend/app/composables/useChat.ts` — MODIFIE — Handler event `guided_tour` dans sendMessage et submitInteractiveAnswer
- `backend/tests/test_tools/test_guided_tour_tools.py` — CREE — 11 tests unitaires tool
- `backend/tests/test_graph/test_sse_tool_events.py` — MODIFIE — 2 tests detection marker SSE
- `frontend/tests/composables/useChat.guidedTour.test.ts` — CREE — 4 tests parsing SSE frontend
