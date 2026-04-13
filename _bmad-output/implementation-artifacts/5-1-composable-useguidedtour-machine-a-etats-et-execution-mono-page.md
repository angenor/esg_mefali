# Story 5.1 : Composable useGuidedTour — machine a etats et execution mono-page

Status: done

## Story

En tant qu'utilisateur,
je veux que le systeme puisse mettre en surbrillance des elements de l'interface avec des explications,
afin de comprendre visuellement ou se trouvent les informations importantes.

## Acceptance Criteria

1. **AC1 — Composable useGuidedTour expose l'API publique**
   - **Given** le composable `useGuidedTour` n'existe pas encore
   - **When** un developpeur le cree dans `composables/useGuidedTour.ts`
   - **Then** il expose : `startTour(tourId, context?)`, `cancelTour()`, `tourState` (ref\<TourState\>)
   - **And** l'etat est declare au niveau module (persistance cross-routes, coherent avec ADR3 architecture.md)

2. **AC2 — Demarrage d'un parcours mono-page**
   - **Given** `startTour('show_carbon_results')` est appele et l'utilisateur est deja sur `/carbon/results`
   - **When** le parcours demarre
   - **Then** Driver.js est charge via `loadDriver()` du composable existant `useDriverLoader.ts` (cache si deja prefetche)
   - **And** le parcours est resolu depuis `tourRegistry` (import manuel — `lib/` pas dans auto-import Nuxt)
   - **And** les placeholders du contexte sont interpoles dans les textes des popovers via regex `/\{\{(\w+)\}\}/g`
   - **And** l'etat passe `idle` -> `loading` -> `highlighting`

3. **AC3 — Affichage sequentiel des etapes**
   - **Given** le parcours est en cours sur la page courante
   - **When** Driver.js affiche les etapes sequentiellement
   - **Then** chaque popover s'affiche en < 200ms apres le precedent (NFR3)
   - **And** les textes sont en francais avec accents

4. **AC4 — Retry element DOM absent**
   - **Given** un element cible n'est pas trouve dans le DOM (8 elements sur 19 sont dans des blocs `v-if` — cf. deferred-work.md story 4-3)
   - **When** `waitForElement(selector)` est appele
   - **Then** le systeme retente 3 fois avec 500ms d'intervalle
   - **And** si l'element est trouve, l'etape continue normalement
   - **And** si l'element n'est pas trouve apres 3 tentatives, l'etape est skippee et un message est ajoute via `addSystemMessage()` : « Je n'ai pas pu pointer cet element. Passons a la suite. »

5. **AC5 — Finalisation du parcours**
   - **Given** toutes les etapes du parcours sont terminees
   - **When** le parcours se finalise
   - **Then** `driver.destroy()` est appele
   - **And** l'etat passe a `'complete'`
   - **And** apres un delai configurable, l'etat revient a `'idle'`

6. **AC6 — addSystemMessage dans useChat**
   - **Given** la methode `addSystemMessage` n'existe pas encore dans `useChat.ts`
   - **When** un developpeur l'ajoute
   - **Then** elle insere un message local (non envoye au LLM) dans la liste `messages` (role `'assistant'`, pas de conversation_id)
   - **And** le message est affiche dans le widget de chat immediatement

7. **AC7 — Validation tour_id invalide**
   - **Given** `startTour` est appele avec un `tour_id` qui n'existe pas dans `tourRegistry`
   - **When** le composable recoit l'appel
   - **Then** le parcours est ignore et un message d'erreur est ajoute via `addSystemMessage()`
   - **And** l'etat reste `'idle'`

8. **AC8 — Interpolation avec placeholders manquants**
   - **Given** un template contient `{{variable}}` mais la cle `variable` n'est pas dans `context`
   - **When** l'interpolation est executee
   - **Then** le placeholder est remplace par une chaine vide `''` (pas de `{{variable}}` brut affiche — cf. deferred-work.md story 4-2)

9. **AC9 — Validation countdown**
   - **Given** une etape a un `countdown` invalide (0, negatif, NaN — cf. deferred-work.md story 4-2)
   - **When** l'etape est evaluee
   - **Then** la valeur est corrigee au minimum 1 seconde (clamp)

10. **AC10 — Zero regression**
    - **Given** les modifications sont terminees
    - **When** on execute les tests frontend (`npx vitest run`)
    - **Then** zero regression sur les 198 tests existants
    - **And** les nouveaux tests couvrent >= 80% du composable

## Tasks / Subtasks

- [x] **Task 1 : Creer `composables/useGuidedTour.ts` — structure et machine a etats** (AC: 1)
  - [x] 1.1 Creer le fichier `frontend/app/composables/useGuidedTour.ts`
  - [x] 1.2 Declarer l'etat module-level : `tourState = ref<TourState>('idle')`, `currentTourId = ref<string | null>(null)`, `currentStepIndex = ref(0)`
  - [x] 1.3 Exporter la fonction composable `useGuidedTour()` retournant `{ startTour, cancelTour, tourState }`
  - [x] 1.4 Importer manuellement : `import { tourRegistry } from '~/lib/guided-tours/registry'` et `import { loadDriver } from '~/composables/useDriverLoader'`
  - [x] 1.5 Importer les types : `import type { TourState, TourContext, GuidedTourDefinition, GuidedTourStep } from '~/types/guided-tour'`

- [x] **Task 2 : Implementer `startTour(tourId, context?)` — resolution et interpolation** (AC: 2, 7, 8, 9)
  - [x] 2.1 Verifier que `tourState.value === 'idle'` (ignorer si un parcours est deja en cours)
  - [x] 2.2 Valider `tourId` dans `tourRegistry` — si absent, appeler `addSystemMessage()` et return
  - [x] 2.3 Passer `tourState` a `'loading'`
  - [x] 2.4 Appeler `await loadDriver()` pour obtenir le module Driver.js
  - [x] 2.5 Resoudre la definition du parcours depuis `tourRegistry[tourId]`
  - [x] 2.6 Interpoler les placeholders dans tous les `popover.title` et `popover.description` : `text.replace(/\{\{(\w+)\}\}/g, (_, key) => String(context?.[key] ?? ''))` — les cles manquantes deviennent `''`
  - [x] 2.7 Valider/clamper les `countdown` (min 1 seconde, fallback `DEFAULT_ENTRY_COUNTDOWN` si NaN/undefined)

- [x] **Task 3 : Implementer l'execution sequentielle des etapes mono-page** (AC: 2, 3, 4, 5)
  - [x] 3.1 Filtrer les etapes dont `step.route` est absent ou === `currentRoute` (etapes mono-page)
  - [x] 3.2 Pour chaque etape, appeler `waitForElement(step.selector)` avant de highlight
  - [x] 3.3 Passer `tourState` a `'highlighting'`
  - [x] 3.4 Utiliser `driver.highlight({ element: selector, popover: { title, description } })` sequentiellement
  - [x] 3.5 Utiliser les callbacks Driver.js `onDestroyStarted` pour passer a l'etape suivante
  - [x] 3.6 A la fin : `driver.destroy()`, `tourState` -> `'complete'`, puis apres `setTimeout(1000)` -> `'idle'`
  - [x] 3.7 Gerer `prefers-reduced-motion` : passer `animate: false` dans la config Driver.js si `uiStore.prefersReducedMotion === true`

- [x] **Task 4 : Implementer `waitForElement(selector)`** (AC: 4)
  - [x] 4.1 Fonction async : `await nextTick()` puis polling 3x avec 500ms d'intervalle
  - [x] 4.2 Si element trouve : retourner l'element
  - [x] 4.3 Si element non trouve apres 3 tentatives : retourner `null`
  - [x] 4.4 L'appelant (Task 3) skip l'etape et appelle `addSystemMessage('Je n\'ai pas pu pointer cet element. Passons a la suite.')`

- [x] **Task 5 : Implementer `cancelTour()`** (AC: 1)
  - [x] 5.1 Si `tourState !== 'idle'` et `tourState !== 'complete'` : appeler `driver.destroy()`
  - [x] 5.2 Passer `tourState` a `'interrupted'`
  - [x] 5.3 Apres `setTimeout(500)` -> `'idle'`
  - [x] 5.4 Ne pas ajouter de message au chat (action volontaire — FR25)

- [x] **Task 6 : Ajouter `addSystemMessage()` dans `useChat.ts`** (AC: 6)
  - [x] 6.1 Ajouter la fonction `addSystemMessage(content: string): void` dans le composable `useChat`
  - [x] 6.2 La fonction cree un `Message` avec `id: crypto.randomUUID()`, `role: 'assistant'`, `content`, `created_at: new Date().toISOString()`
  - [x] 6.3 L'ajouter a `messages.value` de maniere immutable : `messages.value = [...messages.value, msg]`
  - [x] 6.4 L'exposer dans le return de `useChat()` : `{ ..., addSystemMessage }`

- [x] **Task 7 : Corriger le route mismatch dans le registre** (AC: deferred 4-3)
  - [x] 7.1 Dans `frontend/app/lib/guided-tours/registry.ts`, corriger le parcours `show_esg_results` : changer `entryStep.targetRoute` de `'/esg'` a `'/esg/results'` (les 3 elements `esg-score-circle`, `esg-strengths-badges`, `esg-recommendations` sont sur `/esg/results`, pas `/esg`)
  - [x] 7.2 Verifier que les steps du parcours `show_esg_results` ont `route: '/esg/results'` (ou pas de `route` si le parcours est mono-page apres navigation)

- [x] **Task 8 : Tests unitaires** (AC: 10)
  - [x] 8.1 Creer `frontend/tests/composables/useGuidedTour.test.ts`
  - [x] 8.2 **Machine a etats** : idle initial, transitions idle→loading→highlighting→complete→idle
  - [x] 8.3 **startTour valide** : mock `loadDriver()`, mock `tourRegistry`, verifier transitions d'etats et appels Driver.js
  - [x] 8.4 **startTour invalide** : tour_id absent → addSystemMessage appele, etat reste idle
  - [x] 8.5 **startTour en cours** : appel pendant un parcours actif → ignore
  - [x] 8.6 **Interpolation** : `{{key}}` remplace par `context[key]`, cle manquante → `''`
  - [x] 8.7 **waitForElement** : element present → retourne element, element absent → retourne null apres 3 retries
  - [x] 8.8 **cancelTour** : etat → interrupted → idle, driver.destroy() appele
  - [x] 8.9 **Countdown validation** : 0 → 1, -5 → 1, NaN → DEFAULT_ENTRY_COUNTDOWN
  - [x] 8.10 **prefers-reduced-motion** : `animate: false` passe a Driver.js
  - [x] 8.11 Creer `frontend/tests/composables/useChat.addSystemMessage.test.ts`
  - [x] 8.12 **addSystemMessage** : ajoute un message assistant local dans messages, n'envoie rien au backend

- [x] **Task 9 : Verification finale** (AC: 10)
  - [x] 9.1 `npx vitest run` — zero regression sur 198 tests existants + nouveaux tests
  - [x] 9.2 `npx nuxi typecheck` — zero nouvelle erreur de type
  - [x] 9.3 Verifier que `useGuidedTour` n'importe RIEN du backend — composable purement frontend

## Dev Notes

### Portee de cette story

Cette story est **STRICTEMENT frontend** — aucune modification backend. Elle cree le **moteur d'execution des parcours guides** (composable `useGuidedTour`) et une methode utilitaire `addSystemMessage` dans `useChat`.

**Ce que cette story fait :** execution mono-page des parcours guides (etapes sur la page courante).
**Ce que cette story ne fait PAS :** retraction du widget (Story 5.2), navigation multi-pages avec decompteur (Story 5.3), popovers custom (Story 5.4), integration SSE/backend (Story 6.1).

### Architecture et ADRs a respecter

**ADR3 (architecture.md Decision 3)** — Machine a etats module-level dans `useGuidedTour.ts` :
```
idle → loading → ready → navigating → waiting_dom → highlighting → complete
                                │              │
                                └──── interrupted (user cancel)
```
**Pour cette story (mono-page), seuls ces etats sont utilises : `idle → loading → highlighting → complete`** (et `interrupted` via `cancelTour`). Les etats `ready`, `navigating`, `waiting_dom` seront actives dans les Stories 5.2/5.3.

**ADR7 (architecture.md Decision 7)** — Lazy loading Driver.js : utiliser `loadDriver()` de `useDriverLoader.ts` (existe deja). Ne PAS importer Driver.js en top-level.

**ADR5 (architecture.md Decision 5)** — Selectors `[data-guide-target="xxx"]` uniquement. Les 19 selectors sont poses sur le DOM (Story 4.3).

### Fichiers a creer

| Fichier | Description |
|---------|-------------|
| `frontend/app/composables/useGuidedTour.ts` | Composable machine a etats, moteur de guidage |
| `frontend/tests/composables/useGuidedTour.test.ts` | Tests unitaires du composable |
| `frontend/tests/composables/useChat.addSystemMessage.test.ts` | Tests unitaires de addSystemMessage |

### Fichiers a modifier

| Fichier | Modification |
|---------|-------------|
| `frontend/app/composables/useChat.ts` | Ajouter `addSystemMessage(content: string)` |
| `frontend/app/lib/guided-tours/registry.ts` | Corriger route mismatch `show_esg_results` (`'/esg'` → `'/esg/results'`) |

### Fichiers a NE PAS modifier

- `frontend/app/composables/useDriverLoader.ts` — Loader Driver.js deja complet (Story 4.1)
- `frontend/app/types/guided-tour.ts` — Types deja complets (Story 4.2), les etats `TourState` incluent deja tous les etats necessaires
- `frontend/app/assets/css/main.css` — CSS Driver.js deja configure (Story 4.1)
- `frontend/app/stores/ui.ts` — Les champs `guidedTourActive` et `chatWidgetMinimized` seront ajoutes dans Story 5.2 (pas necessaires pour le mono-page)
- `frontend/app/components/copilot/*` — Pas de modification des composants widget
- `backend/**` — Aucune modification backend

### Pattern module-level state (reference useChat.ts)

Le composable existant `useChat.ts` declare toutes ses refs **en dehors** de la fonction composable (lignes 15-45). Cela cree un singleton partage entre toutes les instances. `useGuidedTour` DOIT suivre le meme pattern :

```typescript
// ── Module-level state (singleton cross-routes) ──
const tourState = ref<TourState>('idle')
const currentTourId = ref<string | null>(null)
const currentStepIndex = ref(0)

let driverInstance: ReturnType<typeof import('driver.js').driver> | null = null

export function useGuidedTour() {
  // ... fonctions qui operent sur l'etat module-level
  return { startTour, cancelTour, tourState: readonly(tourState) }
}
```

### Pattern d'import pour lib/ (IMPORTANT)

Le dossier `lib/` n'est PAS dans les dirs auto-import Nuxt (cf. deferred-work.md story 4-2). Tous les imports depuis `lib/` doivent etre explicites :

```typescript
import { tourRegistry } from '~/lib/guided-tours/registry'
import type { GuidedTourDefinition } from '~/types/guided-tour'
```

### Interpolation des templates (detail technique)

Les descriptions de popovers contiennent des placeholders `{{variable}}`. Le `context` vient du LLM (ex: `{ esg_score: 58, sector: 'agroalimentaire' }`).

```typescript
function interpolate(text: string, context: TourContext = {}): string {
  return text.replace(/\{\{(\w+)\}\}/g, (_, key) => String(context[key] ?? ''))
}
```

**Placeholders connus** (extraits du registre) : `{{esg_score}}`, `{{total_tco2}}`, `{{top_category}}`, `{{top_category_pct}}`, `{{sector}}`, `{{matched_count}}`, `{{credit_score}}`, `{{active_actions}}`.

### Utilisation de Driver.js (API)

Driver.js 1.x expose une API fluide. Voici le pattern a suivre :

```typescript
const { driver } = await loadDriver()  // Depuis useDriverLoader.ts

const driverObj = driver({
  showProgress: false,
  showButtons: ['next', 'previous', 'close'],
  animate: !uiStore.prefersReducedMotion,  // NFR14
  onDestroyStarted: () => { /* cleanup */ },
  onDestroyed: () => { /* etat → complete */ },
})

// Pour chaque etape sequentiellement :
driverObj.highlight({
  element: '[data-guide-target="carbon-donut-chart"]',
  popover: {
    title: 'Repartition par categorie',
    description: 'Votre empreinte totale est de 47 tCO2e...'
  }
})

// Fin :
driverObj.destroy()
```

**Points cles Driver.js :**
- `driver()` est une factory qui retourne une instance
- `.highlight()` pointe un seul element avec popover
- `.drive()` execute une serie d'etapes (alternative a highlight sequentiel)
- `.destroy()` nettoie les overlays et popovers du DOM
- Callbacks : `onHighlightStarted`, `onHighlighted`, `onDestroyStarted`, `onDestroyed`

### addSystemMessage dans useChat.ts (detail)

`useChat.ts` gere les messages en module-level avec immutabilite (`messages.value = [...messages.value, newMsg]`). Le type `Message` utilise :

```typescript
interface Message {
  id: string           // crypto.randomUUID()
  role: 'user' | 'assistant'
  content: string
  created_at: string   // ISO 8601
  conversation_id?: string
}
```

`addSystemMessage` cree un message avec `role: 'assistant'` et sans `conversation_id` (message local, pas persiste au backend).

### Issues deferees resolues dans cette story

| Issue | Source | Resolution |
|-------|--------|------------|
| Route mismatch `show_esg_results` (`/esg` vs `/esg/results`) | deferred-work.md (story 4-3) | Task 7 : corriger `entryStep.targetRoute` dans registry.ts |
| `countdown` sans validation (0, negatif, NaN) | deferred-work.md (story 4-2) | AC9 / Task 2.7 : clamp min 1 seconde |
| `TourContext` sans contrat cle manquante | deferred-work.md (story 4-2) | AC8 / Task 2.6 : cle manquante → `''` |
| Elements `data-guide-target` dans des `v-if` | deferred-work.md (story 4-3) | AC4 / Task 4 : waitForElement avec retry 3x + skip |

### Issues deferees NON resolues ici (scope hors story)

- `route` non contraint dans `GuidedTourStep` — validation cross-references a ajouter quand la navigation multi-pages sera implementee (Story 5.3)
- `lib/` pas dans auto-import — choix d'architecture, imports manuels
- `requestIdleCallback` sans timeout — le fallback `loadDriver()` compense

### Intelligence des stories precedentes (Epic 4)

**Learnings cles :**
- Les tests `useDriverLoader.test.ts` utilisent `vi.resetModules()` pour resetter le cache module-level — appliquer le meme pattern pour `useGuidedTour.test.ts`
- Les tests `useChat.test.ts` utilisent `vi.mock()` pour stores, `vi.stubGlobal()` pour globals, et un helper `createMockSSEStream()` — patterns a reutiliser
- Le registre contient 6 tours avec 19 selectors uniques — tous poses dans le DOM (Story 4.3, 198 tests verts)
- `prefetchDriverJs()` est appele dans `FloatingChatWidget.vue` `onMounted()` — Driver.js sera deja cache quand `startTour` sera appele

### Commits recents

```
0749521 4-1/4-2/4-3: done (15 fichiers, 1474 insertions)
c1a24d0 3-2-injection-de-la-page-courante: done
d6889b2 3-2-injection-de-la-page-courante: done
c94a1e2 3-1-transmission-de-la-page-courante: done
c489a6c 2-2-mise-a-jour-de-la-navigation: done
```

### Anti-patterns a eviter

1. **NE PAS importer Driver.js en top-level** — `import('driver.js')` dynamique uniquement, via `loadDriver()`
2. **NE PAS creer un store Pinia pour l'etat du tour** — module-level state dans le composable (ADR3)
3. **NE PAS envoyer les messages system au backend** — `addSystemMessage` est local-only
4. **NE PAS modifier les types** dans `guided-tour.ts` — ils sont complets (TourState inclut deja tous les etats)
5. **NE PAS modifier le store `ui.ts`** — les champs `guidedTourActive`/`chatWidgetMinimized` sont pour Story 5.2
6. **NE PAS gerer la navigation multi-pages** — c'est Story 5.3 (filtrer les etapes mono-page)
7. **NE PAS creer de composant popover custom** — c'est Story 5.4 (utiliser les popovers Driver.js par defaut)
8. **NE PAS laisser de `{{placeholder}}` brut** en cas de cle manquante — remplacer par `''`

### Project Structure Notes

- Frontend : Nuxt 4 SPA (`ssr: false`), structure `app/`
- Composables : `app/composables/` — auto-importes par Nuxt
- Lib : `app/lib/` — PAS auto-importe, import explicite requis
- Types : `app/types/` — auto-importes par Nuxt
- Tests : `frontend/tests/` (miroir de la structure `app/`)
- Vitest 3.0, `@vue/test-utils` 2.4, `happy-dom`
- 198 tests existants, zero regression attendue

### References

- [Source: _bmad-output/planning-artifacts/epics.md — Epic 5, Story 5.1 (lignes 717-763)]
- [Source: _bmad-output/planning-artifacts/architecture.md — ADR3 Decision 3, machine a etats useGuidedTour]
- [Source: _bmad-output/planning-artifacts/architecture.md — ADR5 Decision 5, registre data-guide-target]
- [Source: _bmad-output/planning-artifacts/architecture.md — ADR7 Decision 7, lazy loading Driver.js]
- [Source: _bmad-output/implementation-artifacts/deferred-work.md — 4 issues deferees resolues dans cette story]
- [Source: _bmad-output/implementation-artifacts/4-3-marquage-data-guide-target-sur-les-composants-existants.md — Review findings, 19 selectors, v-if pattern]
- [Source: _bmad-output/implementation-artifacts/4-2-types-et-registre-de-parcours-guides.md — Registry complete, conventions]
- [Source: frontend/app/composables/useChat.ts — Pattern module-level state, structure Message]
- [Source: frontend/app/composables/useDriverLoader.ts — loadDriver(), prefetchDriverJs()]
- [Source: frontend/app/lib/guided-tours/registry.ts — tourRegistry, 6 tours, 19 selectors]
- [Source: frontend/app/types/guided-tour.ts — TourState, TourContext, GuidedTourDefinition]
- [Source: frontend/app/stores/ui.ts — prefersReducedMotion, pas encore guidedTourActive]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

Aucun blocage majeur. Correction d'erreurs de type liees au `satisfies` du registre (typage litteral vs GuidedTourDefinition).

### Completion Notes List

- Composable `useGuidedTour.ts` cree avec machine a etats module-level (ADR3) : idle → loading → highlighting → complete → idle
- `startTour(tourId, context?)` : resolution registre, interpolation `{{placeholders}}`, lazy loading Driver.js (ADR7), filtrage etapes mono-page
- `waitForElement(selector)` : retry 3x/500ms + skip avec message systeme si absent
- `cancelTour()` : destruction Driver.js, transition interrupted → idle (500ms)
- `addSystemMessage(content)` ajoute dans `useChat.ts` : message assistant local (non persiste backend)
- Route mismatch `show_esg_results` corrige : `/esg` → `/esg/results`
- Validation countdown : clamp min 1 seconde (0, negatif, NaN)
- Interpolation : cles manquantes → chaine vide `''`
- `prefers-reduced-motion` : `animate: false` passe a Driver.js
- 21 nouveaux tests (16 useGuidedTour + 5 addSystemMessage), 219 tests totaux, zero regression
- Zero nouvelle erreur de type dans le composable

### File List

| Action | Fichier |
|--------|---------|
| Cree | frontend/app/composables/useGuidedTour.ts |
| Cree | frontend/tests/composables/useGuidedTour.test.ts |
| Cree | frontend/tests/composables/useChat.addSystemMessage.test.ts |
| Modifie | frontend/app/composables/useChat.ts |
| Modifie | frontend/app/lib/guided-tours/registry.ts |

### Review Findings

- [x] [Review][Decision] **onPrevClick avance le tour au lieu de reculer** — Decision : retirer `'previous'` de `showButtons`. Corrige : bouton supprime, callback onPrevClick supprime. [useGuidedTour.ts] (sources: blind+edge)
- [x] [Review][Patch] **Securite async : pas de try/catch ni de signal d'annulation dans startTour** — Corrige : try/catch avec reset d'etat, flag `cancelled` verifie apres chaque await, cancelTour positionne le flag. [useGuidedTour.ts] (sources: blind+edge)
- [x] [Review][Patch] **clampCountdown retourne 1 au lieu de DEFAULT_ENTRY_COUNTDOWN pour NaN** — Corrige : NaN/non-fini → DEFAULT_ENTRY_COUNTDOWN (8), valeur < 1 → 1. [useGuidedTour.ts:22-26] (sources: blind+auditor)
- [x] [Review][Patch] **Race condition setConfig : onDestroyStarted enregistre apres highlight** — Corrige : onDestroyStarted passe dans la config initiale de driver(), via un closure resolveCurrentStep. [useGuidedTour.ts] (sources: blind+edge)
- [x] [Review][Patch] **Tests fragiles + couverture manquante** — Corrige : mock de blocage simplifie, 3 nouveaux tests (loadDriver rejection, zero etapes mono-page, cancelTour pendant loading). 24 tests, 222 total, zero regression. [useGuidedTour.test.ts] (sources: edge+auditor)
- [x] [Review][Defer] **Delai idle hardcode (AC5 "configurable")** — `setTimeout(..., 1000)` est hardcode. AC5 mentionne un delai configurable. Refinement mineur, pas bloquant. [useGuidedTour.ts:162-166] — deferred, refinement futur
- [x] [Review][Defer] **Element supprime entre waitForElement et highlight** — Fenetre de timing tres courte entre le retour de `waitForElement` et l'appel `highlight`. Limitation architecturale pre-existante. [useGuidedTour.ts:112-124] — deferred, pre-existing

### Change Log

- 2026-04-13 : Story 5.1 implementee — composable useGuidedTour (machine a etats, execution mono-page), addSystemMessage dans useChat, correction route registre show_esg_results, 21 tests
- 2026-04-13 : Code review — 1 decision-needed, 4 patch, 2 defer, 6 dismissed
