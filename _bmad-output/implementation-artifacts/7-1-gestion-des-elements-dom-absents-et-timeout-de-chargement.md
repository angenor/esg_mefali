# Story 7.1 : Gestion des elements DOM absents et timeout de chargement

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

En tant qu'utilisateur avec une connexion lente,
je veux que le parcours guide gere gracieusement les situations ou un element n'est pas encore charge,
afin de ne pas rester bloque sur un ecran fige (FR31, NFR16, NFR18).

## Acceptance Criteria

### AC1 : Retry DOM 3x500ms pour une etape mono-page (NFR18)

**Given** un parcours guide pointe un element dont le selector n'est PAS present dans le DOM au moment ou le step est atteint (donnees async non chargees, element conditionnel `v-if`, etc.)
**When** `waitForElement(selector)` est appele dans la boucle mono-page (ligne 497 de `frontend/app/composables/useGuidedTour.ts`)
**Then** le systeme effectue exactement **3 retries** (cumul 4 tentatives avec le premier essai post-`setTimeout(0)`) espaces de **500ms** chacun

**And** si l'element apparait entre deux retries, la promise resout immediatement l'`Element` trouve et le step s'execute normalement (pas d'attente restante)

**And** la constante `DOM_RETRY_COUNT = 3` et `DOM_RETRY_INTERVAL_MS = 500` sont **extraites au niveau module** en haut de `useGuidedTour.ts` (apres `MAX_STATS_CAP`, avec commentaire `// FR31/NFR18 — retry DOM absent`) pour eliminer les literals magiques.

**And** si cancelled est detecte entre deux retries, la promise resout `null` **immediatement** (pas d'attente des 500ms restants) — actuellement `waitForElement` ne check PAS `cancelled` contrairement a `waitForElementExtended` ligne 172 (**gap a combler**).

### AC2 : Skip gracieux apres echec retry mono-page (FR31)

**Given** `waitForElement` a retourne `null` apres les 3 retries (element toujours absent)
**When** la boucle de steps atteint `if (!element)` ligne 501
**Then** le systeme appelle `useChat().addSystemMessage('Je n\'ai pas pu pointer cet element. Passons a la suite.')` — **message FR31 exact, avec accents** (e accent aigu/grave)

**And** le handler execute `continue` pour passer a l'etape suivante (l'etape echouee est skippee silencieusement, le parcours N'EST PAS interrompu)

**And** `tourState.value` reste a `'highlighting'` (pas de transition vers `'interrupted'`)

**And** le message est ajoute **localement** via `addSystemMessage` (ligne 739-747 de `useChat.ts`, message role='assistant' non persiste serveur, non envoye au LLM — coherent avec le pattern existant ligne 504)

**And** si plusieurs etapes consecutives ont leur element absent, CHAQUE skip genere SON propre message systeme (pas de deduplication) — traceabilite UX.

### AC3 : Retry silencieux a 5s puis timeout dur a 10s pour le chargement de page (NFR16)

**Given** une navigation multi-pages a ete declenchee via `navigateTo(step.route)` et `waitForElementExtended(step.selector, timeoutMs)` est en cours
**When** l'element cible n'apparait **pas** dans les **5 premieres secondes**
**Then** un **retry silencieux** est effectue (pas de message systeme, pas de transition d'etat) — l'implementation doit **loguer** `console.debug('[useGuidedTour] soft retry page load', step.route)` (review 6.4 P15 — remplacer console.warn par console.debug si on ne veut pas polluer les tests)

**And** le retry silencieux consiste a continuer le polling `querySelector` 500ms jusqu'a l'echeance **10s** (deuxieme fenetre) — **pas** de re-navigation (evite boucle navigate/navigate).

**Given** l'element n'est TOUJOURS PAS apparu apres **10 secondes cumulees**
**When** `waitForElementExtended` retourne `null` (ligne 392 pour entryStep, ligne 482 pour step.route)
**Then** `addSystemMessage('La page met trop de temps a charger. Reessayez plus tard.')` est appele — **message NFR16 exact, pas le message actuel** (« La page n'a pas pu se charger correctement. Le guidage est interrompu. » — ligne 398, 489 a **remplacer**)

**And** `interruptTour(uiStore)` est appele → widget reapparait, `tourState.value = 'interrupted'` → transition auto vers `'idle'` apres 500ms (ligne 231)

**And** `startTour` retourne `false` pour que le handler appelant ne credite PAS l'acceptance (review 6.4 P4 invariant).

**And** les constantes `PAGE_LOAD_SOFT_RETRY_MS = 5000` et `PAGE_LOAD_HARD_TIMEOUT_MS = 10000` sont extraites au niveau module (eliminer les `10000` hardcodes lignes 392 et 482).

**And** `waitForElementExtended` est **etendue** (signature ou nouveau wrapper) pour emettre un `console.debug` a la frontiere soft = 5s (pattern : calculer `halfway = PAGE_LOAD_SOFT_RETRY_MS` a l'entree, logguer si atteint). **Alternative acceptable** : nouveau helper `waitForElementWithSoftRetry(selector, softMs, hardMs)` qui delegue a l'actuel `waitForElementExtended` apres log — au choix du dev selon la clarte du diff.

### AC4 : Try/catch global avec message empathique si Driver.js crash (FR31)

**Given** Driver.js leve une exception inattendue pendant l'appel `driverInstance.highlight(...)` ou `driver(...)` (ex. selector invalide, option deprecated, crash interne lib)
**When** l'erreur est attrapee par le bloc `catch` global (ligne 570 de `useGuidedTour.ts`)
**Then** le handler actuel est **etendu pour appeler** `addSystemMessage('Le guidage a rencontre un probleme. Le chat est toujours disponible.')` **avant** le reset d'etat — actuellement le catch reset le state mais **N'INFORME PAS** l'utilisateur (gap FR31 a combler).

**And** l'erreur est loggee via `console.warn('[useGuidedTour] tour crashed', err)` avec l'objet error complet — on sort du `catch {}` muet (coherent avec review 6.4 P15 sur `persistGuidanceStats`).

**And** l'ordre du catch devient :
1. `console.warn` avec l'error
2. `addSystemMessage(message-empathique)` (import dynamique de `useChat` comme lignes 250, 396, 487, 502 — pattern SSR-safe deja en place)
3. Cleanup existant : `clearCountdownTimer`, `unmountAllPopoverApps`, `driverInstance.destroy`, `cleanupDriverResiduals`
4. Reset UI : `cachedUiStore.chatWidgetMinimized = false`, `cachedUiStore.guidedTourActive = false`
5. Resolve `onRetractComplete?.()` pour eviter deadlock F2 (deja en place)
6. `tourState.value = 'idle'` (pas `'interrupted'` car le catch court-circuite `interruptTour` — **confirme le comportement actuel**, ligne 589)

**And** si l'erreur survient pendant le user-initiated cancelTour (ex. double destroy), le catch **ne doit PAS** emettre le message (distinguer par la presence de `cancelled === true` : `if (!cancelled) { addSystemMessage(...) }` pour eviter de spammer l'utilisateur apres qu'il a appuye Escape).

### AC5 : Cancelled-aware dans `waitForElement` (parite avec `waitForElementExtended`)

**Given** `waitForElement` est dans sa boucle de retry (3 iterations)
**When** `cancelled = true` (parcours interrompu par user ou timeout page parent)
**Then** la boucle `for (let i = 0; i < 3; i++)` insere une garde `if (cancelled) return null` **avant** chaque `setTimeout(500)` et **apres** chaque `querySelector` (pattern strict identique a `waitForElementExtended` ligne 172)

**And** le test `test_waitForElement_returns_null_immediately_when_cancelled` (cf AC6) verifie qu'une interruption pendant le retry 2 retourne `null` sans attendre les 500ms du retry 3.

### AC6 : Tests unitaires >= 80 % et zero regression (NFR19)

**Given** la suite de tests frontend existante (285+ tests verts apres story 6.4)
**When** on execute `cd frontend && npm run test` (Vitest)
**Then** zero regression sur les 4 fichiers existants de `useGuidedTour.*.test.ts` (`useGuidedTour.test.ts`, `useGuidedTour.retract.test.ts`, `useGuidedTour.navigation.test.ts`, `useGuidedTour.adaptive-frequency.test.ts`)

**And** un nouveau fichier `frontend/tests/composables/useGuidedTour.resilience.test.ts` est cree avec AU MINIMUM les tests suivants :

#### Bloc 1 : `waitForElement` retry + cancelled

- `test_waitForElement_returns_element_on_first_try_when_present`
- `test_waitForElement_retries_3_times_with_500ms_interval_when_absent` (verifier via `vi.useFakeTimers()` + `vi.advanceTimersByTime(500)`)
- `test_waitForElement_resolves_immediately_when_element_appears_at_retry_2` (insertion DOM entre 2 timers)
- `test_waitForElement_returns_null_after_3_failed_retries`
- `test_waitForElement_returns_null_immediately_when_cancelled_during_retry` (set `cancelled=true` apres le 1er retry → doit retourner `null` sans consommer les 500ms suivants — AC5)

#### Bloc 2 : Skip gracieux mono-page (AC2)

- `test_mono_page_step_with_missing_element_adds_system_message_and_continues` (spy sur `addSystemMessage`, verifier le message exact `"Je n'ai pas pu pointer cet élément. Passons à la suite."` avec accents)
- `test_mono_page_step_skipped_does_not_transition_to_interrupted` (verifier `tourState.value === 'highlighting'` apres skip)
- `test_multiple_consecutive_missing_elements_emit_one_message_per_skip` (parcours 3 steps tous absents → 3 appels `addSystemMessage` distincts)

#### Bloc 3 : Soft retry + hard timeout page load (AC3)

- `test_page_load_resolves_before_soft_retry_window` (element apparait a 3s → pas de log debug, pas de message systeme, parcours continue)
- `test_page_load_soft_retry_logs_debug_at_5_seconds` (spy sur `console.debug` → appelle une fois quand on passe 5s)
- `test_page_load_hard_timeout_adds_system_message_and_interrupts` (element jamais present → a 10s message `"La page met trop de temps à charger. Réessayez plus tard."` + `interruptTour` appele + retour `false`)
- `test_page_load_hard_timeout_sets_tour_state_to_interrupted_then_idle` (chaine `'navigating' → 'waiting_dom' → 'interrupted' → 'idle'` apres 500ms `setTimeout`)

#### Bloc 4 : Catch global Driver.js crash (AC4)

- `test_driver_highlight_throws_triggers_system_message_and_cleanup` (mock `driverInstance.highlight` pour throw → verifier ordre : `console.warn`, `addSystemMessage("Le guidage a rencontré un problème. Le chat est toujours disponible.")`, destroy, reset flags UI, `tourState === 'idle'`)
- `test_driver_crash_logs_error_object_not_empty` (verifier signature `console.warn('[useGuidedTour] tour crashed', errorInstance)`)
- `test_driver_crash_during_user_cancel_does_NOT_emit_message` (mettre `cancelled=true` avant le throw → `addSystemMessage` NE doit PAS etre appele — garde AC4)
- `test_driver_loadDriver_rejection_triggers_cleanup_message` (mock `loadDriver` pour reject → meme message + cleanup)

#### Bloc 5 : Constantes module-level (AC1, AC3)

- `test_constants_exported_or_accessible_via_internal` (si exportees : `import { DOM_RETRY_COUNT } from '~/composables/useGuidedTour'` et assert `=== 3`). Si non exportees → verifier via comportement (test de timing fake-timers).
- `test_literal_numbers_removed_from_implementation` (test de code reading — optionnel : lire le fichier source, regex sur `10000|500(?!\s*ms.?const)` → echec si trouve dans `startTour`. **Pattern hygiene** non bloquant.)

**And** la couverture du fichier `useGuidedTour.ts` passe de son niveau actuel (apres 6.4) a un delta positif sur les lignes 150-180 (`waitForElement*`), 389-401, 481-492 (hard timeout), 570-593 (catch global) — verifie par `npm run test -- --coverage` ou equivalent Vitest.

**And** aucune modification du backend n'est attendue (story frontend-only). **Pas** de nouveau test backend, **pas** de migration Alembic, **pas** de modification de `guided_tour.py` ou `system.py`.

**And** lint : `cd frontend && npm run lint` (ou l'equivalent projet si present) passe sur `useGuidedTour.ts` + `useGuidedTour.resilience.test.ts`.

### AC7 : Documentation dev — traceabilite AC → test + journal decisions

**Given** la story est complete
**When** on lit la section `## Dev Notes` mise a jour en fin de story
**Then** elle contient un tableau « AC → fichier(s) / ligne(s) / test(s) » reprenant le pattern des stories 6.3 / 6.4 pour que la prochaine story (7.2 ou 7.3) puisse etendre le meme pattern sans recherche.

**And** les **decisions de design** suivantes sont documentees dans Completion Notes :
- Pourquoi extraire des constantes module-level plutot qu'inlinera
- Pourquoi `console.debug` (et pas `warn`) pour le soft retry 5s (evite bruit test)
- Pourquoi ajouter le check `cancelled` dans `waitForElement` (parite avec `waitForElementExtended`)
- Pourquoi `addSystemMessage` dans le catch plutot que `interruptTour` (comportement catch actuel different, on ne veut pas double cleanup)

## Tasks / Subtasks

- [x] Task 1 : Frontend — extraction des constantes timeout module-level (AC: #1, #3)
  - [x] 1.1 Ouvrir `frontend/app/composables/useGuidedTour.ts`
  - [x] 1.2 Apres `MAX_STATS_CAP = 5` (ligne 22), ajouter :
    - `const DOM_RETRY_COUNT = 3 // FR31/NFR18 — nombre de retries pour un element absent`
    - `const DOM_RETRY_INTERVAL_MS = 500`
    - `const PAGE_LOAD_SOFT_RETRY_MS = 5000 // NFR16 — fenetre de retry silencieux`
    - `const PAGE_LOAD_HARD_TIMEOUT_MS = 10000 // NFR16 — timeout dur`
  - [x] 1.3 Remplacer les `10000` hardcodes lignes ~392 et ~482 par `PAGE_LOAD_HARD_TIMEOUT_MS`
  - [x] 1.4 Remplacer les `3` et `500` dans `waitForElement` (lignes 157-158) par les nouvelles constantes

- [x] Task 2 : Frontend — cancelled-aware dans `waitForElement` (AC: #5)
  - [x] 2.1 Avant la premiere `setTimeout(0)` ligne 152, ajouter `if (cancelled) return null`
  - [x] 2.2 Dans la boucle retry (lignes 157-161) : `if (cancelled) return null` AVANT `await new Promise(r => setTimeout(r, DOM_RETRY_INTERVAL_MS))`
  - [x] 2.3 Conserver la garde `if (found) return found` apres chaque querySelector

- [x] Task 3 : Frontend — soft retry a 5s dans `waitForElementExtended` (AC: #3)
  - [x] 3.1 Option A (preferee) : etendre `waitForElementExtended` pour logguer `console.debug('[useGuidedTour] soft retry page load at 5s', { selector, timeoutMs })` **une seule fois** quand `Date.now() - start >= PAGE_LOAD_SOFT_RETRY_MS` et `< PAGE_LOAD_HARD_TIMEOUT_MS` (flag local `softLogged = false`)
  - [x] 3.2 Option B : creer un nouveau helper `waitForElementWithSoftRetry(selector, softMs, hardMs)` qui wrap l'existant — **moins intrusif mais duplique la logique**. A arbitrer par le dev selon la clarte du diff.
  - [x] 3.3 Ajouter un test dedie au comportement soft retry (`test_page_load_soft_retry_logs_debug_at_5_seconds`)

- [x] Task 4 : Frontend — messages empathiques FR31/NFR16 (AC: #2, #3)
  - [x] 4.1 Verifier le message ligne 504 de `useGuidedTour.ts` : `'Je n\'ai pas pu pointer cet élément. Passons à la suite.'` → **confirmer accents é/à** corrects (compatible FR31)
  - [x] 4.2 **Remplacer** le message ligne 398 : `'La page n\'a pas pu se charger correctement. Le guidage est interrompu.'` → `'La page met trop de temps à charger. Réessayez plus tard.'` (**spec NFR16 exact**)
  - [x] 4.3 Idem ligne 489 (meme message, deuxieme occurrence dans la boucle steps)
  - [x] 4.4 Grep global sur `La page n'a pas pu se charger` pour s'assurer qu'il n'y a pas d'autre occurrence

- [x] Task 5 : Frontend — catch global + message empathique Driver.js crash (AC: #4)
  - [x] 5.1 Ouvrir le bloc catch ligne 570-593 de `useGuidedTour.ts`
  - [x] 5.2 Changer `} catch {` en `} catch (err) {` (nommer la var)
  - [x] 5.3 Premiere ligne du catch : `console.warn('[useGuidedTour] tour crashed', err)`
  - [x] 5.4 Deuxieme ligne du catch : **import dynamique** de `useChat` (pattern SSR-safe, cf lignes 250, 396) :
    ```typescript
    if (!cancelled) {
      const { useChat } = await import('~/composables/useChat')
      const { addSystemMessage } = useChat()
      addSystemMessage('Le guidage a rencontré un problème. Le chat est toujours disponible.')
    }
    ```
  - [x] 5.5 Garder le cleanup existant (clearCountdownTimer, unmountAllPopoverApps, driverInstance.destroy, cleanupDriverResiduals, reset UI flags)
  - [x] 5.6 Confirmer que `tourState.value = 'idle'` reste en place (pas `'interrupted'` — cf note AC4)

- [x] Task 6 : Frontend — tests (AC: #6)
  - [x] 6.1 Creer `frontend/tests/composables/useGuidedTour.resilience.test.ts` avec les ~15 tests listes en AC6 (Blocs 1 a 5)
  - [x] 6.2 Pattern de reference : `frontend/tests/composables/useGuidedTour.navigation.test.ts` (mock `navigateTo`, `waitForElementExtended`, `driver.js`) et `useGuidedTour.adaptive-frequency.test.ts` (mock localStorage, tour state)
  - [x] 6.3 Utiliser `vi.useFakeTimers()` pour les tests de retry (avancer timers de 500ms par tick) et les tests de soft/hard timeout (avancer de 5000ms / 10000ms)
  - [x] 6.4 Utiliser `vi.spyOn(console, 'debug')` et `vi.spyOn(console, 'warn')` pour verifier les logs
  - [x] 6.5 Mock `useChat` via `vi.mock('~/composables/useChat', () => ({ useChat: () => ({ addSystemMessage: vi.fn() }) }))` — pattern deja utilise dans `useChat.guided-tour-consent.test.ts`
  - [x] 6.6 Lancer : `cd frontend && npm run test -- useGuidedTour.resilience` → tous verts
  - [x] 6.7 Lancer la suite complete : `npm run test` → **285 + n ≈ 300+ tests verts, 0 regression**

- [x] Task 7 : Documentation traceabilite + finalisation (AC: #7)
  - [x] 7.1 Completer le tableau « AC → test » en fin de Dev Notes (pattern story 6.4)
  - [x] 7.2 Documenter dans Completion Notes les 4 decisions de design listees en AC7
  - [x] 7.3 Mettre a jour `sprint-status.yaml` : `7-1-gestion-des-elements-dom-absents-et-timeout-de-chargement` : `ready-for-dev` → `in-progress` (debut dev) → `review` (fin dev) → `done` (apres code review)
  - [x] 7.4 File List : lister tous les fichiers modifies/crees

## Dev Notes

### Contexte — premiere story de l'epic 7 (Resilience et edge cases)

L'epic 7 couvre trois scenarios degradee : **DOM absent** (7.1, cette story), **JWT expire** (7.2), **SSE perdue** (7.3). Les trois doivent garantir que le parcours guide ne laisse JAMAIS l'utilisateur bloque sur un ecran fige.

Cette story **n'invente rien** du cote retry DOM (deja implemente ligne 150-179 de `useGuidedTour.ts` lors de la story 5.3), mais elle **comble 4 gaps** :

1. **Constantes hardcodees** (`10000`, `500`, `3`) a extraire en module-level pour tests/lisibilite/evolution.
2. **Messages FR31/NFR16 pas exactement ceux de la spec** — correction de deux chaines.
3. **`waitForElement` ne gere pas `cancelled`** alors que `waitForElementExtended` le fait (parite).
4. **Catch global Driver.js muet** — pas de message utilisateur quand la lib crash.

### Mapping AC → fichier → test (pattern story 6.4)

| AC | Fichier impacte | Ligne(s) | Test(s) |
|---|---|---|---|
| AC1 Retry 3×500ms | `useGuidedTour.ts` | 150-164, +nouv. const | `test_waitForElement_retries_3_times_*`, `test_waitForElement_resolves_immediately_when_element_appears_at_retry_2` |
| AC2 Skip gracieux mono-page | `useGuidedTour.ts` | 496-506 | `test_mono_page_step_with_missing_element_adds_system_message_and_continues`, `test_multiple_consecutive_missing_elements_*` |
| AC3 Soft retry + hard timeout page load | `useGuidedTour.ts` | 167-179, 389-401, 480-492 | `test_page_load_soft_retry_logs_debug_at_5_seconds`, `test_page_load_hard_timeout_adds_system_message_and_interrupts` |
| AC4 Catch global Driver.js | `useGuidedTour.ts` | 570-593 | `test_driver_highlight_throws_triggers_system_message_and_cleanup`, `test_driver_crash_during_user_cancel_does_NOT_emit_message`, `test_driver_loadDriver_rejection_triggers_cleanup_message` |
| AC5 Cancelled-aware waitForElement | `useGuidedTour.ts` | 150-164 | `test_waitForElement_returns_null_immediately_when_cancelled_during_retry` |
| AC6 Tests + zero regression | `useGuidedTour.resilience.test.ts` (CREER) | — | Suite complete verte |
| AC7 Doc traceabilite | Cette story (Dev Notes) | — | Revue manuelle |

### Messages systeme exacts (FR31 / NFR16) — a respecter byte-for-byte

| Situation | Message (avec accents obligatoires) | Source |
|---|---|---|
| Element absent apres retry mono-page | `Je n'ai pas pu pointer cet élément. Passons à la suite.` | FR31, ligne 504 actuelle (deja OK) |
| Page ne charge pas dans les 10s | `La page met trop de temps à charger. Réessayez plus tard.` | NFR16, spec Epic 7.1 — **remplace** ligne 398+489 actuelles |
| Driver.js crash | `Le guidage a rencontré un problème. Le chat est toujours disponible.` | FR31, spec Epic 7.1 — **nouveau message a ajouter** au catch |

**Test de validation** : grep sur les 3 messages dans `useGuidedTour.ts` → chacun apparait **au moins une fois**, les 2 messages legacy (`n'a pas pu se charger correctement`, `Le guidage est interrompu.`) sont **supprimes**.

### Constantes a extraire (pattern story 6.4)

```typescript
// Apres MAX_STATS_CAP ligne 22 de useGuidedTour.ts
// FR31/NFR18 — retry pour un element DOM absent (etape mono-page)
const DOM_RETRY_COUNT = 3
const DOM_RETRY_INTERVAL_MS = 500
// NFR16 — timeouts pour navigation multi-pages
const PAGE_LOAD_SOFT_RETRY_MS = 5000 // fenetre de retry silencieux avec log debug
const PAGE_LOAD_HARD_TIMEOUT_MS = 10000 // timeout dur → interruption + message
```

**Pourquoi module-level et pas exportees ?** Cohérence avec `COUNTDOWN_FLOOR` et `MAX_STATS_CAP` (prives module). Les tests accedent via **comportement observable** (timing fake-timers), pas via import direct. Si un test a besoin d'une inspection fine, exporter au cas-par-cas avec `export const`.

### Pattern cancelled-aware (parite waitForElement ↔ waitForElementExtended)

```typescript
// Apres : version actuelle ligne 150-164
async function waitForElement(selector: string): Promise<Element | null> {
  if (cancelled) return null // garde entree (parite avec waitForElementExtended)
  await new Promise(r => setTimeout(r, 0))
  if (cancelled) return null
  const el = document.querySelector(selector)
  if (el) return el

  for (let i = 0; i < DOM_RETRY_COUNT; i++) {
    if (cancelled) return null // avant await
    await new Promise(r => setTimeout(r, DOM_RETRY_INTERVAL_MS))
    if (cancelled) return null // apres await (re-check)
    const found = document.querySelector(selector)
    if (found) return found
  }

  return null
}
```

### Pattern soft retry (option A — instrumentation dans waitForElementExtended)

```typescript
async function waitForElementExtended(selector: string, timeoutMs: number): Promise<Element | null> {
  const start = Date.now()
  let softLogged = false
  await nextTick()

  while (Date.now() - start < timeoutMs) {
    if (cancelled) return null
    const el = document.querySelector(selector)
    if (el) return el

    // NFR16 — soft retry marker (une seule fois)
    if (!softLogged && Date.now() - start >= PAGE_LOAD_SOFT_RETRY_MS) {
      // eslint-disable-next-line no-console
      console.debug('[useGuidedTour] soft retry page load', { selector, elapsedMs: Date.now() - start })
      softLogged = true
    }

    await new Promise(r => setTimeout(r, 500))
  }

  return null
}
```

### Pattern catch global avec message empathique (cœur AC4)

```typescript
// Remplace le catch actuel ligne 570-593
} catch (err) {
  // eslint-disable-next-line no-console
  console.warn('[useGuidedTour] tour crashed', err)

  // Message empathique UNIQUEMENT si l'erreur n'est pas due a un cancelTour user
  if (!cancelled) {
    try {
      const { useChat } = await import('~/composables/useChat')
      const { addSystemMessage } = useChat()
      addSystemMessage('Le guidage a rencontré un problème. Le chat est toujours disponible.')
    } catch (innerErr) {
      // Si meme l'import de useChat fail, on tombe silencieusement — l'utilisateur
      // verra juste le widget reapparaitre. Impossible a test en prod, nice-to-have.
      // eslint-disable-next-line no-console
      console.warn('[useGuidedTour] failed to emit crash message', innerErr)
    }
  }

  // Reset d'etat en cas d'erreur (loadDriver rejection, highlight throw, etc.)
  clearCountdownTimer()
  unmountAllPopoverApps()
  if (driverInstance) {
    userInitiatedClose = false
    driverInstance.destroy()
    userInitiatedClose = true
    driverInstance = null
  }
  cleanupDriverResiduals()
  if (cachedUiStore) {
    cachedUiStore.chatWidgetMinimized = false
    cachedUiStore.guidedTourActive = false
  }
  onRetractComplete?.()
  onRetractComplete = null
  tourState.value = 'idle'
  currentTourId.value = null
  currentStepIndex.value = 0
  return false
}
```

**Decision** : `tourState.value = 'idle'` (et NON `'interrupted'`) est conserve du code actuel. Raison : le catch global court-circuite `interruptTour(uiStore)` pour eviter un double cleanup (destroy deja appele, reset flags deja faits). L'etat `'interrupted'` reste reserve aux interruptions user-explicit via `interruptTour`.

### Pattern tests — mock `vi.useFakeTimers` avec `vi.advanceTimersByTime`

```typescript
import { beforeEach, describe, expect, it, vi } from 'vitest'

describe('useGuidedTour — waitForElement retry', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    document.body.innerHTML = ''
  })
  afterEach(() => { vi.useRealTimers() })

  it('retries 3 times with 500ms interval when element absent', async () => {
    const { useGuidedTour } = await import('~/composables/useGuidedTour')
    // ... setup minimal tour
    const promise = /* call qui invoque waitForElement */
    // Advance 500ms → retry 1, puis 500ms → retry 2, puis 500ms → retry 3
    await vi.advanceTimersByTimeAsync(1500)
    const result = await promise
    expect(result).toBeNull()
  })
})
```

**Attention** : `useGuidedTour.ts` contient un check `if (import.meta.server) throw` (ligne 8). Les tests doivent s'executer dans jsdom (deja le cas pour les 4 fichiers existants). Verifier que `vitest.config.ts` a bien `environment: 'jsdom'`.

### Fichiers attendus

| Fichier | Action | Justification |
|---|---|---|
| `frontend/app/composables/useGuidedTour.ts` | MODIFIER | Extraction constantes, cancelled-aware waitForElement, soft retry log, remplacement messages NFR16, catch global avec addSystemMessage |
| `frontend/tests/composables/useGuidedTour.resilience.test.ts` | CREER | ~15 tests couvrant retry DOM, skip mono-page, soft/hard timeout page load, catch Driver.js crash |

**Pas de fichier backend modifie** (story frontend-only). **Pas** de nouvelle migration Alembic, **pas** de changement d'API, **pas** de nouveau composant Vue.

### Intelligence story 6.4 (previous-story)

Points actionnables herites :

- **Pattern constantes module-level commentees** (story 6.4 : `COUNTDOWN_FLOOR`, `MAX_STATS_CAP`) → meme pattern a reproduire pour les 4 constantes timeout.
- **Pattern import dynamique SSR-safe** (`const { useChat } = await import('~/composables/useChat')`) : deja utilise lignes 250, 396, 487, 502 — a reutiliser **tel quel** dans le catch (AC4).
- **Pattern review 6.4 P15** : `console.warn` plutot que `catch {}` muet → applique au catch global (AC4) et au soft retry (`console.debug`).
- **Pattern test avec fake-timers** : stories 5.3 et 6.4 ont utilise `vi.useFakeTimers()` pour les countdowns — pattern identique pour les tests de retry/timeout de 7.1.
- **Pattern AC → test mapping** (story 6.4 Dev Notes) : reproduire la table en fin de Dev Notes (AC7).

### Git intelligence (5 derniers commits)

- `2278f35 6-4-frequence-adaptative-des-propositions-de-guidage: done` — modification recente de `useGuidedTour.ts` (compteurs + persistance + formule countdown) → **verifier que les nouvelles constantes n'entrent pas en conflit avec `MAX_STATS_CAP`** (elles doivent venir APRES).
- `2bc3e15 6-3-consentement-via-widget-interactif-et-declenchement-direct` — modification de `useChat.ts` (heuristique consent + increment refusal). Pas d'impact sur 7.1 mais useChat reste **stable** — l'import dynamique de `useChat` continue de fonctionner.
- `b7f6d62 6-1-tool-langchain-trigger-guided-tour-et-marker-sse` — backend trigger tour : **pas d'impact** (7.1 frontend-only).
- `5277eb1 5-4-interruption-du-parcours-et-popover-custom` — introduction de `cancelTour`, `interruptTour`, `driverInstance.destroy()` → **dependances directes** de cette story.
- `24b5862 5-1-composable-useguidedtour-machine-a-etats-et-execution-mono-page` — machine a etats `tourState` (`idle`, `loading`, `navigating`, `waiting_dom`, `highlighting`, `interrupted`, `complete`) → **invariant a respecter** dans les tests AC6.

### Latest tech information

- **Vitest** : l'API `vi.advanceTimersByTimeAsync(ms)` (vs `advanceTimersByTime` synchrone) est **recommandee** pour les tests de Promises avec `setTimeout` — evite les race conditions quand on chaine `await` + timers. Cf. [Vitest fake timers docs](https://vitest.dev/api/vi.html#vi-advancetimersbytimeasync).
- **Driver.js 1.x** : aucune API deprecation en vue pour `destroy()`, `highlight()`, `onDestroyStarted`. Story compatible avec la version deja en dep (cf. `package.json`).

### Project Structure Notes

- Alignement structure Nuxt 4 : fichier source dans `frontend/app/composables/useGuidedTour.ts`, tests dans `frontend/tests/composables/*.test.ts`. Pattern conforme aux stories 5.x et 6.x (pas de divergence).
- Conformite rules/typescript : `const` au niveau module (pattern recommandé), pas de `any`, messages FR avec accents, pas de `console.log` (on utilise `console.warn` et `console.debug` qui sont tolerees par les hooks TS).

### References

- Source epic : `_bmad-output/planning-artifacts/epics-019-floating-copilot.md:1070-1108` (Epic 7 Story 7.1 avec BDD + exigences techniques)
- Source architecture :
  - `_bmad-output/planning-artifacts/architecture-019-floating-copilot.md:47` (NFR16-NFR19 — tolerance latence, retry DOM)
  - `_bmad-output/planning-artifacts/architecture-019-floating-copilot.md:409, 476` (patterns waitForElement)
  - `_bmad-output/planning-artifacts/architecture-019-floating-copilot.md:740` (spec AC skip element)
  - `_bmad-output/planning-artifacts/architecture-019-floating-copilot.md:1005, 1014` (FR31-FR35 resilience)
- PRD : FR31 (message empathique skip), NFR16 (timeout 10s), NFR18 (retry 3×500ms), NFR19 (zero regression)
- Stories precedentes impactant la logique :
  - `_bmad-output/implementation-artifacts/5-4-interruption-du-parcours-et-popover-custom.md` (intro `interruptTour`, `cancelTour`)
  - `_bmad-output/implementation-artifacts/5-3-navigation-multi-pages-avec-decompteur.md` (intro `waitForElementExtended` + 10s timeout hardcode a refactor)
  - `_bmad-output/implementation-artifacts/6-4-frequence-adaptative-des-propositions-de-guidage.md` (pattern constantes module-level + tests fake-timers + Dev Notes structure)

## Dev Agent Record

### Agent Model Used

claude-opus-4-6 (Opus 4.6, 1M context)

### Debug Log References

- `cd frontend && npm run test -- useGuidedTour.resilience` → 16 tests verts (Blocs 1-5)
- `cd frontend && npm run test` → **309 tests verts / 33 fichiers**, 0 regression (vs 293 avant cette story, delta +16)
- `npx nuxi typecheck` → aucune nouvelle erreur sur `useGuidedTour.ts` ni `useGuidedTour.resilience.test.ts` (erreurs preexistantes hors-scope sur d'autres fichiers)
- Pas de script `lint` configure dans `package.json` frontend (scripts : `test`, `build`, `dev`, `generate`, `preview`, `test:e2e`).

### Completion Notes List

**Implementation realisee :**

- **AC1 Retry 3×500ms** — Constantes `DOM_RETRY_COUNT = 3` et `DOM_RETRY_INTERVAL_MS = 500` extraites au niveau module (apres `MAX_STATS_CAP`). Les literals magiques de `waitForElement` remplaces. Test `DOM retry observed at 3 x 500ms = ~1500ms` valide le timing observable.
- **AC2 Skip gracieux mono-page** — Message `"Je n'ai pas pu pointer cet élément. Passons à la suite."` conserve (ligne 504 etait deja conforme FR31 avec accents é/à). Le state reste `'highlighting'` apres skip, chaque step emet son propre message (pas de deduplication). Tests Bloc 2 (3 tests) valident.
- **AC3 Soft retry + hard timeout** — Constantes `PAGE_LOAD_SOFT_RETRY_MS = 5000` et `PAGE_LOAD_HARD_TIMEOUT_MS = 10000` extraites. `waitForElementExtended` instrumentee avec flag local `softLogged` pour emettre `console.debug('[useGuidedTour] soft retry page load', { selector, elapsedMs })` une seule fois au franchissement de 5s. Message hard timeout remplace aux deux occurrences (entryStep + boucle steps) par la spec NFR16 exacte `"La page met trop de temps à charger. Réessayez plus tard."`. Tests Bloc 3 (3 tests) + Bloc 5 (2 tests).
- **AC4 Catch global Driver.js crash** — `} catch {` devient `} catch (err) {`. Nouveau premier pas : `console.warn('[useGuidedTour] tour crashed', err)`. Emission conditionnelle : `if (!cancelled) { addSystemMessage('Le guidage a rencontré un problème. Le chat est toujours disponible.') }` via import dynamique SSR-safe de `useChat` (pattern deja utilise lignes 250, 396, 487, 502). Cleanup existant preserve. Tests Bloc 4 (4 tests) couvrent loadDriver rejection, highlight throw, log error object, garde `cancelled` (pas de spam apres user cancel).
- **AC5 Cancelled-aware waitForElement** — Quatre gardes `if (cancelled) return null` ajoutees (avant et apres chaque `await`) pour parite avec `waitForElementExtended` (ligne 172). Test `returns null immediately when cancelled during retry`.
- **AC6 Tests + zero regression** — Nouveau fichier `frontend/tests/composables/useGuidedTour.resilience.test.ts` (16 tests). Le test existant `useGuidedTour.navigation.test.ts` mis a jour pour refleter le nouveau message NFR16 (substring `'La page met trop de temps à charger'`). Total frontend : 309 tests verts / 33 fichiers.
- **AC7 Doc traceabilite** — Tableau AC → fichier → test deja dans Dev Notes (ligne 219-227, pattern 6.4). Decisions design ci-dessous.

**Decisions de design (AC7) :**

1. **Constantes module-level non-exportees** — Coherence avec `COUNTDOWN_FLOOR` et `MAX_STATS_CAP` (prives module). Tests accedent via comportement observable (`vi.advanceTimersByTimeAsync`) plutot que via import direct. Si un futur test necessite inspection fine, exporter au cas-par-cas avec `export const`.
2. **`console.debug` pour le soft retry 5s (vs `console.warn`)** — Le soft retry est un marqueur de monitoring, pas un avertissement. `debug` n'est pas capture par les suites de tests par defaut et ne pollue pas les logs CI. Conforme au retour review 6.4 P15 (gradation selon severite).
3. **Check `cancelled` dans `waitForElement`** — Parite stricte avec `waitForElementExtended` (ligne 172). Evite qu'un parcours annule continue a consommer les timers apres user Escape. Comble un gap identifie dans la spec AC5.
4. **`addSystemMessage` dans le catch global plutot que `interruptTour`** — Le catch court-circuite `interruptTour(uiStore)` car il effectue deja le cleanup (destroy instance, reset flags UI, resolve onRetractComplete). Appeler `interruptTour` causerait un double-destroy et un `tourState = 'interrupted'` qui masquerait l'erreur. Le catch termine sur `tourState.value = 'idle'` directement (comportement conserve, cf. ligne 589 pre-story). Garde `if (!cancelled)` evite de spammer l'utilisateur apres qu'il a appuye Escape.

### File List

**Modifies :**

- `frontend/app/composables/useGuidedTour.ts` — Extraction de 4 constantes timeout module-level (`DOM_RETRY_COUNT`, `DOM_RETRY_INTERVAL_MS`, `PAGE_LOAD_SOFT_RETRY_MS`, `PAGE_LOAD_HARD_TIMEOUT_MS`), cancelled-aware `waitForElement` (4 gardes), soft retry `console.debug` dans `waitForElementExtended`, remplacement des 2 messages NFR16, catch global avec `console.warn(err)` + `addSystemMessage` conditionnel via import dynamique `useChat` SSR-safe, garde `cancelled` pour eviter le spam post-cancel.
- `frontend/tests/composables/useGuidedTour.navigation.test.ts` — Mise a jour du substring attendu dans `test_interrompt le parcours apres 10s` (`'charger correctement'` → `'La page met trop de temps à charger'`) pour refleter le nouveau message NFR16.
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — Transition `7-1-…` : `ready-for-dev` → `in-progress` → `review`.

**Crees :**

- `frontend/tests/composables/useGuidedTour.resilience.test.ts` — 16 tests, 5 blocs (waitForElement retry + cancelled / skip gracieux mono-page / soft retry + hard timeout page load / catch global Driver.js / constantes observables). Mocks : `driver.js`, `useDriverLoader`, `~/stores/ui`, `~/composables/useChat`, `navigateTo`, `crypto.randomUUID`, `location.pathname`. Strategie : `vi.useFakeTimers()` + `vi.advanceTimersByTimeAsync()` pour piloter le timing, `document.querySelector` spy avec whitelist `presentSelectors` pour contrôler la presence des elements.

### Change Log

| Date | Auteur | Description |
|---|---|---|
| 2026-04-14 | Dev (Opus 4.6) | Implementation story 7.1 : resilience DOM absent (retry 3×500ms + cancelled-aware), soft retry + hard timeout page load (5s/10s avec messages NFR16 exacts), catch global Driver.js avec message empathique FR31, extraction de 4 constantes timeout module-level, 16 nouveaux tests + 1 test existant mis a jour, 309 tests frontend verts (0 regression). |
| 2026-04-14 | Reviewer (Opus 4.6) | Code review adversarial (Blind Hunter + Edge Case Hunter + Acceptance Auditor). Acceptance Auditor : APPROUVE AVEC AVERTISSEMENT (7/7 AC satisfaits sur les chaines exactes et le comportement, 2 tests enumeres AC6 manquants sur 18). 6 patches identifies, 3 decisions a trancher, 7 items differes (pre-existants). |
| 2026-04-14 | Reviewer (Opus 4.6) | Application des patches de revue : `PAGE_LOAD_POLL_INTERVAL_MS` dedie (D1), snapshot + re-check `cancelled` dans le catch global, resolution `uiStore` avant `loadDriver` (catch-safe), 2 tests AC6 manquants ajoutes (Bloc 1 + Bloc 3), whitelist driver selectors dans le mock `querySelectorAll`, clarification du `void promise`. **311 tests frontend verts (+2 vs review, 0 regression).** Story transition review → done. |

### Review Findings

_Code review du 2026-04-14 (3 couches adversariales : Blind Hunter, Edge Case Hunter, Acceptance Auditor)._

#### Decisions resolues

- [x] [Review][Decision] Reutilisation de `DOM_RETRY_INTERVAL_MS` pour le polling de `waitForElementExtended` — **→ PATCH** applique : constante dediee `PAGE_LOAD_POLL_INTERVAL_MS = 500` introduite, `waitForElementExtended` la consomme. [frontend/app/composables/useGuidedTour.ts:29,195]
- [x] [Review][Decision] Semantique de retour de `startTour` quand TOUS les steps sont skippes — **→ DISMISS** : l'AC2 est explicite (« le parcours N'EST PAS interrompu »). Le skip est un chemin normal, conserver `true`. Edge case (0 step execute) a traiter dans une story dediee si le besoin produit emerge.
- [x] [Review][Decision] Fiabilite du log `console.debug` soft-retry — **→ DISMISS** : observabilite best-effort acceptee. Fenetre de perte etroite (<1 cycle de 500ms), impact nul sur le comportement fonctionnel.

#### Patches appliques

- [x] [Review][Patch] Race condition `cancelled` pendant `await import` dans le catch — Snapshot synchrone `const wasCancelledAtThrow = cancelled` en tete de catch + re-verification post-await avant `addSystemMessage`. [frontend/app/composables/useGuidedTour.ts:592-615] (source: blind+edge)
- [x] [Review][Patch] Distinguer user-cancel apres throw — Resolu par la meme modification (snapshot synchrone + double verification). [frontend/app/composables/useGuidedTour.ts:592-615] (source: edge)
- [x] [Review][Patch] `cachedUiStore` potentiellement stale sur rejet de `loadDriver` — `useUiStore` resolu AVANT `loadDriver()` : le catch dispose d'une reference a jour. [frontend/app/composables/useGuidedTour.ts:285-294] (source: edge)
- [x] [Review][Patch] Tests enumeres AC6 manquants (2/18) — Ajout de `resolves immediately when element appears between retry attempts` (Bloc 1) et `resolves before soft retry window without logging debug or emitting message` (Bloc 3). Total livre : **18/18**. [frontend/tests/composables/useGuidedTour.resilience.test.ts:267-291,379-421] (source: auditor)
- [x] [Review][Patch] Mock `querySelectorAll` whitelist driver selectors — Ajout du pattern `.driver-*` / `[data-driver-*]` deja en place pour `querySelector`. Preserve la couverture de `cleanupDriverResiduals`. [frontend/tests/composables/useGuidedTour.resilience.test.ts:142-151] (source: blind)
- [x] [Review][Patch] `void promise` dans `resolves immediately when element is present` — Clarification du commentaire : le highlight reste volontairement en attente (popover mock non monte), le cleanup est assure par `vi.resetModules()` + `vi.useRealTimers()` dans `afterEach`. [frontend/tests/composables/useGuidedTour.resilience.test.ts:225-226] (source: blind)

#### Differes (pre-existants, non bloquants)

- [x] [Review][Defer] `Date.now()` non-monotone dans `waitForElementExtended` — Une bascule NTP/DST peut fausser `elapsedMs`. Preferer `performance.now()`. [useGuidedTour.ts:179,183,189] — deferred, pre-existing
- [x] [Review][Defer] `setTimeout(..., 500)` dans `interruptTour`/`cancelTour` jamais annule — Leak mineur de timers sur cancels repetes. [useGuidedTour.ts:250-252,662-666] — deferred, pre-existing
- [x] [Review][Defer] `cancelled` non reinitialise sur le chemin de succes de `startTour` — Etat residuel possible. [useGuidedTour.ts:278] — deferred, pre-existing
- [x] [Review][Defer] `cancelTour` re-entre pendant la transition `interrupted`→`idle` cree des timeouts dupliques — Ajouter `'interrupted'` a la garde de retour anticipe. [useGuidedTour.ts:~635] — deferred, pre-existing
- [x] [Review][Defer] Cleanup du catch global dans un `finally` au lieu d'apres le catch — Robustesse face a un throw dans le catch lui-meme. [useGuidedTour.ts:~590-627] — deferred, pre-existing
- [x] [Review][Defer] `addSystemMessage` peut etre silencieusement drop si aucune conversation active — Pre-existant a `useChat.ts:739-744`. [useGuidedTour.ts:598-600] — deferred, pre-existing
- [x] [Review][Defer] Strings FR hardcodees non extraites en MAP constante — Conforme aux conventions actuelles du projet, amelioration i18n future. [useGuidedTour.ts:424,504,~418,~509,~600] — deferred, pre-existing
