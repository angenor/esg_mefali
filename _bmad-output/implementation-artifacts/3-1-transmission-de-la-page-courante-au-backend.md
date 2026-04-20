# Story 3.1 : Transmission de la page courante au backend

Status: done

## Story

En tant qu'utilisateur,
je veux que l'assistant sache sur quelle page je me trouve,
afin qu'il puisse me donner des reponses adaptees a mon contexte de navigation.

## Acceptance Criteria

1. **AC1 — Tracking de la route dans le store UI**
   - **Given** l'utilisateur est sur la page `/carbon/results`
   - **When** le FloatingChatWidget est monte dans le layout
   - **Then** `uiStore.currentPage` vaut `'/carbon/results'`

2. **AC2 — Mise a jour en temps reel**
   - **Given** l'utilisateur navigue de `/dashboard` vers `/esg`
   - **When** la route change
   - **Then** `uiStore.currentPage` est mis a jour en temps reel avec `'/esg'`

3. **AC3 — Transmission dans le FormData**
   - **Given** l'utilisateur envoie un message depuis le widget
   - **When** `useChat.sendMessage()` construit le FormData
   - **Then** le champ `current_page` est present avec la valeur de `uiStore.currentPage`

4. **AC4 — Reception et stockage backend**
   - **Given** le backend recoit une requete POST `/api/chat/messages` avec `current_page`
   - **When** le message est traite
   - **Then** `current_page` est stocke dans `ConversationState` et accessible par tous les noeuds LangGraph

5. **AC5 — Coexistence avec active_module (NFR22)**
   - **Given** le champ `current_page` est ajoute a `ConversationState`
   - **When** on verifie le mecanisme `active_module` existant
   - **Then** les deux champs coexistent sans conflit — `current_page` est informatif, `active_module` est decisif pour le routage

6. **AC6 — Zero regression (NFR19)**
   - **Given** le refactoring est termine
   - **When** on execute les tests backend + frontend
   - **Then** zero regression sur les tests existants
   - **And** couverture >= 80% sur les fichiers modifies

## Tasks / Subtasks

- [x] **Task 1 : Ajouter `currentPage` au store `ui.ts`** (AC: 1)
  - [x] 1.1 Ajouter `const currentPage = ref<string>('/')` dans `useUiStore`
  - [x] 1.2 Exposer `currentPage` dans le `return` du store
  - [x] 1.3 NE PAS persister dans localStorage (information transitoire)

- [x] **Task 2 : Watcher de route dans `layouts/default.vue`** (AC: 1, 2)
  - [x] 2.1 Ajouter un `watch(() => route.path, ...)` avec `{ immediate: true }` dans le `<script setup>` existant
  - [x] 2.2 Le watcher met a jour `uiStore.currentPage = newPath`
  - [x] 2.3 Garder SSR-safe : proteger avec `import.meta.client` (meme pattern que le watcher `openChat` existant ligne 17)

- [x] **Task 3 : Envoyer `current_page` dans `useChat.sendMessage()`** (AC: 3)
  - [x] 3.1 Dans `composables/useChat.ts`, ligne ~162, apres `formData.append('content', ...)`, ajouter : `formData.append('current_page', uiStore.currentPage)`
  - [x] 3.2 Importer et appeler `useUiStore()` dans le scope du composable (attention : le composable utilise du module-level state — l'appel a `useUiStore()` doit etre dans la fonction `sendMessage` ou dans `useChat()`, PAS au module-level car Pinia n'est pas initialisee avant l'app)
  - [x] 3.3 Verifier aussi `submitInteractiveAnswer()` (ligne ~536) — ajouter `current_page` au FormData si pertinent (la question interactive est liee a la conversation, le contexte de page est utile)

- [x] **Task 4 : Accepter `current_page` dans l'endpoint backend** (AC: 4)
  - [x] 4.1 Dans `backend/app/api/chat.py`, fonction `send_message` (ligne 615), ajouter le parametre : `current_page: str | None = Form(None)`
  - [x] 4.2 Passer `current_page` a `stream_graph_events()` via un nouveau parametre
  - [x] 4.3 Dans `stream_graph_events()` (ligne 82), ajouter le parametre `current_page: str | None = None`
  - [x] 4.4 Ajouter `"current_page": current_page` dans le dictionnaire `initial_state` (ligne 108-131)
  - [x] 4.5 L'endpoint JSON `send_message_json` (ligne 916) passe `current_page=None` (pas de support page courante sans le widget)

- [x] **Task 5 : Ajouter `current_page` a `ConversationState`** (AC: 4, 5)
  - [x] 5.1 Dans `backend/app/graph/state.py`, ajouter `current_page: str | None` au `TypedDict`
  - [x] 5.2 Le placer apres `active_module_data` (regroupement logique contexte)
  - [x] 5.3 NE PAS modifier `active_module` ni le `router_node` — `current_page` est purement informatif pour cette story (FR11). L'injection dans les prompts est la Story 3.2

- [x] **Task 6 : Tests unitaires frontend** (AC: 1, 2, 3, 6)
  - [x] 6.1 Test store `ui.ts` : `currentPage` est initialise a `'/'`, modifiable, expose
  - [x] 6.2 Test `layouts/default.vue` : le watcher met a jour `uiStore.currentPage` quand `route.path` change
  - [x] 6.3 Test `useChat.sendMessage()` : le FormData contient `current_page` avec la valeur du store

- [x] **Task 7 : Tests unitaires backend** (AC: 4, 5, 6)
  - [x] 7.1 Test `state.py` : `ConversationState` accepte `current_page`
  - [x] 7.2 Test `chat.py` : `send_message` accepte et transmet `current_page`
  - [x] 7.3 Test `stream_graph_events` : `current_page` est present dans `initial_state`
  - [x] 7.4 Verification : les tests existants passent sans regression

- [x] **Task 8 : Verification finale**
  - [x] 8.1 Lancer `cd frontend && npx vitest run` — zero echec
  - [x] 8.2 Lancer `cd backend && source venv/bin/activate && python -m pytest` — zero echec
  - [x] 8.3 Grep verification : `current_page` present dans state.py, chat.py, useChat.ts, ui.ts

## Dev Notes

### Portee de cette story

Cette story couvre UNIQUEMENT la plomberie (FR11) : tracker la page courante et la transmettre au backend. L'injection dans les prompts LLM et l'adaptation des reponses (FR12, FR13) sont la Story 3.2.

### Fichiers a modifier

| Fichier | Action | Lignes cles |
|---------|--------|-------------|
| `frontend/app/stores/ui.ts` | Ajouter `currentPage` ref | Apres ligne 18 (`chatWidgetOpen`) |
| `frontend/app/layouts/default.vue` | Ajouter watcher route → `currentPage` | Dans le `<script setup>` existant, pres du watcher `openChat` (ligne 17) |
| `frontend/app/composables/useChat.ts` | Ajouter `current_page` au FormData | Ligne ~162 (dans `sendMessage`) et ligne ~536 (dans `submitInteractiveAnswer`) |
| `backend/app/api/chat.py` | Ajouter parametre `current_page` | Ligne 615 (`send_message`), ligne 82 (`stream_graph_events`), ligne 108 (`initial_state`) |
| `backend/app/graph/state.py` | Ajouter `current_page: str | None` | Apres ligne 35 (`active_module_data`) |

### Fichiers a NE PAS modifier

- `backend/app/graph/nodes.py` — Aucun noeud ne consomme `current_page` dans cette story
- `backend/app/graph/prompts/*.py` — L'injection dans les prompts est Story 3.2
- `frontend/app/components/copilot/*.vue` — Le widget ne change pas visuellement
- `backend/app/api/chat.py` ligne 916 (`send_message_json`) — Passer `current_page=None` seulement

### Pattern FormData existant

Le sendMessage utilise deja FormData (pas JSON) pour supporter l'upload de fichiers. Ajouter `current_page` est un simple `formData.append()` supplementaire :

```typescript
// useChat.ts, dans sendMessage(), apres ligne 162
const formData = new FormData()
formData.append('content', content || ...)
if (file) { formData.append('file', file) }
formData.append('current_page', uiStore.currentPage)  // NOUVEAU
```

### Acces au store Pinia depuis useChat

`useChat.ts` utilise du module-level state (refs declarees hors de la fonction composable). `useUiStore()` ne peut PAS etre appele au module-level car Pinia n'est pas encore initialisee a ce moment. Deux options :

**Option recommandee** : appeler `useUiStore()` au debut de `sendMessage()` (a chaque appel) :
```typescript
async function sendMessage(content: string, file?: File): Promise<void> {
  const uiStore = useUiStore()
  // ...
  formData.append('current_page', uiStore.currentPage)
}
```

**Option alternative** : appeler `useUiStore()` dans la fonction `useChat()` (une seule fois au mount) et stocker la reference. Mais cela suppose que `useChat()` est appele apres l'init Pinia, ce qui est garanti car le layout l'appelle au mount.

### Pattern watcher route (deja etabli dans default.vue)

Le layout `default.vue` a deja un watcher pour le query param `openChat` (story 2-2). Le nouveau watcher suit le meme pattern :

```typescript
// default.vue, dans <script setup>
if (import.meta.client) {
  watch(() => route.path, (newPath) => {
    uiStore.currentPage = newPath
  }, { immediate: true })
}
```

### Backend : parametre Form vs Body

L'endpoint `send_message` utilise `Form()` (pas `Body()`) pour tous ses parametres car le request est en `multipart/form-data`. Le nouveau `current_page` suit le meme pattern :

```python
async def send_message(
    conversation_id: uuid.UUID,
    content: str = Form(None),
    file: UploadFile | None = File(None),
    interactive_question_id: str | None = Form(None),
    interactive_question_values: str | None = Form(None),
    interactive_question_justification: str | None = Form(None),
    current_page: str | None = Form(None),  # NOUVEAU
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
```

### Coexistence current_page / active_module (NFR22)

- `active_module` (str | None) : module LangGraph actif (esg_scoring, carbon, etc.), gere par le `router_node` et les noeuds specialistes. DECISIF pour le routage.
- `current_page` (str | None) : route frontend courante (/esg, /carbon/results, etc.). INFORMATIF, utilise par les prompts (Story 3.2).

Les deux sont dans `ConversationState` mais ont des cycles de vie independants :
- `active_module` est mis a jour par les noeuds LangGraph pendant le traitement
- `current_page` est ecrit une fois a l'entree du graphe et lu par les prompts

### Tests existants a preserver

- Backend : 935+ tests (`python -m pytest`)
- Frontend : 155+ tests (`npx vitest run`, 15 fichiers)
- Le champ `current_page` est optionnel (`str | None`, defaut `None`), donc les tests existants qui ne le fournissent pas continuent de fonctionner

### Intelligence de la story precedente (2-2)

**Learnings cles :**
- Les auto-imports Nuxt fonctionnent pour `useUiStore()` — pas besoin d'import explicite si le store est dans `stores/`
- Le watcher `openChat` dans `default.vue` utilise `import.meta.client` pour eviter l'execution SSR — suivre le meme pattern
- La story 2-2 a nettoye le dead code `chatPanelOpen` / `toggleChatPanel` du store `ui.ts`
- L'action `openChatWidget()` a ete centralisee dans le store `ui.ts` (review finding de 2-2)

### Commits recents

```
c489a6c 2-2-mise-a-jour-de-la-navigation-et-des-liens-internes: done
b7314e2 2-1-suppression-de-la-page-chat-et-de-chatpanel: done
39bbb14 1-6 + 1-7: done
e27120c 1-3 + 1-4 + 1-5: done
```

### Project Structure Notes

- Nuxt 4 : fichiers source dans `frontend/app/` (pages, components, composables, layouts, stores)
- Backend FastAPI : fichiers dans `backend/app/` (api, graph, schemas, models, services)
- `ConversationState` est un `TypedDict` (pas un Pydantic model) — ajouter un champ est une simple declaration de type
- Le FormData est parse par FastAPI via les decorateurs `Form()` et `File()` — pas de schema Pydantic pour le multipart

### References

- [Source: _bmad-output/planning-artifacts/epics-019-floating-copilot.md — Epic 3, Story 3.1]
- [Source: _bmad-output/planning-artifacts/architecture-019-floating-copilot.md — Conscience contextuelle FR11-FR13, ConversationState, ui.ts currentPage]
- [Source: _bmad-output/planning-artifacts/prd.md — FR11, NFR19, NFR22]
- [Source: _bmad-output/implementation-artifacts/2-2-mise-a-jour-de-la-navigation-et-des-liens-internes.md — Dev Notes, Pattern watcher]
- [Source: backend/app/graph/state.py — ConversationState actuel (36 lignes)]
- [Source: backend/app/api/chat.py — send_message (ligne 615), stream_graph_events (ligne 82)]
- [Source: frontend/app/composables/useChat.ts — sendMessage (ligne 132)]
- [Source: frontend/app/stores/ui.ts — store actuel]

## Dev Agent Record

### Agent Model Used
Claude Opus 4.6 (1M context)

### Debug Log References
- Test frontend layout/default.test.ts : corrige mock `mockRoute` pour inclure `path` (reactivity issue sur remplacement d'objet vs mutation de propriete)
- Test backend test_current_page.py : patch `app.main.compiled_graph` au lieu de `app.api.chat.compiled_graph` (import local dans la fonction)

### Completion Notes List
- Task 1 : `currentPage` ref ajoute au store ui.ts, initialise a `/`, expose dans le return, non persiste dans localStorage
- Task 2 : Watcher `route.path` avec `{ immediate: true }` dans default.vue, protege par `import.meta.client` (SSR-safe)
- Task 3 : `current_page` envoye dans le FormData de `sendMessage()` et `submitInteractiveAnswer()`, import explicite `useUiStore` ajoute pour coherence avec les autres stores
- Task 4 : Parametre `current_page: str | None = Form(None)` ajoute a `send_message`, transmis a `stream_graph_events`, `send_message_json` passe `current_page=None`
- Task 5 : `current_page: str | None` ajoute a `ConversationState` TypedDict apres `active_module_data`, coexistence AC5 verifiee
- Task 6 : 4 tests store ui.ts + 2 tests layout default.vue + 2 tests useChat.ts = 8 nouveaux tests frontend
- Task 7 : 6 nouveaux tests backend (4 state + 2 stream_graph_events), helper `make_conversation_state` mis a jour
- Task 8 : 176 tests frontend verts, 950 tests backend verts, zero regression, grep confirme presence dans les 4 fichiers

### Review Findings

- [x] [Review][Patch] Pas de validation backend sur `current_page` — ajoute strip()+truncate 200 chars dans send_message [backend/app/api/chat.py:638]
- [x] [Review][Patch] Code mort dans le test — supprime le double stub fetch et la variable `originalFetch` inutilisee [frontend/tests/composables/useChat.test.ts]
- [x] [Review][Patch] Isolation de test — deplace reset `mockCurrentPage` dans `afterEach` du describe Story 3.1 [frontend/tests/composables/useChat.test.ts]
- [x] [Review][Defer] Pas d'annotation reducer pour `current_page` dans ConversationState — le champ pourrait ne pas se propager si un noeud retourne un state partiel (risque latent, aucun noeud ne le modifie aujourd'hui) [backend/app/graph/state.py:36] — deferred, pre-existing pattern
- [x] [Review][Defer] `invoke_graph` n'accepte pas `current_page` — inconsistance latente avec `stream_graph_events` (fonction potentiellement inutilisee) [backend/app/api/chat.py:56] — deferred, pre-existing

### Change Log
- 2026-04-13 : Story 3.1 implementee — plomberie current_page du frontend au ConversationState backend

### File List
- frontend/app/stores/ui.ts (modifie)
- frontend/app/layouts/default.vue (modifie)
- frontend/app/composables/useChat.ts (modifie)
- backend/app/api/chat.py (modifie)
- backend/app/graph/state.py (modifie)
- frontend/tests/stores/ui.test.ts (modifie)
- frontend/tests/layouts/default.test.ts (modifie)
- frontend/tests/composables/useChat.test.ts (modifie)
- backend/tests/conftest.py (modifie)
- backend/tests/test_graph/test_current_page.py (nouveau)
