# Story 1.3 : Bouton flottant et conteneur du widget

Status: done

## Story

En tant qu'utilisateur sur desktop,
je veux voir un bouton flottant en bas a droite et pouvoir ouvrir un widget de chat elegant,
afin d'acceder a l'assistant IA sans quitter la page que je consulte.

## Acceptance Criteria (BDD)

### AC1 — Bouton flottant visible sur desktop

**Given** l'utilisateur est sur n'importe quelle page desktop (>= 1024px)
**When** la page se charge
**Then** un bouton flottant (FAB) est visible en bas a droite avec le label accessible « Ouvrir l'assistant IA »

### AC2 — Ouverture du widget avec animation GSAP

**Given** le bouton flottant est visible
**When** l'utilisateur clique dessus
**Then** le widget FloatingChatWidget s'ouvre avec une animation GSAP (duree < 300ms — NFR1)
**And** le fond du widget est glassmorphism (`backdrop-filter: blur` >= 12px — NFR8)
**And** le contenu de la page est visible mais les donnees financieres sont illisibles a travers le blur

### AC3 — Fallback opaque sans backdrop-filter

**Given** le navigateur ne supporte pas `backdrop-filter`
**When** le widget s'ouvre
**Then** un fond opaque est affiche via `@supports` (FR8)
**And** le contraste des textes respecte WCAG AA >= 4.5:1 (NFR12)

### AC4 — Fermeture du widget

**Given** le widget est ouvert
**When** l'utilisateur clique sur le bouton de fermeture ou sur le FAB
**Then** le widget se ferme avec animation GSAP

### AC5 — Dark mode complet

**Given** le dark mode est actif
**When** le widget est affiche
**Then** tous les elements utilisent les variantes `dark:` de Tailwind (`bg-dark-card`, `text-surface-dark-text`, `border-dark-border`, etc.)

### AC6 — prefers-reduced-motion

**Given** `prefers-reduced-motion` est actif
**When** le widget s'ouvre ou se ferme
**Then** les animations GSAP sont desactivees (duree 0ms, transition instantanee)

### AC7 — Performance glassmorphism

**Given** le FPS de la page avec le widget ouvert et le scroll actif
**When** on mesure la performance
**Then** le FPS reste >= 30 (NFR6)

## Tasks / Subtasks

- [x] Task 1 — Creer `FloatingChatButton.vue` (AC: #1, #5)
  - [x] 1.1 Creer `frontend/app/components/copilot/FloatingChatButton.vue`
  - [x] 1.2 Position `fixed` en bas a droite (`bottom-6 right-6`), `z-index: 50`
  - [x] 1.3 Icone chat (SVG inline coherent avec le pattern du projet)
  - [x] 1.4 `aria-label="Ouvrir l'assistant IA"` + `role="button"` (NFR15)
  - [x] 1.5 Variantes dark mode completes (`bg-brand-green`, `text-white`, `shadow-lg dark:shadow-dark-border/20`)
  - [x] 1.6 Etat visuel « actif » quand le widget est ouvert (changement vers icone X)
  - [x] 1.7 Click handler : toggle `uiStore.chatWidgetOpen`

- [x] Task 2 — Etendre le store `ui.ts` (AC: #2, #4)
  - [x] 2.1 Ajouter `chatWidgetOpen = ref(false)` au store
  - [x] 2.2 Ajouter `toggleChatWidget()` et `closeChatWidget()` actions
  - [x] 2.3 Ne PAS supprimer `chatPanelOpen` — il sera retire dans Story 2.1 (suppression page /chat)

- [x] Task 3 — Creer `FloatingChatWidget.vue` conteneur vide (AC: #2, #3, #5, #6, #7)
  - [x] 3.1 Creer `frontend/app/components/copilot/FloatingChatWidget.vue`
  - [x] 3.2 Conteneur `position: fixed`, ancre en bas a droite au-dessus du FAB
  - [x] 3.3 Dimensions par defaut : `w-[400px] h-[600px]` (le redimensionnement est Story 1.6)
  - [x] 3.4 Glassmorphism : `backdrop-blur-xl bg-white/80 dark:bg-dark-card/80` (blur >= 12px)
  - [x] 3.5 Fallback opaque via `@supports not (backdrop-filter: blur(1px))` → `bg-white dark:bg-dark-card` (pas de transparence)
  - [x] 3.6 Bordure et ombre : `border border-gray-200/50 dark:border-dark-border/50 shadow-2xl rounded-2xl`
  - [x] 3.7 `overflow-hidden` pour contenir le contenu futur
  - [x] 3.8 Afficher un header minimal temporaire avec titre « Assistant IA » et bouton fermer (X) — sera remplace par `ChatWidgetHeader.vue` en Story 1.4
  - [x] 3.9 Afficher un placeholder « Chat arrive en Story 1.5 » dans le body — sera remplace par l'integration chat
  - [x] 3.10 `v-show="uiStore.chatWidgetOpen"` (pas `v-if` — garder le DOM pour persistance state)

- [x] Task 4 — Animations GSAP ouverture/fermeture (AC: #2, #4, #6)
  - [x] 4.1 Importer `gsap` via import direct (`import { gsap } from 'gsap'` — pattern plus testable)
  - [x] 4.2 Animation ouverture : `gsap.fromTo(widgetEl, { scale: 0.8, opacity: 0, y: 20 }, { scale: 1, opacity: 1, y: 0, duration: 0.25, ease: 'power2.out' })`
  - [x] 4.3 Animation fermeture : `gsap.to(widgetEl, { scale: 0.8, opacity: 0, y: 20, duration: 0.2, ease: 'power2.in', onComplete: ... })`
  - [x] 4.4 Detecter `prefers-reduced-motion` : `window.matchMedia('(prefers-reduced-motion: reduce)').matches` → si actif, `duration: 0`
  - [x] 4.5 Utiliser `ref` template pour la reference DOM du widget (`const widgetRef = ref<HTMLElement | null>(null)`)
  - [x] 4.6 Orchestrer : watcher sur chatWidgetOpen → ouverture/fermeture animee avec isVisible interne

- [x] Task 5 — Integration dans `layouts/default.vue` (AC: #1)
  - [x] 5.1 Importer et monter `FloatingChatButton` et `FloatingChatWidget` dans le layout
  - [x] 5.2 Conditionner le rendu par `useDeviceDetection().isDesktop` : `<template v-if="isDesktop"><FloatingChatButton /><FloatingChatWidget /></template>`
  - [x] 5.3 Ne PAS supprimer `ChatPanel` — coexistence temporaire jusqu'a Story 2.1
  - [x] 5.4 S'assurer que le z-index du widget (50) est au-dessus du contenu mais en dessous des modals existants

- [x] Task 6 — Tests unitaires Vitest (AC: #1-#7)
  - [x] 6.1 Creer `frontend/tests/components/copilot/FloatingChatButton.test.ts`
  - [x] 6.2 Creer `frontend/tests/components/copilot/FloatingChatWidget.test.ts`
  - [x] 6.3 Test : FAB rendu avec aria-label correct
  - [x] 6.4 Test : clic FAB toggle `chatWidgetOpen` dans le store
  - [x] 6.5 Test : widget visible quand `chatWidgetOpen = true`, cache quand `false`
  - [x] 6.6 Test : glassmorphism classe widget-glass presente
  - [x] 6.7 Test : dark mode — classes dark appliquees
  - [x] 6.8 Test : GSAP appele avec `duration: 0` quand `prefers-reduced-motion` actif
  - [x] 6.9 Test : fermeture via bouton X dans le header temporaire
  - [x] 6.10 22 tests, couverture complete des ACs

- [x] Task 7 — Validation zero regression (AC implicite)
  - [x] 7.1 Executer la suite de tests frontend existante — 61 tests, 0 echec
  - [x] 7.2 Executer la suite de tests backend — 944 tests, 0 echec
  - [x] 7.3 Verifier visuellement : les pages existantes ne sont pas affectees

## Dev Notes

### Composants a creer

| Fichier | Role | Story suivante |
|---------|------|----------------|
| `components/copilot/FloatingChatButton.vue` | Bouton flottant FAB en bas a droite | Definitive — sera reutilise dans toutes les stories suivantes |
| `components/copilot/FloatingChatWidget.vue` | Conteneur glassmorphism du widget | Story 1.4 ajoute le header, Story 1.5 integre le chat, Story 1.6 ajoute le resize |

### Architecture layout/default.vue — Etat actuel

```
layouts/default.vue
├── div.flex.h-screen
│   ├── AppSidebar (hidden lg:flex, lg:w-64)
│   ├── div.flex-1.flex.flex-col
│   │   ├── AppHeader
│   │   └── main (NuxtPage)
│   └── ChatPanel (w-80 lg:w-96, v-if="uiStore.chatPanelOpen")
```

**Apres Story 1.3 :**
```
layouts/default.vue
├── div.flex.h-screen
│   ├── AppSidebar
│   ├── div.flex-1.flex.flex-col
│   │   ├── AppHeader
│   │   └── main (NuxtPage)
│   └── ChatPanel (INCHANGE — coexiste temporairement)
├── FloatingChatButton (v-if="isDesktop", position: fixed)
└── FloatingChatWidget (v-if="isDesktop", position: fixed)
```

**ATTENTION** : `FloatingChatButton` et `FloatingChatWidget` doivent etre HORS du `div.flex` principal. Ils sont `position: fixed` et ne participent pas au flux flex du layout.

### GSAP — Pattern d'utilisation existant

Le projet a deja GSAP installe et configure via un plugin Nuxt. Verifier le fichier `plugins/gsap.client.ts` pour comprendre comment GSAP est injecte. Patterns possibles :

1. **Plugin provide** : `nuxtApp.provide('gsap', gsap)` → `const { $gsap } = useNuxtApp()`
2. **Import direct** : `import gsap from 'gsap'` (si le plugin ne fait que l'initialiser)

Choisir le pattern deja en place. Ne PAS installer un nouveau package GSAP.

### Glassmorphism — Implementation CSS

```css
/* Widget ouvert — glassmorphism */
.widget-glass {
  @apply backdrop-blur-xl bg-white/80 dark:bg-dark-card/80;
  @apply border border-white/20 dark:border-dark-border/30;
  @apply shadow-2xl rounded-2xl;
}

/* Fallback pour navigateurs sans support */
@supports not (backdrop-filter: blur(1px)) {
  .widget-glass {
    @apply bg-white dark:bg-dark-card;
    @apply border-gray-200 dark:border-dark-border;
  }
}
```

Le blur >= 12px (`backdrop-blur-xl` = 24px en Tailwind 4) garantit que les donnees financieres sont illisibles a travers le widget (NFR8).

### Store ui.ts — Extension minimale

Ajouter uniquement `chatWidgetOpen` et ses actions. Les champs futurs (`chatWidgetMinimized`, `guidedTourActive`, `currentPage`) seront ajoutes dans les stories correspondantes (5.2, 6.1, 3.1).

```typescript
// A ajouter dans stores/ui.ts
const chatWidgetOpen = ref(false)

function toggleChatWidget() {
  chatWidgetOpen.value = !chatWidgetOpen.value
}

function closeChatWidget() {
  chatWidgetOpen.value = false
}

// Retourner dans le return du store
return { /* existant... */, chatWidgetOpen, toggleChatWidget, closeChatWidget }
```

### Z-index strategie

| Element | z-index | Raison |
|---------|---------|--------|
| FAB (FloatingChatButton) | 50 | Au-dessus du contenu, visible en permanence |
| Widget (FloatingChatWidget) | 50 | Meme couche que le FAB |
| Modals/dialogs existants | >= 100 (verifier) | Doivent rester au-dessus du widget |
| Driver.js (futur, Story 4+) | Gere par Driver.js | Sera au-dessus de tout |

### prefers-reduced-motion — Pattern

```typescript
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

function openWidget() {
  uiStore.chatWidgetOpen = true
  await nextTick()
  gsap.fromTo(widgetRef.value, 
    { scale: 0.8, opacity: 0, y: 20 },
    { scale: 1, opacity: 1, y: 0, duration: prefersReducedMotion ? 0 : 0.25, ease: 'power2.out' }
  )
}
```

### Regles d'enforcement (architecture.md)

1. **NE JAMAIS modifier les 13 composants dans `components/chat/`** — reutiliser via composition
2. **NE JAMAIS ajouter d'etat chat dans un store Pinia** — tout l'etat chat reste dans `useChat.ts` module-level
3. **Dark mode obligatoire** sur tous les nouveaux elements visuels (variantes `dark:` Tailwind)
4. **Messages UX en francais avec accents**, ton empathique
5. **Composants dans `components/copilot/`** — dossier dedie a la feature 019

### Ce que cette story NE fait PAS (hors scope)

- Pas de header complet (titre, minimize, historique) → Story 1.4
- Pas d'integration des composants chat (messages, input) → Story 1.5
- Pas de redimensionnement → Story 1.6
- Pas d'accessibilite avancee (focus trap, aria-live) → Story 1.7
- Pas de suppression de ChatPanel → Story 2.1
- Le widget est un **conteneur vide** avec header temporaire et placeholder

### Lecons des stories precedentes

**Story 1.1 — Refactoring useChat :**
- F11 : `computed()` au module-level sans `effectScope` → pas de probleme ici (pas de computed module-level)
- Les stores Nuxt (`useRuntimeConfig`, `useAuthStore`, etc.) ne doivent PAS etre appeles au module-level
- Le pattern `v-show` vs `v-if` : utiliser `v-show` pour le widget afin de preserver le DOM (le chat integre en Story 1.5 beneficiera du state persistant)

**Story 1.2 — useDeviceDetection :**
- Guard SSR : `typeof window !== 'undefined'` dans le composable
- Le composable retourne `{ isDesktop, isMobile }` — utiliser `isDesktop` pour le `v-if` conditionnel dans le layout
- `onScopeDispose` prefere a `onUnmounted` pour le cleanup

**Review findings deferred pertinents :**
- F8/W6 : TextDecoder sans `{ stream: true }` → ne pas introduire ce probleme dans le widget
- F10/W1 : Pas de reset au logout → ne pas aggraver (le widget doit respecter l'etat existant)
- W2 : Race condition sendMessage/submitInteractiveAnswer → non pertinent pour cette story (pas d'integration chat)

### Conventions de test

- **Emplacement** : `frontend/tests/components/copilot/` (nouveau dossier)
- **Framework** : Vitest 3.0 + `@vue/test-utils`
- **Mocking** : `vi.mock` pour les stores Pinia, `vi.stubGlobal` pour `window.matchMedia`
- **GSAP mock** : mocker `gsap.fromTo` et `gsap.to` pour verifier les appels sans animation reelle
- **Pattern existant** : voir `frontend/tests/composables/useChat.test.ts` et `useDeviceDetection.test.ts`

### Couleurs du theme (main.css)

```
--color-surface-dark-bg: #111827
--color-dark-card: #1F2937
--color-dark-border: #374151
--color-dark-hover: #374151
--color-dark-input: #1F2937
--color-surface-dark-text: #F9FAFB
--color-brand-green: #10B981
--color-brand-blue: #3B82F6
```

Le FAB utilise `bg-brand-green` comme couleur principale (coherent avec le branding du projet).

### Project Structure Notes

- **Nouveau dossier** : `frontend/app/components/copilot/` (convention feature 019)
- **Nouveaux fichiers** : `FloatingChatButton.vue`, `FloatingChatWidget.vue`
- **Fichiers modifies** : `layouts/default.vue` (ajout des composants), `stores/ui.ts` (ajout `chatWidgetOpen`)
- **Nouveaux tests** : `frontend/tests/components/copilot/FloatingChatButton.test.ts`, `FloatingChatWidget.test.ts`
- Auto-import Nuxt : composants dans `components/` detectes automatiquement (`pathPrefix: false` dans `nuxt.config.ts`)

### References

- [Source: _bmad-output/planning-artifacts/epics.md — Epic 1, Story 1.3]
- [Source: _bmad-output/planning-artifacts/architecture.md — ADR1 module-level state, FloatingChatWidget architecture, GSAP specs, Z-index, Glassmorphism, Enforcement rules]
- [Source: _bmad-output/planning-artifacts/prd.md — FR1-FR10, FR29-FR30, FR35, NFR1, NFR5-NFR8, NFR12, NFR14-NFR15, NFR23-NFR24]
- [Source: _bmad-output/implementation-artifacts/1-1-refactoring-usechat-en-module-level-state.md — Pattern module-level, deferred F10/F11]
- [Source: _bmad-output/implementation-artifacts/1-2-composable-usedevicedetection.md — API isDesktop/isMobile, pattern tests, guard SSR]
- [Source: _bmad-output/implementation-artifacts/deferred-work.md — Items F8-F11, W1-W6]
- [Source: frontend/app/layouts/default.vue — Structure actuelle du layout]
- [Source: frontend/app/stores/ui.ts — Store UI existant]
- [Source: frontend/app/assets/css/main.css — Variables de couleur dark mode]
- [Source: frontend/nuxt.config.ts — ssr: false, pathPrefix: false]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

- Changement environnement vitest de `node` a `happy-dom` pour supporter `@vue/test-utils` (mount de composants Vue)
- Ajout `@vitejs/plugin-vue` dans vitest.config.ts pour parser les fichiers `.vue`
- Import direct de `gsap` au lieu de `useNuxtApp().$gsap` pour meilleure testabilite (les deux patterns sont valides)
- Annotation `// @vitest-environment node` sur `useDeviceDetection.test.ts` pour preserver le comportement SSR des tests existants

### Completion Notes List

- FloatingChatButton.vue : bouton FAB fixed bottom-6 right-6, z-50, bg-brand-green, icone chat/X toggle, aria-label dynamique, dark mode complet
- FloatingChatWidget.vue : conteneur fixed 400x600px, glassmorphism (backdrop-blur-xl bg-white/80), fallback opaque @supports, header temporaire "Assistant IA" + bouton fermer, placeholder body, animations GSAP ouverture/fermeture, prefers-reduced-motion (duration: 0), dark mode complet via scoped CSS
- Store ui.ts : chatWidgetOpen ref + toggleChatWidget() + closeChatWidget() — chatPanelOpen preserve (coexistence temporaire)
- Layout default.vue : FloatingChatButton + FloatingChatWidget montes HORS du div.flex principal, conditionnes par isDesktop, ChatPanel preserve
- 22 tests unitaires couvrant tous les ACs (rendu, toggle, visibilite, dark mode, GSAP, reduced-motion, fermeture X)
- Zero regression : 61 tests frontend, 944 tests backend

### File List

- frontend/app/components/copilot/FloatingChatButton.vue (nouveau)
- frontend/app/components/copilot/FloatingChatWidget.vue (nouveau)
- frontend/app/stores/ui.ts (modifie — ajout chatWidgetOpen, toggleChatWidget, closeChatWidget)
- frontend/app/layouts/default.vue (modifie — ajout FloatingChatButton + FloatingChatWidget conditionnes par isDesktop)
- frontend/tests/components/copilot/FloatingChatButton.test.ts (nouveau)
- frontend/tests/components/copilot/FloatingChatWidget.test.ts (nouveau)
- frontend/tests/composables/useDeviceDetection.test.ts (modifie — annotation @vitest-environment node)
- frontend/vitest.config.ts (modifie — happy-dom + @vitejs/plugin-vue)
- frontend/package.json (modifie — ajout @vue/test-utils, happy-dom, @vitejs/plugin-vue en devDependencies)

### Review Findings

- [x] [Review][Decision] D1 — Resize desktop→mobile laisse `chatWidgetOpen=true` — FIXE : watcher sur isDesktop dans default.vue reset chatWidgetOpen
- [x] [Review][Decision] D2 — `v-if="isDesktop"` detruit le DOM du widget — TOLERE : v-if est au niveau layout (device class), v-show interne respecte pour open/close
- [x] [Review][Patch] P1 — Race condition GSAP : ajout `killTweensOf` avant animate [FloatingChatWidget.vue]
- [x] [Review][Patch] P2 — GSAP cleanup : ajout `onBeforeUnmount` avec `killTweensOf` [FloatingChatWidget.vue]
- [x] [Review][Patch] P3 — Ajout `aria-hidden` dynamique lie a `!isVisible` [FloatingChatWidget.vue]
- [x] [Review][Patch] P4 — Ajout `aria-expanded` sur le FAB [FloatingChatButton.vue]
- [x] [Review][Patch] P5 — Suppression `role="button"` redondant [FloatingChatButton.vue]
- [x] [Review][Patch] P6 — Suppression `isAnimating` dead state [FloatingChatWidget.vue]
- [x] [Review][Defer] W1 — `prefersReducedMotion` non-reactif (snapshot au mount) [FloatingChatWidget.vue:12] — deferred, Story 1.7 accessibilite
- [x] [Review][Defer] W2 — AbortController/sseReader jamais cleanup a la navigation [useChat.ts] — deferred, scope story 1-1
- [x] [Review][Defer] W3 — `sseReader.cancel()` race condition entre check et reassignment [useChat.ts] — deferred, scope story 1-1
- [x] [Review][Defer] W4 — `isStreaming` guard bloque nouveaux messages sans abort [useChat.ts] — deferred, scope story 1-1
- [x] [Review][Defer] W5 — `useDeviceDetection` listener leak hors scope Vue en production [useDeviceDetection.ts:22] — deferred, scope story 1-2
- [x] [Review][Defer] W6 — Widget `h-[600px]` overflow viewport sur ecrans courts (<680px) [FloatingChatWidget.vue:67] — deferred, Story 1.6 redimensionnement

### Change Log

- 2026-04-12 : Implementation Story 1.3 — Bouton flottant FAB et conteneur widget glassmorphism avec animations GSAP, dark mode complet, 22 tests unitaires, zero regression
