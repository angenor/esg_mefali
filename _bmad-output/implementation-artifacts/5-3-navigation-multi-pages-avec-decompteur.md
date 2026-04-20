# Story 5.3 : Navigation multi-pages avec decompteur

Status: review

## Story

En tant qu'utilisateur,
je veux que le parcours guide puisse me diriger vers une autre page avec un decompteur visuel,
afin d'etre accompagne meme quand les informations sont sur une page differente.

## Acceptance Criteria

### AC1 — Detection de navigation necessaire
**Given** le parcours a une etape dont `step.route !== currentRoute` (ou un `entryStep` avec `targetRoute`)
**When** l'etape est atteinte
**Then** l'etat passe a `'navigating'`
**And** Driver.js highlight le lien de navigation (ex: sidebar link) avec un popover contenant un CountdownBadge

### AC2 — Decompteur visuel
**Given** le popover avec decompteur est affiche
**When** le decompteur demarre (defaut 8 secondes, configurable par etape via `popover.countdown`)
**Then** le badge affiche le compte a rebours visuellement (secondes restantes)
**And** le texte du popover invite a cliquer sur le lien

### AC3 — Navigation par clic utilisateur
**Given** l'utilisateur clique sur le lien avant l'expiration du decompteur
**When** la navigation Nuxt s'execute (router.push)
**Then** le decompteur s'arrete
**And** l'etat passe a `'waiting_dom'`

### AC4 — Navigation automatique a expiration
**Given** le decompteur expire sans clic de l'utilisateur
**When** le timer atteint 0
**Then** la navigation est declenchee automatiquement via `router.push(step.targetRoute)`
**And** l'etat passe a `'waiting_dom'`

### AC5 — Attente DOM post-navigation
**Given** la navigation est effectuee (clic ou auto)
**When** la page cible se charge
**Then** le systeme attend `nextTick()` + polling de l'element cible (`waitForElement`)
**And** si l'element est trouve en < 5s, l'etat passe a `'highlighting'` et le parcours reprend
**And** si l'element n'est pas trouve en 5s, retry silencieux
**And** si l'element n'est pas trouve en 10s, le parcours s'interrompt avec message d'erreur dans le chat via `addSystemMessage()`

### AC6 — Dark mode CountdownBadge
**Given** le dark mode est actif
**When** le CountdownBadge est affiche
**Then** il respecte le theme dark (variantes `dark:` Tailwind)

### AC7 — Skip entryStep si deja sur la bonne page
**Given** un parcours avec `entryStep.targetRoute === currentRoute`
**When** `startTour` est appele
**Then** l'entryStep est ignore (pas de decompteur, pas de navigation)
**And** les etapes de la page courante sont executees directement

### AC8 — Zero regression
**Given** les 239 tests existants
**When** la story est implementee
**Then** zero regression + nouveaux tests >= 80% couverture

## Tasks / Subtasks

- [x] Task 1 — Creer le composant CountdownBadge.vue (AC: #1, #2, #6)
  - [x] 1.1 Creer `frontend/app/components/copilot/CountdownBadge.vue`
  - [x] 1.2 Props : `countdown` (number, secondes), `paused` (boolean, defaut false)
  - [x] 1.3 Emit : `expired` quand le timer atteint 0
  - [x] 1.4 Affichage : cercle/badge avec secondes restantes, animation fluide
  - [x] 1.5 Dark mode : `bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300`
  - [x] 1.6 Cleanup : `clearInterval` dans `onBeforeUnmount`
  - [x] 1.7 `prefers-reduced-motion` : desactiver l'animation du cercle (transition instantanee)

- [x] Task 2 — Etendre useGuidedTour : logique entryStep + navigation (AC: #1, #3, #4, #7)
  - [x] 2.1 Utiliser `navigateTo()` (API Nuxt globale, pas besoin de useRouter)
  - [x] 2.2 Dans `startTour()`, apres le chargement Driver.js, verifier si `definition.entryStep` existe ET `entryStep.targetRoute !== currentRoute`
  - [x] 2.3 Si entryStep necessaire : passer `tourState` a `'navigating'`
  - [x] 2.4 Highlighter le selecteur entryStep avec popover contenant le texte + countdown
  - [x] 2.5 Implementer le timer : `setInterval` 1s, decrementer le compteur
  - [x] 2.6 Sur clic lien (detecte via `onNextClick`/`onCloseClick` du popover) : stopper timer, `navigateTo(targetRoute)`, passer a `'waiting_dom'`
  - [x] 2.7 Sur expiration timer : `navigateTo(targetRoute)` automatique, passer a `'waiting_dom'`
  - [x] 2.8 Si entryStep.targetRoute === currentRoute : ignorer entryStep, executer les etapes directement (AC7)

- [x] Task 3 — Etendre useGuidedTour : attente DOM post-navigation (AC: #5)
  - [x] 3.1 Creer `waitForElementExtended(selector, timeoutMs)` : polling toutes les 500ms pendant `timeoutMs`
  - [x] 3.2 Apres `navigateTo()` : `await nextTick()`, puis `waitForElementExtended(firstStepSelector, 10000)`
  - [x] 3.3 Si element trouve < 5s : passer a `'highlighting'`, reprendre les etapes
  - [x] 3.4 Si element non trouve a 5s : retry silencieux (continuer polling)
  - [x] 3.5 Si element non trouve a 10s : appeler `addSystemMessage('La page n\'a pas pu se charger correctement. Le guidage est interrompu.')`, interrompre le tour
  - [x] 3.6 Verifier `cancelled` flag apres chaque await (pattern existant)

- [x] Task 4 — Refactorer la boucle d'etapes pour supporter les routes mixtes (AC: #1, #5)
  - [x] 4.1 Retirer le filtre `monoPageSteps` actuel (lignes 86-88 de useGuidedTour.ts)
  - [x] 4.2 Dans la boucle d'etapes, pour chaque step : verifier si `step.route && step.route !== currentRoute`
  - [x] 4.3 Si navigation necessaire : passer a `'navigating'`, highlighter le lien sidebar correspondant avec countdown, naviguer, attendre DOM
  - [x] 4.4 Apres navigation : mettre a jour `currentRoute` et continuer la boucle
  - [x] 4.5 Si pas de navigation necessaire : executer le highlight normalement (logique existante)

- [x] Task 5 — Tests unitaires Vitest (AC: #8)
  - [x] 5.1 Creer `frontend/tests/components/copilot/CountdownBadge.test.ts` : decompteur, expiration, dark mode, cleanup
  - [x] 5.2 Creer `frontend/tests/composables/useGuidedTour.navigation.test.ts` : entryStep processing, navigation auto a expiration, navigation par clic, skip entryStep si meme page, attente DOM 5s/10s timeout, cancelled flag pendant navigation
  - [x] 5.3 Verifier zero regression : `npx vitest run` — 255 tests, 0 regression
  - [x] 5.4 Verifier types : `npx nuxi typecheck` — aucune nouvelle erreur (3 erreurs pre-existantes dans dashboard.vue, financing/)

## Dev Notes

### Scope
Cette story est **strictement frontend** — aucune modification backend. Elle etend le composable `useGuidedTour` (Story 5.1) avec la logique de navigation cross-pages et cree un nouveau composant `CountdownBadge`.

### Ce que cette story fait :
- Traite les `entryStep` du registre (navigation initiale avec decompteur)
- Navigue entre pages pendant un parcours guide
- Attend le DOM apres navigation (polling avec timeouts 5s/10s)
- Cree le composant CountdownBadge (badge visuel avec timer)

### Ce que cette story ne fait PAS :
- Popover custom (Story 5.4 — GuidedTourPopover.vue)
- Interruption Escape/clic hors zone (Story 5.4)
- Declenchement par le LLM (Story 6.1)
- Consentement utilisateur (Story 6.3)

### Architecture (ADR3 — Machine a etats)

Le composable `useGuidedTour.ts` utilise un etat module-level (singleton). Les etats `'navigating'` et `'waiting_dom'` sont deja definis dans `types/guided-tour.ts` (TourState) mais **jamais utilises** actuellement. Cette story les active :

```
idle → loading → [navigating → waiting_dom →] highlighting → complete
                        │              │
                        └──── interrupted (cancelTour)
```

Transition ajoutee :
- `loading` → `navigating` (quand entryStep ou step.route !== currentRoute)
- `navigating` → `waiting_dom` (apres router.push)
- `waiting_dom` → `highlighting` (quand l'element cible est trouve dans le DOM)
- `waiting_dom` → `interrupted` (si timeout 10s depasse)

### Etat actuel du code (lignes cles dans useGuidedTour.ts)

**Lignes 82-88** — Filtre mono-page a retirer/adapter :
```typescript
const currentRoute = window.location.pathname
const monoPageSteps = definition.steps.filter(
  (step) => !step.route || step.route === currentRoute,
)
```
Ce filtre exclut les etapes sur d'autres routes. Il faut le remplacer par un traitement sequentiel qui gere la navigation quand `step.route !== currentRoute`.

**Ligne 63** — L'`entryStep` n'est jamais lu :
```typescript
const definition: GuidedTourDefinition | undefined = tourRegistry[tourId ...]
// definition.entryStep existe mais n'est jamais traite
```

**Lignes 41-55** — `waitForElement` existant : retry 3x/500ms, retourne `null` si absent. Pour la navigation post-page, il faut un timeout etendu (5s puis 10s) car le chargement de page prend plus de temps que l'apparition d'un element.

### Registre existant (6 parcours avec entryStep)

Tous les 6 parcours dans `lib/guided-tours/registry.ts` ont un `entryStep` avec :
- `selector` : lien sidebar (ex: `[data-guide-target="sidebar-carbon-link"]`)
- `popover.countdown` : `DEFAULT_ENTRY_COUNTDOWN` (8 secondes)
- `targetRoute` : route cible (ex: `/carbon/results`)

Les steps ont un champ `route` optionnel. Exemple `show_esg_results` :
- Step 1 : `route: '/esg/results'` + selector `esg-score-circle`
- Step 2 : pas de route (meme page) + selector `esg-strengths-badges`
- Step 3 : pas de route + selector `esg-recommendations`

### Pattern de navigation (Nuxt 4 SPA)

```typescript
const router = useRouter()
await router.push('/carbon/results')
await nextTick() // Attendre le cycle de rendu Vue
// Puis polling waitForElement pour l'element cible
```

**IMPORTANT** : `useRouter()` doit etre appele dans un contexte Vue (setup, composable). Dans le module-level de useGuidedTour, il faut soit :
- Appeler `useRouter()` a l'interieur de `useGuidedTour()` (dans la portee du composable) et le cacher en module-level
- Ou utiliser `navigateTo()` de Nuxt (auto-importe, fonctionne hors setup)

**Recommandation** : Utiliser `navigateTo(targetRoute)` (API Nuxt, auto-importee) plutot que `router.push()` car elle est disponible globalement sans besoin de `useRouter()`.

### CountdownBadge — Specifications visuelles

```vue
<!-- Minimal : badge inline dans le popover Driver.js -->
<template>
  <span class="inline-flex items-center gap-1 rounded-full px-2.5 py-1
    bg-green-100 dark:bg-green-900/30
    text-green-700 dark:text-green-300
    text-sm font-semibold tabular-nums">
    <svg><!-- icone horloge --></svg>
    {{ remaining }}s
  </span>
</template>
```

Le CountdownBadge sera integre dans le popover Driver.js. Pour cette story, on l'injecte dans la `description` du popover via `popoverRender` (Driver.js permet un callback de rendu custom) **OU** on cree un element DOM insere dans le popover apres `.highlight()`.

**Approche recommandee** : Utiliser la propriete `popoverClass` et injecter le badge en tant que noeud DOM dans `onHighlightStarted` callback. Plus simple que `popoverRender` (Story 5.4 couvrira les popovers custom complets).

**Alternative plus propre** : Creer un conteneur `div` avec le badge monte via `createApp()` de Vue dans le contenu du popover. Pattern :

```typescript
import { createApp, h } from 'vue'
import CountdownBadge from '~/components/copilot/CountdownBadge.vue'

// Apres highlight, trouver le popover et y injecter le badge
const popoverDesc = document.querySelector('.driver-popover-description')
if (popoverDesc) {
  const badgeContainer = document.createElement('div')
  popoverDesc.appendChild(badgeContainer)
  const app = createApp({ render: () => h(CountdownBadge, { countdown: 8, onExpired: handleExpired }) })
  app.mount(badgeContainer)
  // Cleanup: app.unmount() quand on quitte l'etape
}
```

### Integration avec la retraction widget (Story 5.2)

La retraction du widget se produit AVANT la navigation. Sequence complete :
1. `startTour()` appele
2. `guidedTourActive = true`, `chatWidgetMinimized = true`
3. GSAP retracte le widget → `notifyRetractComplete()`
4. **NOUVEAU** : Si entryStep et navigation necessaire → highlight entryStep avec countdown
5. Navigation (clic ou auto-expiration)
6. Attente DOM post-navigation
7. Highlighting des etapes
8. Fin → widget reapparait

### Cleanup et annulation pendant navigation

Si `cancelTour()` est appele pendant la navigation (etat `'navigating'` ou `'waiting_dom'`) :
- Stopper le timer countdown (`clearInterval`)
- Detruire Driver.js (`driverInstance.destroy()`)
- Ne PAS faire de `router.push` inverse (on reste sur la page courante)
- Reapparition widget (flags uiStore reset — logique existante)

### Fichiers a creer

| Fichier | Description |
|---------|-------------|
| `frontend/app/components/copilot/CountdownBadge.vue` | Badge decompteur visuel avec timer |
| `frontend/tests/components/copilot/CountdownBadge.test.ts` | Tests unitaires CountdownBadge |
| `frontend/tests/composables/useGuidedTour.navigation.test.ts` | Tests navigation multi-pages |

### Fichiers a modifier

| Fichier | Modification |
|---------|-------------|
| `frontend/app/composables/useGuidedTour.ts` | Logique entryStep, navigation, waitForElementExtended, refactoring boucle etapes |

### Anti-patterns a eviter

1. **Ne PAS creer de middleware Nuxt** pour la navigation du tour — tout passe par `router.push` / `navigateTo` dans le composable
2. **Ne PAS utiliser `watch(route)` global** — utiliser des Promises/polling pour detecter l'arrivee sur la page cible
3. **Ne PAS modifier `waitForElement` existant** — creer `waitForElementExtended` separement (le retry 3x/500ms existant est utilise pour les elements sur la page courante)
4. **Ne PAS creer GuidedTourPopover.vue** — c'est Story 5.4. Utiliser le popover par defaut de Driver.js avec injection DOM du CountdownBadge
5. **Ne PAS gerer l'interruption Escape/clic hors zone** — c'est Story 5.4
6. **Ne PAS importer `useRouter` au niveau module** — utiliser `navigateTo()` (API Nuxt globale) ou cacher le router dans le scope composable
7. **Ne PAS oublier `clearInterval`** sur le timer countdown dans tous les chemins (expiration, clic, annulation, erreur)

### Patterns de test (reference Story 5.1)

Les tests utilisent :
- `vi.mock('~/composables/useDriverLoader')` pour mocker Driver.js
- `vi.mock('~/stores/ui')` pour mocker le store Pinia
- `vi.stubGlobal('document', ...)` pour le DOM
- `vi.useFakeTimers()` pour les timers (countdown)
- `vi.resetModules()` entre les tests pour reseter le state module-level

Pour les tests de navigation, mocker aussi :
- `navigateTo` (auto-import Nuxt) : `vi.stubGlobal('navigateTo', vi.fn())`
- `window.location.pathname` : `vi.stubGlobal('location', { pathname: '/dashboard' })`

### Imports existants dans useGuidedTour.ts

```typescript
import { ref, readonly } from 'vue'
import type { TourState, TourContext, GuidedTourDefinition } from '~/types/guided-tour'
import { tourRegistry, DEFAULT_ENTRY_COUNTDOWN } from '~/lib/guided-tours/registry'
import { loadDriver } from '~/composables/useDriverLoader'
```

Nouveaux imports necessaires :
```typescript
import { nextTick } from 'vue'
// navigateTo est auto-importe par Nuxt (pas d'import explicite)
```

### Types existants (aucune modification necessaire)

- `TourState` inclut deja `'navigating'` et `'waiting_dom'`
- `GuidedTourEntryStep` a `selector`, `popover` (avec `countdown`), `targetRoute`
- `GuidedTourStep` a `route?`, `selector`, `popover`
- `DEFAULT_ENTRY_COUNTDOWN` = 8 (exporte depuis le registre)
- `clampCountdown()` existe deja dans useGuidedTour.ts (validation countdown)
- `interpolate()` existe deja (placeholders → contexte)

### Exigences non-fonctionnelles

- **NFR14** : `prefers-reduced-motion` → pas d'animation sur le CountdownBadge (transition instantanee)
- **NFR16** : Timeout 10s maximum pour le chargement page → interruption avec message chat
- **FR22** : Navigation auto a expiration du decompteur
- **FR23** : Reprise du parcours apres navigation reussie

### Project Structure Notes

- Frontend : Nuxt 4 SPA (`ssr: false`), structure `app/`
- Composables : `app/composables/` — auto-importes par Nuxt
- Composants : `app/components/copilot/` — auto-importes par Nuxt (pathPrefix: false)
- Lib : `app/lib/` — PAS auto-importe, import explicite requis
- Tests : `frontend/tests/` (miroir de `app/`)
- Vitest 3.0, `@vue/test-utils` 2.4, `happy-dom`
- 239 tests existants (post Story 5.2), zero regression attendue

### References

- [Source: _bmad-output/planning-artifacts/epics-019-floating-copilot.md — Epic 5, Story 5.3]
- [Source: _bmad-output/planning-artifacts/architecture-019-floating-copilot.md — Decision 3 (machine a etats useGuidedTour)]
- [Source: _bmad-output/planning-artifacts/architecture-019-floating-copilot.md — Decision 5 (registre data-guide-target)]
- [Source: _bmad-output/planning-artifacts/architecture-019-floating-copilot.md — Decision 6 (orchestration retraction widget)]
- [Source: _bmad-output/planning-artifacts/architecture-019-floating-copilot.md — Decision 7 (lazy loading Driver.js)]
- [Source: _bmad-output/implementation-artifacts/5-1-composable-useguidedtour-machine-a-etats-et-execution-mono-page.md]
- [Source: _bmad-output/implementation-artifacts/5-2-retraction-et-reapparition-animee-du-widget-pendant-le-guidage.md]
- [Source: frontend/app/composables/useGuidedTour.ts — code actuel, lignes 82-88 (filtre mono-page)]
- [Source: frontend/app/types/guided-tour.ts — TourState inclut 'navigating' et 'waiting_dom']
- [Source: frontend/app/lib/guided-tours/registry.ts — 6 parcours avec entryStep]

## Dev Agent Record

### Agent Model Used
Claude Opus 4.6 (1M context)

### Debug Log References
- Test regression fixee : test `tour_other_route` mis a jour pour reflet du nouveau comportement navigation multi-pages (avant: filtre mono-page, maintenant: navigateTo)
- Test `prefersReducedMotion` fixe : mock UI store unifie avec guidedTourActive/chatWidgetMinimized/chatWidgetOpen
- Import GuidedTourStep inutilise supprime apres refactoring

### Completion Notes List
- CountdownBadge.vue : composant autonome avec timer setInterval, props countdown/paused, emit expired, dark mode, motion-reduce, cleanup onBeforeUnmount. 9 tests unitaires.
- useGuidedTour.ts : ajout `waitForElementExtended` (polling 500ms, timeout configurable), logique entryStep avec countdown DOM injecte dans popover Driver.js, navigation via `navigateTo()` (API Nuxt globale), attente DOM post-navigation (10s max avec interruption+message chat), refactoring boucle etapes pour routes mixtes (navigation intra-boucle), nettoyage timer countdown dans cancelTour et catch.
- 7 tests de navigation (entryStep, auto-expiration, skip meme page, tour sans entry, timeout DOM 10s, navigation intra-boucle, annulation pendant navigation).
- 255 tests totaux, zero regression, zero nouvelle erreur de types.

### File List
- `frontend/app/components/copilot/CountdownBadge.vue` (NOUVEAU)
- `frontend/app/composables/useGuidedTour.ts` (MODIFIE)
- `frontend/tests/components/copilot/CountdownBadge.test.ts` (NOUVEAU)
- `frontend/tests/composables/useGuidedTour.navigation.test.ts` (NOUVEAU)
- `frontend/tests/composables/useGuidedTour.test.ts` (MODIFIE — adaptation mocks UI store + test tour_other_route)

### Review Findings
- [x] [Review][Patch] Supprimer CountdownBadge.vue + test (code mort, injection DOM brute preferee) [CountdownBadge.vue, CountdownBadge.test.ts] — FIXED
- [x] [Review][Patch] Remplacer innerHTML par createElement/textContent pour le badge countdown [useGuidedTour.ts:185] — FIXED
- [x] [Review][Patch] Ajouter badge countdown visuel dans la navigation intra-boucle [useGuidedTour.ts:282-313] — FIXED
- [x] [Review][Patch] Extraire bloc interrupt/cleanup duplique 3x en helper interruptTour() [useGuidedTour.ts:238-256, 340-358] — FIXED
- [x] [Review][Patch] Supprimer variable mockPrefersReducedMotion inutilisee [useGuidedTour.test.ts:26] — FIXED
- [x] [Review][Defer] Bouton retour navigateur pendant tour multi-pages — 10s de widget minimise sans UI — deferred, pre-existing (Story 7 resilience)

## Change Log
- Story 5.3 implementation complete : navigation multi-pages avec decompteur dans les parcours guides. Composant CountdownBadge, logique entryStep, waitForElementExtended, boucle etapes multi-routes. 16 nouveaux tests (9 CountdownBadge + 7 navigation), 255 tests totaux, zero regression. (Date: 2026-04-13)
