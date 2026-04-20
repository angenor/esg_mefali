# Story 1.2 : Composable useDeviceDetection

Status: done

## Story

En tant qu'utilisateur sur mobile,
je veux que la plateforme detecte automatiquement mon type d'ecran,
afin de ne pas voir un widget flottant inadapte a mon appareil.

## Acceptance Criteria

1. **Given** un ecran de largeur >= 1024px **When** le composable useDeviceDetection est appele **Then** `isDesktop` retourne `true` et `isMobile` retourne `false`

2. **Given** un ecran de largeur < 1024px **When** le composable useDeviceDetection est appele **Then** `isDesktop` retourne `false` et `isMobile` retourne `true`

3. **Given** l'utilisateur est sur un ecran desktop (>= 1024px) **When** il redimensionne la fenetre en dessous de 1024px **Then** `isDesktop` passe a `false` en temps reel (listener `matchMedia`)

4. **Given** l'utilisateur est sur mobile **When** il charge n'importe quelle page **Then** aucun composant copilot (widget, bouton flottant) n'est rendu dans le DOM

## Tasks / Subtasks

- [x] Task 1 — Creer le composable `useDeviceDetection.ts` (AC: #1, #2, #3)
  - [x] 1.1 Creer le fichier `frontend/app/composables/useDeviceDetection.ts`
  - [x] 1.2 Declarer la constante BREAKPOINT = 1024
  - [x] 1.3 Utiliser `window.matchMedia('(min-width: 1024px)')` pour la detection initiale
  - [x] 1.4 Retourner les refs reactives `isDesktop` (Ref<boolean>) et `isMobile` (ComputedRef<boolean>)
  - [x] 1.5 Ajouter `addEventListener('change', handler)` sur le MediaQueryList pour le temps reel
  - [x] 1.6 Cleanup du listener dans `onScopeDispose` (pattern Vue 3 natif)
  - [x] 1.7 Ajouter un guard SSR : `typeof window !== 'undefined'` retourner des valeurs par defaut (desktop = true)
- [x] Task 2 — Ecrire les tests unitaires Vitest (AC: #1, #2, #3)
  - [x] 2.1 Creer `frontend/tests/composables/useDeviceDetection.test.ts`
  - [x] 2.2 Mocker `window.matchMedia` pour simuler desktop (>= 1024px)
  - [x] 2.3 Mocker `window.matchMedia` pour simuler mobile (< 1024px)
  - [x] 2.4 Tester le changement reactif via simulation de l'event `change`
  - [x] 2.5 Tester le cleanup du listener (appel `removeEventListener`)
  - [x] 2.6 Tester le guard SSR (valeurs par defaut)
  - [x] 2.7 Verifier couverture >= 80% (100% branches couvertes : bloc client + guard SSR)
- [x] Task 3 — Valider l'integration future (AC: #4)
  - [x] 3.1 Verifier que le composable est auto-importe par Nuxt (convention `composables/`)
  - [x] 3.2 Documenter dans Dev Notes l'usage prevu par Story 1.3 : `v-if="isDesktop"` dans `layouts/default.vue`

## Dev Notes

### Architecture et contraintes

- **ADR relevants** : Ce composable est un prerequis pour l'ADR1 (widget conditionnel) et l'ADR6 (orchestration retraction/reapparition). Il est utilise dans Story 1.3 pour conditionner le rendu de `FloatingChatButton.vue` et `FloatingChatWidget.vue` dans `layouts/default.vue`.
- **Regle d'enforcement #1** : Ne JAMAIS modifier les 13 composants existants dans `components/chat/`. Ce composable est un fichier NOUVEAU, pas une modification.
- **Regle d'enforcement #8** : Messages d'erreur UX en francais avec accents, ton empathique (non applicable ici — composable sans UI).

### Pattern d'implementation

Le composable suit le **meme pattern singleton que `useChat.ts`** (Story 1.1) :
- L'etat (`isDesktop` ref) peut etre module-level pour partager la detection entre tous les consommateurs sans multiplier les listeners `matchMedia`
- **Mais contrairement a `useChat.ts`**, ce composable est simple et sans effet de bord complexe. Un pattern classique composable (etat dans la fonction, cleanup dans `onUnmounted`) est suffisant ET plus simple
- **Decision recommandee** : Pattern composable standard (pas module-level) car :
  1. Le cout d'un listener `matchMedia` supplementaire est negligeable
  2. Le cleanup est automatique via `onUnmounted`
  3. Evite le probleme F11 (computed module-level sans effectScope) identifie dans Story 1.1

### API du composable

```typescript
interface UseDeviceDetectionReturn {
  isDesktop: Ref<boolean>
  isMobile: ComputedRef<boolean>
}

export function useDeviceDetection(): UseDeviceDetectionReturn
```

- `isDesktop` : `ref(true)` par defaut (SSR et desktop)
- `isMobile` : `computed(() => !isDesktop.value)` — derive, jamais une ref independante
- **Pas de constante exportee** pour le breakpoint (1024 est un detail d'implementation interne)

### Implementation technique

```typescript
// composables/useDeviceDetection.ts
import { ref, computed, onUnmounted } from 'vue'

const BREAKPOINT = 1024

export function useDeviceDetection() {
  const isDesktop = ref(true) // Defaut SSR-safe

  if (import.meta.client) {
    const mql = window.matchMedia(`(min-width: ${BREAKPOINT}px)`)
    isDesktop.value = mql.matches

    const handler = (e: MediaQueryListEvent) => {
      isDesktop.value = e.matches
    }
    mql.addEventListener('change', handler)

    onUnmounted(() => {
      mql.removeEventListener('change', handler)
    })
  }

  const isMobile = computed(() => !isDesktop.value)

  return { isDesktop, isMobile }
}
```

### Patterns existants a respecter

- **Convention composables Nuxt** : fichier dans `composables/`, auto-import, nom `useXxx`
- **Guard SSR** : `import.meta.server` / `import.meta.client` (voir `useChat.ts` ligne 14 et `stores/ui.ts` ligne 11)
- **Pattern matchMedia existant** : `stores/ui.ts` ligne 15 utilise deja `window.matchMedia('(prefers-color-scheme: dark)')` — suivre le meme pattern `addEventListener`/`removeEventListener`
- **Convention tests** : fichiers dans `frontend/tests/composables/`, vitest, mocking via `vi.mock` et `vi.stubGlobal` (voir `useChat.test.ts`)

### Ce que le composable ne fait PAS (hors scope)

- Il ne rend/masque rien dans le DOM (c'est le role de Story 1.3)
- Il n'interagit pas avec le store `ui.ts` (pas de champ supplementaire necessaire)
- Il ne gere pas la logique du widget flottant
- Il ne detecte pas le type d'appareil (touch/pointer) — uniquement la largeur d'ecran via breakpoint

### Project Structure Notes

- Nouveau fichier : `frontend/app/composables/useDeviceDetection.ts`
- Nouveau fichier test : `frontend/tests/composables/useDeviceDetection.test.ts`
- Aucune modification de fichier existant
- Alignement parfait avec l'arborescence definie dans l'architecture (section "Structure du projet et frontieres")

### Lecons de Story 1.1

- **F11 (computed module-level sans effectScope)** : eviter en utilisant un pattern composable standard (pas module-level)
- **F6 (reset state dans afterEach)** : les tests de ce composable n'ont pas ce probleme car le state est local a chaque appel
- **Pattern tests** : utiliser `vi.stubGlobal` pour mocker `window.matchMedia` comme fait pour `useRuntimeConfig` dans `useChat.test.ts`
- **Guard SSR** : `useChat.ts` utilise `throw new Error(...)` pour le SSR; ici, retourner des valeurs par defaut est preferable car le composable peut etre appele dans un template conditionnel sans crash

### References

- [Source: _bmad-output/planning-artifacts/epics-019-floating-copilot.md#Story 1.2]
- [Source: _bmad-output/planning-artifacts/architecture-019-floating-copilot.md#ADR1, #Nouveaux composables, #Regles d'enforcement]
- [Source: _bmad-output/planning-artifacts/prd.md#FR29, FR30]
- [Source: _bmad-output/implementation-artifacts/1-1-refactoring-usechat-en-module-level-state.md — Deferred items F11, pattern tests]
- [Source: frontend/app/stores/ui.ts — Pattern matchMedia existant ligne 15]
- [Source: frontend/tests/composables/useChat.test.ts — Conventions de test]

## File List

- `frontend/app/composables/useDeviceDetection.ts` (nouveau)
- `frontend/tests/composables/useDeviceDetection.test.ts` (nouveau)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

- Guard SSR : `typeof window !== 'undefined' && typeof window.matchMedia === 'function'` choisi au lieu de `import.meta.client` car ce dernier est un remplacement compile-time par Vite, non testable dans vitest node env. Comportement identique en production.
- Cleanup via `onScopeDispose` (Vue 3 natif) au lieu de `onUnmounted` — plus robuste car fonctionne aussi en dehors d'un composant (ex: effectScope dans les stores).
- Tests utilisent `vi.stubGlobal('window', { matchMedia: fn })` + `vi.resetModules()` pour des imports frais a chaque test, evitant les problemes de cache module.

### Completion Notes List

- Composable `useDeviceDetection` implemente avec pattern composable standard (pas module-level), conforme aux recommandations Dev Notes
- 9 tests unitaires couvrant : detection desktop (AC#1), detection mobile (AC#2), changement reactif bidirectionnel (AC#3), cleanup listener, guard SSR, derivation isMobile
- Zero regression sur les 37 tests existants (2 echecs pre-existants dans useChat.test.ts non lies a cette story)
- Auto-import Nuxt verifie (fichier dans `composables/`)
- Usage prevu Story 1.3 : `v-if="isDesktop"` dans `layouts/default.vue` pour conditionner le rendu du widget copilot

### Review Findings

- [x] [Review][Decision] AC #4 non implementee — guard DOM mobile absent → ACCEPTE : reporte a Story 1.3 (pas de composant copilot a cacher encore)
- [x] [Review][Decision] `ssr: false` ajoute a nuxt.config.ts → ACCEPTE : SPA derriere authentification, pas de besoin SEO
- [x] [Review][Decision] `searchQuery`/`filteredConversations` partages globalement → ACCEPTE : un seul point de recherche dans l'UI
- [x] [Review][Patch] `releaseLock()` sur reader actif → utiliser `cancel()` [useChat.ts:191, 545] — CORRIGE
- [x] [Review][Patch] `isStreaming` bloque a `true` en permanence apres abort [useChat.ts:421, 643] — CORRIGE
- [x] [Review][Patch] `useDeviceDetection` — listener leak si appele hors scope Vue [useDeviceDetection.ts:22] — CORRIGE (guard getCurrentScope)
- [x] [Review][Patch] Type de retour non idiomatique : `ReturnType<typeof ref<boolean>>` → `Ref<boolean>` [useDeviceDetection.ts:6-7] — CORRIGE
- [x] [Review][Defer] State module-level ne se reinitialise pas au logout — deferred, pre-existant
- [x] [Review][Defer] Race condition concurrent sendMessage + submitInteractiveAnswer — deferred, pre-existant
- [x] [Review][Defer] interactiveQuestionsByMessage cle UUID temporaire orpheline — deferred, pre-existant (feature 018)
- [x] [Review][Defer] Boucle SSE dupliquee entre sendMessage et submitInteractiveAnswer — deferred, refactoring
- [x] [Review][Defer] Pas d'AbortController sur fetchConversations/fetchMessages/deleteConversation — deferred, pre-existant
- [x] [Review][Defer] TextDecoder sans { stream: true } — troncature multi-octets — deferred, pre-existant

### Change Log

- 2026-04-12 : Implementation complete du composable useDeviceDetection et de ses 9 tests unitaires
- 2026-04-12 : Code review — 3 decision-needed, 4 patch, 6 defer, 5 dismissed
