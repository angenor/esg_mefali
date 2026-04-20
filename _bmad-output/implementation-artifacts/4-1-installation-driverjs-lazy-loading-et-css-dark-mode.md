# Story 4.1 : Installation Driver.js, lazy loading et CSS dark mode

Status: done

## Story

En tant que developpeur,
je veux que Driver.js soit disponible en import dynamique sans impacter le bundle initial,
afin que le premier parcours guide demarre en < 500ms sans penaliser le chargement des pages.

## Acceptance Criteria

1. **AC1 — Installation de la dependance**
   - **Given** Driver.js n'est pas encore installe dans le projet
   - **When** un developpeur ajoute la dependance
   - **Then** `driver.js` est present dans `dependencies` de `package.json`
   - **And** `package-lock.json` est mis a jour

2. **AC2 — Cache module-level et import dynamique**
   - **Given** Driver.js est installe
   - **When** `loadDriver()` est appele pour la premiere fois
   - **Then** un `import('driver.js')` dynamique est execute
   - **And** le module est stocke dans un cache module-level (`driverModule`)
   - **And** les appels subsequents retournent le module depuis le cache sans re-import

3. **AC3 — Pre-chargement opportuniste via requestIdleCallback**
   - **Given** le `FloatingChatWidget` est monte
   - **When** `onMounted` est execute
   - **Then** `prefetchDriverJs()` est appele via `requestIdleCallback`
   - **And** Driver.js est pre-charge en arriere-plan sans bloquer le rendu

4. **AC4 — Zero impact sur le bundle initial (NFR4)**
   - **Given** le bundle initial est construit (`npm run build`)
   - **When** on analyse les chunks generes
   - **Then** Driver.js n'apparait pas dans le chunk initial — 0 Ko ajoute au bundle initial
   - **And** Driver.js apparait dans un chunk separe charge a la demande

5. **AC5 — CSS inclus et overrides dark mode**
   - **Given** le CSS de Driver.js est necessaire pour le rendu des popovers
   - **When** `main.css` est charge
   - **Then** `@import 'driver.js/dist/driver.css'` est present
   - **And** les overrides dark mode sont definis (`.dark .driver-popover` avec `bg-dark-card`, `text-surface-dark-text`, `border-dark-border`)

6. **AC6 — Rendu correct en dark mode**
   - **Given** le dark mode est actif (classe `.dark` sur `<html>`)
   - **When** un popover Driver.js est affiche (via `loadDriver()` + `driver().highlight()`)
   - **Then** le popover respecte le theme dark : fond sombre, texte clair, bordures dark
   - **And** les boutons de navigation (Suivant, Precedent, Fermer) sont stylises en dark

7. **AC7 — Zero regression (NFR19)**
   - **Given** les modifications sont terminees
   - **When** on execute les tests frontend (`npx vitest run`)
   - **Then** zero regression sur les tests existants (176+ tests)
   - **And** couverture >= 80% sur les fichiers nouveaux

## Tasks / Subtasks

- [x] **Task 1 : Installer Driver.js** (AC: 1)
  - [x] 1.1 Executer `npm install driver.js` dans le dossier `frontend/`
  - [x] 1.2 Verifier que `driver.js` apparait dans `dependencies` de `package.json` (PAS dans devDependencies — c'est une dependance runtime)
  - [x] 1.3 Verifier l'installation : `ls node_modules/driver.js/dist/driver.css` doit exister

- [x] **Task 2 : Creer les fonctions utilitaires de lazy loading** (AC: 2, 3, 4)
  - [x] 2.1 Creer le fichier `frontend/app/composables/useDriverLoader.ts` (voir Dev Notes pour le code exact)
  - [x] 2.2 Implementer la variable module-level `driverModule` comme cache singleton
  - [x] 2.3 Implementer `prefetchDriverJs()` : verifie le cache, appelle `requestIdleCallback(() => import('driver.js'))` si non charge
  - [x] 2.4 Implementer `loadDriver()` : retourne le module depuis le cache ou execute `await import('driver.js')` puis met en cache
  - [x] 2.5 Exporter les deux fonctions en tant que named exports

- [x] **Task 3 : Integrer le pre-chargement dans FloatingChatWidget** (AC: 3)
  - [x] 3.1 Dans `frontend/app/components/copilot/FloatingChatWidget.vue`, importer `prefetchDriverJs` depuis `~/composables/useDriverLoader`
  - [x] 3.2 Appeler `prefetchDriverJs()` dans le hook `onMounted()` du composant (apres les initialisations existantes)

- [x] **Task 4 : Ajouter le CSS Driver.js et les overrides dark mode** (AC: 5, 6)
  - [x] 4.1 Dans `frontend/app/assets/css/main.css`, ajouter `@import 'driver.js/dist/driver.css';` AVANT la ligne `@import "tailwindcss";`
  - [x] 4.2 Ajouter les overrides CSS pour `.driver-popover` en mode clair (voir Dev Notes)
  - [x] 4.3 Ajouter les overrides CSS pour `.dark .driver-popover` en dark mode (voir Dev Notes)
  - [x] 4.4 Ajouter les overrides pour les boutons de navigation Driver.js (`.driver-popover-navigation-btns`)
  - [x] 4.5 Ajouter l'override pour `prefers-reduced-motion` : desactiver les transitions/animations Driver.js (NFR14)

- [x] **Task 5 : Tests unitaires Vitest** (AC: 2, 3, 4, 7)
  - [x] 5.1 Creer `frontend/tests/composables/useDriverLoader.test.ts`
  - [x] 5.2 Test : `loadDriver()` retourne un module avec une propriete `driver` (fonction)
  - [x] 5.3 Test : `loadDriver()` appele 2x ne fait qu'un seul `import()` dynamique (cache)
  - [x] 5.4 Test : `prefetchDriverJs()` appelle `requestIdleCallback`
  - [x] 5.5 Test : `prefetchDriverJs()` appele 2x ne re-importe pas
  - [x] 5.6 Mocker `import('driver.js')` avec `vi.mock` pour isoler les tests

- [x] **Task 6 : Verification finale** (AC: 4, 7)
  - [x] 6.1 `npx vitest run` — tous les tests passent, zero regression
  - [x] 6.2 `npm run build` — build reussit, Driver.js est dans un chunk separe (verifier dans `.output/`)
  - [x] 6.3 Couverture >= 80% sur `useDriverLoader.ts`

### Review Findings

- [x] [Review][Patch] Rejet de promesse non gere dans `prefetchDriverJs` — ajoute `.catch()` sur `importOnce()` dans prefetch + reset `inflight` sur erreur [useDriverLoader.ts]
- [x] [Review][Patch] Race condition prefetch/loadDriver — refactorise avec `importOnce()` partage et promesse `inflight` pour deduplication [useDriverLoader.ts]
- [x] [Review][Patch] Test manquant : flux prefetch → loadDriver — ajoute test "prefetch remplit le cache reutilise par loadDriver" [useDriverLoader.test.ts]
- [x] [Review][Defer] Pas de `timeout` sur `requestIdleCallback` — sous charge CPU le prefetch peut ne jamais se declencher avant le premier guidage [useDriverLoader.ts:25] — deferred, pre-existing pattern
- [x] [Review][Defer] Couleurs hexadecimales hardcodees en mode clair — incohérence avec le dark mode qui utilise des variables CSS [main.css] — deferred, pre-existing design choice

## Dev Notes

### Portee de cette story

Cette story est STRICTEMENT frontend — aucune modification backend. Elle pose l'infrastructure pour les Epics 4-5-6 en installant Driver.js et en preparant le lazy loading. Le composable `useGuidedTour.ts` (machine a etats, orchestration des parcours) est dans l'**Epic 5, Story 5.1** — ne PAS le creer ici.

### Pourquoi un fichier separe `useDriverLoader.ts` et pas directement dans `useGuidedTour.ts`

L'architecture (ADR7) place les fonctions `prefetchDriverJs` et `loadDriver` dans `composables/useGuidedTour.ts`. Cependant, `useGuidedTour.ts` n'existe pas encore (Story 5.1) et cette story doit etre auto-contenue. Creer `useDriverLoader.ts` comme module utilitaire dedie au chargement. A la Story 5.1, `useGuidedTour.ts` importera et reutilisera `loadDriver()` depuis `useDriverLoader.ts`.

### Code exact de `useDriverLoader.ts`

```typescript
// frontend/app/composables/useDriverLoader.ts

/**
 * Utilitaire de chargement lazy de Driver.js.
 * Cache module-level : un seul import() dynamique, reutilise ensuite.
 * Sera consomme par useGuidedTour.ts (Story 5.1).
 */

let driverModule: typeof import('driver.js') | null = null

/**
 * Pre-charge Driver.js en arriere-plan via requestIdleCallback.
 * Appele dans FloatingChatWidget.onMounted().
 * Sur connexions rapides : le module est deja en cache quand le premier guidage arrive.
 * Sur connexions lentes : loadDriver() attendra le chargement (budget 500ms — NFR2).
 */
export function prefetchDriverJs(): void {
  if (driverModule) return

  const callback = () => {
    import('driver.js').then((m) => {
      driverModule = m
    })
  }

  if (typeof requestIdleCallback === 'function') {
    requestIdleCallback(callback)
  } else {
    // Fallback pour Safari < 17 qui ne supporte pas requestIdleCallback
    setTimeout(callback, 200)
  }
}

/**
 * Charge Driver.js et retourne le module.
 * Si deja en cache (via prefetch ou appel precedent), retour immediat.
 */
export async function loadDriver(): Promise<typeof import('driver.js')> {
  if (!driverModule) {
    driverModule = await import('driver.js')
  }
  return driverModule
}
```

### Fallback `requestIdleCallback`

Safari ne supporte `requestIdleCallback` que depuis la version 17+ (mars 2024). La SPA cible des PME africaines dont certains devices tournent sur Safari plus ancien. Le fallback `setTimeout(callback, 200)` couvre ce cas sans perte de fonctionnalite.

### CSS Driver.js — Code exact des overrides

```css
/* A ajouter dans frontend/app/assets/css/main.css */

/* === Driver.js overrides === */

/* Mode clair */
.driver-popover {
  background-color: #ffffff;
  color: var(--color-surface-text);
  border: 1px solid #e5e7eb; /* gray-200 */
  border-radius: 0.5rem;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
}

.driver-popover .driver-popover-title {
  font-weight: 600;
  font-size: 0.95rem;
}

.driver-popover .driver-popover-description {
  color: #4b5563; /* gray-600 */
  font-size: 0.875rem;
  line-height: 1.5;
}

/* Mode sombre */
.dark .driver-popover {
  background-color: var(--color-dark-card);
  color: var(--color-surface-dark-text);
  border-color: var(--color-dark-border);
}

.dark .driver-popover .driver-popover-description {
  color: #9ca3af; /* gray-400 */
}

/* Boutons de navigation */
.driver-popover .driver-popover-navigation-btns button {
  border-radius: 0.375rem;
  font-size: 0.875rem;
  padding: 0.375rem 0.75rem;
}

.driver-popover .driver-popover-next-btn {
  background-color: var(--color-brand-green);
  color: #ffffff;
}

.driver-popover .driver-popover-next-btn:hover {
  opacity: 0.9;
}

.driver-popover .driver-popover-prev-btn {
  background-color: transparent;
  color: var(--color-surface-text);
  border: 1px solid #d1d5db; /* gray-300 */
}

.dark .driver-popover .driver-popover-prev-btn {
  color: var(--color-surface-dark-text);
  border-color: var(--color-dark-border);
}

.driver-popover .driver-popover-close-btn {
  color: #6b7280; /* gray-500 */
}

.dark .driver-popover .driver-popover-close-btn {
  color: #9ca3af; /* gray-400 */
}

/* Overlay (fond semi-transparent) */
.driver-overlay {
  background-color: rgba(0, 0, 0, 0.5);
}

/* Reduction de mouvement (NFR14) */
@media (prefers-reduced-motion: reduce) {
  .driver-popover,
  .driver-overlay {
    transition: none !important;
    animation: none !important;
  }
}
```

### Structure de `main.css` apres modification

```css
@import 'driver.js/dist/driver.css';
@import "tailwindcss";

@custom-variant dark (&:where(.dark, .dark *));

@theme {
  /* Design system ESG Mefali — INCHANGE */
  --color-brand-green: #10B981;
  /* ... reste inchange ... */
}

/* === Driver.js overrides === */
/* ... overrides ci-dessus ... */
```

**ATTENTION** : L'`@import 'driver.js/dist/driver.css'` doit etre AVANT `@import "tailwindcss"` pour que les overrides Tailwind puissent surcharger les styles par defaut de Driver.js. Si place apres, les styles par defaut de Driver.js pourraient avoir une specificite superieure.

### Modification de FloatingChatWidget.vue

L'appel a `prefetchDriverJs()` doit etre ajoute dans le `onMounted()` existant. Chercher le hook `onMounted` dans le composant et ajouter l'appel a la fin :

```typescript
import { prefetchDriverJs } from '~/composables/useDriverLoader'

// Dans le onMounted existant, ajouter a la fin :
onMounted(() => {
  // ... code existant inchange ...
  
  // Pre-chargement opportuniste de Driver.js (ADR7)
  prefetchDriverJs()
})
```

Ne PAS creer un second `onMounted` — ajouter l'appel dans celui qui existe deja.

### Pattern de test — Mock de l'import dynamique

```typescript
// frontend/tests/composables/useDriverLoader.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock de driver.js
const mockDriverModule = {
  driver: vi.fn(() => ({
    highlight: vi.fn(),
    drive: vi.fn(),
    destroy: vi.fn(),
  })),
}

vi.mock('driver.js', () => mockDriverModule)

describe('useDriverLoader', () => {
  beforeEach(() => {
    vi.resetModules()
    // Re-importer pour reset le cache module-level
  })

  describe('loadDriver', () => {
    it('retourne le module driver.js', async () => {
      const { loadDriver } = await import('~/composables/useDriverLoader')
      const mod = await loadDriver()
      expect(mod).toBeDefined()
      expect(mod.driver).toBeDefined()
    })

    it('met en cache le module apres le premier appel', async () => {
      const { loadDriver } = await import('~/composables/useDriverLoader')
      const mod1 = await loadDriver()
      const mod2 = await loadDriver()
      expect(mod1).toBe(mod2) // meme reference
    })
  })

  describe('prefetchDriverJs', () => {
    it('appelle requestIdleCallback', async () => {
      const mockRIC = vi.fn((cb: () => void) => { cb(); return 0 })
      vi.stubGlobal('requestIdleCallback', mockRIC)

      const { prefetchDriverJs } = await import('~/composables/useDriverLoader')
      prefetchDriverJs()
      expect(mockRIC).toHaveBeenCalledOnce()

      vi.unstubAllGlobals()
    })

    it('utilise setTimeout comme fallback si requestIdleCallback absent', async () => {
      vi.stubGlobal('requestIdleCallback', undefined)
      const spy = vi.spyOn(globalThis, 'setTimeout')

      const { prefetchDriverJs } = await import('~/composables/useDriverLoader')
      prefetchDriverJs()
      expect(spy).toHaveBeenCalledWith(expect.any(Function), 200)

      vi.unstubAllGlobals()
      spy.mockRestore()
    })
  })
})
```

**Note** : Le cache module-level necessite `vi.resetModules()` + re-import dans `beforeEach` pour isoler les tests. Sans cela, le cache persiste entre les tests.

### Fichiers a modifier

| Fichier | Action | Detail |
|---------|--------|--------|
| `frontend/package.json` | Modifie | Ajout `driver.js` dans `dependencies` (via `npm install`) |
| `frontend/app/composables/useDriverLoader.ts` | Nouveau | Fonctions `prefetchDriverJs()` et `loadDriver()` avec cache module-level |
| `frontend/app/assets/css/main.css` | Modifie | `@import 'driver.js/dist/driver.css'` + overrides dark mode + prefers-reduced-motion |
| `frontend/app/components/copilot/FloatingChatWidget.vue` | Modifie | Appel `prefetchDriverJs()` dans `onMounted()` |
| `frontend/tests/composables/useDriverLoader.test.ts` | Nouveau | Tests unitaires avec mock de l'import dynamique |

### Fichiers a NE PAS modifier

- `frontend/app/composables/useGuidedTour.ts` — N'existe pas encore, sera cree Story 5.1
- `frontend/app/types/guided-tour.ts` — Story 4.2
- `frontend/app/lib/guided-tours/registry.ts` — Story 4.2
- `backend/**` — Aucune modification backend dans cette story
- `frontend/nuxt.config.ts` — Pas de plugin Nuxt pour Driver.js (import dynamique suffit)
- `frontend/app/stores/ui.ts` — Pas de nouveaux champs ici (Story 5.1)
- `frontend/app/components/copilot/FloatingChatButton.vue` — Pas concerne
- `frontend/app/components/copilot/ChatWidgetHeader.vue` — Pas concerne

### Versions et compatibilite

- **Driver.js** : `^1.4.0` (derniere version stable, TypeScript natif, 5 Ko gzippe, zero dependance)
- **Import `driver()`** : `import { driver } from 'driver.js'` — ESM natif
- **CSS** : `driver.js/dist/driver.css` (~2 Ko)
- **TypeScript** : Types inclus nativement, pas de `@types/driver.js` necessaire
- **Nuxt 4** : L'import dynamique `import('driver.js')` est gere nativement par Vite/Rollup (code splitting automatique)

### Intelligence de la story precedente (3-2)

**Learnings cles :**
- Le pattern d'injection conditionnelle (si valeur presente → ajouter, sinon → ignorer) fonctionne bien pour les fonctionnalites incrementales
- Les tests avec `vi.resetModules()` sont necessaires quand on teste du state module-level (exact meme besoin ici pour le cache `driverModule`)
- 979 tests backend + 176 tests frontend au dernier commit
- Le `FloatingChatWidget.vue` existe deja dans `components/copilot/` et a un `onMounted()` existant
- Convention du projet : composables exportent des fonctions nommees (pas de default export)
- Dark mode : la classe `.dark` est sur `<html>`, geree par `stores/ui.ts`

### Commits recents

```
d6889b2 3-2-injection-de-la-page-courante-dans-les-prompts-et-adaptation-des-reponses: done
c94a1e2 3-1-transmission-de-la-page-courante-au-backend: done
c489a6c 2-2-mise-a-jour-de-la-navigation-et-des-liens-internes: done
b7314e2 2-1-suppression-de-la-page-chat-et-de-chatpanel: done
39bbb14 1-6-redimensionnement-du-widget: done + 1-7-accessibilite-et-navigation-clavier-du-widget: done
```

### Project Structure Notes

- Frontend : Nuxt 4 SPA (`ssr: false`), structure `app/`, composants PascalCase sans prefixe de dossier (`pathPrefix: false`)
- CSS : Tailwind v4, `@custom-variant dark`, variables `@theme` dans `main.css`
- Tests : Vitest 3.0, `@vue/test-utils` 2.4, `happy-dom` pour le DOM
- Composables : `frontend/app/composables/`, 16 fichiers existants, pattern named exports
- Copilot : `frontend/app/components/copilot/` contient deja `FloatingChatWidget.vue`, `FloatingChatButton.vue`, `ChatWidgetHeader.vue`

### References

- [Source: _bmad-output/planning-artifacts/epics-019-floating-copilot.md — Epic 4, Story 4.1]
- [Source: _bmad-output/planning-artifacts/architecture-019-floating-copilot.md — ADR7 Lazy loading Driver.js, lignes 534-578]
- [Source: _bmad-output/planning-artifacts/architecture-019-floating-copilot.md — Overrides CSS dark mode, lignes 569-578]
- [Source: _bmad-output/planning-artifacts/architecture-019-floating-copilot.md — Arborescence fichiers, lignes 786-868]
- [Source: _bmad-output/planning-artifacts/prd.md — NFR2 (chargement < 500ms), NFR4 (0 Ko bundle), NFR14 (prefers-reduced-motion), NFR23 (dark mode)]
- [Source: _bmad-output/implementation-artifacts/3-2-injection-de-la-page-courante-dans-les-prompts-et-adaptation-des-reponses.md — Completion Notes, Project Structure Notes]
- [Source: frontend/app/assets/css/main.css — Structure @theme existante]
- [Source: frontend/package.json — Dependances actuelles, absence de driver.js]
- [Source: frontend/app/components/copilot/ — FloatingChatWidget.vue, FloatingChatButton.vue, ChatWidgetHeader.vue existants]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

Aucun probleme rencontre.

### Completion Notes List

- driver.js ^1.4.0 installe dans dependencies (pas devDependencies)
- Composable `useDriverLoader.ts` cree avec cache module-level singleton, `prefetchDriverJs()` (requestIdleCallback + fallback setTimeout) et `loadDriver()` (async avec cache)
- Pre-chargement opportuniste integre dans `FloatingChatWidget.vue` via `onMounted()` existant
- CSS Driver.js importe AVANT Tailwind dans `main.css` pour garantir la surcharge
- Overrides complets : mode clair, dark mode (`.dark .driver-popover`), boutons navigation, overlay, et `prefers-reduced-motion` (NFR14)
- 5 tests unitaires couvrant toutes les branches : loadDriver return, cache singleton, prefetch via requestIdleCallback, fallback setTimeout, skip si deja en cache
- 181 tests frontend passent (zero regression, +5 nouveaux)
- Build reussi, Driver.js isole dans un chunk separe (~20 Ko), 0 Ko ajoute au bundle initial

### Change Log

- 2026-04-13 : Implementation complete de la Story 4.1 — installation Driver.js, lazy loading, CSS dark mode, 5 tests

### File List

- `frontend/package.json` — Modifie (ajout driver.js ^1.4.0 dans dependencies)
- `frontend/package-lock.json` — Modifie (lock file mis a jour)
- `frontend/app/composables/useDriverLoader.ts` — Nouveau (prefetchDriverJs + loadDriver avec cache module-level)
- `frontend/app/assets/css/main.css` — Modifie (import CSS Driver.js + overrides dark mode + prefers-reduced-motion)
- `frontend/app/components/copilot/FloatingChatWidget.vue` — Modifie (import + appel prefetchDriverJs dans onMounted)
- `frontend/tests/composables/useDriverLoader.test.ts` — Nouveau (5 tests unitaires)
