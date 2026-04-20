# Story 1.6 : Redimensionnement du widget

Status: done

## Story

En tant qu'utilisateur,
je veux pouvoir redimensionner le widget de chat en tirant ses bords ou coins,
afin d'adapter sa taille au contenu consulte (tableaux, graphiques, conversations longues).

## Acceptance Criteria (BDD)

### AC1 — Redimensionnement par drag des bords/coins

**Given** le widget est ouvert
**When** l'utilisateur appuie (pointerdown) sur un bord ou un coin du widget puis deplace le curseur
**Then** le widget se redimensionne en suivant le curseur en temps reel
**And** la taille respecte les limites min (300x400) et max (window.innerWidth - 100, window.innerHeight - 100)

### AC2 — Persistance localStorage

**Given** l'utilisateur a redimensionne le widget a 500x700
**When** il ferme puis rouvre le widget
**Then** la taille restauree est 500x700

### AC3 — Preservation cross-routes

**Given** l'utilisateur a redimensionne le widget
**When** il navigue vers une autre page
**Then** la taille du widget est preservee (meme session, pas de rechargement)

### AC4 — prefers-reduced-motion

**Given** l'utilisateur a active `prefers-reduced-motion`
**When** il redimensionne le widget
**Then** le redimensionnement fonctionne sans transition CSS (pas de `transition` sur width/height)

### AC5 — Overhead memoire

**Given** le widget est monte dans le layout
**When** on mesure la memoire consommee
**Then** l'overhead total du widget (incluant le resize) est < 5 MB (NFR5)

### AC6 — Viewport court (deferred W6)

**Given** le widget est ouvert sur un ecran de hauteur < 680px
**When** le widget s'affiche
**Then** la hauteur est clampee au max (window.innerHeight - 100) au lieu de deborder

### AC7 — Double-clic pour reset

**Given** l'utilisateur a redimensionne le widget
**When** il double-clique sur une poignee de redimensionnement
**Then** la taille revient aux dimensions par defaut (400x600)

## Tasks / Subtasks

- [x] Task 1 — Extension du store ui.ts (AC: 2, 3)
  - [x] 1.1 Ajouter `chatWidgetWidth: ref(400)` et `chatWidgetHeight: ref(600)` au store
  - [x] 1.2 Ajouter `setChatWidgetSize(width: number, height: number)` qui persiste dans localStorage (cle `esg_mefali_widget_size`)
  - [x] 1.3 Ajouter `resetChatWidgetSize()` qui remet 400x600 et supprime la cle localStorage
  - [x] 1.4 Charger la taille sauvegardee dans `initWidgetSize()` dedie, appele dans `onMounted` du widget

- [x] Task 2 — Logique de resize dans FloatingChatWidget.vue (AC: 1, 4, 6)
  - [x] 2.1 Remplacer les classes Tailwind fixes `w-[400px] h-[600px]` par des `:style="widgetStyle"` lies au store via computed
  - [x] 2.2 Ajouter 4 zones de poignee invisibles (bord gauche, bord superieur, coin sup-gauche, coin sup-droit) avec curseurs CSS adequats
  - [x] 2.3 Implementer les handlers `startResize` / `onPointerMove` (via `document`) / `onPointerUp` avec `setPointerCapture` pour un drag fluide
  - [x] 2.4 Calculer les nouvelles dimensions en respectant les limites : `clamp(300, newWidth, window.innerWidth - 100)` et `clamp(400, newHeight, window.innerHeight - 100)`
  - [x] 2.5 Le widget est ancre en `bottom-right` : le redimensionnement par le bord gauche et le coin superieur-gauche augmente la largeur vers la gauche (approche simplifiee V1 avec right/bottom fixes)
  - [x] 2.6 Au `pointerup`, appeler `uiStore.setChatWidgetSize(width, height)` pour persister
  - [x] 2.7 Ajouter un handler `dblclick` sur les poignees pour `uiStore.resetChatWidgetSize()` (AC7)

- [x] Task 3 — Gestion du viewport (AC: 6)
  - [x] 3.1 Ajouter un `window.resize` listener pour reclamper si le viewport shrink en dessous de la taille actuelle du widget
  - [x] 3.2 Cleanup du listener dans `onBeforeUnmount`

- [x] Task 4 — Suppression de la transition pendant le resize (AC: 4)
  - [x] 4.1 Pendant le drag actif, `isResizing` active `select-none` et retire `overflow-hidden` du root pour eviter les clippings; la zone messages passe en `overflow-hidden` pour empecher le scroll
  - [x] 4.2 Aucune transition CSS sur width/height n'est ajoutee; `prefers-reduced-motion` n'a pas d'impact car pas de transition de taille

- [x] Task 5 — Tests unitaires Vitest (AC: tous)
  - [x] 5.1 Tester le store : `setChatWidgetSize` persiste dans localStorage, `resetChatWidgetSize` restaure les defauts
  - [x] 5.2 Tester le store : chargement initial depuis localStorage au demarrage (+ edge cases JSON invalide, objet incomplet)
  - [x] 5.3 Tester le composant : les dimensions du widget refletent le store
  - [x] 5.4 Tester le composant : les poignees de resize sont presentes dans le DOM
  - [x] 5.5 Tester le composant : un pointerdown + pointermove + pointerup modifie les dimensions
  - [x] 5.6 Tester le composant : les dimensions sont clampees aux min/max
  - [x] 5.7 Tester le composant : double-clic reset aux defauts
  - [x] 5.8 Mettre a jour le test existant qui assertait `w-[400px]` et `h-[600px]` → verifie maintenant `element.style.width/height`
  - [x] 5.9 Couverture >= 80% — 112/112 tests passent, zero regression

### Review Findings

- [x] [Review][Patch] F1 — Documenter le pattern deferred-save (mutation directe pendant drag, persistance au pointerup) [FloatingChatWidget.vue:132-133]
- [x] [Review][Patch] F2 — Extraire constantes partagees WIDGET_DEFAULT_WIDTH/HEIGHT entre store et composant [ui.ts:90-91, FloatingChatWidget.vue:12-13]
- [x] [Review][Patch] F3 — Ajouter validation d'entree dans setChatWidgetSize (negatif, zero, NaN) et initWidgetSize [ui.ts:85-89]
- [x] [Review][Patch] F4 — Guard isVisible dans startResize pour eviter race condition avec GSAP close animation [FloatingChatWidget.vue:87-104]
- [x] [Review][Patch] F5 — Ajouter try/catch autour de setPointerCapture pour eviter fuite de listeners [FloatingChatWidget.vue:90]
- [x] [Review][Patch] F6 — Persister la taille corrigee dans localStorage apres clampToViewport [FloatingChatWidget.vue:160-168]
- [x] [Review][Patch] F7 — Gerer le cas viewport < WIDGET_MIN_WIDTH + WIDGET_MARGIN dans clampWidth/clampHeight [FloatingChatWidget.vue:77-80]
- [x] [Review][Patch] F8 — releasePointerCapture sur l'element original (stocker la ref du handle) [FloatingChatWidget.vue:139-141]
- [x] [Review][Patch] F9 — Ajouter test AC4 assertant l'absence de CSS transition sur width/height [Tests]
- [x] [Review][Defer] D1 — prefersReducedMotion statique, ne reagit pas aux changements OS — deferred, Story 1.7 accessibilite
- [x] [Review][Defer] D2 — Focus non retourne au bouton declencheur a la fermeture — deferred, Story 1.7 accessibilite
- [x] [Review][Defer] D3 — Resize concurrent + window resize cause saut visuel — deferred, edge case rare
- [x] [Review][Defer] D4 — Double mecanisme import.meta.client (plugin Vite + setup.ts) — deferred, pre-existant

## Dev Notes

### Architecture et contraintes

- **Fichiers a modifier :**
  - `frontend/app/stores/ui.ts` — ajouter `chatWidgetWidth`, `chatWidgetHeight`, `setChatWidgetSize`, `resetChatWidgetSize`
  - `frontend/app/components/copilot/FloatingChatWidget.vue` — remplacer dimensions fixes par style dynamique + ajouter poignees resize
  - `frontend/tests/components/copilot/FloatingChatWidget.test.ts` — mettre a jour les assertions de dimension + ajouter tests resize
  - `frontend/tests/stores/ui.test.ts` — ajouter tests pour les nouvelles fonctions du store (creer si inexistant)

- **Fichiers a NE PAS modifier :**
  - Aucun composant dans `components/chat/` (regle absolue de l'Epic 1)
  - `FloatingChatButton.vue` — pas concerne
  - `ChatWidgetHeader.vue` — pas concerne
  - `useChat.ts` — pas concerne
  - `layouts/default.vue` — pas concerne

### Patterns etablis dans les stories precedentes

1. **Dark mode obligatoire** : toute poignee visible (si on ajoute un indicateur visuel) doit avoir ses variantes `dark:`. Les poignees invisibles n'ont pas besoin de dark mode.
2. **GSAP** : import direct `import { gsap } from 'gsap'`. L'animation d'ouverture/fermeture existante utilise GSAP — le resize ne doit PAS interferer avec ces animations (ne pas modifier `scale`/`opacity` pendant un resize).
3. **Store Pinia** : utiliser le pattern existant avec `ref()` + fonctions exportees. Pas de getters complexes.
4. **localStorage** : cle `esg_mefali_widget_size`, format JSON `{ width: number, height: number }`. Pattern de lecture : `JSON.parse(localStorage.getItem(...))` avec try/catch et fallback aux defauts.
5. **`import.meta.client` guard** : toute lecture/ecriture localStorage doit etre gardee par `if (import.meta.client)` (bien que `ssr: false`, par coherence avec le pattern du store).
6. **Auto-import Nuxt** : `pathPrefix: false` — pas besoin d'importer explicitement les composants.
7. **Tailwind v4** : pas de `tailwind.config.ts`, config dans `main.css` via `@theme`. Les classes arbitraires `w-[Xpx]` fonctionnent, mais ici on passe a `:style` dynamique.

### Pointer Events vs Mouse Events

Utiliser les **Pointer Events** (`pointerdown`, `pointermove`, `pointerup`) et non les Mouse Events :
- Fonctionnent avec souris, tactile et stylet
- `setPointerCapture(pointerId)` garantit la reception de `pointermove` meme si le curseur sort du widget
- `releasePointerCapture(pointerId)` au `pointerup`
- Pas besoin de `touch-action: none` si `setPointerCapture` est utilise

### Ancrage bottom-right et redimensionnement multi-directionnel

Le widget est actuellement positionne avec `fixed bottom-24 right-6`. Le redimensionnement doit :
- **Bord droit / coin bas-droite** : modifier `width` / `height` vers la droite/bas — trivial car l'ancrage est en bottom-right, on augmente la taille en changeant le positionnement effectif
- **Bord gauche / coin haut-gauche** : necessitent de recalculer la position. Approche recommandee : basculer de `right`/`bottom` a `left`/`top` calcules dynamiquement, ou utiliser `right` et `bottom` fixes et modifier width/height tout en ajustant `right`/`bottom` pour compenser.
- **Approche simplifiee (recommandee pour V1)** : ne permettre le resize que par le bord gauche, le bord superieur, et le coin superieur-gauche (car le widget est ancre en bas-droite, ces directions sont naturelles). Garder `right: 24px` et `bottom: 96px` fixes. Calculer `width` et `height` en consequence.

### Deferred item W6 (Story 1.3)

Cette story resout le W6 : « Widget h-[600px] overflows viewport on short screens (<680px) ». Le clamp dynamique `max = window.innerHeight - 100` regle ce probleme. A l'ouverture, la hauteur initiale doit aussi etre clampee.

### Constantes

```typescript
const WIDGET_MIN_WIDTH = 300
const WIDGET_MIN_HEIGHT = 400
const WIDGET_DEFAULT_WIDTH = 400
const WIDGET_DEFAULT_HEIGHT = 600
const WIDGET_MARGIN = 100 // marge par rapport aux bords du viewport
const WIDGET_STORAGE_KEY = 'esg_mefali_widget_size'
```

### Structure des poignees de resize (suggestion)

```html
<!-- Bord gauche -->
<div class="absolute left-0 top-2 bottom-2 w-1 cursor-ew-resize" @pointerdown="startResize('left', $event)" />
<!-- Bord superieur -->
<div class="absolute top-0 left-2 right-2 h-1 cursor-ns-resize" @pointerdown="startResize('top', $event)" />
<!-- Coin superieur-gauche -->
<div class="absolute top-0 left-0 w-3 h-3 cursor-nwse-resize" @pointerdown="startResize('top-left', $event)" />
<!-- (optionnel) Coin superieur-droit -->
<div class="absolute top-0 right-0 w-3 h-3 cursor-nesw-resize" @pointerdown="startResize('top-right', $event)" />
```

Les poignees sont invisibles (pas de background) mais interactives. Largeur de 4px (w-1) pour les bords, 12px (w-3/h-3) pour les coins — compromis entre facilite de clic et discretion visuelle.

### Gestion de l'etat isResizing

Pendant le resize :
- `isResizing = ref(false)` — passe a `true` au `pointerdown`, `false` au `pointerup`
- Pendant `isResizing`, ajouter `select-none` sur le widget pour empecher la selection de texte
- Pendant `isResizing`, desactiver temporairement le scroll dans la zone de messages (`overflow: hidden` au lieu de `overflow-y: auto`)

### Tests existants a mettre a jour

Le fichier `FloatingChatWidget.test.ts` (695 lignes) assert explicitement les classes `w-[400px]` et `h-[600px]` aux lignes ~237-241. Ces assertions doivent etre remplacees par des verifications du style inline (`element.style.width`, `element.style.height`) ou des valeurs du store.

### Project Structure Notes

- Alignement avec la structure : tous les composants copilot dans `components/copilot/`, store dans `stores/ui.ts`
- Pas de nouveau fichier composable necessaire — la logique de resize vit dans le composant `FloatingChatWidget.vue`
- Si la logique de resize depasse ~80 lignes, envisager un composable `composables/useWidgetResize.ts` pour la separer

### References

- [Source: _bmad-output/planning-artifacts/epics-019-floating-copilot.md — Epic 1, Story 1.6]
- [Source: _bmad-output/planning-artifacts/prd.md — Must-Have #3 : Redimensionnement]
- [Source: _bmad-output/planning-artifacts/architecture-019-floating-copilot.md — ADR1 module-level state, stores Pinia]
- [Source: _bmad-output/implementation-artifacts/1-5-integration-du-chat-complet-dans-le-widget.md — structure widget actuelle]
- [Source: _bmad-output/implementation-artifacts/1-3-bouton-flottant-et-conteneur-du-widget.md — W6 viewport overflow]
- [Source: _bmad-output/implementation-artifacts/deferred-work.md — W6 et constantes de dimension]

## Previous Story Intelligence

### Story 1.5 — Learnings critiques

- **Reference implementation** : `pages/chat.vue` est la reference, pas `ChatPanel.vue`
- **`v-show` (pas `v-if`)** : le widget utilise `v-show` pour preserver le DOM et l'etat
- **GSAP** : `gsap.killTweensOf(widgetRef.value)` avant toute animation pour eviter les race conditions
- **`onBeforeUnmount`** : cleanup GSAP obligatoire
- **`prefersReducedMotion`** : snapshot non-reactif au mount (W1, deferred a 1.7)
- **Reducted motion close fix** : `animateClose` retourne immediatement si `prefersReducedMotion` pour eviter que `isVisible` reste bloque

### Story 1.3 — Patterns de positionnement

- Position : `fixed bottom-24 right-6 z-50`
- Glassmorphism : `.widget-glass` avec backdrop-blur-xl et fallback opaque
- Z-index strategy : FAB et Widget a z-50, modals a z >= 100
- Classes `overflow-hidden` sur le root — a remplacer par `overflow-hidden` seulement hors resize, ou utiliser `overflow-clip` pour le conteneur externe et `overflow-y-auto` pour la zone messages interne

### Warnings des stories precedentes

- Ne PAS ajouter de transition CSS sur les dimensions pendant le drag — cela cree un lag visuel
- Ne PAS utiliser `v-if` pour les poignees — elles doivent toujours etre dans le DOM quand le widget est visible
- Ne PAS modifier le `z-index` des poignees — elles doivent etre au-dessus du contenu du widget mais en dessous de tout overlay

## Dev Agent Record

### Agent Model Used
Claude Opus 4.6 (1M context)

### Debug Log References
- `import.meta.client` non defini en environnement Vitest/happy-dom : resolu par un plugin Vite custom `nuxtImportMetaPlugin` dans `vitest.config.ts` qui remplace `import.meta.client` par `true` et `import.meta.server` par `false` au compile time.
- Test 5.3 echouait car `clampToViewport()` dans `onMounted` reduit la hauteur selon `window.innerHeight` de happy-dom (768). Resolu en mockant `window.innerWidth/innerHeight` dans le test.

### Completion Notes List
- Store ui.ts enrichi avec `chatWidgetWidth`, `chatWidgetHeight`, `setChatWidgetSize`, `resetChatWidgetSize`, `initWidgetSize` — persistance localStorage avec cle `esg_mefali_widget_size`, try/catch avec fallback aux defauts.
- FloatingChatWidget.vue : dimensions dynamiques via `:style="widgetStyle"`, 4 poignees de resize invisibles (left, top, top-left, top-right), pointer events avec `setPointerCapture`, clamp min 300x400 / max viewport-100, `select-none` pendant drag, `overflow-hidden` dans la zone messages pendant drag, double-clic reset.
- Viewport clamping : `window.resize` listener avec cleanup dans `onBeforeUnmount`, `clampToViewport()` au mount.
- Vitest config : ajout plugin `nuxtImportMetaPlugin` et `setupFiles` pour simuler l'environnement Nuxt.
- 16 nouveaux tests (10 store + 6 composant), 112 tests total, zero regression.

### File List
- frontend/app/stores/ui.ts (modifie)
- frontend/app/components/copilot/FloatingChatWidget.vue (modifie)
- frontend/tests/components/copilot/FloatingChatWidget.test.ts (modifie)
- frontend/tests/stores/ui.test.ts (nouveau)
- frontend/tests/setup.ts (nouveau)
- frontend/vitest.config.ts (modifie)

### Change Log
- Story 1.6 : Redimensionnement du widget — implementation complete (Date: 2026-04-13)
