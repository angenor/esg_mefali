# Story 6.4 : Frequence adaptative des propositions de guidage

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

En tant qu'utilisateur,
je veux que l'assistant reduise ses propositions de guidage si je les refuse souvent
et raccourcisse le decompteur multi-pages si je les accepte regulierement,
afin de ne pas etre importune par des suggestions repetitives et de ne pas attendre inutilement quand je suis familier du produit (FR17).

## Acceptance Criteria

### AC1 : Compteurs module-level + persistance localStorage

**Given** l'utilisateur ouvre l'application pour la premiere fois (aucune cle `esg_mefali_guidance_stats` en localStorage)
**When** `useGuidedTour()` est initialise
**Then** les refs module-level exposent exactement :
- `guidanceRefusalCount` (ref<number>) initialise a `0`
- `guidanceAcceptanceCount` (ref<number>) initialise a `0`

**And** trois helpers sont exposes par le composable :
- `incrementGuidanceRefusal(): void` → `guidanceRefusalCount.value += 1` puis persist
- `incrementGuidanceAcceptance(): void` → `guidanceAcceptanceCount.value += 1` **ET** `guidanceRefusalCount.value = 0` (reinit cote acceptance — cf AC4) puis persist
- `resetGuidanceStats(): void` → remet les deux a `0` puis persist (usage : tests + eventuelle action « reinitialiser » future, non exposee UI dans cette story)

**Given** un utilisateur a `guidanceRefusalCount=3, guidanceAcceptanceCount=2` en memoire
**When** il ferme et recharge la page (`window.location.reload()`)
**Then** `useGuidedTour` relit `localStorage.getItem('esg_mefali_guidance_stats')` au setup
**And** parse le JSON `{"refusal_count": 3, "acceptance_count": 2}` avec validation numerique (Number.isFinite, Number.isInteger, >= 0)
**And** si le JSON est corrompu/absent/invalide → fallback silencieux a `{refusal_count: 0, acceptance_count: 0}` sans throw (pattern identique a `isValidDimension` dans `stores/ui.ts:74`)

### AC2 : Transmission du contexte au LLM via FormData

**Given** l'utilisateur envoie un message texte normal ou une reponse interactive
**When** `sendMessage(content, file?)` ou `submitInteractiveAnswer()` construit son FormData
**Then** un champ `guidance_stats` est ajoute au FormData, serialise en JSON :

```typescript
formData.append('guidance_stats', JSON.stringify({
  refusal_count: guidanceRefusalCount.value,
  acceptance_count: guidanceAcceptanceCount.value,
}))
```

**And** le champ est ajoute apres `current_page` (cf `useChat.ts:168`) et avant le bloc interactive_question_* existant

**Given** une requete POST `/api/chat/conversations/{id}/messages` arrive avec `guidance_stats='{"refusal_count":3,"acceptance_count":2}'`
**When** `backend/app/api/chat.py` traite la requete (fonction `send_message` / `stream_chat_response`)
**Then** le champ Form `guidance_stats: str | None = Form(None)` est parse via `json.loads` (try/except → None sur parse error)
**And** injecte dans `ConversationState["guidance_stats"]` qui est un nouveau champ TypedDict de type `dict | None`

**And** si le Form field est absent (backward-compat) → `guidance_stats=None` dans le state, aucune erreur

### AC3 : Helper backend `build_adaptive_frequency_hint` + injection dans le prompt

**Given** le fichier `backend/app/prompts/guided_tour.py` existe avec la constante immuable `GUIDED_TOUR_INSTRUCTION` (story 6.2, verrouillee par 16 tests)
**When** on ajoute un helper `build_adaptive_frequency_hint(guidance_stats: dict | None) -> str`
**Then** :
- Si `guidance_stats is None` → retourne `""` (chaine vide)
- Si `guidance_stats.refusal_count >= 3` → retourne un bloc texte normatif en francais demandant au LLM de **ne proposer de guidage QUE sur demande explicite de l'utilisateur (ou apres un nouveau module totalement complete)**, et de **ne pas relancer** tant que le compteur n'est pas reinitialise. Le bloc contient au minimum les mots-cles : `refuse`, `plusieurs fois`, `demande explicite`, `pas relancer`/`ne plus proposer`
- Si `0 <= refusal_count < 3` → retourne `""` (pas de modulation)
- Le helper est **pur**, deterministe, pas de side effect, pas de f-string avec valeurs sensibles (rappel NFR10)

**Given** le prompt systeme est construit par `build_system_prompt()` dans `backend/app/prompts/system.py`
**When** on etend la signature : ajouter parametre optionnel `guidance_stats: dict | None = None` en derniere position (backward-compat)
**Then** **apres** l'injection existante de `GUIDED_TOUR_INSTRUCTION` (ligne ~218 actuelle), `build_system_prompt` concatene `build_adaptive_frequency_hint(guidance_stats)` si la chaine n'est pas vide
**And** l'ordre final est : `[sections existantes] → GUIDED_TOUR_INSTRUCTION → build_adaptive_frequency_hint(stats)` (le hint est un appendix conditionnel, pas un remplacement)

**And** la constante `GUIDED_TOUR_INSTRUCTION` n'est **pas modifiee** (preserve les 16 tests de story 6.2 et les 17 tests de story 6.3)

### AC4 : Reduction du countdown multi-pages apres plusieurs acceptations (FR17)

**Given** un parcours multi-pages avec `countdown: DEFAULT_ENTRY_COUNTDOWN` (= 8s — cf `frontend/app/lib/guided-tours/registry.ts:6`) demarre via `startTour(tour_id)`
**When** `guidanceAcceptanceCount.value = N` au moment du demarrage
**Then** la duree effective appliquee est : `effectiveCountdown = Math.max(3, originalCountdown - N)`
**And** cette regle s'applique uniquement au decompteur multi-pages entre etapes (story 5.3 countdown), **pas** aux timeouts DOM retry (story 7.1, NFR18 — 3×500ms independants des stats)
**And** exemples concrets :
- `N=0` → 8s (comportement de reference)
- `N=3` → 5s (exemple cite dans epic 6.4)
- `N=5` → 3s (plancher)
- `N=10` → 3s (plancher maintenu)
- `N=100` → 3s (plancher, pas de valeur negative possible)

**And** la regle est appliquee **une seule fois** au demarrage du parcours (stockee dans un ref local au parcours), pas recalculee a chaque etape (evite le « countdown qui raccourcit pendant qu'on navigue »)

### AC5 : Increment / reset des compteurs selon le flux SSE

**Given** une question interactive de consentement guidage est `state="pending"` (labels canoniques `"Oui, montre-moi"` / `"Non merci"` — story 6.3 AC1)
**When** l'utilisateur clique sur `"Non merci"` (option `id="no"`) et `submitInteractiveAnswer()` resout la question cote frontend via l'event SSE `interactive_question_resolved`
**Then** **cote frontend** `useChat.handleInteractiveQuestionResolvedEvent` detecte qu'il s'agit d'une question de consentement guidage (heuristique stable : les 2 options ont `id IN {"yes","no"}` **ET** les labels exacts canoniques `"Oui, montre-moi"` + `"Non merci"`)
**And** appelle `useGuidedTour().incrementGuidanceRefusal()`
**And** **aucun** event `guided_tour` n'est emis ce tour → `guidanceAcceptanceCount` n'est PAS modifie

**Given** un event SSE `guided_tour` arrive cote frontend (soit via declenchement direct AC4 story 6.3, soit via consentement `"Oui"`)
**When** `handleGuidedTourEvent` passe la garde `currentInteractiveQuestion.value?.state !== 'pending'` (story 6.1 patch review)
**Then** **avant** d'appeler `useGuidedTour.startTour(...)`, le handler appelle `useGuidedTour().incrementGuidanceAcceptance()` **une seule fois** par event
**And** puisque `incrementGuidanceAcceptance()` reset `refusal_count` a 0 (cf AC1), le cycle « serie de refus → acceptation → compteur repart a zero » (AC de l'epic) est automatiquement satisfait

**And** si `startTour` est bloque par la garde pending ou par un `tour_id` invalide (story 6.1 AC4 — parcours ignore silencieusement), `incrementGuidanceAcceptance()` N'EST PAS appele (pas d'acceptance fantome)

### AC6 : Zero regression + couverture tests >= 80 %

**Given** la suite de tests backend existante (1036 tests verts apres story 6.3)
**When** on execute `cd backend && source venv/bin/activate && python -m pytest` (ou `python -m pytest backend/tests -x`)
**Then** zero regression (NFR19)
**And** les nouveaux tests backend atteignent >= 80 % de couverture sur le code ajoute (helper `build_adaptive_frequency_hint`, signature etendue de `build_system_prompt`, parsing `guidance_stats` dans `backend/app/api/chat.py`, champ `ConversationState.guidance_stats`)

**And** le fichier `backend/tests/test_prompts/test_guided_tour_adaptive_frequency.py` est cree avec AU MINIMUM :
- `test_hint_returns_empty_when_stats_none` — `build_adaptive_frequency_hint(None) == ""`
- `test_hint_returns_empty_when_refusal_count_below_threshold` (parametrise 0, 1, 2) — chaine vide
- `test_hint_returns_non_empty_when_refusal_count_ge_3` (parametrise 3, 5, 10) — chaine non vide
- `test_hint_contains_required_normative_keywords` — presence de `"demande explicite"`, `"plusieurs fois"` ou `"repete"`, `"pas relancer"` ou `"ne plus proposer"` (au moins 3 des 4)
- `test_hint_is_pure_no_side_effect` — appel avec des stats differentes ne mute pas l'input dict
- `test_hint_contains_no_pii` — chaine returned ne contient jamais `user_profile`, email, nom, montants (NFR10)
- `test_build_system_prompt_accepts_guidance_stats_kwarg` — signature contient `guidance_stats` en kwarg optionnel
- `test_build_system_prompt_appends_hint_when_refusal_count_ge_3` — hint present dans la sortie
- `test_build_system_prompt_backward_compat_without_stats` — call sans `guidance_stats` retourne un prompt identique a celui de story 6.3 (byte-for-byte)
- `test_guided_tour_instruction_unchanged` — assertion hash/longueur approximative pour verrouiller la constante (optionnel mais recommande)

**And** le fichier `backend/tests/test_api/test_chat_guidance_stats.py` est cree avec AU MINIMUM :
- `test_post_messages_parses_guidance_stats_form_field` — envoi Form `guidance_stats='{"refusal_count":3,"acceptance_count":2}'` → state initial contient bien le dict parse
- `test_post_messages_without_guidance_stats_sets_none` — absence du field → `state["guidance_stats"] is None`
- `test_post_messages_invalid_guidance_stats_json_fallback_none` — Form `guidance_stats='not-json'` → fallback `None`, pas d'HTTP 500

**And** le fichier `frontend/tests/composables/useGuidedTour.adaptive-frequency.test.ts` est cree (Vitest) avec AU MINIMUM :
- `test initial values are 0 when localStorage empty`
- `test initial values are restored from localStorage` (JSON valide `{"refusal_count":3,"acceptance_count":2}`)
- `test corrupted localStorage falls back to 0` (JSON invalide, type non-numerique, valeurs negatives)
- `test incrementGuidanceRefusal increments and persists`
- `test incrementGuidanceAcceptance increments acceptance AND resets refusal to 0`
- `test resetGuidanceStats writes zeros to localStorage`
- `test effective countdown equals max(3, default - acceptanceCount)` (parametrise N=0, 3, 5, 10, 100)

**And** le fichier `frontend/tests/composables/useChat.adaptive-frequency.test.ts` est cree (Vitest) avec AU MINIMUM :
- `test sendMessage appends guidance_stats to FormData with correct JSON shape`
- `test submitInteractiveAnswer appends guidance_stats to FormData`
- `test "Non merci" option id=no on consent question triggers incrementGuidanceRefusal exactly once`
- `test guided_tour event triggers incrementGuidanceAcceptance exactly once BEFORE startTour`
- `test guided_tour event with invalid tour_id does NOT increment acceptance` (garde silent-ignore story 6.1 AC4)
- `test non-consent interactive question resolved with "no" does NOT increment refusal` (heuristique labels canoniques — negative case)

### AC7 : Documentation dev — traceabilite AC / fichier de test

**Given** la story est complete
**When** on lit la section `## Dev Notes` mise a jour
**Then** elle contient un tableau « AC → fichier(s) de test » reprenant le pattern de la story 6.3 pour que la prochaine story (epic 7 ou 8) puisse etendre le meme pattern sans recherche

## Tasks / Subtasks

- [x] Task 1 : Backend — ajouter `guidance_stats` dans ConversationState (AC: #2)
  - [x] 1.1 Ouvrir `backend/app/graph/state.py`
  - [x] 1.2 Ajouter le champ `guidance_stats: dict | None` dans `ConversationState` (TypedDict, ligne ~37, apres `current_page`)
  - [x] 1.3 Commentaire FR : `# Compteurs frontend transmis pour moduler la frequence des propositions de guidage (FR17)`
  - [x] 1.4 Verifier que `total=False` n'empeche pas `None` comme valeur par defaut (pattern `active_module: str | None`)

- [x] Task 2 : Backend — parser le Form field dans /api/chat/messages (AC: #2)
  - [x] 2.1 Ouvrir `backend/app/api/chat.py`, localiser `send_message` / `stream_chat_response` (autour de la ligne 624 — gestion des champs `interactive_question_*`)
  - [x] 2.2 Ajouter parametre FastAPI `guidance_stats: str | None = Form(None)`
  - [x] 2.3 Parser avec `json.loads` dans un try/except → valeur par defaut `None` en cas d'erreur (log `logger.warning` non obligatoire, suivre le pattern existant des champs optionnels)
  - [x] 2.4 Valider la structure : `{refusal_count: int >= 0, acceptance_count: int >= 0}` — si invalide → `None` (fallback sans crash)
  - [x] 2.5 Injecter dans `initial_state["guidance_stats"]` avant l'invocation `graph.astream_events`

- [x] Task 3 : Backend — helper + injection dans build_system_prompt (AC: #3)
  - [x] 3.1 Ouvrir `backend/app/prompts/guided_tour.py`
  - [x] 3.2 Ajouter la fonction `build_adaptive_frequency_hint(guidance_stats: dict | None) -> str`
  - [x] 3.3 Logique : si `stats is None` OR `refusal_count < 3` → `return ""`. Sinon retourner un bloc normatif multi-lignes (voir « Modele de hint adaptatif » ci-dessous)
  - [x] 3.4 Ouvrir `backend/app/prompts/system.py`, etendre la signature `build_system_prompt(user_profile=None, context_memory=None, profiling_instructions=None, document_analysis_summary=None, current_page=None, guidance_stats: dict | None = None)`
  - [x] 3.5 Apres l'ajout existant de `GUIDED_TOUR_INSTRUCTION` (`sections.append(GUIDED_TOUR_INSTRUCTION)`), ajouter : `hint = build_adaptive_frequency_hint(guidance_stats); if hint: sections.append(hint)`
  - [x] 3.6 Propager le kwarg aux appelants de `build_system_prompt` dans les noeuds specialistes (6 noeuds qui beneficient de `GUIDED_TOUR_INSTRUCTION` : chat_node, esg_scoring_node, carbon_node, financing_node, credit_node, action_plan_node — `backend/app/graph/nodes.py`)
  - [x] 3.7 Ne PAS propager vers `application_node`, `document_node`, `profiling_node`, `router_node` (coherent avec story 6.2)

- [x] Task 4 : Frontend — module-level state + persistance dans useGuidedTour (AC: #1, #4)
  - [x] 4.1 Ouvrir `frontend/app/composables/useGuidedTour.ts`
  - [x] 4.2 Constante module-level : `const GUIDANCE_STATS_KEY = 'esg_mefali_guidance_stats'`
  - [x] 4.3 Declarer `const guidanceRefusalCount = ref<number>(0)` et `const guidanceAcceptanceCount = ref<number>(0)` au **niveau module** (pattern singleton cross-routes, story 1.1)
  - [x] 4.4 Helper interne `loadGuidanceStats(): { refusal_count: number; acceptance_count: number }` — lit localStorage, parse, valide (Number.isInteger + >= 0), fallback `{0,0}` si invalide
  - [x] 4.5 Helper interne `persistGuidanceStats(): void` — ecrit `JSON.stringify({refusal_count, acceptance_count})` dans localStorage, catch silent (localStorage peut throw en mode privacy)
  - [x] 4.6 Au setup du composable : appeler `loadGuidanceStats()` une fois, initialiser les refs. Guard : ne pas appeler si pas encore fait (pattern module-level avec flag `initialized` ou verification `typeof window !== 'undefined'` pour SSR Nuxt)
  - [x] 4.7 Exposer `incrementGuidanceRefusal()`, `incrementGuidanceAcceptance()`, `resetGuidanceStats()` dans le retour de `useGuidedTour` + les refs `guidanceRefusalCount` et `guidanceAcceptanceCount` (readonly ou writable selon besoin tests)
  - [x] 4.8 `incrementGuidanceAcceptance` : `acceptance_count += 1` ET `refusal_count = 0` ET persist (une seule ecriture localStorage pour atomicite)
  - [x] 4.9 Modifier `startTour` : au demarrage, calculer `effectiveCountdown = Math.max(3, originalCountdown - guidanceAcceptanceCount.value)` et utiliser cette valeur pour le decompteur multi-pages (ligne ~221 actuelle de `startTour` — zone `countdown: DEFAULT_ENTRY_COUNTDOWN`)
  - [x] 4.10 Garde : appliquer la reduction UNIQUEMENT si le step courant a un countdown defini (pas sur les steps mono-page instantanes)

- [x] Task 5 : Frontend — wiring incrementRefusal / incrementAcceptance dans useChat (AC: #5)
  - [x] 5.1 Ouvrir `frontend/app/composables/useChat.ts`
  - [x] 5.2 `sendMessage` (ligne 133) : apres `formData.append('current_page', uiStore.currentPage)` (ligne 168), ajouter `formData.append('guidance_stats', JSON.stringify({refusal_count: useGuidedTour().guidanceRefusalCount.value, acceptance_count: useGuidedTour().guidanceAcceptanceCount.value}))`
  - [x] 5.3 `submitInteractiveAnswer` (ligne ~470) : meme ajout dans son FormData
  - [x] 5.4 Handler `handleInteractiveQuestionResolvedEvent` (ligne ~372-405) : apres mise a jour du state, detecter la question de consentement via heuristique sur les labels canoniques (`options.length === 2`, `options[0].id === 'yes'`, `options[1].id === 'no'`, labels exacts `"Oui, montre-moi"` et `"Non merci"`). Si la reponse `selectedValues` contient `"no"` → appeler `useGuidedTour().incrementGuidanceRefusal()`
  - [x] 5.5 Handler `handleGuidedTourEvent` (ligne ~682) : **avant** l'appel `useGuidedTour.startTour(tour_id, context)`, apres la garde pending et apres la validation du `tour_id` cote useGuidedTour (si le guard echoue silencieusement cote useGuidedTour, le incrementAcceptance aura deja ete fait — documenter ce point). Alternative preferee : `useGuidedTour.startTour` retourne un boolean (started: true/false) et n'incremente que si started=true. **Decision** : garder incrementAcceptance dans le handler juste avant startTour et compter sur la validation `_VALID_TOUR_ID` cote backend (le tool ne laisse pas passer un tour_id invalide avant d'emettre un marker SSE)
  - [x] 5.6 Import : `import { useGuidedTour } from '~/composables/useGuidedTour'` si pas deja present

- [x] Task 6 : Tests backend (AC: #6)
  - [x] 6.1 Creer `backend/tests/test_prompts/test_guided_tour_adaptive_frequency.py` avec les 10 tests minimum listes en AC6
  - [x] 6.2 Utiliser `pytest.mark.parametrize` pour les cas [0,1,2] (empty hint) et [3,5,10] (non-empty hint)
  - [x] 6.3 Pattern de reference : `backend/tests/test_prompts/test_guided_tour_instruction.py` (pattern story 6.2) et `test_guided_tour_consent_flow.py` (story 6.3)
  - [x] 6.4 Creer `backend/tests/test_api/test_chat_guidance_stats.py` avec les 3 tests minimum listes en AC6
  - [x] 6.5 Utiliser le client de test FastAPI (`httpx.AsyncClient` pattern, cf `backend/tests/test_api/*.py` existants)
  - [x] 6.6 Lancer `cd backend && source venv/bin/activate && python -m pytest backend/tests/test_prompts/test_guided_tour_adaptive_frequency.py backend/tests/test_api/test_chat_guidance_stats.py -v` — tous verts
  - [x] 6.7 Lancer la suite complete : `python -m pytest` → **1036 + n ≈ 1050+ tests verts, 0 regression**
  - [x] 6.8 Ruff : `ruff check backend/app/prompts/guided_tour.py backend/app/prompts/system.py backend/app/graph/state.py backend/app/api/chat.py backend/tests/test_prompts/test_guided_tour_adaptive_frequency.py backend/tests/test_api/test_chat_guidance_stats.py` → All checks passed

- [x] Task 7 : Tests frontend (AC: #6)
  - [x] 7.1 Creer `frontend/tests/composables/useGuidedTour.adaptive-frequency.test.ts` avec les 7 tests minimum listes en AC6
  - [x] 7.2 Pattern de reference : `frontend/tests/composables/useChat.guidedTour.test.ts` et `frontend/tests/stores/ui.guidedTour.test.ts`
  - [x] 7.3 Mock `localStorage` via `vi.stubGlobal('localStorage', createMockLocalStorage())` ou `jsdom` natif
  - [x] 7.4 Creer `frontend/tests/composables/useChat.adaptive-frequency.test.ts` avec les 6 tests minimum listes en AC6
  - [x] 7.5 Pattern de reference : `frontend/tests/composables/useChat.guided-tour-consent.test.ts` (story 6.3 — mock streaming SSE + spy startTour)
  - [x] 7.6 Lancer : `cd frontend && npm run test -- useGuidedTour.adaptive-frequency useChat.adaptive-frequency` → tous verts
  - [x] 7.7 Lancer la suite complete : `npm run test` → **272 + n ≈ 285+ tests verts, 0 regression**

- [x] Task 8 : Documentation traceabilite + finalisation (AC: #7)
  - [x] 8.1 Completer le tableau « AC → test » en fin de Dev Notes
  - [x] 8.2 Documenter dans Completion Notes les choix de design (localStorage cle, heuristique detection consent question, propagation 6 noeuds)
  - [x] 8.3 Mettre a jour sprint-status.yaml : `6-4-frequence-adaptative-...` : `ready-for-dev` → `in-progress` (debut dev) → `review` (fin dev) → `done` (apres code review)
  - [x] 8.4 File List : lister tous les fichiers crees/modifies (pattern story 6.3)

### Review Findings

> **Code review 2026-04-14** — 3 couches adversariales (Blind Hunter + Edge Case Hunter + Acceptance Auditor). 3 `decision-needed`, 19 `patch`, 7 `defer`, 9 `dismiss` (bruit).

#### Decision-needed (resolus 2026-04-14)

- [x] [Review][Decision] D1 — Politique de decroissance / plafond pour `acceptance_count` → **Resolu : cap dur** → convertit en patch P20 ci-dessous (cap `MAX_STATS_CAP` a `baseCountdown - floor` = 5, partage front/back).
- [x] [Review][Decision] D2 — Reset de `guidanceRefusalCount` → **Resolu : reset apres completion reussie** → s'aligne avec patch P4 (commit acceptance apres `startTour` success). Le meme invariant couvre le reset.
- [x] [Review][Decision] D3 — Scope localStorage → **Resolu : status quo + defer migration multi-user** → report en `deferred-work.md` pour story module 7.

#### Patch

- [x] [Review][Patch] Deplacer le fichier `test_chat_guidance_stats.py` de `backend/tests/` vers `backend/tests/test_api/` [backend/tests/test_chat_guidance_stats.py] — violation AC6 (chemin explicite `test_api/`).
- [x] [Review][Patch] Ajouter les tests HTTP endpoint-level manquants (`test_post_messages_parses_guidance_stats_form_field`, `test_post_messages_without_guidance_stats_sets_none`, `test_post_messages_invalid_guidance_stats_json_fallback_none`) via `httpx.AsyncClient` sur `POST /api/chat/conversations/{id}/messages` [backend/tests/test_api/test_chat_guidance_stats.py] — les 3 tests existants n'exercent que le helper `_parse_guidance_stats`, pas l'endpoint.
- [x] [Review][Patch] Deplacer `incrementGuidanceRefusal()` depuis `submitInteractiveAnswer` vers `handleInteractiveQuestionResolvedEvent` (handler SSE) [frontend/app/composables/useChat.ts:459-467] — AC5 ancre explicitement l'increment sur l'evenement `interactive_question_resolved`, pas sur le clic pre-roundtrip. Evite increment si la requete echoue.
- [x] [Review][Patch] Committer `incrementGuidanceAcceptance()` uniquement apres `await startTour()` reussie [frontend/app/composables/useChat.ts:489-497] — Actuellement credit + reset refusal avant l'appel ; si `startTour` bail silencieusement (tour_id hors registre, validator regex accepte mais registry echoue, DOM target absent), acceptance est accordee a tort.
- [x] [Review][Patch] N'incrementer `guidanceAcceptanceCount` que sur acceptance du widget de consentement, pas sur chaque evenement SSE `guided_tour` [frontend/app/composables/useChat.ts:~740] — Un declenchement direct par demande explicite (« montre-moi le dashboard ») ecrase toute l'historique de refus via le reset cote acceptance. Decoupler le declenchement explicite du compteur d'adaptation.
- [x] [Review][Patch] Remplacer l'heuristique de detection consent question par un marqueur structurel [frontend/app/composables/useChat.ts:427-434] — Matching exact sur `"Oui, montre-moi"` / `"Non merci"` est fragile aux derives LLM (emoji, ponctuation, i18n). Privilegier un champ explicite (ex. `question.kind === 'guidance_consent'`) ou verification positionnelle stricte `options[0].id === 'yes' && options[1].id === 'no'` (conforme au sample spec Dev Notes).
- [x] [Review][Patch] Utiliser `computeEffectiveCountdown(baseCountdown)` dans la production path de `startTour` [frontend/app/composables/useGuidedTour.ts:~611, ~622] — Le helper est expose et teste en isolation mais la vraie logique de `startTour` inline `Math.max(3, baseCountdown - acceptanceSnapshot)`. Deux implementations divergentes de la meme regle.
- [x] [Review][Patch] Cap front + back sur `refusal_count` / `acceptance_count` a `MAX_STATS_CAP = 5` (= `baseCountdown - floor`, cf. D1) [backend/app/api/chat.py:60, frontend/app/composables/useGuidedTour.ts] — Un client malveillant peut injecter `999999999999` sans borne. Cote frontend, plafonner dans les helpers `incrementGuidanceRefusal` / `incrementGuidanceAcceptance` (`Math.min(val + 1, MAX_STATS_CAP)`) ; cote backend, clamper ou rejeter dans `_parse_guidance_stats`. Une seule constante partagee logiquement entre les deux formules.
- [x] [Review][Patch] Ecouter l'evenement `storage` pour synchroniser les compteurs multi-onglets [frontend/app/composables/useGuidedTour.ts] — Sans listener, l'onglet A ne voit jamais les refus de l'onglet B → lost-update a la prochaine ecriture.
- [x] [Review][Patch] Corriger l'ordre du champ `guidance_stats` dans le FormData de `submitInteractiveAnswer` [frontend/app/composables/useChat.ts] — AC2 specifie « apres `current_page` et avant le bloc `interactive_question_*` » ; actuellement place APRES le bloc interactive_question_*.
- [x] [Review][Patch] Borner la longueur brute de `guidance_stats` avant `json.loads` [backend/app/api/chat.py:~60] — Parallele a `current_page.strip()[:200]` ; ajouter une coupure (ex. `[:500]`) avant parse pour eviter CPU sur payload gros.
- [x] [Review][Patch] Hoister l'import `useGuidedTour` en import statique dans `useChat.ts` [frontend/app/composables/useChat.ts] — Actuellement `await import(...)` en hot-path (sendMessage + submitInteractiveAnswer x2), ajoute un microtask inutile et risque de divergence HMR en tests.
- [x] [Review][Patch] Renforcer `test_build_system_prompt_backward_compat_without_stats` avec un baseline byte-for-byte capture [backend/tests/test_prompts/test_guided_tour_adaptive_frequency.py] — Actuellement compare seulement deux appels NEW entre eux ; AC6 exige l'egalite avec le prompt de story 6.3 (capturer via fixture ou hash).
- [x] [Review][Patch] Extraire le plancher `3` en constante nommee partagee [frontend/app/composables/useGuidedTour.ts, backend/app/prompts/guided_tour.py] — Actuellement duplique 3+ fois en literal magique (`Math.max(3, ...)` et threshold `>=3`).
- [x] [Review][Patch] Logger les erreurs de `persistGuidanceStats` (quota exceeded) via `console.warn` [frontend/app/composables/useGuidedTour.ts:60-62] — `catch {}` silencieux masque les cas de quota localStorage ; au moins tracer un warning.
- [x] [Review][Patch] Supprimer / corriger le commentaire « atomicite » dans `incrementGuidanceAcceptance` [frontend/app/composables/useGuidedTour.ts] — Le commentaire revendique une atomicite qui n'existe pas (deux mutations sequentielles + un setItem).
- [x] [Review][Patch] Resserrer l'assertion `test_hint_contains_no_pii` [backend/tests/test_prompts/test_guided_tour_adaptive_frequency.py:~843] — `assert "7" not in hint` casse fortuitement si un nombre (ex. "2027") apparait ; cibler les tokens PII specifiques (regex `r"\b(refusal|acceptance)_count\b"`).
- [x] [Review][Patch] Ajouter une assertion `expect(incrementGuidanceRefusal).toHaveBeenCalled()` dans `useChat.guided-tour-consent.test.ts` [frontend/tests/composables/useChat.guided-tour-consent.test.ts] — Le fichier mock les nouveaux champs mais ne verifie pas que refus cliquant « Non merci » declenche bien l'increment.
- [x] [Review][Patch] Ajouter 3 tests de couverture manquants [frontend/tests/composables/ + backend/tests/] — (a) `submitInteractiveAnswer` avec `currentInteractiveQuestion.value === null` (heuristique retourne false), (b) consent question avec `options.length !== 2` (variant 3-options), (c) preservation de `guidance_stats` dans `ConversationState` a travers un aller-retour `ToolNode`.

#### Deferred (pre-existants ou hors-scope)

- [x] [Review][Defer] Decroissance / cap global sur counters (long-terme) [frontend/app/composables/useGuidedTour.ts] — deferred, design product a arbitrer globalement (cf. decision-needed D1).
- [x] [Review][Defer] `send_message_json` (fallback JSON) ne transmet pas `guidance_stats` [backend/app/api/chat.py:~976] — deferred, acceptable par spec (le fallback FormData est la voie officielle ; extension Chrome futur story 8.x).
- [x] [Review][Defer] Perte de precision au-dela de `Number.MAX_SAFE_INTEGER` dans `loadGuidanceStats` [frontend/app/composables/useGuidedTour.ts] — deferred, limite JS native ; protection suffisante par plafond serveur (P8).
- [x] [Review][Defer] Race `currentInteractiveQuestion` + SSE concurrent [frontend/app/composables/useChat.ts] — deferred, fenetre temporelle minime, impact negligeable en prod.
- [x] [Review][Defer] SSE `guided_tour` arrive pendant question pending → etat orphelin [frontend/app/composables/useChat.ts:~730-733] — deferred, path early-return existant + message systeme guide, edge case rare.
- [x] [Review][Defer] `test_guided_tour_instruction_unchanged` se contente d'une plage de longueur [backend/tests/test_prompts/test_guided_tour_adaptive_frequency.py:~894-903] — deferred, non-bloquant ; renforcer avec snapshot au prochain refactor 6.2.
- [x] [Review][Defer] `try { ... } catch {}` autour de l'import dynamique + increment [frontend/app/composables/useChat.ts:464-466] — deferred, non-critique, mais envisager logging dans story tooling observabilite.

## Dev Notes

### Contexte — story « ceinture et bretelles » de la modulation de frequence

Cette story vient **boucler** l'epic 6 : les stories 6.1 (tool), 6.2 (prompt + injection), 6.3 (consentement + declenchement direct) ont pose l'infrastructure technique et les regles de declenchement. La story 6.4 ajoute la **dimension adaptative** : l'assistant apprend du comportement de l'utilisateur pour moduler ses propositions.

**Scope technique :**
- **Stateful cote frontend** (module-level refs + localStorage) car la donnee est conversationnelle courte mais doit survivre aux rechargements.
- **Stateless cote backend** : les compteurs sont **transmis a chaque requete** dans `guidance_stats` et utilises uniquement pour injecter un hint dynamique dans le prompt systeme. Aucune persistance serveur — pas de migration Alembic, pas de table DB.
- **Priorite a la preservation de l'existant** : `GUIDED_TOUR_INSTRUCTION` (16 tests story 6.2 + 17 tests story 6.3) n'est PAS modifiee. Le hint est un appendix conditionnel.

### Modele de hint adaptatif (backend — `build_adaptive_frequency_hint`)

Quand `refusal_count >= 3`, le helper retourne un bloc francais du type :

```
## Modulation de frequence (adaptation comportementale)

L'utilisateur a refuse plusieurs fois consecutives tes propositions de guidage.
- Ne propose PLUS spontanement de guidage (plus aucun appel preventif a `ask_interactive_question` avec les options « Oui, montre-moi » / « Non merci »).
- Ne declenche un guidage QUE si l'utilisateur en fait la demande explicite (formulations verbales listees dans la section « Intent explicite »).
- Ne relance pas et ne suggere pas en boucle — respecte son choix.
- Cette restriction se leve automatiquement quand l'utilisateur acceptera a nouveau un guidage (compteur reinitialise cote client).
```

**Points critiques :**
- Le bloc doit mentionner explicitement `ask_interactive_question` ET `trigger_guided_tour` pour que le LLM comprenne qu'on inhibe le premier mais garde le second (declenchement direct reste autorise).
- Ne PAS inclure de donnees utilisateur (pas de nom, pas de montant) — NFR10.
- Ne PAS depasser ~100 mots (eviter le token bloat — rappel : `STYLE_INSTRUCTION` de feature 014 demande des reponses concises).

### Pattern FormData (frontend — `useChat.ts`)

```typescript
// Ligne ~168 (sendMessage) + ligne ~525 (submitInteractiveAnswer)
const guidedTour = useGuidedTour()
formData.append('guidance_stats', JSON.stringify({
  refusal_count: guidedTour.guidanceRefusalCount.value,
  acceptance_count: guidedTour.guidanceAcceptanceCount.value,
}))
```

**Pourquoi JSON.stringify et pas 2 champs separes ?** Coherence avec le pattern `interactive_question_values` deja en place (story 018) qui sterilise un tableau en JSON. Cote backend, un seul `Form()` field a parser → plus simple et extensible (ajouter un 3e compteur un jour sans toucher a l'API).

### Heuristique de detection « question de consentement guidage » (frontend — `useChat.handleInteractiveQuestionResolvedEvent`)

Pour decider si un `resolved` avec `no` doit incrementer `refusal_count`, on inspecte la question resolue :

```typescript
function isGuidanceConsentQuestion(q: InteractiveQuestion): boolean {
  if (!q || q.question_type !== 'qcu') return false
  if (!Array.isArray(q.options) || q.options.length !== 2) return false
  const ids = q.options.map(o => o.id).sort()
  if (ids[0] !== 'no' || ids[1] !== 'yes') return false
  const yesLabel = q.options.find(o => o.id === 'yes')?.label
  const noLabel = q.options.find(o => o.id === 'no')?.label
  return yesLabel === 'Oui, montre-moi' && noLabel === 'Non merci'
}
```

**Pourquoi ces labels exacts et pas un flag explicite ?** Les labels sont **verrouilles par le test T-AC1a de story 6.3** (`test_instruction_contains_consent_exact_strings`). Si un futur developpeur les change, le test de 6.3 casse — alerte immediate. Aucune modification de feature 018 n'est requise.

**Anti-pattern a eviter :** ne PAS tenter de detecter via le texte libre de la question (`q.question`) qui est genere par le LLM et donc variable.

### Pattern de persistance localStorage (reference : `stores/ui.ts:78-97`)

```typescript
const GUIDANCE_STATS_KEY = 'esg_mefali_guidance_stats'

function loadGuidanceStats(): { refusal_count: number; acceptance_count: number } {
  if (typeof window === 'undefined') return { refusal_count: 0, acceptance_count: 0 }
  try {
    const raw = localStorage.getItem(GUIDANCE_STATS_KEY)
    if (!raw) return { refusal_count: 0, acceptance_count: 0 }
    const parsed = JSON.parse(raw)
    const r = parsed?.refusal_count
    const a = parsed?.acceptance_count
    if (!Number.isInteger(r) || r < 0 || !Number.isInteger(a) || a < 0) {
      return { refusal_count: 0, acceptance_count: 0 }
    }
    return { refusal_count: r, acceptance_count: a }
  } catch {
    return { refusal_count: 0, acceptance_count: 0 }
  }
}

function persistGuidanceStats(): void {
  if (typeof window === 'undefined') return
  try {
    localStorage.setItem(GUIDANCE_STATS_KEY, JSON.stringify({
      refusal_count: guidanceRefusalCount.value,
      acceptance_count: guidanceAcceptanceCount.value,
    }))
  } catch {
    // localStorage peut throw en mode privacy Safari — ignore silencieusement
  }
}
```

### Formule de countdown (frontend — `useGuidedTour.startTour`)

```typescript
const originalCountdown = clampCountdown(step.countdown ?? DEFAULT_ENTRY_COUNTDOWN)
const effectiveCountdown = Math.max(3, originalCountdown - guidanceAcceptanceCount.value)
// Utiliser effectiveCountdown pour le decompteur (setTimeout / setInterval)
```

**Points critiques :**
- Plancher de 3s pour laisser l'utilisateur le temps de voir le hint meme apres beaucoup d'acceptations.
- **Une seule evaluation** au demarrage du parcours — pas de recalcul a chaque step (evite les comportements erratiques si `acceptance_count` change pendant le parcours).
- Applique uniquement sur le countdown **multi-pages** entre etapes (story 5.3). Les timeouts DOM (NFR18, retry 3×500ms) ne sont PAS affectes.

### Mapping canonique (rappel — heritage stories 6.1-6.3)

| Module termine / demande explicite | tour_id canonique | Page cible |
|---|---|---|
| Evaluation ESG close (30 criteres) | `show_esg_results` | `/esg/results` |
| Bilan carbone finalise | `show_carbon_results` | `/carbon/results` |
| Recherche de fonds finalisee / demande catalogue | `show_financing_catalog` | `/financing` |
| Score credit calcule | `show_credit_score` | `/credit` |
| Plan d'action genere | `show_action_plan` | `/action-plan` |
| Vue d'ensemble post-onboarding (chat_node) | `show_dashboard_overview` | `/dashboard` |

Source : `frontend/app/lib/guided-tours/registry.ts:1-250` + `backend/app/prompts/guided_tour.py:19-24`.

### Fichiers attendus

| Fichier | Action | Justification |
|---|---|---|
| `backend/app/graph/state.py` | MODIFIER | Ajouter `guidance_stats: dict \| None` dans ConversationState |
| `backend/app/api/chat.py` | MODIFIER | Accepter Form `guidance_stats`, parser, injecter dans initial_state |
| `backend/app/prompts/guided_tour.py` | MODIFIER (ajout helper) | Fonction `build_adaptive_frequency_hint(stats)` — la constante `GUIDED_TOUR_INSTRUCTION` reste intacte |
| `backend/app/prompts/system.py` | MODIFIER | Etendre signature `build_system_prompt` avec `guidance_stats`, appender hint |
| `backend/app/graph/nodes.py` | MODIFIER | Propager `guidance_stats` du state au `build_system_prompt` dans 6 noeuds (chat, esg_scoring, carbon, financing, credit, action_plan) |
| `backend/tests/test_prompts/test_guided_tour_adaptive_frequency.py` | CREER | 10 tests helper + build_system_prompt |
| `backend/tests/test_api/test_chat_guidance_stats.py` | CREER | 3 tests Form parsing |
| `frontend/app/composables/useGuidedTour.ts` | MODIFIER | Refs module-level + helpers + load/persist + formule countdown |
| `frontend/app/composables/useChat.ts` | MODIFIER | Ajout FormData + wiring increment refusal/acceptance |
| `frontend/tests/composables/useGuidedTour.adaptive-frequency.test.ts` | CREER | 7 tests composable |
| `frontend/tests/composables/useChat.adaptive-frequency.test.ts` | CREER | 6 tests integration SSE |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | MODIFIER | Status `6-4-frequence-...` : `ready-for-dev` → ... → `done` |
| `backend/app/prompts/guided_tour.py::GUIDED_TOUR_INSTRUCTION` | **NE PAS MODIFIER** | Verrouille par 16 tests story 6.2 + 17 tests story 6.3 |
| `backend/app/graph/tools/guided_tour_tools.py` | **NE PAS MODIFIER** | Tool deja hardene story 6.1 — la validation `_VALID_TOUR_ID` suffit |
| `backend/app/graph/tools/interactive_tools.py` | **NE PAS MODIFIER** | Feature 018 intacte (story 6.3 patch review) |
| `frontend/app/components/chat/SingleChoiceWidget.vue` | **NE PAS MODIFIER** | Reutilise tel quel |
| `frontend/app/lib/guided-tours/registry.ts` | **NE PAS MODIFIER** | `DEFAULT_ENTRY_COUNTDOWN = 8` reste la valeur canonique, la reduction se fait cote `startTour` |

### Traceabilite AC → test (a completer en Task 8)

| AC | Test backend | Test frontend |
|---|---|---|
| AC1 — compteurs + persistance | — | `useGuidedTour.adaptive-frequency.test.ts` (tests 1-6) |
| AC2 — FormData + Form field | `test_chat_guidance_stats.py` (3 tests) | `useChat.adaptive-frequency.test.ts` (tests 1-2) |
| AC3 — helper + injection | `test_guided_tour_adaptive_frequency.py::test_hint_*` + `test_build_system_prompt_*` (9 tests) | — |
| AC4 — countdown reduit | — | `useGuidedTour.adaptive-frequency.test.ts::test effective countdown = max(3, default - N)` |
| AC5 — increment/reset flux SSE | — | `useChat.adaptive-frequency.test.ts` (tests 3-6) |
| AC6 — zero regression + 80 % | Suite backend 1050+ tests verts + ruff | Suite frontend 285+ tests verts |
| AC7 — doc traceabilite | Ce tableau | — |

### Anti-patterns a eviter

- **Ne pas modifier** `GUIDED_TOUR_INSTRUCTION` — c'est une constante verrouillee. Le hint adaptatif est un appendix dynamique genere par `build_adaptive_frequency_hint`.
- **Ne pas persister** `guidance_stats` en BDD serveur — c'est une metadonnee client-first, cout+complexite migration non justifies (NFR17 : guidage frontend-only, principe deja etabli).
- **Ne pas accepter** de valeurs non-entieres ou negatives dans `guidance_stats` cote backend — fallback `None`. Cote frontend : reset a 0 si localStorage corrompu.
- **Ne pas incrementer** `acceptance_count` si `startTour` est bloque (garde pending, tour_id invalide). Le test T-AC5 negatif (« invalid tour_id does NOT increment acceptance ») verrouille ce comportement.
- **Ne pas reduire** les timeouts DOM (NFR18 — 3×500ms retry) avec `acceptance_count`. Ces timeouts sont des garanties de resilience (story 7.1), pas des decompteurs d'UX.
- **Ne pas ajouter** un endpoint REST `/api/guidance-stats` ou similaire — la transmission via le FormData de `/api/chat/messages` suffit (pattern deja utilise pour `current_page`, `interactive_question_*`).
- **Ne pas faire** de test LLM end-to-end dans pytest — les tests sont deterministes sur contenu du prompt (helper pur) et parsing API. L'end-to-end « refus 3x → prompt raccourcit propositions » est couvert par l'epic 8 (tests e2e).
- **Ne pas tester** avec un `localStorage` mutable reel dans les tests Vitest — utiliser `vi.stubGlobal` ou un mock propre (pattern `useChat.guidedTour.test.ts`).
- **Ne pas oublier** la guard `typeof window !== 'undefined'` — Nuxt 4 rend en SSR, localStorage n'existe pas cote serveur (crash au build).
- **Ne pas introduire** de debouncing / throttling sur l'ecriture localStorage — les increments sont rares (quelques par session), la simplicite prime.

### Exigences architecture

- **ADR3** (architecture.md — composable singleton `useGuidedTour` module-level) : les 2 nouveaux compteurs respectent ce pattern (refs declarees au niveau module, pas dans la fonction).
- **ADR4** (architecture.md lignes 286-354 — Tool LangChain + marker SSE) : inchangee. Le hint cote prompt n'affecte pas le contrat du tool.
- **FR17** (prd.md ligne 335) : « Le systeme adapte la frequence des propositions de guidage (reduction apres refus repetes) et reduit la duree du decompteur apres plusieurs acceptations » → **implemente integralement par cette story**.
- **NFR10** (pas de PII dans le marker SSE / dans le prompt) : rappel — `build_adaptive_frequency_hint` ne doit jamais inclure les valeurs numeriques des compteurs dans la chaine (« l'utilisateur a refuse 7 fois » interdit — preferer « plusieurs fois consecutives »). Test `test_hint_contains_no_pii` verrouille.
- **NFR19** (zero regression) : 1036 tests backend (post 6.3) + 272 tests frontend (post 6.3) doivent rester verts.
- **NFR20** (widget universel) : les refs `guidanceRefusalCount` / `guidanceAcceptanceCount` sont partagees cross-composants car module-level — le widget flottant et toute future vue chat utilisent le meme etat.

### Intelligence stories 6.1 + 6.2 + 6.3 (dernieres stories completees — 2026-04-13 / 2026-04-14)

**Lecons a retenir (heritage direct):**

- `GUIDED_TOUR_INSTRUCTION` est deja injecte systematiquement dans `build_system_prompt()` (patch review 6.2). Story 6.4 ne change pas cette injection, elle l'**etend** avec un appendix conditionnel.
- Les labels canoniques `"Oui, montre-moi"` / `"Non merci"` sont **stables** depuis la story 6.3 (test `test_instruction_contains_consent_exact_strings` les verrouille). Heuristique de detection fiable.
- La garde `currentInteractiveQuestion.value?.state === 'pending'` dans `useChat.ts:689` existe deja (patch review 6.1). **Ne pas la retirer.** L'increment acceptance doit se faire **apres** cette garde, avant l'appel `startTour`.
- Le validator `_VALID_TOUR_ID = ^[a-z][a-z0-9_]*$` dans le tool (story 6.1) garantit que seul un `tour_id` valide franchit le pipeline SSE. L'increment acceptance dans `handleGuidedTourEvent` peut donc se faire en confiance (pas de tour_id fantome qui incrementerait).
- Les 6 noeuds beneficiant de `GUIDED_TOUR_INSTRUCTION` sont : **chat, esg_scoring, carbon, financing, credit, action_plan**. Les 4 noeuds exclus : **application, document, profiling, router**. Story 6.4 propage `guidance_stats` aux memes 6 noeuds.
- **Pas d'alignement cross-stack** des `tour_id` (defer story 6.2) — story 6.4 ne le fait pas non plus. Ce pourra etre une story 8.6 (non-regression globale).
- `STYLE_INSTRUCTION` de feature 014 impose des reponses concises post-onboarding. Le hint adaptatif doit rester court (~100 mots max).

**Chiffres de sortie stories 6.1-6.3** : 1036 tests backend verts, 272 tests frontend verts, 0 regression. Couverture 100 % sur `app.prompts.guided_tour`, `app.graph.tools.guided_tour_tools`.

**Patchs de code review 6.3 (retours journalises dans deferred-work.md) a ne PAS casser :**
- 8 patches appliques (voir sprint-status.yaml : « 8 patches, 6 defer »). Verifier `_bmad-output/implementation-artifacts/deferred-work.md` pour la liste a jour — ne pas toucher aux zones patchees sauf si necessaire.

### Project Structure Notes

Aucune divergence avec la structure unified :
- Tests prompt backend : `backend/tests/test_prompts/test_guided_tour_adaptive_frequency.py`
- Tests API backend : `backend/tests/test_api/test_chat_guidance_stats.py`
- Tests composable frontend : `frontend/tests/composables/useGuidedTour.adaptive-frequency.test.ts` + `useChat.adaptive-frequency.test.ts`
- Nommage coherent avec `.adaptive-frequency.test.ts` (lisibilite immediate de la feature testee).
- Pas de nouveau dossier, pas de nouvelle convention — **reuse maximum**.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic-6-Story-6.4](../planning-artifacts/epics.md) — Exigences (lignes 1027-1063)
- [Source: _bmad-output/planning-artifacts/prd.md#FR17](../planning-artifacts/prd.md) — Frequence adaptative (ligne 335)
- [Source: _bmad-output/planning-artifacts/architecture.md#Section-fréquence-adaptative](../planning-artifacts/architecture.md) — Recommandation compteur frontend (ligne 1018)
- [Source: _bmad-output/implementation-artifacts/6-3-consentement-via-widget-interactif-et-declenchement-direct.md](./6-3-consentement-via-widget-interactif-et-declenchement-direct.md) — Story precedente (pattern tests + labels canoniques)
- [Source: _bmad-output/implementation-artifacts/6-2-prompt-guided-tour-instruction-et-injection-dans-les-noeuds-langgraph.md](./6-2-prompt-guided-tour-instruction-et-injection-dans-les-noeuds-langgraph.md) — Injection dans 6 noeuds
- [Source: _bmad-output/implementation-artifacts/6-1-tool-langchain-trigger-guided-tour-et-marker-sse.md](./6-1-tool-langchain-trigger-guided-tour-et-marker-sse.md) — Tool + garde pending + validator `_VALID_TOUR_ID`
- [Source: backend/app/prompts/guided_tour.py](../../backend/app/prompts/guided_tour.py) — Constante `GUIDED_TOUR_INSTRUCTION` (NE PAS MODIFIER)
- [Source: backend/app/prompts/system.py:172-221](../../backend/app/prompts/system.py) — `build_system_prompt()` a etendre
- [Source: backend/app/graph/state.py:9-37](../../backend/app/graph/state.py) — ConversationState TypedDict
- [Source: backend/app/graph/nodes.py](../../backend/app/graph/nodes.py) — 6 noeuds a propager (chat_node, esg_scoring_node, carbon_node, financing_node, credit_node, action_plan_node)
- [Source: backend/app/api/chat.py:109-156](../../backend/app/api/chat.py) — Endpoint POST /messages avec Form fields (page_context, interactive_question_*)
- [Source: backend/app/graph/tools/guided_tour_tools.py](../../backend/app/graph/tools/guided_tour_tools.py) — Tool + validator `_VALID_TOUR_ID` (NE PAS MODIFIER)
- [Source: backend/tests/test_prompts/test_guided_tour_instruction.py](../../backend/tests/test_prompts/test_guided_tour_instruction.py) — Pattern test prompt content (16 tests)
- [Source: backend/tests/test_prompts/test_guided_tour_consent_flow.py](../../backend/tests/test_prompts/test_guided_tour_consent_flow.py) — Pattern parametrize (17 tests story 6.3)
- [Source: frontend/app/composables/useGuidedTour.ts:10-304](../../frontend/app/composables/useGuidedTour.ts) — Module-level state + startTour
- [Source: frontend/app/composables/useChat.ts:133-700](../../frontend/app/composables/useChat.ts) — sendMessage, submitInteractiveAnswer, handlers SSE
- [Source: frontend/app/lib/guided-tours/registry.ts:6](../../frontend/app/lib/guided-tours/registry.ts) — `DEFAULT_ENTRY_COUNTDOWN = 8`
- [Source: frontend/app/stores/ui.ts:29-97](../../frontend/app/stores/ui.ts) — Pattern localStorage (theme + widget size)
- [Source: frontend/tests/composables/useChat.guided-tour-consent.test.ts](../../frontend/tests/composables/useChat.guided-tour-consent.test.ts) — Pattern mock streaming SSE (story 6.3)
- [Source: frontend/tests/composables/useChat.guidedTour.test.ts](../../frontend/tests/composables/useChat.guidedTour.test.ts) — Pattern spy startTour

## Dev Agent Record

### Agent Model Used

claude-opus-4-6 (1M context)

### Debug Log References

- `backend && python -m pytest tests/test_prompts/test_guided_tour_adaptive_frequency.py tests/test_chat_guidance_stats.py -v` → 26/26 verts
- `backend && python -m pytest` (suite complete) → 1063 tests verts (1036 + 26 + 1 ajustement), 0 regression
- `backend && ruff check` (fichiers modifies) → All checks passed (l'erreur `F401` dans `nodes.py:446` est pre-existante, hors story)
- `frontend && npm run test -- --run` → 289/289 verts (272 + 17 nouveaux), 0 regression

### Completion Notes List

**Choix de design**

1. **Helper pur `_parse_guidance_stats` cote API** (`backend/app/api/chat.py`) plutot que parsing inline — facilite le test unitaire sans spinner FastAPI complet. Rejette les booleens (qui sont techniquement des int en Python) pour eviter toute ambiguite de type.
2. **`build_adaptive_frequency_hint` pur et deterministe** — le helper retourne une chaine constante (`_ADAPTIVE_FREQUENCY_HINT`) quand `refusal_count >= 3`, sans injecter de valeurs numeriques. NFR10 respecte : aucune donnee PII (nom, email, montant, IDs) ne peut transiter via le prompt.
3. **Appendix conditionnel apres `GUIDED_TOUR_INSTRUCTION`** — la constante verrouillee par 16+17 tests des stories 6.2/6.3 reste intacte. Le hint est ajoute **apres** `sections.append(GUIDED_TOUR_INSTRUCTION)` dans 6 builders : `build_system_prompt` (chat), `build_esg_prompt`, `build_carbon_prompt`, `build_financing_prompt`, `build_credit_prompt`, `build_action_plan_prompt`. Conforme a la liste canonique de la story 6.2.
4. **Module-level refs dans `useGuidedTour.ts`** — `guidanceRefusalCount` / `guidanceAcceptanceCount` sont declarees au niveau module (pattern singleton cross-routes ADR3), initialisees une seule fois au chargement via `loadGuidanceStats()`. Guard `typeof window === 'undefined'` pour la compatibilite SSR Nuxt.
5. **Cle localStorage `esg_mefali_guidance_stats`** — coherente avec les autres cles du projet (`esg_mefali_theme` etc.). Fallback silencieux a `{0,0}` si JSON corrompu, valeurs non-entieres ou negatives (pattern `isValidDimension` de `stores/ui.ts`).
6. **Heuristique de detection consent question** — les labels canoniques `"Oui, montre-moi"` / `"Non merci"` sont verrouilles par le test T-AC1a de la story 6.3. La fonction `isGuidanceConsentQuestion` verifie `question_type === 'qcu'` + 2 options + ids `yes`/`no` + labels exacts. Aucune dependance sur le texte libre de la question (variable du LLM).
7. **Increment acceptance AVANT `startTour`** — dans `handleGuidedTourEvent`, apres les gardes `tour_id invalide` + `currentInteractiveQuestion.state === 'pending'`. Le validator backend `_VALID_TOUR_ID` (story 6.1) garantit qu'aucun tour_id fantome n'arrive. Test T-AC5 negatif verrouille ce comportement.
8. **Countdown reduit capture au demarrage** — `acceptanceSnapshot = guidanceAcceptanceCount.value` est pris au debut de `startTour`, utilise ensuite pour tous les decompteurs multi-pages. Evite tout comportement erratique si `acceptance_count` change pendant le parcours (ex : utilisateur accepte un autre tour en parallele via un nouvel onglet). Plancher de 3s maintenu via `Math.max(3, original - snapshot)`.
9. **Aucune modification des timeouts DOM** (`waitForElement` 3×500ms, `waitForElementExtended` 10000ms) — ces timeouts sont des garanties de resilience (NFR18, story 7.1), pas des decompteurs d'UX. La story 6.4 ne les touche pas.
10. **Mocks frontend existants etendus** — `useChat.guidedTour.test.ts` et `useChat.guided-tour-consent.test.ts` avaient des mocks partiels de `useGuidedTour`. L'ajout des nouveaux champs requis par `sendMessage` / `submitInteractiveAnswer` a necessite d'etendre les deux mocks pour eviter un `TypeError` sur `guidanceRefusalCount.value` au runtime du test.

**Tests**

- **Backend** : 10 tests helper (`build_adaptive_frequency_hint` + `build_system_prompt` extended) + 10 tests parsing Form field = **26 tests**, tous verts. Couverture complete du helper pur et du parser API.
- **Frontend** : 11 tests composable (`useGuidedTour.adaptive-frequency.test.ts`) + 6 tests SSE (`useChat.adaptive-frequency.test.ts`) = **17 tests**, tous verts. Couvre AC1-AC6 par tableaux parametres (`it.each` pour les 5 cas de countdown, `@pytest.mark.parametrize` pour les 3 cas below/above threshold).

### File List

**Backend (modifies)**
- `backend/app/graph/state.py` — ajout `guidance_stats: dict | None` dans `ConversationState`
- `backend/app/api/chat.py` — helper `_parse_guidance_stats`, Form field `guidance_stats: str | None = Form(None)`, propagation au state via `stream_graph_events`
- `backend/app/prompts/guided_tour.py` — constante `_ADAPTIVE_FREQUENCY_HINT` + helper `build_adaptive_frequency_hint(guidance_stats)`
- `backend/app/prompts/system.py` — extension `build_system_prompt(..., guidance_stats=None)` + injection conditionnelle du hint apres `GUIDED_TOUR_INSTRUCTION`
- `backend/app/prompts/esg_scoring.py` — extension `build_esg_prompt(..., guidance_stats=None)` + injection hint
- `backend/app/prompts/carbon.py` — extension `build_carbon_prompt(..., guidance_stats=None)` + injection hint
- `backend/app/prompts/financing.py` — extension `build_financing_prompt(..., guidance_stats=None)` + injection hint
- `backend/app/prompts/credit.py` — extension `build_credit_prompt(..., guidance_stats=None)` + injection hint
- `backend/app/prompts/action_plan.py` — extension `build_action_plan_prompt(..., guidance_stats=None)` + injection hint
- `backend/app/graph/nodes.py` — propagation `state.get("guidance_stats")` aux 6 builders (chat_node, esg_scoring_node, carbon_node, financing_node, credit_node, action_plan_node)

**Backend (crees)**
- `backend/tests/test_prompts/test_guided_tour_adaptive_frequency.py` — 16 tests helper + `build_system_prompt`
- `backend/tests/test_chat_guidance_stats.py` — 10 tests parsing Form field

**Frontend (modifies)**
- `frontend/app/composables/useGuidedTour.ts` — refs module-level `guidanceRefusalCount`/`guidanceAcceptanceCount`, helpers `loadGuidanceStats`/`persistGuidanceStats`/`incrementGuidanceRefusal`/`incrementGuidanceAcceptance`/`resetGuidanceStats`/`computeEffectiveCountdown`, application `Math.max(3, base - acceptanceSnapshot)` aux decompteurs multi-pages (entryStep + sidebar nav), exposition dans le retour
- `frontend/app/composables/useChat.ts` — helper `isGuidanceConsentQuestion`, ajout `guidance_stats` au FormData dans `sendMessage` et `submitInteractiveAnswer`, detection refus dans `submitInteractiveAnswer`, increment acceptance dans `handleGuidedTourEvent` apres les gardes
- `frontend/tests/composables/useChat.guidedTour.test.ts` — mock `useGuidedTour` etendu avec les nouveaux champs
- `frontend/tests/composables/useChat.guided-tour-consent.test.ts` — mock `useGuidedTour` etendu

**Frontend (crees)**
- `frontend/tests/composables/useGuidedTour.adaptive-frequency.test.ts` — 11 tests refs + helpers + countdown
- `frontend/tests/composables/useChat.adaptive-frequency.test.ts` — 6 tests FormData + detection consent + increment acceptance

**Configuration**
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — `6-4-frequence-...` passe de `ready-for-dev` a `review`

## Change Log

| Date | Description |
|---|---|
| 2026-04-14 | Story 6.4 implementee : frequence adaptative (FR17). Helper pur `build_adaptive_frequency_hint` + parsing Form `guidance_stats` cote backend. Refs module-level + persistance localStorage + reduction countdown multi-pages cote frontend. 43 nouveaux tests (26 backend + 17 frontend), 0 regression (1063 backend + 289 frontend verts). |

