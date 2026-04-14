# Story 7.2 : Renouvellement JWT transparent pendant le guidage

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

En tant qu'utilisateur qui suit un parcours guide sur plusieurs pages,
je veux que mon token d'authentification soit renouvele automatiquement pendant le guidage,
afin de ne pas etre interrompu par une deconnexion inattendue (FR32, NFR9).

## Contexte — etat actuel (VERIFIE avant redaction)

Audit du code existant (2026-04-14) :

- `frontend/app/composables/useAuth.ts` expose deja :
  - `apiFetch<T>(url, options)` (lignes 11-31) — wrapper fetch qui ajoute le header `Authorization: Bearer {accessToken}` et **throw** brut sur `!response.ok` (ligne 25-28). **Aucun intercepteur 401 → refresh → retry.**
  - `refresh(): Promise<boolean>` (lignes 67-81) — appelle `POST /auth/refresh` avec le refresh_token du store. Retourne `true` sur succes (tokens re-persistes via `authStore.setTokens`), `false` sur echec (clear auth). **Fonction jamais appelee automatiquement** aujourd'hui.
  - `logout()` (lignes 83-86) — `authStore.clearAuth()` + `router.push('/login')`.
- `frontend/app/stores/auth.ts` persiste `access_token` et `refresh_token` en **localStorage** (lignes 18-22, 34-36).
- Backend `POST /auth/refresh` (`backend/app/api/auth.py:115-129`) :
  - Entree : `{refresh_token: string}` (schema `RefreshRequest` dans `schemas/auth.py`).
  - Sortie `TokenResponse` (`access_token: str, token_type: "bearer", expires_in: 3600, refresh_token: str | None = None`) — **le refresh endpoint ne retourne PAS de nouveau refresh_token** (pas de rotation). Le `refresh_token` cote client reste inchange et continue de servir jusqu'a sa propre expiration (30 jours, cf. `backend/app/core/config.py:21`).
  - 401 `"Refresh token invalide ou expiré"` si le refresh_token est lui-meme rejete.
- `frontend/app/middleware/auth.global.ts` (lignes 3-23) — middleware Nuxt qui redirige vers `/login` si non authentifie ET route non-publique (`/login`, `/register`). **Ne detecte pas les expirations runtime** (pas de hook sur les 401 runtime).
- **Les composables metier (`useDashboard`, `useEsg`, `useCarbon`, `useFinancing`, `useApplications`, `useCreditScore`, `useActionPlan`, `useReports`, `useDocuments`, `useCompanyProfile`) n'utilisent PAS `apiFetch`** — chacun implemente son propre `getHeaders()` + `fetch()` direct (ex. `useDashboard.ts:11-26`). **Consequence critique pour cette story** : si on ne renforce QUE `apiFetch`, les pages cibles du guidage multi-pages (`/dashboard`, `/esg`, `/carbon`, `/financing`) continueront de tomber en 401 silencieux parce que leurs composables ne passent pas par `apiFetch`. **Deux options** (a trancher par le dev) :
  - **Option A (recommandee — scope minimal pour le guidage)** : enrichir `apiFetch` avec l'intercepteur 401, PUIS migrer **uniquement** les 4 composables utilises par le guidage multi-pages (`useDashboard`, `useEsg`, `useCarbon`, `useFinancing`) vers `apiFetch`. Les autres (`useApplications`, `useCreditScore`, `useActionPlan`, `useReports`, `useDocuments`, `useCompanyProfile`) restent inchanges — **dette technique documentee** en Completion Notes pour une future story hors-epic 7.
  - **Option B (scope max)** : migrer TOUS les composables vers `apiFetch`. **Non recommande** : gros diff, risque de regression sur des modules hors-epic (dashboard, ESG, carbone, financement). Out-of-scope de cette story.
- **Aucun test d'auth existant** (`frontend/tests/composables/useAuth.*.test.ts` : introuvable). Cette story introduit la premiere suite.
- **Driver.js ne fait aucun appel API** (purement frontend — `useGuidedTour.ts` orchestre uniquement la navigation et les popovers). L'expiration JWT n'impacte donc QUE les pages cibles chargees (qui font des appels API au mount).

Cette story comble 3 gaps identifies par l'architecture (`architecture.md:1014`) :

1. **Intercepteur 401 → refresh → retry absent** dans `apiFetch`.
2. **Pas de single-flight** pour eviter un "refresh storm" (N requetes paralleles qui font chacune un refresh).
3. **Pas de propre interruption** du parcours guide si le refresh_token lui-meme est expire (pas d'appel a `cancelTour`).

## Acceptance Criteria

### AC1 : Intercepteur 401 → refresh → retry dans `apiFetch` (FR32, NFR9)

**Given** une requete authentifiee est emise via `apiFetch<T>(url, options)` dans `useAuth.ts`
**And** le serveur repond avec un statut HTTP **401** (access_token expire)
**When** `apiFetch` detecte le 401 sur la **premiere** tentative
**Then** `apiFetch` :
1. Appelle automatiquement `refresh()` (reutilise la fonction existante ligne 67-81, **ne pas la reimplementer**)
2. Si `refresh()` retourne `true` (nouveau `access_token` en store + localStorage), rejoue la requete **une seule fois** avec le nouveau token dans le header `Authorization`
3. Si la requete rejouee reussit (2xx), retourne le JSON parse (comportement normal)
4. Si la requete rejouee echoue encore (401, 403, 500, network), `apiFetch` **throw** normalement comme aujourd'hui (pas de boucle infinie)

**And** si `refresh()` retourne `false` (refresh_token lui-meme expire ou 401 sur `/auth/refresh`) :
1. `apiFetch` **throw** une `Error` avec le message `"Session expirée, veuillez vous reconnecter."` (message FR avec accents, a utiliser dans les tests comme substring exact)
2. Le store a deja ete clear par `refresh()` (ligne 78)
3. La redirection vers `/login` est declenchee **au niveau du caller** (AC2), pas dans `apiFetch` (separation responsabilites : `apiFetch` ne connait pas le router de maniere directe — il utilise deja `useRouter()` de `useAuth` contextuellement via `logout()`, mais on prefere eviter le couplage)
4. **Alternative acceptable** : si le dev trouve plus pratique de rediriger directement dans `apiFetch` (via `router.push('/login')`), le faire **uniquement** apres le throw pour que les composables metier puissent attraper l'exception et afficher un toast s'ils le souhaitent — documenter la decision dans Completion Notes.

**And** les endpoints `/auth/login`, `/auth/register`, `/auth/refresh`, `/auth/detect-country` sont **exclus** du cycle 401 → refresh (sinon boucle infinie : un 401 sur `/auth/refresh` appellerait `refresh()` qui appellerait a nouveau `/auth/refresh`). **Implementation** : detecter via `url.startsWith('/auth/')` et bypasser l'intercepteur (laisser le throw se propager).

**And** les requetes sans `Authorization` header (ex. `/auth/login` anonyme) ne declenchent pas le cycle — condition guard : `if (authStore.accessToken && response.status === 401 && !isAuthEndpoint) { ... }`.

### AC2 : Redirection vers /login + interruption du parcours si refresh expire

**Given** un parcours guide multi-pages est en cours (`useGuidedTour().tourState.value !== 'idle'` OU `useUiStore().guidedTourActive === true`)
**And** `apiFetch` throw `"Session expirée, veuillez vous reconnecter."` (AC1, refresh lui-meme expire)
**When** le composable metier appelant (`useDashboard.fetchSummary`, `useEsg.loadAssessment`, etc.) attrape l'erreur dans son `try/catch`
**Then** le composable metier delegue a un nouveau helper `handleAuthFailure()` (a creer dans `useAuth.ts`, expose) qui :
1. Detecte qu'un parcours guide est actif via `useUiStore().guidedTourActive`
2. Si actif → appelle `useGuidedTour().cancelTour()` pour un cleanup propre (destroy Driver.js, reset UI flags, reset state a `'idle'`)
3. Appelle `useChat().addSystemMessage('Votre session a expiré. Veuillez vous reconnecter.')` pour informer l'utilisateur (**uniquement** si parcours guide actif — evite les doubles notifications hors-guidage)
4. Appelle `router.push('/login')` (ou `navigateTo('/login')`)

**And** si aucun parcours guide n'est actif, `handleAuthFailure()` ne fait que `router.push('/login')` (comportement classique, pas de message chat).

**And** le message chat `"Votre session a expiré. Veuillez vous reconnecter."` est ajoute **avant** la redirection (pour que l'utilisateur le voie si le widget est encore ouvert au moment de la redirection — NFR9 UX).

**And** les composables metier sont **libres** d'appeler `handleAuthFailure()` ou de laisser l'erreur se propager vers le composant Vue appelant, SELON leur pattern actuel. Pour cette story, on couvre explicitement :
- `useDashboard.fetchSummary` (ligne 34-36 — catch actuel → ajouter `handleAuthFailure` si substring `"Session expirée"`)
- `useEsg.loadAssessment`, `useEsg.submitResponses` (meme pattern)
- `useCarbon.loadAssessment`, `useCarbon.submitResponses`
- `useFinancing.loadMatches`, `useFinancing.expressInterest`

**And** les autres composables (`useApplications`, `useCreditScore`, `useActionPlan`, `useReports`, `useDocuments`, `useCompanyProfile`) ne sont **PAS** modifies dans cette story — documente en Completion Notes comme dette technique.

### AC3 : Single-flight pour eviter le refresh storm (NFR9)

**Given** N requetes paralleles (>= 2) sont emises via `apiFetch` quasi-simultanement (ex. une page charge qui fait 3 appels en `Promise.all`)
**And** toutes recoivent un 401 (access_token tout juste expire)
**When** chacune declenche la logique AC1
**Then** **une seule** requete `POST /auth/refresh` est emise (single-flight)
**And** les N appels attendent la meme Promise puis rejouent leurs requetes originales avec le nouveau token

**Implementation** : ajouter une variable module-level (ou closure du composable) `let refreshPromise: Promise<boolean> | null = null`. Dans le cycle refresh :
```typescript
if (!refreshPromise) {
  refreshPromise = refresh().finally(() => { refreshPromise = null })
}
const ok = await refreshPromise
```

**Rationale** : sans cette garde, un refresh_token peut etre invalide cote backend apres le 1er appel (certains backends invalident l'ancien refresh token des emission d'un nouveau — ce n'est PAS le cas ici puisque le backend ne fait pas de rotation, mais le pattern est **neanmoins recommande** pour eviter de surcharger `/auth/refresh` et simplifie les tests).

**And** si `refresh()` retourne `false` durant le refresh partage, les N appels attendent tous la meme Promise `false` et throw chacun `"Session expirée, veuillez vous reconnecter."` — comportement deterministe.

**And** `refreshPromise` est **reset** apres completion (dans `.finally`), pour que la prochaine fenetre d'expiration (1 heure apres le nouveau token) redemarre un cycle propre.

**And** la variable `refreshPromise` doit etre **module-level** (pas scopee au `useAuth()` qui est re-instancie a chaque appel — cf. `export const refreshPromise = null` en haut du fichier, a la maniere de module-level state de `useChat.ts`). **Alternative** : colocaliser dans un fichier dedie `frontend/app/composables/internal/refreshGate.ts` si le dev prefere isoler — arbitrage design du dev.

### AC4 : Parcours Driver.js pur inchange par le refresh (FR32, isolation)

**Given** un parcours guide Driver.js mono-page est en cours (ex. une serie de 5 steps tous sur `/dashboard` — pas de navigation)
**And** le JWT expire entre deux steps
**When** aucun appel API n'est emis pendant les steps (Driver.js highlight pur DOM)
**Then** le parcours **continue sans interruption** — aucun refresh n'est declenche (rien ne 401)

**And** si la page ou le parcours mono-page s'execute fait un appel API de fond (ex. polling via `useDashboard`), l'intercepteur AC1 prend le relais **de maniere transparente** — le parcours Driver.js n'est pas concerne (le refresh se fait en parallele sans toucher Driver.js).

**Test dedie** : `test_driverjs_mono_page_tour_survives_jwt_expiration_without_api_call` — mock JWT expire mais aucun `fetch` mocke → parcours tourne jusqu'a completion sans que `refresh()` soit appelee.

### AC5 : Parcours multi-pages — refresh pendant navigation transparent

**Given** un parcours multi-pages est actif (`useGuidedTour`, state `'navigating'`)
**And** la navigation `navigateTo(step.route)` declenche le mount de la page cible qui fait un `fetch` vers une API authentifiee
**When** ce fetch retourne 401 car le access_token vient d'expirer pendant la navigation
**Then** l'intercepteur AC1 effectue `refresh()` → retry → 200
**And** le parcours continue : `waitForElementExtended(step.selector, PAGE_LOAD_HARD_TIMEOUT_MS)` voit l'element apparaitre apres le mount reussi
**And** aucun message systeme n'est ajoute (refresh silencieux, conforme NFR9)

**Given** le refresh echoue pendant la navigation (refresh_token expire)
**When** l'apiFetch throw `"Session expirée"`
**Then** `handleAuthFailure()` (AC2) est appele → `cancelTour()` + message chat + redirect `/login`
**And** le parcours passe par un cleanup propre (`driver.destroy`, widget reapparait, state `'idle'`)

**Test dedie** : `test_multi_page_tour_silent_refresh_during_navigation` (mock un 401 sur `/dashboard/summary` au 1er appel puis 200 au 2eme, verifier que le parcours continue sans message d'erreur).

### AC6 : Composables `useDashboard`, `useEsg`, `useCarbon`, `useFinancing` migres vers `apiFetch`

**Given** les 4 composables metier utilises par le guidage multi-pages utilisent actuellement `fetch()` direct avec `getHeaders()` local
**When** cette story est completee
**Then** chacun des 4 composables **delegue a `apiFetch`** pour ses appels (remplacer `fetch(\`${apiBase}${url}\`, { headers: getHeaders() })` par `apiFetch(url, options)`)

**And** les fonctions locales `getHeaders()` sont **supprimees** dans les 4 composables (DRY — la logique Bearer est centralisee dans `apiFetch`).

**And** les composables gardent leur logique metier (store update, error handling via store.setError, loading flags) — SEULE l'emission de la requete HTTP change.

**And** les messages d'erreur existants (`"Erreur lors du chargement du tableau de bord"`, etc.) sont **conserves** — mais pour l'erreur 401 specifique, le throw `"Session expirée, veuillez vous reconnecter."` de `apiFetch` doit etre **propage** intact (verifier avec `if (e.message.includes("Session expirée")) { await handleAuthFailure() }` dans le catch).

**And** les tests unitaires existants de ces composables (s'il y en a) restent verts (zero regression).

**Liste exhaustive des fichiers a modifier** :
- `frontend/app/composables/useDashboard.ts` (1 appel : `fetchSummary`)
- `frontend/app/composables/useEsg.ts` (a auditer — recenser tous les `fetch()` et migrer)
- `frontend/app/composables/useCarbon.ts` (idem)
- `frontend/app/composables/useFinancing.ts` (idem)

**NON inclus dans cette story** : `useApplications`, `useCreditScore`, `useActionPlan`, `useReports`, `useDocuments`, `useCompanyProfile`, `useChat` — documente en Completion Notes comme dette technique future.

### AC7 : Tests unitaires Vitest >= 80% et zero regression (NFR19)

**Given** la suite de tests frontend existante (309+ tests verts apres story 7.1)
**When** on execute `cd frontend && npm run test`
**Then** zero regression sur l'ensemble

**And** un nouveau fichier `frontend/tests/composables/useAuth.refresh.test.ts` est cree avec AU MINIMUM les tests suivants :

#### Bloc 1 : Intercepteur 401 → refresh → retry (AC1)

- `test_apiFetch_returns_data_on_first_200_without_triggering_refresh` (chemin normal, pas de refresh call)
- `test_apiFetch_triggers_refresh_on_401_then_retries_with_new_token` (mock 1er fetch 401 → POST /auth/refresh 200 → 2e fetch 200, verifier 3 calls fetch)
- `test_apiFetch_throws_session_expired_when_refresh_fails` (mock 401 → POST /auth/refresh 401 → throw avec substring `"Session expirée"`)
- `test_apiFetch_does_not_retry_when_second_attempt_also_401` (mock 401 → refresh 200 → 401 → throw avec message du serveur — pas de boucle infinie, verifier exactement 3 calls fetch)
- `test_apiFetch_bypasses_refresh_for_auth_endpoints` (mock POST /auth/login 401 → throw direct, **zero** call POST /auth/refresh)
- `test_apiFetch_bypasses_refresh_when_no_access_token` (authStore vide → 401 → throw direct, pas de refresh)

#### Bloc 2 : Single-flight (AC3)

- `test_concurrent_401s_share_a_single_refresh_call` (lancer 3 `apiFetch` en `Promise.all`, tous 401 → **un seul** POST /auth/refresh → les 3 rejouent avec le meme nouveau token → 3 resolves)
- `test_refreshPromise_reset_after_completion` (apres un cycle de refresh, relancer un 401 → declenche un **nouveau** POST /auth/refresh, pas de reuse stale)
- `test_concurrent_refresh_all_fail_together_when_refresh_rejects` (3 apiFetch paralleles, refresh 401 → les 3 throw `"Session expirée"`)

#### Bloc 3 : handleAuthFailure (AC2)

- `test_handleAuthFailure_cancels_guided_tour_when_active` (mock `uiStore.guidedTourActive = true` → verifier appel a `cancelTour` + addSystemMessage + router.push('/login'))
- `test_handleAuthFailure_skips_chat_message_when_no_guided_tour` (uiStore.guidedTourActive = false → pas d'appel `addSystemMessage`, seulement `router.push('/login')`)
- `test_handleAuthFailure_called_from_useDashboard_catch` (mock apiFetch throw "Session expirée" → fetchSummary catch → handleAuthFailure called)

#### Bloc 4 : Migration composables metier (AC6)

- `test_useDashboard_fetchSummary_delegates_to_apiFetch` (mock apiFetch, assert called with `/dashboard/summary`)
- `test_useEsg_assessment_calls_go_through_apiFetch` (au moins un assessment load)
- `test_useCarbon_assessment_calls_go_through_apiFetch`
- `test_useFinancing_matches_calls_go_through_apiFetch`

#### Bloc 5 : Scenario integre parcours guide (AC5)

- `test_multi_page_tour_silent_refresh_during_navigation` (scenario full : tourState='navigating', mock fetch sur `/dashboard/summary` 401 → refresh 200 → retry 200, assert zero addSystemMessage, tourState continue)
- `test_multi_page_tour_cancelled_when_refresh_expires` (scenario full : 401 → refresh 401 → cancelTour appele, addSystemMessage `"Votre session a expiré..."`, tourState='idle', router.push('/login'))

**And** la couverture du fichier `useAuth.ts` passe de 0% (aucun test) a >= 80% sur les lignes touchees (intercepteur + handleAuthFailure + single-flight).

**And** aucune modification backend n'est attendue (story **frontend-only** comme 7.1). **Pas** de migration Alembic, **pas** de modification de `backend/app/api/auth.py`, **pas** de changement de schemas.

**And** lint/typecheck : `cd frontend && npx nuxi typecheck` ne doit pas introduire de nouvelle erreur sur `useAuth.ts`, `useDashboard.ts`, `useEsg.ts`, `useCarbon.ts`, `useFinancing.ts` ni sur les tests.

### AC8 : Documentation dev — traceabilite AC → test + journal decisions

**Given** la story est complete
**When** on lit la section `## Dev Notes` mise a jour en fin de story
**Then** elle contient un tableau « AC → fichier(s) / ligne(s) / test(s) » reprenant le pattern des stories 6.3 / 6.4 / 7.1

**And** les **decisions de design** suivantes sont documentees dans Completion Notes :
- Pourquoi enrichir `apiFetch` plutot que creer un plugin Nuxt global (`$fetch` intercepteur)
- Pourquoi migrer **seulement** les 4 composables du guidage (vs tous) — dette technique identifiee
- Pourquoi single-flight avec variable module-level (vs closure)
- Pourquoi separer `handleAuthFailure` du `apiFetch` (separation of concerns : apiFetch ne connait pas le router)
- Pourquoi le refresh endpoint ne retourne pas de nouveau refresh_token (comportement backend **non change** dans cette story) et pourquoi c'est acceptable

## Tasks / Subtasks

- [x] Task 1 : Frontend — intercepteur 401 dans `apiFetch` (AC: #1, #3)
  - [x] 1.1 Ouvrir `frontend/app/composables/useAuth.ts`
  - [x] 1.2 En tete du fichier (hors `useAuth()`), declarer la variable module-level single-flight :
    - `let refreshPromise: Promise<boolean> | null = null`
    - `const AUTH_BYPASS_ENDPOINTS = ['/auth/login', '/auth/register', '/auth/refresh', '/auth/detect-country']`
    - `const SESSION_EXPIRED_MESSAGE = 'Session expirée, veuillez vous reconnecter.'`
    - `const CHAT_SESSION_EXPIRED_MESSAGE = 'Votre session a expiré. Veuillez vous reconnecter.'`
  - [x] 1.3 Modifier `apiFetch` : apres `const response = await fetch(...)`, intercepter 401 avant le throw actuel :
    ```typescript
    const isAuthEndpoint = AUTH_BYPASS_ENDPOINTS.some(ep => url.startsWith(ep))
    if (response.status === 401 && authStore.accessToken && !isAuthEndpoint) {
      // Single-flight refresh
      if (!refreshPromise) {
        refreshPromise = refresh().finally(() => { refreshPromise = null })
      }
      const ok = await refreshPromise
      if (!ok) {
        throw new Error(SESSION_EXPIRED_MESSAGE)
      }
      // Rejouer la requete avec le nouveau access_token
      const retryHeaders: Record<string, string> = {
        'Content-Type': 'application/json',
        ...((options.headers as Record<string, string>) || {}),
        Authorization: `Bearer ${authStore.accessToken}`,
      }
      const retry = await fetch(`${apiBase}${url}`, { ...options, headers: retryHeaders })
      if (!retry.ok) {
        const error: ApiError = await retry.json().catch(() => ({ detail: 'Erreur inconnue' }))
        throw new Error(error.detail || `Erreur ${retry.status}`)
      }
      return retry.json() as Promise<T>
    }
    ```
  - [x] 1.4 Verifier que le comportement hors 401 reste **strictement identique** (meme throw, meme message, meme parse JSON)
  - [x] 1.5 Note subtile : `refresh()` appelle `apiFetch<TokenResponse>('/auth/refresh', ...)` (ligne 71) — grace au bypass AUTH_BYPASS_ENDPOINTS, pas de recursion.

- [x] Task 2 : Frontend — `handleAuthFailure` exporte depuis `useAuth` (AC: #2)
  - [x] 2.1 Ajouter import : `import { useUiStore } from '~/stores/ui'`
  - [x] 2.2 Creer la fonction (a l'interieur de `useAuth`, apres `refresh`) :
    ```typescript
    async function handleAuthFailure(): Promise<void> {
      const uiStore = useUiStore()
      if (uiStore.guidedTourActive) {
        // Import dynamique SSR-safe (pattern deja en place dans useGuidedTour.ts)
        try {
          const { useGuidedTour } = await import('~/composables/useGuidedTour')
          useGuidedTour().cancelTour()
        } catch { /* cleanup best-effort */ }
        try {
          const { useChat } = await import('~/composables/useChat')
          useChat().addSystemMessage(CHAT_SESSION_EXPIRED_MESSAGE)
        } catch { /* cleanup best-effort */ }
      }
      router.push('/login')
    }
    ```
  - [x] 2.3 Exposer `handleAuthFailure` dans le return du composable (ligne 88-97)

- [x] Task 3 : Frontend — migration des 4 composables metier vers `apiFetch` (AC: #6)
  - [x] 3.1 `frontend/app/composables/useDashboard.ts` : remplacer le `fetch` direct par `const { apiFetch } = useAuth()` + `apiFetch<DashboardSummary>('/dashboard/summary')`. Supprimer `getHeaders()`. Ajouter dans le `catch (e)` : `if (e instanceof Error && e.message.includes('Session expirée')) { await handleAuthFailure() }`.
  - [x] 3.2 `frontend/app/composables/useEsg.ts` : auditer tous les `fetch()`, migrer chacun vers `apiFetch`. Supprimer `getHeaders()` local. Meme pattern de catch `"Session expirée"`.
  - [x] 3.3 `frontend/app/composables/useCarbon.ts` : idem.
  - [x] 3.4 `frontend/app/composables/useFinancing.ts` : idem (+ migration du blob via `apiFetchBlob` pour la fiche de preparation).
  - [x] 3.5 Grep sur chacun apres migration : zero match (uniquement apiFetch/apiFetchBlob).
  - [x] 3.6 Laisser `useApplications.ts`, `useCreditScore.ts`, `useActionPlan.ts`, `useReports.ts`, `useDocuments.ts`, `useCompanyProfile.ts`, `useChat.ts` **inchanges** (documente en Completion Notes).

- [x] Task 4 : Frontend — tests (AC: #7)
  - [x] 4.1 Creer `frontend/tests/composables/useAuth.refresh.test.ts` avec 19 tests (Blocs 1 a 5)
  - [x] 4.2 Pattern de reference : `useGuidedTour.resilience.test.ts` + `useChat.addSystemMessage.test.ts` (stubGlobal + vi.mock + vi.doMock pour stores metier)
  - [x] 4.3 Mock `globalThis.fetch` via `vi.stubGlobal('fetch', mockFetch)` avec `mockImplementation` selon scenario
  - [x] 4.4 Mock `useAuthStore` avec accessToken/refreshToken predefinis + reset dans beforeEach
  - [x] 4.5 Mock `useUiStore` pour les tests de Bloc 3 (guidedTourActive true/false)
  - [x] 4.6 Mock `useRouter` via `vi.stubGlobal('useRouter', ...)` — auto-import Nuxt, pattern eprouve
  - [x] 4.7 `npm run test -- useAuth.refresh` → **19/19 verts**
  - [x] 4.8 Suite complete : **330 tests verts, 0 regression**
  - [x] 4.9 `npx nuxi typecheck` : **aucune nouvelle erreur** sur `useAuth.ts`, `useDashboard.ts`, `useEsg.ts`, `useCarbon.ts`, `useFinancing.ts`, `useAuth.refresh.test.ts` (les erreurs TS restantes sont toutes pre-existantes : ScoreHistory, ProfileForm, useChat, useFocusTrap, pages/*)

- [x] Task 5 : Documentation traceabilite + finalisation (AC: #8)
  - [x] 5.1 Tableau AC → test complete (pattern story 7.1 deja present lignes 325-334)
  - [x] 5.2 Decisions de design documentees en Completion Notes
  - [x] 5.3 Dette technique : composables `useApplications`, `useCreditScore`, `useActionPlan`, `useReports`, `useDocuments`, `useCompanyProfile`, `useChat` non migres — story future `X-Y-migration-composables-vers-apifetch` proposee
  - [x] 5.4 `sprint-status.yaml` : `ready-for-dev` → `in-progress` (debut) → `review` (fin)
  - [x] 5.5 File List completee

## Dev Notes

### Contexte — deuxieme story de l'epic 7 (Resilience et edge cases)

L'epic 7 couvre trois scenarios degradees : **DOM absent** (7.1 ✅ done/review), **JWT expire** (7.2, cette story), **SSE perdue** (7.3 backlog). Les trois garantissent que le parcours guide ne laisse jamais l'utilisateur bloque.

Cette story **s'appuie sur l'existant** :
- `refresh()` est deja implementee (`useAuth.ts:67-81`) — pas a reimplementer.
- Le backend est deja fonctionnel — pas a modifier.
- Le middleware auth est deja en place — pas a modifier.

Elle comble **3 gaps** :

1. **Pas d'intercepteur 401** dans `apiFetch` → ajout d'une logique refresh+retry (AC1).
2. **Pas de single-flight** → variable module-level partagee (AC3).
3. **Pas de cleanup parcours** si refresh expire → `handleAuthFailure` integre avec `useGuidedTour` (AC2, AC5).

**Et un chantier collateral** : 4 composables metier ne passent pas par `apiFetch`, rendant l'intercepteur invisible pour eux. Migration ciblee (AC6).

### Mapping AC → fichier → test (pattern story 7.1)

| AC | Fichier impacte | Ligne(s) / zone | Test(s) |
|---|---|---|---|
| AC1 Intercepteur 401 | `useAuth.ts` | bloc `apiFetch` apres ligne 23 | `test_apiFetch_triggers_refresh_on_401_then_retries_with_new_token`, `test_apiFetch_throws_session_expired_when_refresh_fails`, `test_apiFetch_bypasses_refresh_for_auth_endpoints`, `test_apiFetch_does_not_retry_when_second_attempt_also_401`, `test_apiFetch_bypasses_refresh_when_no_access_token`, `test_apiFetch_returns_data_on_first_200_without_triggering_refresh` |
| AC2 handleAuthFailure + cleanup parcours | `useAuth.ts` | nouvelle fonction | `test_handleAuthFailure_cancels_guided_tour_when_active`, `test_handleAuthFailure_skips_chat_message_when_no_guided_tour`, `test_handleAuthFailure_called_from_useDashboard_catch` |
| AC3 Single-flight | `useAuth.ts` | variable module-level `refreshPromise` | `test_concurrent_401s_share_a_single_refresh_call`, `test_refreshPromise_reset_after_completion`, `test_concurrent_refresh_all_fail_together_when_refresh_rejects` |
| AC4 Driver.js mono-page sans API | `useAuth.ts` (comportement) | — | `test_driverjs_mono_page_tour_survives_jwt_expiration_without_api_call` |
| AC5 Multi-pages avec refresh transparent | `useAuth.ts` + `useGuidedTour.ts` (scenario) | — | `test_multi_page_tour_silent_refresh_during_navigation`, `test_multi_page_tour_cancelled_when_refresh_expires` |
| AC6 Migration 4 composables | `useDashboard.ts`, `useEsg.ts`, `useCarbon.ts`, `useFinancing.ts` | toutes les fonctions fetch | `test_useDashboard_fetchSummary_delegates_to_apiFetch`, `test_useEsg_*`, `test_useCarbon_*`, `test_useFinancing_*` |
| AC7 Tests + zero regression | `useAuth.refresh.test.ts` (CREER) | — | Suite complete verte |
| AC8 Doc traceabilite | Cette story (Dev Notes) | — | Revue manuelle |

### Messages exacts (FR32 / NFR9) — a respecter byte-for-byte

| Situation | Message (avec accents obligatoires) | Source |
|---|---|---|
| Throw apiFetch apres refresh echoue | `Session expirée, veuillez vous reconnecter.` | Nouveau, spec AC1 |
| Message chat si refresh expire pendant guidage | `Votre session a expiré. Veuillez vous reconnecter.` | Nouveau, spec AC2 (cote utilisateur — distinction volontaire du message d'erreur technique) |

**Test de validation** : grep sur les 2 messages dans `useAuth.ts` et `useAuth.refresh.test.ts` → chacun apparait au moins une fois. Les tests substring-matchent sur `"Session expirée"` et `"Votre session a expiré"` respectivement.

### Constantes a declarer (module-level, pattern story 6.4 / 7.1)

```typescript
// Dans useAuth.ts, hors de useAuth()
let refreshPromise: Promise<boolean> | null = null

const AUTH_BYPASS_ENDPOINTS = ['/auth/login', '/auth/register', '/auth/refresh', '/auth/detect-country']
const SESSION_EXPIRED_MESSAGE = 'Session expirée, veuillez vous reconnecter.'
const CHAT_SESSION_EXPIRED_MESSAGE = 'Votre session a expiré. Veuillez vous reconnecter.'
```

**Pourquoi module-level pour `refreshPromise`** : `useAuth()` est re-instancie a chaque appel (composable pattern), donc une variable interne au composable ne partagerait pas l'etat entre deux appels paralleles. Le pattern module-level est deja utilise par `useChat.ts` (story 1.1) et `useGuidedTour.ts` (stories 5.x / 6.x) — coherent.

### Patterns de reference (stories precedentes)

- **Import dynamique SSR-safe** pour briser les cycles :
  ```typescript
  const { useChat } = await import('~/composables/useChat')
  useChat().addSystemMessage(...)
  ```
  Pattern deja utilise dans `useGuidedTour.ts:250, 396, 487, 502, 596` — reutiliser tel quel dans `handleAuthFailure`.

- **Test fake-timers pour Promise + setTimeout** : pattern story 6.4 / 7.1 avec `vi.useFakeTimers()` + `vi.advanceTimersByTimeAsync(ms)`. **Pour 7.2 les timers ne sont pas critiques** (pas de setTimeout dans l'intercepteur) — utiliser `vi.fn()` sur fetch + resolve/reject synchrone.

- **Test concurrency avec `Promise.all`** : pattern pour le single-flight — lancer 3 apiFetch, assert un seul call `/auth/refresh`.

### Fichiers attendus

| Fichier | Action | Justification |
|---|---|---|
| `frontend/app/composables/useAuth.ts` | MODIFIER | Intercepteur 401 + single-flight + handleAuthFailure + 3 constantes module-level |
| `frontend/app/composables/useDashboard.ts` | MODIFIER | Migration `fetch()` → `apiFetch`, suppression getHeaders, catch Session expirée |
| `frontend/app/composables/useEsg.ts` | MODIFIER | Idem |
| `frontend/app/composables/useCarbon.ts` | MODIFIER | Idem |
| `frontend/app/composables/useFinancing.ts` | MODIFIER | Idem |
| `frontend/tests/composables/useAuth.refresh.test.ts` | CREER | ~17 tests (5 blocs) |

**Pas de fichier backend modifie** (story frontend-only). **Pas** de migration Alembic, **pas** de changement d'API backend, **pas** de nouveau composant Vue.

### Intelligence story 7.1 (previous-story)

Points actionnables herites :

- **Pattern constantes module-level commentees** (story 7.1 : 4 constantes timeout) → meme pattern pour `refreshPromise` + 3 messages/liste.
- **Pattern import dynamique SSR-safe** — applique dans `handleAuthFailure` pour importer `useGuidedTour` et `useChat` sans cycle.
- **Pattern Dev Notes AC → test mapping** — reproduire pour coherence.
- **Pattern garde avec flag pour eviter double-action** (story 7.1 `if (!cancelled) { addSystemMessage(...) }`) → ici `if (uiStore.guidedTourActive) { ... }` pour eviter les notifications hors-guidage.
- **Pattern tests avec mocks de composables** — `vi.mock('~/composables/useChat', () => ({ useChat: () => ({ addSystemMessage: vi.fn() }) }))` et meme pour `useGuidedTour`.

### Git intelligence (5 derniers commits)

- `2278f35 6-4-frequence-adaptative-des-propositions-de-guidage: done` — modifications `useGuidedTour.ts` + `useChat.ts`. Zero impact sur `useAuth.ts`.
- `2bc3e15 6-3-consentement-via-widget-interactif-et-declenchement-direct` — `useChat.ts` modifie. Import dynamique `useChat` dans handleAuthFailure doit verifier que `addSystemMessage` reste exporte (verifie : ligne 739-747 de `useChat.ts`).
- `b7f6d62 6-1-tool-langchain-trigger-guided-tour-et-marker-sse` — backend trigger tour. Aucun impact.
- `5277eb1 5-4-interruption-du-parcours-et-popover-custom` — intro `cancelTour`, `interruptTour`. **Dependance directe** : `handleAuthFailure` appelle `cancelTour`.
- `24b5862 5-1-composable-useguidedtour-machine-a-etats-et-execution-mono-page` — intro `tourState`. **Invariant a respecter** dans les tests : apres `cancelTour`, tourState doit etre `'idle'`.

**Verification `useChat.ts`** : `addSystemMessage` signature `addSystemMessage(content: string): void` — utilisation deja rodee par useGuidedTour dans les stories 5.x et 7.1. OK.

**Verification `useGuidedTour.ts`** : `cancelTour()` signature `cancelTour(): Promise<void> | void` — effectue `driver.destroy()`, `cleanupDriverResiduals()`, reset UI flags, `tourState.value = 'idle'`. OK pour l'appel depuis `handleAuthFailure`.

### Latest tech information

- **Fetch API** : `Response.status === 401` est le discriminant fiable. Note : certains backends renvoient 401 ET 403 selon expired vs invalid — le backend ESG Mefali renvoie toujours **401** pour "access_token expired" (cf. `backend/app/core/security.py` + `get_current_user` dans `backend/app/api/deps.py`). **Ne pas intercepter le 403** (reserves aux autorisations metier — ex. "role insuffisant").
- **Vitest `vi.spyOn(globalThis, 'fetch')`** — preferer `globalThis` a `global` pour la compatibilite Nuxt / Vite. Pattern deja utilise dans des stories precedentes.
- **Module-level state en Nuxt 4** : attention a la SSR — le fichier `useAuth.ts` est importe cote serveur, mais `authStore.accessToken` est `null` cote SSR (localStorage inexistant), donc le code `if (response.status === 401 && authStore.accessToken && !isAuthEndpoint)` est naturellement bypasse cote serveur. Aucun risque.
- **Backend refresh endpoint sans rotation** : le choix **actuel** de ne pas retourner de nouveau refresh_token a chaque refresh est documente dans `backend/app/api/auth.py:125-128`. Cette story **ne modifie pas** ce comportement. Une evolution future (rotation) serait transparente cote frontend grace a `authStore.setTokens(tokens)` ligne 75 qui gere deja le cas `tokens.refresh_token !== undefined`.

### Project Structure Notes

- Alignement Nuxt 4 : fichier source dans `frontend/app/composables/`, tests dans `frontend/tests/composables/*.test.ts`. Pattern conforme aux stories 5.x, 6.x, 7.1.
- Conformite rules/typescript : `type` pour unions, messages FR avec accents, pas de `any` (utiliser `unknown` + narrowing pour le catch), pas de `console.log`.

### References

- Source epic : `_bmad-output/planning-artifacts/epics.md:1112-1145` (Epic 7 Story 7.2 avec BDD + exigences techniques)
- Source PRD :
  - `_bmad-output/planning-artifacts/prd.md:150` (guidage + scores + auth existante)
  - `_bmad-output/planning-artifacts/prd.md:164` (matrice risque JWT expire → FR32/NFR9)
  - `_bmad-output/planning-artifacts/prd.md:362` (FR32 — renouvellement automatique)
  - `_bmad-output/planning-artifacts/prd.md:386` (NFR9 — aucune interruption visible)
- Source architecture :
  - `_bmad-output/planning-artifacts/architecture.md:38` (FR29-FR35 resilience + renouvellement JWT)
  - `_bmad-output/planning-artifacts/architecture.md:45` (NFR8-NFR11 securite + renouvellement transparent)
  - `_bmad-output/planning-artifacts/architecture.md:1003` (couverture NFR)
  - `_bmad-output/planning-artifacts/architecture.md:1014` (**gap identifie** : logique refresh "a completer")
- Story precedente impactant la logique :
  - `_bmad-output/implementation-artifacts/7-1-gestion-des-elements-dom-absents-et-timeout-de-chargement.md` (pattern constantes module-level, pattern import dynamique useChat dans catch, pattern tests avec mocks composables)
  - `_bmad-output/implementation-artifacts/5-4-interruption-du-parcours-et-popover-custom.md` (`cancelTour`, `interruptTour`, cleanup proprement — dependance AC2)
- Code de reference actuel :
  - `frontend/app/composables/useAuth.ts:11-31` (`apiFetch` — a enrichir)
  - `frontend/app/composables/useAuth.ts:67-81` (`refresh` — a reutiliser tel quel)
  - `frontend/app/stores/auth.ts:12-24, 30-38` (`setTokens`, `clearAuth`)
  - `backend/app/api/auth.py:115-129` (`POST /auth/refresh` — retourne access_token seul, pas rotation)
  - `frontend/app/middleware/auth.global.ts:3-23` (redirect /login — sera complementaire, pas remplace)
  - `frontend/app/composables/useDashboard.ts:11-41` (exemple migration fetch → apiFetch)
  - `frontend/app/composables/useGuidedTour.ts` (pour `cancelTour` signature et `tourState` transitions)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context) — claude-opus-4-6[1m]

### Debug Log References

- `frontend && npm run test -- useAuth.refresh` → 19/19 verts (56ms)
- `frontend && npm run test` → 330/330 verts (0 regression, 5.74s)
- `frontend && npx nuxi typecheck` → zero nouvelle erreur sur les 5 fichiers modifies + 1 fichier cree (erreurs existantes sur ScoreHistory, ProfileForm, useChat, useFocusTrap, pages/* non liees a cette story)

### Completion Notes List

#### Decisions de design (AC8)

1. **Enrichissement de `apiFetch` vs plugin Nuxt `$fetch` global** — Choix d'enrichir `apiFetch` dans `useAuth.ts` plutot que d'injecter un intercepteur via un plugin Nuxt. Rationale : (a) le code existant expose deja `refresh()` dans `useAuth`, rester co-localise evite de disperser la logique auth ; (b) un plugin global appliquerait l'intercepteur a TOUS les `$fetch`, y compris les appels Nuxt internes (ex. `$fetch` en SSR), ce qui creerait des effets de bord difficiles a tester ; (c) l'intercepteur par composable laisse les composants non-migres explicitement visibles (dette technique tracee), alors qu'un plugin global masquerait les composables qui n'utilisent pas `$fetch`.

2. **Migration ciblee des 4 composables du guidage uniquement** — Les composables `useDashboard`, `useEsg`, `useCarbon`, `useFinancing` sont ceux utilises par les parcours multi-pages de l'epic 5/6. Migrer uniquement ces 4 limite le diff et le risque de regression. **Dette technique** : `useApplications`, `useCreditScore`, `useActionPlan`, `useReports`, `useDocuments`, `useCompanyProfile`, `useChat` n'utilisent pas encore `apiFetch` → story future `X-Y-migration-composables-vers-apifetch` proposee (hors epic 7).

3. **Single-flight via variable module-level** — `let refreshPromise: Promise<boolean> | null = null` declare hors de `useAuth()`. Rationale : `useAuth()` est re-instancie a chaque appel (pattern composable Vue/Nuxt), donc une variable interne au composable ne partagerait pas l'etat entre deux appels paralleles. Le pattern module-level est deja utilise par `useChat.ts` (story 1.1) et `useGuidedTour.ts` — coherent avec le reste du codebase.

4. **Separation `handleAuthFailure` / `apiFetch`** — `apiFetch` ne connait pas le router : il throw `"Session expirée, veuillez vous reconnecter."` et laisse au caller (composables metier) la responsabilite d'appeler `handleAuthFailure()`. Cela evite un couplage fort (apiFetch → router) et permet aux composables non-guides de catcher l'erreur et afficher un toast au lieu de rediriger brutalement.

5. **Backend refresh endpoint sans rotation** — Le endpoint `POST /auth/refresh` actuel ne retourne PAS de nouveau `refresh_token` (seulement un nouveau `access_token`). Ce comportement **n'est pas modifie** dans cette story. C'est acceptable car : (a) `authStore.setTokens(tokens)` gere deja le cas `tokens.refresh_token !== undefined` — une future evolution (rotation cote backend) sera transparente cote frontend ; (b) l'absence de rotation simplifie le single-flight (pas d'invalidation en cascade de l'ancien refresh_token) ; (c) le refresh_token a une duree de vie de 30 jours (config backend), suffisante pour les parcours utilisateurs.

#### Ajustements design hors-brief (declares)

- **`apiFetchBlob` ajoute en complement** — La fiche de preparation financement (`/financing/matches/{id}/preparation-sheet`) retourne un PDF Blob, incompatible avec `apiFetch` qui parse JSON. J'ai ajoute une variante `apiFetchBlob` qui reproduit le cycle 401 → refresh → retry pour les endpoints binaires. Cela evite une exception a la regle « zero fetch direct » dans `useFinancing.ts`.

- **Classe `ApiFetchError` exportee** — Pour que `useFinancing.fetchMatches` puisse distinguer le 428 metier (« evaluation ESG requise ») d'une erreur technique, `apiFetch` throw desormais une `ApiFetchError` enrichie (`status`, `body`) au lieu d'une `Error` generique. Les callers existants continuent de fonctionner (ApiFetchError extends Error) ; les nouveaux callers peuvent faire `e instanceof ApiFetchError && e.status === 428`.

- **Helper `extractDetailMessage`** — Parse proprement `{detail: string}` (format classique FastAPI) vs `{detail: {message: string}}` (format 428 metier). Remplace l'ancien `new Error(error.detail || "Erreur {status}")` qui affichait `"[object Object]"` quand `detail` etait un objet.

#### Dette technique

- **Composables non-migres** : `useApplications`, `useCreditScore`, `useActionPlan`, `useReports`, `useDocuments`, `useCompanyProfile`, `useChat` — tous emettent encore des `fetch()` directs avec `getHeaders()` local. Ils ne beneficient pas de l'intercepteur 401 introduit dans cette story → si un utilisateur tombe sur un 401 depuis une page hors guidage (ex. `/applications`), pas de refresh automatique, l'erreur remonte brute. Story future proposee : `X-Y-migration-composables-vers-apifetch` (hors epic 7).

- **Backend sans rotation refresh_token** : voir decision #5. A traiter dans une future story de durcissement securite si besoin.

### File List

**Modifies** :
- `frontend/app/composables/useAuth.ts` — Intercepteur 401 + single-flight + `handleAuthFailure` + `apiFetchBlob` + classe `ApiFetchError` + helper `extractDetailMessage` + 3 constantes module-level
- `frontend/app/composables/useDashboard.ts` — Migration `fetch()` → `apiFetch`, suppression `getHeaders()`, catch `Session expirée`
- `frontend/app/composables/useEsg.ts` — Idem (5 fonctions migrees) + helper `handleError` mutualise
- `frontend/app/composables/useCarbon.ts` — Idem (7 fonctions migrees)
- `frontend/app/composables/useFinancing.ts` — Idem (10 fonctions dont fiche de preparation via `apiFetchBlob`), gestion 428 via `ApiFetchError.status`
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — Transition statut `ready-for-dev` → `in-progress` → `review`

**Crees** :
- `frontend/tests/composables/useAuth.refresh.test.ts` — 19 tests Vitest (5 blocs : intercepteur 401, single-flight, handleAuthFailure, scenarios guidage, migration composables)

**Pas de fichier backend modifie** (story frontend-only comme 7.1). Aucune migration Alembic, aucune modification de `backend/app/api/auth.py`, aucun changement de schema.

### Change Log

| Date | Auteur | Description |
|---|---|---|
| 2026-04-14 | Scrum Master (Opus 4.6) | Story 7.2 creee — intercepteur JWT 401 → refresh → retry dans apiFetch, single-flight module-level, handleAuthFailure avec cleanup parcours guide, migration des 4 composables metier (useDashboard/useEsg/useCarbon/useFinancing), ~17 tests Vitest, 0 regression cible. |
| 2026-04-14 | Code Review (Opus 4.6) | Revue adversariale multi-layer (Blind+Edge+Auditor) → 7 patches appliques : retry 401 → SessionExpiredError + clearAuth (CRITIQUE), single-flight handleAuthFailure (idempotence), navigateTo() isomorphe, apiFetchBlob parse JSON error body, classe sentinel `SessionExpiredError` + migration 4 composables, fix test `is401Turn`, console.warn dev sur catches. 20/20 tests useAuth.refresh verts, 331/331 suite complete verte, zero nouvelle erreur typecheck. Status → done. |

### Review Findings

Revue adversariale multi-layer (Blind Hunter + Edge Case Hunter + Acceptance Auditor) effectuee le 2026-04-14 sur le diff de la story (uncommitted). 29 findings uniques apres deduplication — aucune violation bloquante d'AC, mais plusieurs defauts de robustesse.

#### Patch — fixes appliques (2026-04-14)

- [x] [Review][Patch] **[CRITIQUE] Retry 401 apres refresh → `handleAuthFailure` jamais declenche** [`useAuth.ts`] — ✅ **Fixed** : `apiFetch` et `apiFetchBlob` detectent maintenant `retry.status === 401`, appellent `authStore.clearAuth()` et throw `SessionExpiredError`. Meme semantique que refresh-fail.
- [x] [Review][Patch] **[HIGH] `handleAuthFailure` non-idempotent sur appels paralleles** [`useAuth.ts`] — ✅ **Fixed** : single-flight module-level `authFailurePromise`. N appels concurrents partagent la meme promise → 1 seul `cancelTour`, 1 seul `addSystemMessage`, 1 seul `navigateTo`. Test `test_handleAuthFailure_is_idempotent_on_concurrent_calls` ajoute.
- [x] [Review][Patch] **[HIGH] `router.push('/login')` non-isomorphe** [`useAuth.ts`] — ✅ **Fixed** : remplace par `await navigateTo('/login')` (Nuxt isomorphe SSR+client).
- [x] [Review][Patch] **[MEDIUM] `apiFetchBlob` perd le body JSON d'erreur** [`useAuth.ts`] — ✅ **Fixed** : lit `await response.json().catch(() => null)` avant throw, utilise `extractDetailMessage` pour le message, symetrie complete avec `apiFetch`.
- [x] [Review][Patch] **[MEDIUM] Detection « Session expirée » par `message.includes()` fragile** [4 composables] — ✅ **Fixed** : classe sentinel `SessionExpiredError extends Error` exportee depuis `useAuth.ts`. Les 4 composables (`useDashboard`, `useEsg`, `useCarbon`, `useFinancing`) detectent desormais via `e instanceof SessionExpiredError`. Bonus : `handleError()` skip `error.value` sur session expirée pour eviter un flash d'erreur avant redirection (NFR9).
- [x] [Review][Patch] **[MEDIUM] Test `test_refreshPromise_reset_after_completion` — logique `is401Turn` fragile** — ✅ **Fixed** : remplace `mockFetch.mock.calls.filter(...).length === 1` par un `Map<string, number>` explicite `seenByUrl`.
- [x] [Review][Patch] **[LOW] `handleAuthFailure` — `catch {}` muet sans log** [`useAuth.ts`] — ✅ **Fixed** : ajout de `if (import.meta.dev) console.warn(...)` dans les 2 catches d'import dynamique.

#### Patch — non appliques (a la revue)

- [x] [Review][Patch][N/A] **[HIGH] `cancelTour()` et `addSystemMessage()` non awaites** — Verification : les deux fonctions retournent `void` (synchrones) dans `useGuidedTour.ts:643` et `useChat.ts:739`. L'ordre AC2 (message chat avant redirection) est deja garanti par la sequence synchrone post-`await import(...)`. Pas de changement necessaire.
- [x] [Review][Patch][N/A] **[MEDIUM] `Content-Type: application/json` override sur retry** — Verification : l'ordre est deja symetrique entre requete initiale (`useAuth.ts:48-51`) et retry (`useAuth.ts:76-79`) — `'Content-Type'` est d'abord pose, puis le spread `...options.headers` permet a l'appelant d'overrider. Pas de changement necessaire.

#### Defer — pre-existant ou gap non bloquant

- [x] [Review][Defer] **`refreshPromise` module-level risque de partage SSR** [`useAuth.ts:49`] — deferred, le composable est client-only en pratique, mais pas de guard `import.meta.client` explicite. A traiter dans une story de durcissement SSR future.
- [x] [Review][Defer] **`useCarbon.fetchBenchmark` / `useEsg.fetchBenchmark` avalent toutes les erreurs non-session-expirée en retournant `null`** [`useCarbon.ts:93-98`, `useEsg.ts:90-96`] — deferred, comportement pre-existant (avant migration). L'UI ne peut pas distinguer 404 vs 500. A traiter globalement dans une story de gestion d'erreurs.
- [x] [Review][Defer] **Tests manquants : cycle 401 sur `apiFetchBlob`, `/auth/me`, echec import dynamique dans `handleAuthFailure`** [`useAuth.refresh.test.ts`] — deferred, les scenarios principaux sont couverts (19 tests verts), ces edge cases peuvent etre ajoutes en story de test-hardening ou lors du prochain bug s'il en emerge.
- [x] [Review][Defer] **Composables non-migres (`useApplications`, `useCreditScore`, `useActionPlan`, `useReports`, `useDocuments`, `useCompanyProfile`, `useChat`) ne beneficient pas de l'intercepteur 401** — deferred, dette technique deja documentee dans Completion Notes § Dette technique. Story future `X-Y-migration-composables-vers-apifetch` proposee.

#### Dismiss (pour memoire)

- Ecarts d'organisation tests (Blocs 4/5 inverses, nom `test_handleAuthFailure_called_from_useDashboard_catch`) — tests presents, scenarios couverts, simple divergence cosmetique.
- Ajustements declares dans Completion Notes (`apiFetchBlob`, `ApiFetchError`) — acceptes.
- `/auth/refresh-extended` false match, URL absolue non bypassee — preventifs, aucun call site concerne aujourd'hui.
- `router.push('/login')` alors que deja sur `/login` — warning Vue Router benin.
- EC1 (boucle recursive theorique refresh dans refresh) — `AUTH_BYPASS_ENDPOINTS` couvre `/auth/refresh` correctement.
- EC2/EC3 (rejet de `refreshPromise` par exception `setTokens`) — `refresh()` catch interne rend le scenario non realiste.
- `useFinancing.expressInterest` mentionne dans la spec mais inexistant dans le code — erreur de la spec, pas du code.
- `extractDetailMessage` asymetrique sur 428 useFinancing — comportement actuel correct avec fallback.
| 2026-04-14 | Dev Agent (Opus 4.6) | Story 7.2 implementee — `useAuth.ts` enrichi (intercepteur 401, single-flight, handleAuthFailure, apiFetchBlob, ApiFetchError). Migration complete des 4 composables metier (useDashboard/useEsg/useCarbon/useFinancing). 19 tests Vitest ecrits, 330/330 verts, 0 regression. Statut : `review`. |
