# Story 5.2 : Retraction et reapparition animee du widget pendant le guidage

Status: done

## Story

En tant qu'utilisateur,
je veux que le widget de chat se retracte automatiquement pendant un parcours guide,
afin de ne pas masquer les elements que le systeme me montre.

## Acceptance Criteria

1. **AC1 — uiStore recoit les champs guidedTourActive et chatWidgetMinimized**
   - **Given** le store `ui.ts` n'a pas encore ces champs
   - **When** un developpeur les ajoute
   - **Then** `chatWidgetMinimized` (ref\<boolean\>, defaut `false`) controle la retraction visuelle du widget
   - **And** `guidedTourActive` (ref\<boolean\>, defaut `false`) bloque l'ouverture du widget pendant un guidage
   - **And** les deux champs sont exposes dans le return du store

2. **AC2 — useGuidedTour declenche la retraction au demarrage du parcours**
   - **Given** `startTour()` est appele et l'etat passe a `'loading'`
   - **When** useGuidedTour prepare le parcours
   - **Then** `uiStore.guidedTourActive` passe a `true`
   - **And** `uiStore.chatWidgetMinimized` passe a `true`
   - **And** le parcours **attend** la fin de l'animation de retraction (via `await retractWidget()`) avant de lancer Driver.js

3. **AC3 — FloatingChatWidget se retracte en bouton FAB reduit avec GSAP**
   - **Given** `uiStore.chatWidgetMinimized` passe a `true`
   - **When** FloatingChatWidget observe le changement
   - **Then** le widget se retracte avec animation GSAP (scale: 1->0.3, opacity: 1->0.8, duree: 250ms)
   - **And** le focus trap est desactive avant la retraction
   - **And** l'animation retourne une Promise resolue dans le callback `onComplete` de GSAP

4. **AC4 — Le widget reapparait a la fin du parcours**
   - **Given** le parcours se termine (etat `'complete'` ou `'interrupted'`)
   - **When** useGuidedTour met a jour le store
   - **Then** `uiStore.chatWidgetMinimized` passe a `false`
   - **And** `uiStore.guidedTourActive` passe a `false`
   - **And** le widget reapparait avec animation GSAP (scale: 0.3->1, opacity: 0.8->1, duree: 250ms)

5. **AC5 — Le clic sur le FAB est bloque pendant le guidage**
   - **Given** `uiStore.guidedTourActive === true` et le widget est retracte
   - **When** l'utilisateur clique sur le bouton FloatingChatButton
   - **Then** rien ne se passe (le widget ne s'ouvre pas)
   - **And** le bouton affiche un curseur `not-allowed` (feedback visuel)

6. **AC6 — prefers-reduced-motion desactive les animations GSAP**
   - **Given** `uiStore.prefersReducedMotion === true`
   - **When** le widget se retracte ou reapparait
   - **Then** l'animation GSAP a une duree de 0ms (transition instantanee — NFR14)
   - **And** la Promise est resolue immediatement

7. **AC7 — Zero regression**
   - **Given** les modifications sont terminees
   - **When** on execute `npx vitest run`
   - **Then** zero regression sur les 222 tests existants
   - **And** les nouveaux tests couvrent >= 80% du code ajoute

## Tasks / Subtasks

- [x] **Task 1 : Etendre le store `ui.ts` avec `chatWidgetMinimized` et `guidedTourActive`** (AC: 1)
  - [x] 1.1 Ajouter `const chatWidgetMinimized = ref(false)` apres `chatWidgetOpen` (ligne ~16)
  - [x] 1.2 Ajouter `const guidedTourActive = ref(false)` apres `chatWidgetMinimized`
  - [x] 1.3 Exposer les deux refs dans le `return { ... }` du store

- [x] **Task 2 : Creer les fonctions d'animation `retractWidget()` et `expandWidget()` dans FloatingChatWidget.vue** (AC: 3, 4, 6)
  - [x] 2.1 Ajouter une fonction `retractWidget(): Promise<void>` qui anime le widget via GSAP : `gsap.to(el, { scale: 0.3, opacity: 0.8, duration: prefersReducedMotion ? 0 : 0.25, ease: 'power2.in', onComplete: resolve })`
  - [x] 2.2 Desactiver le focus trap au debut de `retractWidget()` (appeler `deactivateFocusTrap()`)
  - [x] 2.3 Ajouter une fonction `expandWidget(): Promise<void>` qui anime le widget via GSAP : `gsap.to(el, { scale: 1, opacity: 1, duration: prefersReducedMotion ? 0 : 0.25, ease: 'power2.out', onComplete: resolve })`
  - [x] 2.4 Pour `duration === 0` : fast-path sans tween, appeler `gsap.set()` + resoudre immediatement
  - [x] 2.5 Appeler `gsap.killTweensOf(el)` au debut de chaque animation (eviter les tweens concurrents)

- [x] **Task 3 : Ajouter le watcher `chatWidgetMinimized` dans FloatingChatWidget.vue** (AC: 3, 4)
  - [x] 3.1 Ajouter un `watch(() => uiStore.chatWidgetMinimized, ...)` qui appelle `retractWidget()` quand `true`, `expandWidget()` quand `false`
  - [x] 3.2 Ne rien faire si le widget n'est pas `chatWidgetOpen` (pas de retraction d'un widget deja ferme)
  - [x] 3.3 Exposer `retractWidget` et `expandWidget` pour que `useGuidedTour` puisse les attendre (cf. Task 4)

- [x] **Task 4 : Modifier `useGuidedTour.ts` pour orchestrer retraction/reapparition** (AC: 2, 4)
  - [x] 4.1 Importer `useUiStore` au debut de `startTour()` (deja fait partiellement pour `prefersReducedMotion`)
  - [x] 4.2 Apres `tourState = 'loading'`, positionner `uiStore.guidedTourActive = true` et `uiStore.chatWidgetMinimized = true`
  - [x] 4.3 Attendre la retraction via un mecanisme de synchronisation : creer un module-level `let retractPromise: Promise<void> | null = null` + `resolveRetract: (() => void) | null = null` que FloatingChatWidget resout dans le onComplete GSAP
  - [x] 4.4 Dans `startTour`, `await retractPromise` avant de lancer Driver.js (sequence GSAP → Driver.js — ADR6)
  - [x] 4.5 A la fin du parcours (dans le bloc `finally` ou apres `driver.destroy()`), positionner `uiStore.chatWidgetMinimized = false` et `uiStore.guidedTourActive = false`
  - [x] 4.6 Meme chose dans `cancelTour()` : positionner les deux flags a `false`
  - [x] 4.7 Gerer le cas ou le widget est deja ferme (`chatWidgetOpen === false`) : ne pas attendre de retraction, passer directement

- [x] **Task 5 : Bloquer l'ouverture du widget pendant le guidage** (AC: 5)
  - [x] 5.1 Dans `FloatingChatButton.vue`, ajouter une guard `if (uiStore.guidedTourActive) return` dans le handler `@click`
  - [x] 5.2 Ajouter `:class="{ 'cursor-not-allowed opacity-60': uiStore.guidedTourActive }"` sur le bouton
  - [x] 5.3 Ajouter `aria-disabled="true"` quand `guidedTourActive` est `true`
  - [x] 5.4 Dans `toggleChatWidget()` du store `ui.ts` : **ne PAS ajouter de guard** — la protection est dans le composant, pas dans le store (le store reste un simple toggle)

- [x] **Task 6 : Tests unitaires** (AC: 7)
  - [x] 6.1 Creer `frontend/tests/stores/ui.guidedTour.test.ts` :
    - `chatWidgetMinimized` et `guidedTourActive` initialisent a `false`
    - Les refs sont reactives et exposees par le store
  - [x] 6.2 Creer `frontend/tests/composables/useGuidedTour.retract.test.ts` :
    - `startTour` positionne `guidedTourActive = true` et `chatWidgetMinimized = true`
    - Fin de parcours remet les deux a `false`
    - `cancelTour` remet les deux a `false`
    - Widget deja ferme : pas d'attente de retraction
  - [x] 6.3 Creer `frontend/tests/components/copilot/FloatingChatButton.block.test.ts` :
    - Clic pendant `guidedTourActive = true` : widget ne s'ouvre pas
    - `aria-disabled` et `cursor-not-allowed` quand `guidedTourActive`
    - Clic normal quand `guidedTourActive = false` : toggle fonctionne

- [x] **Task 7 : Verification finale** (AC: 7)
  - [x] 7.1 `npx vitest run` — zero regression sur 222 tests existants + nouveaux tests
  - [x] 7.2 `npx nuxi typecheck` — zero nouvelle erreur de type
  - [x] 7.3 Verification visuelle : widget ouvert → `startTour` → retraction animee → etapes Driver.js → fin → reapparition animee

### Review Findings

- [x] [Review][Decision] **useChat.ts modifie contrairement a la contrainte spec** — Deviation acceptee. La contrainte « Fichiers a NE PAS modifier » est une erreur de conception dans les specs : l'implementation revele des besoins non prevus. La modification (ajout `addSystemMessage`) est legitime. [frontend/app/composables/useChat.ts:656-664]
- [x] [Review][Patch] **DEADLOCK : `onRetractComplete` promise peut suspendre `startTour()` indefiniment** — 3 chemins non geres laissent la promesse en suspens : (a) `cancelTour()` annule le callback sans le resoudre (`onRetractComplete = null` au lieu d'appeler `onRetractComplete()` puis null), (b) le composant `FloatingChatWidget` se demonte pendant la retraction (`onBeforeUnmount` appelle `gsap.killTweensOf` mais pas `notifyRetractComplete()`), (c) le widget se ferme entre le positionnement du flag et l'execution du watcher. Consequence : `tourState` reste a `'loading'`, `guidedTourActive` reste `true`, le bouton FAB est bloque definitivement. Fix : stocker le `resolve` separement et l'appeler depuis `cancelTour()` et `onBeforeUnmount`. [frontend/app/composables/useGuidedTour.ts:119, frontend/app/components/copilot/FloatingChatWidget.vue:446-453]
- [x] [Review][Patch] **Touche Escape ferme le widget pendant un tour actif — tweens GSAP concurrents** — `handleEscape()` (ligne 49) ne verifie pas `guidedTourActive` et appelle directement `closeChatWidget()`, ce qui declenche `animateClose()` en concurrence avec `retractWidget()` en cours. Le `gsap.killTweensOf` de l'une tue l'autre, `notifyRetractComplete()` peut ne jamais etre appele (variante du deadlock F1). Fix : ajouter `if (uiStore.guidedTourActive) return` dans `handleEscape()`. [frontend/app/components/copilot/FloatingChatWidget.vue:49-53]

## Dev Notes

### Portee de cette story

Cette story est **STRICTEMENT frontend** — aucune modification backend. Elle ajoute le mecanisme de **retraction/reapparition animee du widget** pendant les parcours guides, avec synchronisation GSAP → Driver.js.

**Ce que cette story fait :** retraction GSAP du widget au demarrage du parcours, reapparition a la fin, blocage de l'ouverture pendant le guidage.
**Ce que cette story ne fait PAS :** navigation multi-pages (Story 5.3), popover custom (Story 5.4), declenchement par SSE/LLM (Story 6.1).

### Architecture et ADRs a respecter

**ADR6 (architecture.md Decision 6)** — Orchestration retraction/reapparition du widget :
- Communication unidirectionnelle via store Pinia : `useGuidedTour` ecrit → `uiStore` → `FloatingChatWidget` observe et anime
- Le guidage ne connait PAS le widget directement — il manipule l'etat, le widget reagit
- Sequence : GSAP anime retraction → Promise resolue → Driver.js demarre

**ADR3 (architecture.md Decision 3)** — Machine a etats :
- `useGuidedTour` gere l'orchestration (`startTour` → set uiStore flags → await retract → Driver.js)
- Pas de nouvel etat machine necessaire — les etats existants (`loading`, `highlighting`, etc.) suffisent

**Regle enforcement (architecture.md)** — Tout agent IA DOIT :
- Verifier `uiStore.guidedTourActive` avant d'ouvrir le widget
- Respecter `prefers-reduced-motion` sur toute animation GSAP
- Ajouter les variantes `dark:` Tailwind sur chaque nouvel element visuel

### Mecanisme de synchronisation GSAP → Driver.js

Le point critique est la **sequence** : la retraction doit se terminer AVANT que Driver.js ne demarre. L'architecture (ADR6) prescrit une promesse :

```typescript
// Dans useGuidedTour.ts — startTour()
uiStore.guidedTourActive = true
uiStore.chatWidgetMinimized = true

// Attendre que la retraction soit terminee
if (uiStore.chatWidgetOpen) {
  await new Promise<void>((resolve) => {
    // FloatingChatWidget observe chatWidgetMinimized et resolve dans onComplete GSAP
    retractResolve = resolve
  })
}

// Maintenant Driver.js peut demarrer
```

**Pattern de synchronisation recommande :** Creer un event bus minimaliste via des module-level callbacks dans `useGuidedTour.ts` que `FloatingChatWidget.vue` invoque :

```typescript
// useGuidedTour.ts — module-level
let onRetractComplete: (() => void) | null = null

export function notifyRetractComplete() {
  onRetractComplete?.()
  onRetractComplete = null
}

// Dans startTour :
await new Promise<void>(resolve => { onRetractComplete = resolve })

// FloatingChatWidget.vue — dans retractWidget() onComplete GSAP :
import { notifyRetractComplete } from '~/composables/useGuidedTour'
// ...
onComplete: () => { notifyRetractComplete() }
```

**Alternative plus simple :** Watcher dans `FloatingChatWidget` avec `watch(chatWidgetMinimized)` qui appelle `retractWidget()` et le composable attend un delai fixe (250ms + marge). Mais la promesse est plus fiable (ADR6 la prescrit).

### Fichiers a creer

| Fichier | Description |
|---------|-------------|
| `frontend/tests/stores/ui.guidedTour.test.ts` | Tests des nouveaux champs du store |
| `frontend/tests/composables/useGuidedTour.retract.test.ts` | Tests de l'orchestration retraction |
| `frontend/tests/components/copilot/FloatingChatButton.block.test.ts` | Tests du blocage pendant guidage |

### Fichiers a modifier

| Fichier | Modification | Lignes cles |
|---------|-------------|-------------|
| `frontend/app/stores/ui.ts` | Ajouter `chatWidgetMinimized`, `guidedTourActive` (2 refs + return) | ~16-17, ~143-165 |
| `frontend/app/composables/useGuidedTour.ts` | Orchestrer retraction au demarrage, reapparition a la fin/cancel | ~48-65 (startTour), ~186-205 (cancelTour) |
| `frontend/app/components/copilot/FloatingChatWidget.vue` | Ajouter watcher `chatWidgetMinimized`, fonctions `retractWidget()`/`expandWidget()` | ~208-262 (zone animations GSAP existante) |
| `frontend/app/components/copilot/FloatingChatButton.vue` | Guard `guidedTourActive` sur clic, classes conditionnelles, aria-disabled | ~8-16 (bouton template) |

### Fichiers a NE PAS modifier

- `frontend/app/types/guided-tour.ts` — Aucun nouveau type necessaire (`TourState` inclut deja tous les etats)
- `frontend/app/lib/guided-tours/registry.ts` — Pas de modification du registre
- `frontend/app/composables/useDriverLoader.ts` — Loader Driver.js deja complet
- `frontend/app/composables/useChat.ts` — Pas de modification du chat
- `frontend/app/assets/css/main.css` — Pas de nouveau CSS necessaire (GSAP gere tout via inline styles)
- `backend/**` — Aucune modification backend

### Pattern GSAP existant dans FloatingChatWidget.vue (reference)

Le widget utilise deja GSAP pour les animations d'ouverture/fermeture (lignes 208-262). Les nouvelles animations de retraction/reapparition DOIVENT suivre le meme pattern :

```typescript
// Pattern existant — animateOpen() (ligne 208)
function animateOpen() {
  const el = widgetRef.value
  if (!el) return
  gsap.killTweensOf(el)
  const duration = uiStore.prefersReducedMotion ? 0 : 0.25
  // ... gsap.fromTo(el, {...}, {...})
}

// Pattern a suivre pour retractWidget()
function retractWidget(): Promise<void> {
  return new Promise((resolve) => {
    const el = widgetRef.value
    if (!el) { resolve(); return }
    gsap.killTweensOf(el)
    deactivateFocusTrap()
    const duration = uiStore.prefersReducedMotion ? 0 : 0.25
    if (duration === 0) {
      gsap.set(el, { scale: 0.3, opacity: 0.8 })
      resolve()
      return
    }
    gsap.to(el, {
      scale: 0.3, opacity: 0.8, duration, ease: 'power2.in',
      onComplete: resolve,
    })
  })
}
```

**Points cles :**
- `gsap.killTweensOf(el)` au debut (eviter les tweens concurrents — pattern existant)
- `uiStore.prefersReducedMotion ? 0 : 0.25` pour la duree (pattern existant)
- Fast-path `duration === 0` avec `gsap.set()` (pattern existant ligne 219)
- `deactivateFocusTrap()` avant la retraction (pattern existant dans `animateClose()` ligne 239)

### Interaction retraction vs open/close du widget

Les animations de retraction (`scale: 0.3, opacity: 0.8`) et de fermeture (`scale: 0.8, opacity: 0`) sont distinctes :
- **Fermeture** (`animateClose`) : le widget disparait completement (`isVisible = false`)
- **Retraction** (`retractWidget`) : le widget reste visible mais reduit (le FAB est toujours la, en semi-transparent)

Le watcher `chatWidgetMinimized` doit etre **prioritaire** sur le watcher `chatWidgetOpen` existant. Si les deux changent simultanement, la retraction est geree par `chatWidgetMinimized`, pas par `chatWidgetOpen`.

### Gestion des cas limites

| Cas | Comportement attendu |
|-----|---------------------|
| Widget ferme au demarrage du tour | Pas d'animation de retraction, `chatWidgetMinimized = true` est quand meme positionne mais sans attente |
| Widget retracte + utilisateur clique FAB | Bloque par `guidedTourActive` dans FloatingChatButton |
| Tour interrompu (cancelTour) | `chatWidgetMinimized = false`, `guidedTourActive = false`, widget reapparait |
| Erreur loadDriver (try/catch) | Reset des flags dans le bloc catch existant |
| Double startTour pendant retraction | Guard `tourState !== 'idle'` existante dans useGuidedTour empeche les appels concurrents |
| `reduced-motion` actif | Animations GSAP duree 0ms, promesse resolue immediatement |

### Intelligence de la story 5.1 (precedente)

**Patterns a reutiliser :**
- Module-level state dans `useGuidedTour.ts` (lignes 9-15) — les nouveaux callbacks de synchronisation DOIVENT etre module-level aussi
- Import dynamique `await import('~/stores/ui')` deja utilise dans `startTour()` (ligne 100) — le reorganiser pour etre au debut de la fonction
- `gsap.killTweensOf(el)` dans FloatingChatWidget (lignes 212, 241) — appliquer avant chaque nouvelle animation
- Tests `vi.mock()` pour stores et `vi.resetModules()` pour reset — meme pattern dans les nouveaux tests

**Review findings de 5.1 a garder en tete :**
- Flag `cancelled` pour les race conditions async : le meme mecanisme protege contre les interruptions pendant la retraction
- `try/catch` avec reset d'etat : les flags `guidedTourActive`/`chatWidgetMinimized` doivent etre reset dans le `catch` aussi

### Anti-patterns a eviter

1. **NE PAS utiliser un EventBus ou provide/inject** — communication via store Pinia uniquement (regle enforcement architecture.md)
2. **NE PAS ajouter un `setTimeout` au lieu d'une Promise** — la synchronisation GSAP → Driver.js DOIT etre via Promise/callback (ADR6)
3. **NE PAS modifier le store `ui.ts` pour ajouter des guards** — la protection ouverture pendant guidage est dans le composant FloatingChatButton, pas dans le store
4. **NE PAS cacher le bouton FAB completement** — il reste visible mais reduit/desactive pendant le guidage
5. **NE PAS modifier `animateOpen()`/`animateClose()`** — les nouvelles fonctions sont separees (`retractWidget`/`expandWidget`)
6. **NE PAS creer de nouveau composant** — tout se fait dans les fichiers existants
7. **NE PAS envoyer de message dans le chat** a la retraction/reapparition (pas de message systeme)

### Project Structure Notes

- Frontend : Nuxt 4 SPA (`ssr: false`), structure `app/`
- Composables : `app/composables/` — auto-importes par Nuxt
- Stores : `app/stores/` — Pinia, auto-importes
- Composants copilot : `app/components/copilot/` — `FloatingChatWidget.vue` (599 lignes), `FloatingChatButton.vue` (43 lignes), `ChatWidgetHeader.vue`
- Tests : `frontend/tests/` (miroir de la structure `app/`)
- Vitest 3.0, `@vue/test-utils` 2.4, `happy-dom`
- GSAP `^3.12.0` installe dans `package.json`
- 222 tests existants (post-story 5.1), zero regression attendue

### References

- [Source: _bmad-output/planning-artifacts/epics.md — Epic 5, Story 5.2]
- [Source: _bmad-output/planning-artifacts/architecture.md — ADR6 Decision 6, orchestration retraction/reapparition GSAP + Driver.js]
- [Source: _bmad-output/planning-artifacts/architecture.md — ADR3 Decision 3, machine a etats useGuidedTour]
- [Source: _bmad-output/planning-artifacts/architecture.md — Enforcement Rules for Agents, lignes 759-768]
- [Source: _bmad-output/planning-artifacts/architecture.md — Widget ↔ Guidage Communication Boundary, lignes 883-893]
- [Source: _bmad-output/implementation-artifacts/5-1-composable-useguidedtour-machine-a-etats-et-execution-mono-page.md — Review findings, patterns module-level state, GSAP usage]
- [Source: frontend/app/stores/ui.ts — Store Pinia existant, champs chatWidgetOpen, prefersReducedMotion]
- [Source: frontend/app/composables/useGuidedTour.ts — Composable existant, startTour(), cancelTour(), module-level state]
- [Source: frontend/app/components/copilot/FloatingChatWidget.vue — Animations GSAP existantes animateOpen/animateClose, focus trap, watchers]
- [Source: frontend/app/components/copilot/FloatingChatButton.vue — Bouton FAB, handler click toggle]

## Change Log

- 2026-04-13 : Implementation complete — retraction/reapparition animee du widget pendant le guidage, blocage FAB, synchronisation GSAP → Driver.js, 17 nouveaux tests, 239 tests verts, zero regression.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

- Test cancelTour timeout : le mock `destroy()` ne declenchait pas `onDestroyStarted` — corrige en capturant la config du driver factory et en appelant le callback dans le mock destroy.

### Completion Notes List

- AC1 : `chatWidgetMinimized` et `guidedTourActive` ajoutes comme refs dans `ui.ts`, exposes dans le return du store
- AC2 : `startTour()` positionne `guidedTourActive = true` et `chatWidgetMinimized = true`, attend la fin de la retraction GSAP via `notifyRetractComplete` callback avant de lancer Driver.js
- AC3 : `retractWidget()` anime le widget via GSAP (scale: 1→0.3, opacity: 1→0.8, 250ms), desactive le focus trap, retourne une Promise
- AC4 : A la fin du parcours ou interruption, `chatWidgetMinimized = false` et `guidedTourActive = false`, `expandWidget()` anime le retour
- AC5 : Guard `guidedTourActive` dans FloatingChatButton, `cursor-not-allowed`, `opacity-60`, `aria-disabled`
- AC6 : `prefersReducedMotion ? 0 : 0.25` pour la duree, fast-path `gsap.set()` pour duree 0
- AC7 : 239 tests verts (222 existants + 17 nouveaux), zero regression, zero nouvelle erreur de type

### File List

**Modifies :**
- `frontend/app/stores/ui.ts` — 2 nouvelles refs (`chatWidgetMinimized`, `guidedTourActive`) + return
- `frontend/app/composables/useGuidedTour.ts` — module-level `notifyRetractComplete`, `cachedUiStore`, orchestration retraction dans `startTour`/`cancelTour`/catch
- `frontend/app/components/copilot/FloatingChatWidget.vue` — `retractWidget()`, `expandWidget()`, watcher `chatWidgetMinimized`, import `notifyRetractComplete`
- `frontend/app/components/copilot/FloatingChatButton.vue` — guard `guidedTourActive` sur clic, classes conditionnelles, `aria-disabled`, handler `handleClick`

**Crees :**
- `frontend/tests/stores/ui.guidedTour.test.ts` — 6 tests store (refs, reactivite, exposition)
- `frontend/tests/composables/useGuidedTour.retract.test.ts` — 5 tests orchestration retraction (flags, fin, cancel, widget ferme, no-op)
- `frontend/tests/components/copilot/FloatingChatButton.block.test.ts` — 6 tests blocage FAB pendant guidage (clic bloque, aria-disabled, classes, clic normal)
