# Story 9.1 : Rate limiting FR-013 sur l'endpoint chat (SlowAPI, 30 msg/min/user)

Status: done

**Priorité** : P1 (sécurité — dette spec 002)
**Source** : [spec-audits/index.md §P1 #2](./spec-audits/index.md) & [spec-002-audit.md §3.1](./spec-audits/spec-002-audit.md)
**Spec d'origine** : [specs/002-chat-rich-visuals/spec.md FR-013](../../specs/002-chat-rich-visuals/spec.md)
**Durée estimée** : 3 à 5 h (install + code + tests + revue)

<!-- Note : Validation est optionnelle. Lancer `validate-create-story` pour un quality check avant `dev-story`. -->

---

## Story

En tant que **responsable de la plateforme Mefali**,
je veux que l'endpoint d'envoi de messages chat refuse les requêtes d'un même utilisateur au-delà de 30 messages par minute (réponse HTTP 429 avec header `Retry-After`),
afin de **protéger la plateforme contre les abus, contrôler le coût des tokens LLM pris en charge par Mefali, et honorer l'exigence fonctionnelle FR-013 déjà promise au frontend**.

## Contexte

- L'audit 2026-04-16 de la spec 002 a confirmé qu'aucune logique de rate limiting ni de réponse 429 n'existe dans [backend/app/api/chat.py](../../backend/app/api/chat.py) : `grep -n "rate|429|throttl"` ne retourne rien.
- Le frontend gère déjà une partie des 429 dans [frontend/app/composables/useChat.ts:574-577](../../frontend/app/composables/useChat.ts) — **uniquement pour la création de titre** de conversation. **Aucun handler 429 sur l'envoi de message**. AC5 ajoute ce handler.
- Vulnérabilité d'abuse : l'endpoint `/api/chat/conversations/{id}/messages` est exposé sans throttling. Chaque requête consomme des tokens LLM payés par Mefali.
- Endpoints réels ciblés (attention, l'énoncé d'origine écrivait « `/api/chat/messages` » — la route correcte est `/api/chat/conversations/{conversation_id}/messages` en SSE et `/api/chat/conversations/{conversation_id}/messages/json` en fallback JSON).

---

## Critères d'acceptation

1. **AC1** — Given un utilisateur authentifié, When il envoie 30 messages en moins de 60 s, Then le 31ᵉ renvoie `HTTP 429` **avec un header `Retry-After` en secondes**.
2. **AC2** — Given un utilisateur a atteint la limite, When 60 s se sont écoulées depuis la fenêtre, Then un nouveau message est accepté (code 200/SSE).
3. **AC3** — Given deux utilisateurs distincts (`user_A`, `user_B`) authentifiés, When `user_A` atteint 30 messages/minute, Then `user_B` n'est **pas** limité (**isolation par `user_id`, pas par IP**).
4. **AC4** — Given l'endpoint SSE `POST /api/chat/conversations/{id}/messages`, When le rate limiter déclenche, Then la réponse est `429` **avant l'ouverture du stream** (aucun `StreamingResponse`, aucun événement SSE envoyé).
5. **AC5** — Given le frontend reçoit `429` sur l'envoi d'un message chat, When il déchiffre le header `Retry-After`, Then il affiche le message « Trop de messages, réessayez dans X secondes » (où X est la valeur de `Retry-After`). **Le handler 429 pour la création de titre existe déjà à `useChat.ts:574` — il faut ajouter l'équivalent sur le chemin d'envoi de message dans `sendMessage()`.**
6. **AC6** — Given le second endpoint `POST /api/chat/conversations/{id}/messages/json`, When il est appelé, Then il applique le **même quota 30/minute/user** (pas de contournement par route alternative).
7. **AC7** — Given la configuration SlowAPI, When un utilisateur non authentifié (token absent ou invalide) tente d'envoyer un message, Then la réponse est `401` **avant** toute vérification de quota (le rate limiting s'applique aux utilisateurs authentifiés uniquement — pas de fallback IP globale).

---

## Tasks / Subtasks

- [x] **T1 — Dépendances (AC1, AC4)**
  - [x] Ajouter `slowapi>=0.1.9` à [backend/requirements.txt](../../backend/requirements.txt) (section LLM ou nouvelle section « Rate limiting »)
  - [x] Ajouter `freezegun>=1.5.0` à [backend/requirements-dev.txt](../../backend/requirements-dev.txt) (section Tests)
  - [x] `pip install -r backend/requirements-dev.txt` dans le venv (`source backend/venv/bin/activate`)

- [x] **T2 — Configuration du limiter (AC1, AC3, AC7)**
  - [x] Créer `backend/app/core/rate_limit.py` exposant :
    - une fonction `get_user_id_from_request(request: Request) -> str` qui extrait `request.state.user.id` (rempli par `get_current_user` via dépendance FastAPI)
    - `limiter = Limiter(key_func=get_user_id_from_request, default_limits=[], headers_enabled=True)`
    - Fallback : si `request.state.user` est absent, `get_remote_address(request)` est utilisé. En pratique `get_current_user` emet 401 avant le decorateur, donc cette branche ne compte pas comme requete utilisateur reelle.
    - **Ajout** : `headers_enabled=True` indispensable pour que le handler SlowAPI injecte le header `Retry-After` dans la reponse 429 (par defaut il ne le fait pas).
  - [x] Dans [backend/app/main.py](../../backend/app/main.py) :
    - Importer `limiter` et `_rate_limit_exceeded_handler` de SlowAPI
    - `app.state.limiter = limiter`
    - `app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)` (retourne 429 + `Retry-After`)
    - **Ne pas** ajouter `SlowAPIMiddleware` global — on applique le décorateur ciblé sur les 2 endpoints seulement, pour éviter de throttler `/api/auth/*`, `/api/health`, etc.
  - [x] Mise a jour `backend/app/api/deps.py` : ajout du parametre `request: Request` dans `get_current_user` + `request.state.user = user` avant le `return user`, afin que le key_func SlowAPI puisse lire l'identifiant utilisateur.

- [x] **T3 — Application du limiter sur les 2 endpoints messages (AC1, AC4, AC6)**
  - [x] Dans [backend/app/api/chat.py](../../backend/app/api/chat.py) :
    - Importer `limiter` depuis `app.core.rate_limit`
    - Ajouter le paramètre `request: Request` dans la signature des 2 endpoints
    - Décorer `send_message` avec `@limiter.limit("30/minute")`
    - Décorer `send_message_json` avec `@limiter.limit("30/minute")`
    - **Verification AC4** : le decorateur SlowAPI leve `RateLimitExceeded` avant le corps de la fonction → la reponse 429 est bien `JSONResponse(429)` et **aucun StreamingResponse** n'est cree.
    - **Verification double comptage** : slowapi utilise `request.state._rate_limiting_complete` (voir `extension.py:730`) pour detecter qu'un decorateur a deja tourne sur la meme requete — donc quand `send_message_json` appelle `send_message(...)` en interne, le deuxieme decorateur skippe la verification. **Pas de double comptage.**

- [x] **T4 — Frontend : handler 429 sur `sendMessage()` (AC5)**
  - [x] Dans [frontend/app/composables/useChat.ts](../../frontend/app/composables/useChat.ts) :
    - Ajout du bloc `if (response.status === 429) { ... }` apres le fetch d'envoi de message
    - Lecture de `response.headers.get('Retry-After')` avec validation `^\d+$` (fallback "patientez quelques instants" si absent ou non-numerique)
    - Message : `Trop de messages, réessayez dans ${retryAfter} secondes.` (ou fallback)
    - **Idempotence** : retrait du message utilisateur de `messages.value` via filtre par id (la requete a ete refusee, on ne doit pas laisser un message orphelin)
    - `isStreaming` est remis a `false` via le bloc `finally` existant

- [x] **T5 — Tests backend (AC1, AC2, AC3, AC6, AC7)**
  - [x] Dans [backend/tests/test_chat.py](../../backend/tests/test_chat.py), classe `TestRateLimit` avec 6 tests :
    - `test_rate_limit_trips_at_31st_message` (AC1) — 30 messages OK, 31e → 429 + Retry-After numerique
    - `test_rate_limit_returns_retry_after_header` (AC1) — verification explicite du header numerique > 0
    - `test_rate_limit_resets_after_60s` (AC2) — `freezegun.freeze_time` + tick 61s, le message suivant passe
    - `test_rate_limit_isolated_per_user` (AC3) — 2 users distincts, A epuise son quota, B passe en 200
    - `test_rate_limit_on_json_fallback_endpoint` (AC6) — meme test sur `/messages/json`
    - `test_rate_limit_unauthenticated_returns_401_not_429` (AC7) — sans token → 401 (pas 429)
  - [x] Mock de `stream_graph_events` + `async_session_factory` pour ne pas hitter la DB Postgres ni Claude

- [x] **T6 — Fixture conftest : reset du limiter entre tests**
  - [x] Fixture `reset_rate_limiter` (autouse) ajoutee dans `backend/tests/conftest.py`
  - [x] Verification : les 54 tests de `test_chat.py` + `test_auth.py` + `test_chat_document.py` + `test_chat_profiling.py` + `test_interactive_question_api.py` passent sans regression

- [x] **T7 — Tests frontend (AC5)**
  - [x] Fichier cree : `frontend/tests/composables/useChat.rateLimit.test.ts` — 4 tests Vitest
    - Retry-After=42 → message contient "42" + "seconde"
    - Sans Retry-After → fallback "Trop de messages, patientez quelques instants"
    - Idempotence : le message user refuse est retire de `messages.value`
    - Retry-After non-numerique (date HTTP) → fallback sans interpoler la date

- [x] **T8 — Quality gate**
  - [x] `pytest tests/test_chat.py::TestRateLimit -v` → **6/6 verts**
  - [x] `pytest tests/test_chat.py tests/test_auth.py tests/test_chat_document.py tests/test_chat_profiling.py tests/test_interactive_question_api.py` → **54/54 verts**
  - [x] `pytest tests/` → **1085 passed, 3 failed (preexistants, hors scope 9.1 : tests guided_tour sur longueur de prompt)**
  - [x] `npx vitest run tests/composables/useChat.*.test.ts` → **35/35 verts** (useChat.test.ts + connection + rateLimit)
  - [x] `ruff check app/core/rate_limit.py app/main.py app/api/deps.py app/api/chat.py tests/conftest.py` → **All checks passed**
  - [x] Revue manuelle : decorateur applique uniquement sur `send_message` et `send_message_json`. Les autres endpoints (`/api/auth/*`, `/api/health`, `/api/company/*`, etc.) ne sont **pas** impactes (pas de SlowAPIMiddleware global).

---

## Dev Notes

### Choix techniques — justifications

- **SlowAPI plutôt que middleware custom** : pkg léger, officiellement recommandé pour FastAPI, supporte Redis en backend si besoin de scale multi-process. Par défaut en in-memory (suffisant pour un process uvicorn unique en dev/staging). En production multi-worker, prévoir Redis dans un futur story (hors scope V1).
- **Key par `user_id` et pas par IP** : le projet cible des PME africaines qui partagent souvent des connexions (NAT, café internet, bureaux partagés). IP-based rate limiting créerait des faux positifs. Multi-device pour un même user reste légitime → key par `user_id` est la bonne granularité.
- **Décorateur ciblé vs middleware global** : appliquer `SlowAPIMiddleware` globalement appliquerait `default_limits` à toutes les routes, or on ne veut throttler QUE le chat. Utilisation de `@limiter.limit("30/minute")` endpoint par endpoint.
- **`Request` requis dans la signature** : SlowAPI inspecte `request.state.user` via le `key_func`. La dépendance `Depends(get_current_user)` doit s'exécuter **avant** le décorateur — en FastAPI, les dépendances passent avant l'exécution du corps, et SlowAPI accède à `request.state` après résolution des dépendances. Vérifier l'ordre en test AC7.

### Pièges à éviter

- **NE PAS oublier `request: Request` dans la signature** des 2 endpoints — sans ce paramètre, SlowAPI lève une erreur à l'import.
- **NE PAS ajouter `SlowAPIMiddleware`** globalement sans vérifier l'impact sur les autres endpoints (le frontend fait du polling sur `/api/action-plan/reminders` toutes les 60 s, voir spec 011).
- **NE PAS appliquer de quota IP-based** (fallback) si le key_func échoue — préférer laisser passer la requête, la dépendance `get_current_user` aura déjà retourné 401 si non authentifié.
- **NE PAS tester avec `time.sleep(60)`** dans les tests — utiliser `freezegun.freeze_time` pour contrôler le temps virtuellement. Sinon la CI prend 10 min pour 3 tests.
- **Attention au `send_message_json` qui appelle `send_message`** : le décorateur `@limiter.limit` sur `send_message` ne se redéclenche pas lors d'un appel Python direct (pas via HTTP routing), donc pas de double comptage. Mais appliquer le décorateur sur `send_message_json` aussi, sinon cet endpoint est non-protégé.
- **Handler 429 côté frontend existant** : [useChat.ts:574](../../frontend/app/composables/useChat.ts) n'est que pour la création de titre. Le handler pour `sendMessage()` n'existe pas encore → AC5 est un **ajout**, pas une vérification.

### Architecture actuelle — repères

- Les endpoints chat sont dans [backend/app/api/chat.py](../../backend/app/api/chat.py) (1103 lignes)
- Le router est monté avec préfixe `/api/chat` dans [backend/app/main.py:74](../../backend/app/main.py)
- La dépendance `get_current_user` se trouve dans [backend/app/api/deps.py:17](../../backend/app/api/deps.py) et popule `request.state.user` implicitement via le paramètre `current_user: User = Depends(get_current_user)`. Pour que SlowAPI puisse accéder au user via le key_func, il faudra soit écrire dans `request.state.user` depuis `get_current_user`, soit utiliser un key_func qui réinvoque la résolution du JWT. **Option retenue** : modifier `get_current_user` pour faire `request.state.user = user` avant le `return user` (1 ligne, non-breaking).

### Références

- [Source : specs/002-chat-rich-visuals/spec.md#FR-013](../../specs/002-chat-rich-visuals/spec.md) ligne 169 : « Le systeme DOIT limiter l'envoi a 30 messages par minute par utilisateur. »
- [Source : _bmad-output/implementation-artifacts/spec-audits/spec-002-audit.md#3.1](./spec-audits/spec-002-audit.md) : Cause racine + leçon
- [Source : _bmad-output/implementation-artifacts/spec-audits/index.md#P1-2](./spec-audits/index.md) : Action P1 #2 consolidée
- SlowAPI docs : https://slowapi.readthedocs.io/en/latest/ (section FastAPI + per-user key)
- Freezegun : https://github.com/spulec/freezegun (contrôle du temps virtuel pour tests)

---

## Hors scope (stories futures)

- Pas de dashboard admin pour ajuster les quotas par utilisateur (futur si besoin métier)
- Pas de tiering free/premium — V1 : tous les utilisateurs au même quota `30/minute`
- Pas de quota mensuel — uniquement par minute (FR-013)
- Pas de rate limit distribué Redis multi-worker — V1 : in-memory SlowAPI (suffisant < 5 uvicorn workers)
- Pas de rate limiting sur les autres endpoints coûteux (`/api/reports/generate`, `/api/action-plan/generate`) — couvert par la dette P1 #6 « Queue asynchrone pour opérations longues » dans un autre story

---

## Structure projet — alignement

- **Nouveau fichier** : `backend/app/core/rate_limit.py` — cohérent avec la convention `backend/app/core/` (à côté de `config.py`, `database.py`, `security.py`)
- **Fichiers modifiés** :
  - `backend/app/main.py` — init limiter (< 10 lignes ajoutées)
  - `backend/app/api/chat.py` — 2 décorateurs + 2 params `request: Request` (< 15 lignes)
  - `backend/app/api/deps.py` — 1 ligne pour `request.state.user = user`
  - `backend/requirements.txt` — 1 ligne `slowapi>=0.1.9`
  - `backend/requirements-dev.txt` — 1 ligne `freezegun>=1.5.0`
  - `backend/tests/conftest.py` — fixture `reset_rate_limiter`
  - `backend/tests/test_chat.py` — classe `TestRateLimit` (~100 lignes, 6 tests)
  - `frontend/app/composables/useChat.ts` — gestion 429 dans `sendMessage()` (~10 lignes)
  - `frontend/tests/unit/useChat.test.ts` — 1 test Vitest 429 (fichier à créer si absent)
- **Conventions respectées** : snake_case Python, Pydantic v2, FastAPI router pattern, test pytest async, dark mode non-impacté (pas d'UI nouvelle, juste un message d'erreur existant).

---

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7 (1M context) — `claude-opus-4-7[1m]`

### Debug Log References

- `pytest tests/test_chat.py::TestRateLimit -v` : 6/6 passed (8.37s)
- `pytest tests/test_chat.py tests/test_auth.py tests/test_chat_document.py tests/test_chat_profiling.py tests/test_interactive_question_api.py -q` : 54/54 passed (57.57s)
- `pytest tests/` : 1085 passed, 3 failed. Les 3 echecs (test_guided_tour_instruction_unchanged + 2 test_guided_tour_consent_flow) sont preexistants sur `main@99f2fb4` et non lies a la story 9.1 (verifie via `git stash + run`).
- `npx vitest run tests/composables/useChat.*.test.ts` : 35/35 passed (618ms)
- `ruff check` sur les fichiers modifies : All checks passed

### Completion Notes List

**Story 9.1 — Rate limiting FR-013 chat endpoint (2026-04-17)**

- Integration SlowAPI en cle `user_id` (non IP — evite faux positifs sur NAT/connexions partagees PME africaines)
- 2 endpoints couverts : `POST /api/chat/conversations/{id}/messages` (SSE) + `/messages/json` (fallback)
- Handler 429 avec header `Retry-After` (active via `headers_enabled=True` sur le Limiter — **point manquant dans les specs, decouvert en RED phase** : par defaut SlowAPI n'injecte pas ce header)
- Frontend : handler 429 idempotent dans `sendMessage()` (retire le message utilisateur refuse, affiche "Trop de messages, réessayez dans X secondes")
- Fixture `reset_rate_limiter` (autouse) dans conftest.py → aucune fuite d'etat entre tests
- Aucun double comptage : slowapi utilise `request.state._rate_limiting_complete` pour les appels Python imbriques (`send_message_json → send_message`)
- `get_current_user` expose `request.state.user` pour que le key_func SlowAPI lise l'identifiant utilisateur (modification 1 ligne, non-breaking)

**Edge cases verifies** :

- Utilisateur non authentifie → 401 avant tout decompte (AC7)
- Fenetre glissante 60s : 31e message bloque, reset apres 61s (AC1/AC2 via freezegun)
- Isolation par user : quotas independants entre users (AC3)
- Fallback JSON : meme quota 30/min (AC6)
- AC4 : la reponse 429 est `JSONResponse` pur, pas de stream SSE ouvert

**Hors scope** : pas de Redis (in-memory suffisant < 5 workers, V1). Pas de tiering free/premium. Pas de dashboard admin. Pas de quotas mensuels. Rate limiting des autres endpoints couteux (reports/action-plan) reporte au story P1 #6 « Queue asynchrone ».

### File List

**Nouveaux fichiers** :
- `backend/app/core/rate_limit.py` — Limiter SlowAPI + key_func user_id
- `backend/tests/` : pas de nouveau fichier (tests ajoutes dans `test_chat.py`)
- `frontend/tests/composables/useChat.rateLimit.test.ts` — 4 tests Vitest AC5

**Fichiers modifies** :
- `backend/app/main.py` — init `app.state.limiter` + exception handler RateLimitExceeded
- `backend/app/api/deps.py` — `request: Request` param + `request.state.user = user`
- `backend/app/api/chat.py` — import `limiter`, `request: Request` + `@limiter.limit("30/minute")` sur `send_message` et `send_message_json`
- `backend/requirements.txt` — ajout `slowapi>=0.1.9`
- `backend/requirements-dev.txt` — ajout `freezegun>=1.5.0`
- `backend/tests/conftest.py` — fixture `reset_rate_limiter` (autouse)
- `backend/tests/test_chat.py` — classe `TestRateLimit` (~180 lignes, 6 tests)
- `frontend/app/composables/useChat.ts` — handler 429 dans `sendMessage()` (bloc ~14 lignes)

### Change Log

- 2026-04-17 — Implementation complete rate limiting FR-013 (6+4 tests, 0 regression). Status `in-progress → review`.

---

### Review Findings

Code review adversariale parallèle (Blind Hunter + Edge Case Hunter + Acceptance Auditor) — 2026-04-17.

- [x] [Review][Decision → Patch] Contradiction interne de la spec sur le fallback IP du `key_func` — Résolue 2026-04-17 par choix utilisateur (option 3 : fail-fast `RuntimeError`). Le fallback `get_remote_address` est retiré. `get_user_id_from_request` lève désormais `RuntimeError` si `request.state.user` est absent (invariant : tout endpoint décoré DOIT déclarer `Depends(get_current_user)`). [backend/app/core/rate_limit.py:21-36]
- [x] [Review][Patch] Garde défensive sur `user.id` dans le key_func (raise `RuntimeError` si None) [backend/app/core/rate_limit.py:31-35]
- [x] [Review][Patch] `_send_one_message` draine le body sur tous les status (évite la fuite HTTPX pool sur 429/401) [backend/tests/test_chat.py:470-473]
- [x] [Review][Patch] Pluriel conditionnel « seconde/secondes » pour `Retry-After: 1` [frontend/app/composables/useChat.ts:284-288]
- [x] [Review][Patch] AC4 verrouillé : assertion `content-type != text/event-stream` sur la réponse 429 [backend/tests/test_chat.py::test_rate_limit_trips_at_31st_message]
- [x] [Review][Defer] Pas de limiter Redis multi-worker — explicitement hors scope V1 (story « Hors scope ») [backend/app/core/rate_limit.py]
- [x] [Review][Defer] Pas de log/métrique émis sur les 429 (observabilité abuse prevention) [backend/app/main.py]
- [x] [Review][Defer] Import du symbole privé `_rate_limit_exceeded_handler` depuis slowapi (surface non stable, à pin narrow) [backend/app/main.py:9]
- [x] [Review][Defer] Upload de fichier volumineux consommé avant que le 429 ne tire (gaspillage bande passante) [backend/app/api/chat.py:send_message]
- [x] [Review][Defer] Rate-limit avant validation d'input : les requêtes invalides consomment quota (comportement standard) [backend/app/api/chat.py:send_message]
- [x] [Review][Defer] Déconnexion SSE mid-stream laisse le quota décompté (pas de refund) [backend/app/api/chat.py:976-983]
- [x] [Review][Defer] Double-clic utilisateur pendant fenêtre 429 : pas de cooldown côté client (UX enhancement) [frontend/app/composables/useChat.ts:279-289]
- [x] [Review][Defer] Nettoyage partiel sur 429 : `documentProgress`, `activeToolCall`, `abortController` pas explicitement réinitialisés (le `finally` couvre `isStreaming` seulement) [frontend/app/composables/useChat.ts:279-289]
- [x] [Review][Defer] Input utilisateur perdu sur 429 (pas de préservation dans le composer pour retry) — l'idempotence AC5 retire le message de la liste [frontend/app/composables/useChat.ts:287]
- [x] [Review][Defer] Headers `X-RateLimit-Remaining`/`X-RateLimit-Limit` émis (via `headers_enabled=True`) mais ignorés côté frontend (UX proactive inutilisée) [frontend/app/composables/useChat.ts]

**Dismissed (29)** : incluant notamment : signature `get_current_user` breaking (aucun appel positional, tous via `Depends`), double-counting JSON fallback (empiriquement contré par `test_rate_limit_on_json_fallback_endpoint`), fixture autouse `limiter.reset()` (reset cheap, pas de dépendance), ordre CORS + exception handler (CORSMiddleware outside ExceptionMiddleware, headers appliqués correctement), freezegun + JWT (access_token_expire 480 min, tick 61s négligeable), stub tests avec `...` (faux positif du diff abrégé, code complet vérifié en `test_chat.py:565-640+`).
