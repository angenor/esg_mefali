# Architecture d'intégration — Frontend ↔ Backend

## 1. Vue d'ensemble

Le monorepo comporte **deux parties autonomes** qui communiquent exclusivement via HTTP. Aucun partage de code, de binaire ou de base de données en dehors de l'API publique.

```
┌───────────────────────┐                      ┌─────────────────────────┐
│  Frontend Nuxt 4      │   REST JSON          │  Backend FastAPI        │
│  (Vue 3 + Pinia)      │─────────────────────▶│  /api/*                 │
│                       │◀────────────────────│                          │
│  useAuth().apiFetch() │   JWT Bearer auth    │  get_current_user dep   │
│                       │                      │                          │
│  useChat.ts           │   SSE text/event-    │  POST /api/chat/…/      │
│  (fetch streaming)    │◀─────────────────────│  messages (StreamingResp)│
│                       │                      │                          │
│  FormData uploads     │   multipart/form-    │  POST /api/documents/   │
│                       │─────────────────────▶│  upload                  │
└───────────────────────┘                      └─────────────────────────┘
         │                                                 │
         │     Au centre : LangGraph orchestre 9 nœuds,    │
         └──── ~36 tools LangChain, persiste l'état ──────┘
                dans PostgreSQL + pgvector
```

## 2. Configuration de la connexion

### Base URL API

- **Source** : `runtimeConfig.public.apiBase` de Nuxt 4.
- **Variable d'env** : `NUXT_PUBLIC_API_BASE`.
- **Valeur dev** : `http://localhost:8000/api`.
- **Valeur prod** : `/api` (relative, nginx reverse-proxifie vers l'upstream `esg_mefali_backend:8000`).

### CORS

Configuré dans [backend/app/main.py](../backend/app/main.py) :

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Limite connue** : la liste est codée en dur et ne couvre que le dev. En prod, le frontend et l'API sont servis sous la **même origine** (`esg.mefali.com`) donc le CORS ne s'applique pas — mais la valeur littérale reste à nettoyer. Voir [technical-debt-backlog.md](./technical-debt-backlog.md).

## 3. Authentification

### Flux JWT HS256

| Étape | Endpoint | Payload | Réponse |
|---|---|---|---|
| Inscription | `POST /api/auth/register` | `{email, password, full_name, company_name}` | Création utilisateur + `CompanyProfile` |
| Login | `POST /api/auth/login` | `{email, password}` | `{access_token, refresh_token, token_type: "bearer", expires_in: 3600}` |
| Rafraîchissement | `POST /api/auth/refresh` | `{refresh_token}` | `{access_token}` (réutilise le refresh token en cours) |
| Identité | `GET /api/auth/me` | — | `UserResponse` (id, email, full_name, company_name) |
| Détection pays | `GET /api/auth/detect-country` | — | `{country_code, country_name, supported_countries}` (via IP) |

- **Access token** : 60 min en dev, 480 min en prod.
- **Refresh token** : 30 jours.
- **Algorithme** : HS256 ; `SECRET_KEY` via env.
- **Hash mot de passe** : bcrypt.

### Attachement du token (frontend)

Composable central : [frontend/app/composables/useAuth.ts](../frontend/app/composables/useAuth.ts).

```ts
apiFetch<T>(path, options)
  └─ Ajoute Authorization: Bearer ${authStore.accessToken}
  └─ Gestion 401 : auto-retry via refreshPromise (single-flight module-level)
  └─ Sur échec de refresh : SessionExpiredError → redirect /login
```

Points critiques (spec 7-2, « renouvellement JWT transparent ») :
- **Single-flight** : une seule requête `/refresh` concurrente à la fois (`let refreshPromise: Promise<string> | null` au niveau module).
- **Isolement tour guidé** : si un tour est actif lors de l'expiration, `handleAuthFailure()` annule le tour avant redirection pour éviter qu'un popover `driver.js` reste orphelin.

### Store Pinia

[frontend/app/stores/auth.ts](../frontend/app/stores/auth.ts) persiste `accessToken` et `refreshToken` dans `localStorage`. Rechargé via `loadFromStorage()` au premier appel du middleware `auth.global.ts`.

## 4. Streaming SSE (chat IA)

### Endpoint

```
POST /api/chat/conversations/{conversation_id}/messages
Content-Type: multipart/form-data
Authorization: Bearer <access_token>

Champs form :
  content                     (str)   — message utilisateur
  document_upload             (file)  — optionnel, pièce jointe
  document_analysis_summary   (str)   — optionnel, résumé déjà calculé
  interactive_question_id     (str)   — optionnel, réponse à un widget (spec 018)
  widget_response             (json)  — optionnel, payload du widget
  current_page                (str)   — optionnel, page courante (spec 3, injection contexte)
  guidance_stats              (json)  — optionnel, stats tours guidés (spec 6-4)
```

Réponse : `text/event-stream` (SSE), format `data: {JSON}\n\n` ligne par ligne.

### Consommation côté frontend

[frontend/app/composables/useChat.ts](../frontend/app/composables/useChat.ts) implémente un **reader fetch streaming** (pas `EventSource`, pour pouvoir poster du FormData + headers custom) :

```ts
const response = await fetch(url, { method: 'POST', headers, body: formData });
const reader = response.body!.getReader();
const decoder = new TextDecoder();
// boucle : reader.read() → decoder → parseLines → router selon event.type
```

**Résilience réseau** (spec 7-3, « résilience SSE et indicateur de reconnexion ») :
- `AbortController` module-level pour annuler proprement.
- Surveillance `navigator.onLine` + events `online`/`offline`.
- Classification d'erreur : `abort` (annulation volontaire), `network` (reconnexion possible), `http` (erreur métier), `other`.
- Bandeau UI `ConnectionStatusBadge.vue` affiche l'état.

**État module-level** (depuis le refactor widget spec 019) :
- La navigation entre pages ne doit pas casser le stream en cours → le `reader` et l'`AbortController` sont partagés au niveau module (et non au niveau composant), ce qui permet au chat flottant d'être conservé à travers la navigation.

### Événements SSE émis par le backend

| Type | Emis par | Charge utile | Usage frontend |
|---|---|---|---|
| `token` | `chat_node`, `esg_scoring_node`, … | `{content: str}` | Append au message assistant en construction |
| `tool_call_start` | `ToolNode` | `{tool_name, tool_call_id}` | Afficher `ToolCallIndicator.vue` en mode "en cours" |
| `tool_call_end` | `ToolNode` | `{tool_name, tool_call_id, duration_ms}` | Masquer / finaliser l'indicateur |
| `tool_call_error` | `ToolNode` | `{tool_name, error}` | Afficher erreur dans l'indicateur |
| `interactive_question` | `ask_interactive_question` tool (spec 018) | `{id, type, prompt, options, min_selections, max_selections, requires_justification}` | Monter `InteractiveQuestionHost.vue` + verrouiller input texte |
| `interactive_question_resolved` | Backend à la réception d'une réponse | `{id, response_values, response_justification, state}` | Démonter le widget, débloquer l'input |
| `guided_tour` | `trigger_guided_tour` tool (spec 019) | `{tour_id, context?}` | `useGuidedTour.start(tour_id, context)` |
| `profile_update` | `update_user_profile` tool | `{field, value}` | Refresh `useCompanyProfile` |
| `profile_completion` | `profiling_node` | `{completion_pct}` | Toast "profil complété à X%" |
| `document_analysis_complete` | `analyze_uploaded_document` tool | `{document_id, summary}` | Notification |
| `done` | Fin de stream | `{}` | Scroll bas, icône "terminé" |
| `error` | Tout échec d'astream | `{message}` | Toast erreur |

### Marker SSE embarqué

Pour éviter un événement SSE distinct, certains payloads sont injectés **dans le flux token** via un marker HTML-commentaire scanné par le parser :

```
<!--SSE:{"__sse_interactive_question__":true,"payload":{...}}-->
```

Le parser de `useChat.ts` détecte ce pattern, extrait le JSON, l'émet en tant qu'événement `interactive_question`, et **retire le marker** du texte affiché. Cette technique préserve la compatibilité avec le streaming token-par-token de LangGraph `astream_events()`.

### Whitelist côté frontend

Pour sécuriser la consommation, seuls les types SSE dans la whitelist de [useChat.ts](../frontend/app/composables/useChat.ts) sont pris en compte. Tout autre type est ignoré silencieusement. Liste exhaustive : voir le composable (section `handleSSEEvent`).

## 5. Upload de fichiers

### Endpoints

| Endpoint | Rôle | Types acceptés |
|---|---|---|
| `POST /api/documents/upload` | Upload libre, déclenche extraction + OCR + embeddings | PDF, DOCX, XLSX |
| `POST /api/chat/conversations/{id}/messages` | Upload avec message (champ form `document_upload`) | Idem |

### Pipeline backend

```
Upload
  └─ Stockage local (backend/uploads/<user_id>/<doc_id>.<ext>)
  └─ Détection du type
  └─ Extraction texte :
       PDF → PyMuPDF (fitz) → fallback OCR pytesseract + pdf2image si texte vide
       DOCX → docx2txt
       XLSX → openpyxl
  └─ Chunking via LangChain text splitters
  └─ Embeddings OpenAI text-embedding-3-small → pgvector
  └─ Résumé LLM (Claude) injecté dans la conversation comme contexte
```

### Limite

`client_max_body_size 50M;` au niveau nginx (prod). Côté FastAPI, pas de limite stricte (mais `python-multipart` consomme de la mémoire).

## 6. Orchestration LangGraph (cœur backend)

### État partagé (`ConversationState`)

[backend/app/graph/state.py](../backend/app/graph/state.py) — TypedDict contenant :

- `messages` : liste `BaseMessage` (reducer `add_messages`).
- `user_id`, `user_profile`, `context_memory`, `profiling_instructions`.
- `document_upload`, `document_analysis_summary`, `has_document`.
- Sous-états par module : `esg_assessment`, `carbon_data`, `financing_data`, `application_data`, `credit_data`, `action_plan_data`, accompagnés chacun d'un flag routage `_route_<module>`.
- `tool_call_count` : compteur boucle (max 5).
- **`active_module` + `active_module_data`** (spec 013) : maintient le contexte entre les tours, permet la classification binaire continuation/changement par le router.
- **`current_page`** (spec 3) : injecté dans les prompts pour adaptation contextuelle.
- **`guidance_stats`** (spec 019) : `{refusal_count, acceptance_count}`, utilisé pour moduler la fréquence des propositions de tour.

### Graphe (simplifié)

```
START
  │
  ▼
router_node ────────── classification LLM : quel module ?
  │
  ├─→ esg_scoring_node        ────┐
  ├─→ carbon_node              ───┤
  ├─→ financing_node            ──┤
  ├─→ application_node           ─┤    Chaque nœud :
  ├─→ credit_node                ─┤    ├─ prompt spécialisé + STYLE + WIDGET + GUIDED_TOUR
  ├─→ action_plan_node           ─┤    ├─ invoke LLM (bind_tools)
  ├─→ document_node ──→ chat_node ┤    ├─ if tool_calls : ToolNode → ré-entre (max 5 iter)
  └─→ chat_node                  ─┘    └─ else : END
```

### Boucle tool calling

- Max 5 itérations par tour (MAX_TOOL_CALLS_PER_TURN).
- Retry 1x en cas d'échec de tool (spec 016).
- Chaque appel journalisé dans `tool_call_logs` (user_id, conversation_id, node_name, tool_name, args, result, status, duration_ms, retry_count, error_message).

## 7. Contexte de page courante (spec 3)

Le frontend envoie la page actuellement affichée dans chaque message :

```ts
formData.append('current_page', uiStore.currentPage);
```

Le backend stocke dans `ConversationState.current_page`, puis injecte dans les prompts spécialistes (ex. "L'utilisateur se trouve sur `carbon/results`, adapte ta réponse…"). Cela évite les incohérences du type "l'utilisateur demande si le bilan est sauvegardé alors qu'il le regarde à l'écran".

## 8. Tours guidés (spec 019)

Séquence complète :

```
1. L'utilisateur parle au copilote.
2. Le LLM décide d'utiliser trigger_guided_tour(tour_id="show_esg_results", context={…}).
3. Le tool émet un marker SSE : <!--SSE:{"__sse_guided_tour__":true, "payload":{…}}-->
4. useChat.ts détecte le marker → émet l'event `guided_tour`.
5. Une bulle de consentement (widget interactif QCU yes/no) apparaît avant déclenchement.
6. Sur acceptation, useGuidedTour.start(tour_id, context) déclenche :
     - Rétraction animée du widget chat (GSAP) → notifyRetractComplete()
     - Lazy-load driver.js (via useDriverLoader)
     - Navigation éventuelle vers la page cible (entryStep + route par step)
     - Polling DOM (3 essais × 500 ms ; soft timeout 5 s, hard 10 s)
     - Rendu du popover custom (GuidedTourPopover.vue)
     - Countdown adaptatif selon guidance_stats
7. Fin de tour → incrément acceptance_count → persisté localStorage (multi-tab sync via storage event).
```

Registre : [frontend/app/lib/guided-tours/registry.ts](../frontend/app/lib/guided-tours/registry.ts). 6 tours :
- `show_esg_results`, `show_carbon_results`, `show_financing_catalog`, `show_credit_score`, `show_action_plan`, `show_dashboard_overview`.

Marqueurs `data-guide-target` semés dans les composants cibles (14 emplacements à travers 7 fichiers).

## 9. Widgets interactifs (spec 018)

Format unique orchestré par le tool `ask_interactive_question`. Quatre variantes :

- `qcu` — choix unique.
- `qcm` — choix multiples (bornes `min_selections`, `max_selections`).
- `qcu_justification` — choix unique + texte libre (400 chars max).
- `qcm_justification` — choix multiple + texte libre (400 chars max).

Invariant : **une seule question `pending` par conversation**. Une nouvelle question invalide les précédentes (`state` passe à `expired`). La réponse peut aussi être fournie via message texte libre (bouton "Répondre autrement" → marquage `abandoned` + message normal). Persistance dans la table [`interactive_questions`](./data-models-backend.md#interactivequestion).

## 10. Observabilité

- Table `tool_call_logs` (spec 012) : audit exhaustif des tool calls LangChain. Indexée sur `(user_id, created_at)`, `(conversation_id)`, `(tool_name, status)`.
- Logs Python standard (`logging`) dans le backend, aucune stack (Loki/ELK) en place.
- Pas de métrique exposée (Prometheus) ni de tracing distribué (OpenTelemetry).

## 11. Limites connues

| Sujet | État | Détail |
|---|---|---|
| Rate limiting | ❌ | Aucun middleware. Risque à l'ouverture publique. |
| CORS multi-origines | ❌ | Codé en dur localhost:3000. OK tant que prod = même origine. |
| WebSocket bidirectionnel | ❌ | Non utilisé ; SSE unidirectionnel + polling suffisent actuellement. |
| Scheduler de rappels | ⚠️ | Les `reminders` sont stockés mais pas déclenchés par un worker cron. Affichage "on-demand" uniquement via `/action-plan/reminders/upcoming`. |
| Scan antivirus uploads | ❌ | Aucun. |
| Compression SSE | ❌ | Gzip désactivé sur le flux (pour éviter la mise en cache / buffering). |
| Tests d'intégration cross-parties | ⚠️ | Les E2E Playwright mockent le backend. L'équivalent "live" est le script shell `8-3-parcours-aminata.sh` — à étendre. |

Voir [technical-debt-backlog.md](./technical-debt-backlog.md) pour la priorisation.
