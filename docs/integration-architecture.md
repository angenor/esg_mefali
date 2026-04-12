# Architecture d'intégration — Frontend ↔ Backend

## 1. Vue d'ensemble

Le monorepo ESG Mefali est composé de **deux parties** qui communiquent exclusivement via **HTTP + SSE** :

```
┌────────────────────────┐                      ┌────────────────────────┐
│  Frontend Nuxt 4       │                      │  Backend FastAPI       │
│                        │  ① REST JSON         │                        │
│  app/composables/      │─────────────────────►│  app/api/*             │
│    useAuth.ts          │◄─────────────────────│  app/modules/*/router  │
│    useEsg.ts           │     JSON responses   │                        │
│    useCarbon.ts        │                      │                        │
│    ...                 │  ② SSE stream        │                        │
│                        │─────────────────────►│  POST /api/chat/       │
│  app/composables/      │                      │    {id}/messages       │
│    useChat.ts          │◄─────────────────────│    (text/event-stream) │
│                        │     events typés      │                        │
│                        │                      │                        │
│                        │  ③ Multipart upload  │                        │
│                        │─────────────────────►│  POST /api/documents/  │
│                        │     (FormData)        │                        │
└────────────────────────┘                      └────────────────────────┘
```

**Aucune autre forme d'intégration** : pas de GraphQL, pas de WebSocket, pas de message queue, pas de gRPC, pas de BDD partagée. Le couplage est minimal et testable unitairement.

## 2. Points d'intégration

### 2.1 REST JSON (appels synchrones)

| Frontend | Backend | Usage |
|---|---|---|
| `composables/useAuth.ts` | `/api/auth/*` | Login, register, refresh, me |
| `composables/useCompanyProfile.ts` | `/api/company/*` | Profil entreprise |
| `composables/useEsg.ts` | `/api/esg/*` | Évaluations ESG |
| `composables/useCarbon.ts` | `/api/carbon/*` | Empreinte carbone |
| `composables/useFinancing.ts` | `/api/financing/*` | Fonds + matching |
| `composables/useApplications.ts` | `/api/applications/*` | Dossiers candidature |
| `composables/useCreditScore.ts` | `/api/credit/*` | Score crédit |
| `composables/useActionPlan.ts` | `/api/action-plan/*` | Plan d'action + rappels |
| `composables/useDashboard.ts` | `/api/dashboard/summary` | Vue consolidée |
| `composables/useDocuments.ts` | `/api/documents/*` | Liste/preview/suppression |
| `composables/useReports.ts` | `/api/reports/*` | Téléchargement PDF |

**Format** : JSON typé côté frontend via `types/*.ts`, validé côté backend via Pydantic v2.

**Authentification** : header `Authorization: Bearer <access_token>` ajouté par `useAuth.apiFetch`. Token stocké en `localStorage`.

### 2.2 SSE streaming — Chat IA

**Endpoint** : `POST /api/chat/{conversation_id}/messages`

**Requête** : `multipart/form-data`

| Champ | Type | Rôle |
|---|---|---|
| `content` | string | Message texte utilisateur |
| `file` | File \| null | Document optionnel à analyser (PDF/DOCX/XLSX/image) |
| `interactive_question_id` | UUID \| null | Si réponse à une question interactive |
| `interactive_question_answer` | JSON \| null | Réponse sélectionnée |
| `interactive_question_justification` | string (≤400) \| null | Justification textuelle |

**Réponse** : `Content-Type: text/event-stream` avec des événements typés :

| Event | Payload | Consommateur frontend |
|---|---|---|
| `token` | `{content}` | `ChatMessage.vue` (append stream) |
| `done` | `{message_id, conversation_id}` | Marque la fin et persiste le message |
| `document_upload` | `{document_id, filename, size}` | `DocumentUpload.vue` |
| `document_status` | `{document_id, status}` | Progress bar upload |
| `document_analysis` | `{document_id, summary}` | Mise à jour UI documents |
| `profile_update` | `{field, old_value, new_value}` | Store `company`, `ProfileNotification.vue` |
| `profile_completion` | `{identity, esg, overall}` | `ProfileProgress.vue` |
| `tool_call_start` | `{tool_name, args}` | `ToolCallIndicator.vue` (spinner + label FR) |
| `tool_call_end` | `{tool_name, output}` | `ToolCallIndicator.vue` (check ok) |
| `tool_call_error` | `{tool_name, error}` | `ToolCallIndicator.vue` (erreur) |
| `interactive_question` | `{question_id, type, options, question_text, ...}` | `InteractiveQuestionHost.vue` (feature 018) |
| `interactive_question_resolved` | `{question_id, state, answer}` | Ferme le widget |

**Implémentation frontend** (`composables/useChat.ts`) :

```ts
const response = await fetch(`${apiBase}/chat/${convId}/messages`, {
  method: 'POST',
  headers: { Authorization: `Bearer ${token}` },
  body: formData,
})
const reader = response.body!.getReader()
const decoder = new TextDecoder()
let buffer = ''
while (true) {
  const { done, value } = await reader.read()
  if (done) break
  buffer += decoder.decode(value, { stream: true })
  // parse `data: {...}\n\n` events
}
```

**Implémentation backend** (`app/api/chat.py`) : `StreamingResponse` consommant `app/graph/stream_graph_events()` qui appelle `compiled_graph.astream_events(...)` et sérialise les events au format SSE (`data: {...}\n\n`).

### 2.3 Upload de documents

- **Endpoint dédié** : `POST /api/documents/` (upload seul, hors chat)
- **Endpoint chat** : `POST /api/chat/{id}/messages` avec `file` (upload + analyse IA en une passe)
- **Format** : `multipart/form-data`
- **Pipeline backend** : stockage `/uploads/` → extraction (PyMuPDF / docx2txt / openpyxl / pytesseract OCR) → chunking → embeddings OpenAI `text-embedding-3-small` (1536 dim) → insertion `document_chunks` pgvector → analyse LLM résumée dans `document_analyses`

## 3. Authentification et sessions

| Aspect | Détail |
|---|---|
| Protocole | JWT Bearer HS256 |
| Durée access token | 8 h (prod), 1 h (dev — paramétrable via `ACCESS_TOKEN_EXPIRE_MINUTES`) |
| Durée refresh token | 30 jours |
| Stockage frontend | `localStorage` (access + refresh) |
| Header | `Authorization: Bearer <access_token>` |
| Rechargement | `auth.loadFromStorage()` au premier render (middleware global `auth.global.ts`) |
| Refresh | À confirmer / compléter côté `useAuth` — endpoint `/api/auth/refresh` disponible, logique de rafraîchissement automatique non observée |

> **TODO intégration** : documenter / implémenter le rafraîchissement silencieux du token d'accès (intercepteur sur 401).

## 4. Gestion du state partagé

Le frontend ne maintient **aucun état serveur en local durable** hors JWT et thème UI : chaque donnée métier est re-fetchée au besoin via les composables ; les stores Pinia servent de **cache mémoire** par écran.

Les events SSE enrichissent le cache en temps réel :

- `profile_update` → met à jour `companyStore.profile` et déclenche un toast
- `profile_completion` → met à jour `companyStore.completion`
- `interactive_question_resolved` → retire le widget en cours et débloque `ChatInput`

## 5. CORS et sécurité

### Côté backend (`app/main.py`)

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

En production, cette liste doit être **externalisée** (env `CORS_ORIGINS`) pour accepter le domaine public.

### Côté frontend

- Appels `fetch()` avec `credentials: 'omit'` par défaut (le JWT est en header, pas en cookie)
- Upload multipart : pas de header `Content-Type` manuel (le navigateur pose le `boundary`)
- Les réponses SSE ne nécessitent aucune configuration CORS particulière au-delà de `allow_origins`

## 6. Observabilité de l'intégration

- **Backend** : table `tool_call_logs` enregistre tous les appels aux tools LangChain (input_args, output, status, duration_ms, error_message)
- **Frontend** : `ToolCallIndicator.vue` affiche en temps réel l'exécution des tools
- **Santé globale** : `/api/health` interrogé par Nginx et par le monitoring

## 7. Contrat de données — invariants clés

- Les IDs sont toujours des **UUID v4** string
- Les timestamps sont en **ISO 8601 UTC**
- Les montants financiers sont en **entiers FCFA** (pas de float pour éviter les erreurs d'arrondi)
- Les scores ESG / crédit / complétude sont en **pourcentage `0-100`** (float)
- Les émissions carbone sont en **tonnes CO2 équivalent** (`tCO2e`, float)
- Une conversation ne peut avoir **qu'une seule question interactive `pending`** à la fois (feature 018)

## 8. Risques et points d'attention

- **Pas de rate limiting** côté backend — risque d'abus de l'endpoint SSE (consomme des tokens OpenRouter)
- **Pas de versioning API** (`/v1/`) — rupture de contrat possible sur refonte
- **Refresh token** : logique de rafraîchissement automatique à compléter
- **Gestion des déconnexions SSE** : à surveiller sur mobile / réseaux dégradés (timeout, reconnexion manuelle ?)
- **CORS en dur** : bloquera toute mise en ligne en dehors de `localhost:3000`
- **Tests E2E** : Playwright installé mais aucun scénario critique E2E écrit → zéro filet de sécurité sur le flux chat complet

## 9. Références croisées

- [Contrats d'API](./api-contracts-backend.md)
- [Architecture Backend](./architecture-backend.md)
- [Architecture Frontend](./architecture-frontend.md)
