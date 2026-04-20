# Story 5.4 : Interruption du parcours et popover custom

Status: done

## Story

En tant qu'utilisateur,
je veux pouvoir interrompre un parcours guide a tout moment et voir des popovers bien designes,
afin de garder le controle de mon experience sans me sentir piege.

## Acceptance Criteria

### AC1 — Interruption via Escape
**Given** un parcours guide est en cours
**When** l'utilisateur appuie sur Escape
**Then** le parcours s'interrompt immediatement
**And** `driver.destroy()` est appele
**And** le widget reapparait (`uiStore.chatWidgetMinimized = false`)
**And** l'etat passe a `'interrupted'`
**And** aucun message n'est ajoute au chat (action volontaire — FR25)

### AC2 — Interruption via clic hors zone
**Given** un parcours guide est en cours
**When** l'utilisateur clique hors de la zone highlight/popover
**Then** le comportement est identique a Escape (interruption propre)

### AC3 — Popover custom avec titre et description
**Given** le popover custom GuidedTourPopover est affiche
**When** l'utilisateur le consulte
**Then** il affiche le titre et la description en francais avec accents
**And** il integre le CountdownBadge si l'etape a un countdown
**And** le design est coherent avec le style de la plateforme (arrondi, ombres, typographie)

### AC4 — Dark mode popovers
**Given** le dark mode est actif
**When** les popovers sont affiches
**Then** ils utilisent les couleurs dark (`bg-dark-card`, `text-surface-dark-text`, `border-dark-border`)

### AC5 — Respect prefers-reduced-motion
**Given** `prefers-reduced-motion` est actif
**When** Driver.js affiche les popovers
**Then** `animate: false` est passe dans la configuration Driver.js (NFR14)

### AC6 — Cleanup DOM complet
**Given** le parcours est interrompu ou termine
**When** le cleanup s'execute
**Then** aucun overlay, popover, ou classe CSS de Driver.js ne reste dans le DOM

### AC7 — Zero regression
**Given** les 246 tests existants
**When** la story est implementee
**Then** zero regression + nouveaux tests >= 80% couverture

## Tasks / Subtasks

- [x] Task 1 — Creer le composant GuidedTourPopover.vue (AC: #3, #4)
  - [x] 1.1 Creer `frontend/app/components/copilot/GuidedTourPopover.vue`
  - [x] 1.2 Props : `title` (string), `description` (string), `countdown` (number | undefined), `currentStep` (number), `totalSteps` (number)
  - [x] 1.3 Emit : `close` (bouton fermer ou clic bouton X), `next` (bouton suivant), `countdownExpired`
  - [x] 1.4 Slots : badge countdown integre si `countdown` est defini — reutiliser la logique du badge DOM existant (Story 5.3) en composant Vue reactif
  - [x] 1.5 Style plateforme : `rounded-xl shadow-xl` + typographie coherente avec le widget chat
  - [x] 1.6 Dark mode complet : `bg-white dark:bg-dark-card`, `text-surface-text dark:text-surface-dark-text`, `border border-gray-200 dark:border-dark-border`
  - [x] 1.7 Bouton fermer (X) en haut a droite + bouton « Suivant » en bas
  - [x] 1.8 Indicateur de progression : « Etape {currentStep}/{totalSteps} »
  - [x] 1.9 Accessibilite : `role="dialog"`, `aria-label` sur le popover, focus trap sur les boutons du popover

- [x] Task 2 — Integrer GuidedTourPopover dans Driver.js via popoverRender (AC: #3, #5)
  - [x] 2.1 Dans `useGuidedTour.ts`, utiliser la config Driver.js `popoverClass` pour appliquer les classes custom
  - [x] 2.2 Implementer `popoverRender` (callback Driver.js) pour monter le composant Vue `GuidedTourPopover` dans le conteneur popover
  - [x] 2.3 Utiliser `createApp()` + `h()` de Vue pour monter/demonter `GuidedTourPopover` dans le noeud DOM du popover Driver.js
  - [x] 2.4 Passer les props (title, description, countdown, currentStep, totalSteps) et ecouter les emits (close → cancelTour, next → resolveCurrentStep, countdownExpired → navigation auto)
  - [x] 2.5 Cleanup : `app.unmount()` a chaque changement d'etape et a la fin du parcours
  - [x] 2.6 Remplacer l'injection DOM brute `injectCountdownBadge()` (Story 5.3) par le popover custom

- [x] Task 3 — Brancher l'interruption utilisateur dans useGuidedTour (AC: #1, #2)
  - [x] 3.1 Dans la config Driver.js, setter `allowClose: true` (permet clic overlay + Escape)
  - [x] 3.2 Utiliser le callback `onDestroyStarted` (deja en place) pour detecter l'interruption utilisateur
  - [x] 3.3 Dans `onDestroyStarted`, distinguer interruption volontaire (Escape/clic overlay) vs fin programmatique (navigation inter-etape) — verifier si `cancelled` est deja true ou si c'est un appel inattendu
  - [x] 3.4 Sur interruption volontaire : appeler `cancelTour()` (deja existant dans useGuidedTour.ts:435-464) qui gere le cleanup complet
  - [x] 3.5 Verifier que l'interruption fonctionne dans chaque etat : `'loading'`, `'navigating'`, `'waiting_dom'`, `'highlighting'`
  - [x] 3.6 Aucun message chat sur interruption volontaire (FR25) — le `cancelTour()` existant ne poste pas de message, c'est correct

- [x] Task 4 — Cleanup DOM complet post-parcours (AC: #6)
  - [x] 4.1 Apres `driver.destroy()`, verifier et supprimer tout residu : `.driver-popover`, `.driver-overlay`, `.driver-highlighted-element`, `[data-driver-active-element]`
  - [x] 4.2 Creer une fonction `cleanupDriverResiduals()` qui `querySelectorAll` et `remove()` les elements orphelins
  - [x] 4.3 Appeler `cleanupDriverResiduals()` dans : fin de parcours (complete), `cancelTour()`, bloc catch
  - [x] 4.4 Restaurer les classes CSS eventuellement ajoutees par Driver.js sur les elements cibles (`driver-highlighted-element`, `driver-no-animation`)
  - [x] 4.5 Cleanup des mini-apps Vue montees via `createApp()` dans le popoverRender (Task 2.5)

- [x] Task 5 — Tests unitaires Vitest (AC: #7)
  - [x] 5.1 Creer `frontend/tests/components/copilot/GuidedTourPopover.test.ts` : rendu titre/description, dark mode classes, bouton fermer emit, bouton suivant emit, countdown integre, indicateur progression, accessibilite role/aria
  - [x] 5.2 Etendre `frontend/tests/composables/useGuidedTour.test.ts` : interruption via `onDestroyStarted` callback, cleanup DOM post-destroy, pas de message chat sur interruption volontaire
  - [x] 5.3 Tester `cleanupDriverResiduals()` : elements orphelins supprimes, elements non-driver preserves
  - [x] 5.4 Verifier zero regression : `npx vitest run` — 263 tests, 0 regression
  - [x] 5.5 Verifier types : `npx nuxi typecheck` — aucune nouvelle erreur

### Review Findings

- [x] [Review][Decision] Focus trap absent dans GuidedTourPopover.vue — Corrigé : focus trap ajouté (handleKeydown + focus initial + aria-modal)
- [x] [Review][Patch] Re-entrance `onDestroyStarted` → `cancelTour()` → `destroy()` potentielle boucle infinie — Corrigé : guard `if (cancelled) return` ajouté
- [x] [Review][Patch] Double-clic « Suivant » peut laisser `userInitiatedClose = false` — Corrigé : flag `nextClicked` + `:disabled` sur le bouton
- [x] [Review][Patch] `countdown=0` bloque le popover — Corrigé : guard `if (countdown <= 0)` émet `countdownExpired` via `queueMicrotask`
- [x] [Review][Patch] `cleanupDriverResiduals()` supprime les éléments `.driver-active-element` — Corrigé : `classList.remove()` au lieu de `el.remove()`

## Dev Notes

### Scope
Cette story est **strictement frontend** — aucune modification backend. Elle cree le composant `GuidedTourPopover.vue` et branche l'interruption utilisateur (Escape/clic hors zone) dans `useGuidedTour.ts`.

### Ce que cette story fait :
- Cree le popover custom (`GuidedTourPopover.vue`) monte via `createApp()` dans Driver.js
- Branche le callback `onDestroyStarted` pour l'interruption utilisateur
- Remplace l'injection DOM brute `injectCountdownBadge()` par le popover custom
- Ajoute le cleanup DOM residuel post-parcours

### Ce que cette story ne fait PAS :
- Declenchement par le LLM (Story 6.1)
- Consentement utilisateur (Story 6.3)
- Gestion bouton retour navigateur pendant tour (Story 7 — resilience)
- Modifier les 6 parcours du registre (ils restent identiques)
- Modifier le backend

### Architecture (ADR3 — Machine a etats)

L'etat machine dans `useGuidedTour.ts` ne change PAS. Les etats existants suffisent :

```
idle → loading → [navigating → waiting_dom →] highlighting → complete
                        │              │
                        └──── interrupted (cancelTour)
```

L'interruption via Escape/clic hors zone utilise `cancelTour()` existant (lignes 435-464) qui gere deja :
- `cancelled = true`
- `clearCountdownTimer()`
- `driverInstance.destroy()`, `driverInstance = null`
- Reset flags widget (`chatWidgetMinimized = false`, `guidedTourActive = false`)
- `tourState → 'interrupted'` → `'idle'` (apres 500ms)

### Etat actuel du code (points d'ancrage dans useGuidedTour.ts)

**Lignes 175-182** — Creation instance Driver.js avec `onDestroyStarted` :
```typescript
driverInstance = driverModule.driver({
  showProgress: false,
  showButtons: ['next', 'close'],
  animate: !uiStore.prefersReducedMotion,
  onDestroyStarted: () => {
    resolveCurrentStep?.()
  },
})
```
Ce callback est appele quand l'utilisateur clique overlay ou Escape. Actuellement il resolve la Promise de l'etape en cours mais ne declenche PAS `cancelTour()`. **C'est le point central a modifier** : il faut distinguer l'interruption volontaire de la resolution programmatique.

**Lignes 98-113** — `injectCountdownBadge()` (injection DOM brute) :
```typescript
function injectCountdownBadge(seconds: number): HTMLSpanElement { ... }
```
Cette fonction cree un `<span>` DOM et l'injecte dans `.driver-popover-description`. Elle sera **remplacee** par le montage du composant Vue `GuidedTourPopover` via `popoverRender`.

**Lignes 374-391** — Highlight standard par etape :
```typescript
await new Promise<void>((resolve) => {
  resolveCurrentStep = resolve
  driverInstance!.highlight({
    element: step.selector,
    popover: {
      title: step.popover.title,
      description: step.popover.description,
      side: step.popover.side,
      onNextClick: () => { resolve() },
      onCloseClick: () => { resolve() },
    },
  })
})
```
Les callbacks `onNextClick` et `onCloseClick` resolvent la Promise. Il faut intercepter `onCloseClick` pour differencier « bouton fermer du popover custom » (interruption) vs « bouton next » (avancer).

### Strategie d'integration GuidedTourPopover dans Driver.js

Driver.js expose `popoverRender` dans sa config (ou par etape) : un callback qui recoit `(popover: PopoverDOM, opts: { config, state })` et permet de remplacer le contenu du popover.

**Approche recommandee** :

```typescript
// Dans la config Driver.js
popoverRender: (popover) => {
  // Vider le contenu par defaut de Driver.js
  popover.wrapper.innerHTML = ''

  // Monter le composant Vue
  const container = document.createElement('div')
  popover.wrapper.appendChild(container)

  const app = createApp({
    render: () => h(GuidedTourPopover, {
      title: currentStepData.title,
      description: currentStepData.description,
      countdown: currentStepData.countdown,
      currentStep: currentStepIndex.value + 1,
      totalSteps: totalSteps,
      onClose: () => cancelTour(),
      onNext: () => resolveCurrentStep?.(),
      onCountdownExpired: () => handleCountdownExpired(),
    })
  })
  app.mount(container)

  // Stocker pour cleanup
  mountedApps.push(app)
}
```

**IMPORTANT** : `popoverRender` est appele a chaque `highlight()`. Il faut demonter (`app.unmount()`) la mini-app precedente avant d'en monter une nouvelle.

### CountdownBadge dans le popover custom

La Story 5.3 review a constate que `CountdownBadge.vue` est du code mort (injection DOM brute preferee). Dans cette story, le countdown est integre DANS `GuidedTourPopover.vue` directement :
- Un `ref(countdown)` reactif qui decremente via `setInterval`
- Affichage conditionnel `v-if="countdown !== undefined"`
- Emit `countdownExpired` quand le timer atteint 0
- Cleanup `clearInterval` dans `onBeforeUnmount`
- Le badge utilise les memes classes : `bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300`

Ne PAS creer un composant CountdownBadge separe — il a ete supprime en review 5.3.

### Distinguer interruption volontaire vs resolution programmatique

Le callback `onDestroyStarted` est appele dans TOUS les cas de destruction Driver.js. Il faut un flag pour distinguer :

```typescript
let userInitiatedClose = true  // defaut = interruption utilisateur

// Avant resolve programmatique (next, countdown expired, navigation) :
userInitiatedClose = false
resolveCurrentStep?.()

// Dans onDestroyStarted :
onDestroyStarted: () => {
  if (userInitiatedClose) {
    cancelTour()
  }
  resolveCurrentStep?.()
  userInitiatedClose = true  // reset pour la prochaine etape
}
```

### Cleanup DOM residuel

Driver.js laisse parfois des elements orphelins (overlay, classes CSS). Fonction defensive :

```typescript
function cleanupDriverResiduals(): void {
  // Supprimer les elements overlay/popover orphelins
  document.querySelectorAll(
    '.driver-popover, .driver-overlay, .driver-active-element'
  ).forEach(el => el.remove())

  // Retirer les attributs/classes Driver.js des elements cibles
  document.querySelectorAll('[data-driver-active-element]').forEach(el => {
    el.removeAttribute('data-driver-active-element')
  })
}
```

Appeler dans : `interruptTour()`, fin de parcours (complete), bloc catch.

### Fichiers a creer

| Fichier | Description |
|---------|-------------|
| `frontend/app/components/copilot/GuidedTourPopover.vue` | Popover custom avec titre, description, countdown, progression |
| `frontend/tests/components/copilot/GuidedTourPopover.test.ts` | Tests unitaires GuidedTourPopover |

### Fichiers a modifier

| Fichier | Modification |
|---------|-------------|
| `frontend/app/composables/useGuidedTour.ts` | Integration `popoverRender` avec GuidedTourPopover, interruption via `onDestroyStarted`, cleanup DOM, remplacement `injectCountdownBadge` |
| `frontend/tests/composables/useGuidedTour.test.ts` | Tests interruption, cleanup DOM |

### Anti-patterns a eviter

1. **Ne PAS creer un CountdownBadge.vue separe** — il a ete supprime en review Story 5.3. Integrer le timer directement dans GuidedTourPopover
2. **Ne PAS modifier le registre des parcours** (`lib/guided-tours/registry.ts`) — les definitions restent identiques
3. **Ne PAS utiliser `innerHTML`** pour le contenu du popover — utiliser `createApp()` + `h()` (securite XSS + reactivite Vue)
4. **Ne PAS oublier `app.unmount()`** des mini-apps Vue montees dans les popovers — fuite memoire si non demontees
5. **Ne PAS poster de message chat sur interruption volontaire** (FR25) — `cancelTour()` ne poste pas de message, et c'est intentionnel
6. **Ne PAS ajouter un EventListener global `keydown`** pour Escape — Driver.js gere deja Escape via `allowClose: true` et le callback `onDestroyStarted`
7. **Ne PAS modifier les 13 composants chat existants** dans `components/chat/`
8. **Ne PAS modifier le store `ui.ts`** — les flags necessaires (`guidedTourActive`, `chatWidgetMinimized`, `prefersReducedMotion`) existent deja

### Patterns de test (reference Stories 5.1-5.3)

Les tests utilisent :
- `vi.mock('~/composables/useDriverLoader')` pour mocker Driver.js
- `vi.mock('~/stores/ui')` pour mocker le store Pinia
- `vi.stubGlobal('document', ...)` pour le DOM
- `vi.useFakeTimers()` pour les timers (countdown)
- `vi.resetModules()` entre les tests pour reseter le state module-level
- `vi.stubGlobal('navigateTo', vi.fn())` pour la navigation Nuxt

Pour les tests du popover :
- `@vue/test-utils` `mount()` pour le composant GuidedTourPopover
- Verifier les classes dark mode via `wrapper.classes()` ou `wrapper.html().includes()`
- Tester les emits via `wrapper.emitted()`
- `vi.useFakeTimers()` pour le countdown integre

### Imports existants dans useGuidedTour.ts

```typescript
import { ref, readonly, nextTick } from 'vue'
import type { TourState, TourContext, GuidedTourDefinition } from '~/types/guided-tour'
import { tourRegistry, DEFAULT_ENTRY_COUNTDOWN } from '~/lib/guided-tours/registry'
import { loadDriver } from '~/composables/useDriverLoader'
```

Nouveaux imports necessaires :
```typescript
import { createApp, h } from 'vue'
import GuidedTourPopover from '~/components/copilot/GuidedTourPopover.vue'
```

### Types existants (aucune modification necessaire)

- `TourState` inclut deja `'interrupted'`
- `GuidedTourPopover` (l'interface type) : `title`, `description`, `side?`, `countdown?`
- `GuidedTourStep` et `GuidedTourEntryStep` inchanges
- `DEFAULT_ENTRY_COUNTDOWN` = 8

### Exigences non-fonctionnelles

- **NFR3** : Chaque popover s'affiche en < 200ms apres le precedent
- **NFR13** : Les popovers Driver.js se ferment via Escape. Focus piege dans le popover
- **NFR14** : `prefers-reduced-motion` → `animate: false` dans Driver.js (deja en place ligne 178)
- **FR25** : Interruption a tout moment sans message chat

### Project Structure Notes

- Frontend : Nuxt 4 SPA (`ssr: false`), structure `app/`
- Composables : `app/composables/` — auto-importes par Nuxt
- Composants : `app/components/copilot/` — auto-importes par Nuxt (`pathPrefix: false`)
- Tests : `frontend/tests/` (miroir de `app/`)
- Vitest 3.0, `@vue/test-utils` 2.4, `happy-dom`
- 246 tests existants (post Story 5.3 + commit), zero regression attendue

### References

- [Source: _bmad-output/planning-artifacts/epics-019-floating-copilot.md — Epic 5, Story 5.4]
- [Source: _bmad-output/planning-artifacts/architecture-019-floating-copilot.md — Decision 3 (machine a etats useGuidedTour)]
- [Source: _bmad-output/planning-artifacts/architecture-019-floating-copilot.md — Decision 5 (registre data-guide-target)]
- [Source: _bmad-output/planning-artifacts/architecture-019-floating-copilot.md — Decision 7 (lazy loading Driver.js)]
- [Source: _bmad-output/implementation-artifacts/5-3-navigation-multi-pages-avec-decompteur.md — Review: CountdownBadge.vue supprime]
- [Source: frontend/app/composables/useGuidedTour.ts — code actuel complet, 471 lignes]
- [Source: frontend/app/types/guided-tour.ts — TourState, GuidedTourPopover, GuidedTourStep]
- [Source: frontend/tests/composables/useGuidedTour.test.ts — patterns de mock existants]

## Dev Agent Record

### Agent Model Used
Claude Opus 4.6 (1M context)

### Debug Log References
- Propriete Driver.js : `onPopoverRender` (pas `popoverRender`) — corrige apres typecheck
- Mocks des tests adaptes pour le nouveau flux `onPopoverRender` → montage composant Vue → clic bouton next

### Completion Notes List
- Task 1 : Composant GuidedTourPopover.vue cree avec props, emits, countdown reactif integre, dark mode complet, accessibilite (role="dialog", aria-label), indicateur de progression
- Task 2 : Integration via `onPopoverRender` callback Driver.js dans useGuidedTour.ts. `createApp()` + `h()` pour monter/demonter le composant Vue dans le DOM du popover. Suppression de `injectCountdownBadge()`. `showButtons: []` car le composant gere ses propres boutons
- Task 3 : Flag `userInitiatedClose` pour distinguer interruption volontaire (Escape/overlay) vs resolution programmatique (next/countdown/navigation). `allowClose: true` dans la config Driver.js. cancelTour() appele uniquement sur interruption volontaire. Aucun message chat sur interruption (FR25)
- Task 4 : Fonctions `cleanupDriverResiduals()` et `unmountAllPopoverApps()` ajoutees. Appelees dans : finalisation, cancelTour, catch. Suppression elements orphelins (.driver-popover, .driver-overlay, .driver-active-element, [data-driver-active-element]) et classes CSS (driver-highlighted-element, driver-no-animation)
- Task 5 : 11 nouveaux tests GuidedTourPopover + 6 nouveaux tests useGuidedTour (interruption, cleanup DOM, popoverRender). 3 fichiers de tests existants adaptes pour le nouveau flux. 263 tests totaux, 0 regression. Typecheck OK

### File List
- `frontend/app/components/copilot/GuidedTourPopover.vue` (NEW)
- `frontend/app/composables/useGuidedTour.ts` (MODIFIED)
- `frontend/tests/components/copilot/GuidedTourPopover.test.ts` (NEW)
- `frontend/tests/composables/useGuidedTour.test.ts` (MODIFIED)
- `frontend/tests/composables/useGuidedTour.retract.test.ts` (MODIFIED)
- `frontend/tests/composables/useGuidedTour.navigation.test.ts` (MODIFIED)

### Change Log
- 2026-04-13 : Story 5.4 implementee — composant GuidedTourPopover.vue, integration onPopoverRender Driver.js, interruption utilisateur via Escape/overlay, cleanup DOM residuel, 17 nouveaux tests (263 total, 0 regression)
