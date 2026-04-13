# Story 4.2 : Types et registre de parcours guides

Status: done

## Story

En tant que developpeur,
je veux un registre extensible de parcours guides avec des types TypeScript stricts,
afin d'ajouter de nouveaux parcours sans modifier le moteur de guidage.

## Acceptance Criteria

1. **AC1 — Interfaces TypeScript dans types/guided-tour.ts**
   - **Given** les types n'existent pas encore
   - **When** un developpeur cree `types/guided-tour.ts`
   - **Then** les interfaces suivantes sont definies :
     - `GuidedTourStep` avec `route?` (string), `selector` (string), `popover` (`{ title: string, description: string, side?: 'top' | 'bottom' | 'left' | 'right', countdown?: number }`)
     - `GuidedTourDefinition` avec `id` (string), `steps` (GuidedTourStep[]), `entryStep?` (objet avec `selector`, `popover`, `targetRoute`)
     - `TourContext` = `Record<string, unknown>`
     - `TourState` = `'idle' | 'loading' | 'ready' | 'navigating' | 'waiting_dom' | 'highlighting' | 'complete' | 'interrupted'`

2. **AC2 — Registre tourRegistry dans lib/guided-tours/registry.ts**
   - **Given** le registre n'existe pas encore
   - **When** un developpeur cree `lib/guided-tours/registry.ts`
   - **Then** `tourRegistry` est un `Record<string, GuidedTourDefinition>` contenant 6 parcours pre-definis

3. **AC3 — 6 parcours pre-definis avec ids uniques**
   - **Given** les 6 parcours pre-definis
   - **When** on les inspecte
   - **Then** chacun a un id unique suivant la convention `show_[module]_[page]` en snake_case :
     - `show_esg_results` (score, forces/faiblesses, recommandations)
     - `show_carbon_results` (donut, benchmark, plan reduction)
     - `show_financing_catalog` (catalogue fonds)
     - `show_credit_score` (score credit vert)
     - `show_action_plan` (timeline plan d'action)
     - `show_dashboard_overview` (vue d'ensemble tableau de bord)

4. **AC4 — Placeholders interpolables dans les textes**
   - **Given** un parcours contient des placeholders dans ses textes (ex: `{{total_tco2}} tCO2e`)
   - **When** un `TourContext` est fourni avec les valeurs correspondantes
   - **Then** les textes sont interpolables (la logique d'interpolation sera dans `useGuidedTour`, Epic 5)

5. **AC5 — Extensibilite sans modification du moteur**
   - **Given** un developpeur veut ajouter un 7eme parcours
   - **When** il ajoute une entree dans `tourRegistry`
   - **Then** le parcours est disponible sans modifier aucun autre fichier (FR28)

6. **AC6 — Zero regression**
   - **Given** les modifications sont terminees
   - **When** on execute les tests frontend (`npx vitest run`)
   - **Then** zero regression sur les tests existants (181+ tests)
   - **And** couverture >= 80% sur les fichiers nouveaux

## Tasks / Subtasks

- [x] **Task 1 : Creer les types TypeScript** (AC: 1)
  - [x] 1.1 Creer `frontend/app/types/guided-tour.ts`
  - [x] 1.2 Definir l'interface `GuidedTourStep` avec les champs `route?`, `selector`, `popover` (objet avec `title`, `description`, `side?`, `countdown?`)
  - [x] 1.3 Definir l'interface `GuidedTourDefinition` avec `id`, `steps[]`, `entryStep?` (objet avec `selector`, `popover`, `targetRoute`)
  - [x] 1.4 Definir le type `TourContext` = `Record<string, unknown>`
  - [x] 1.5 Definir le type `TourState` = union de 8 etats
  - [x] 1.6 Exporter toutes les interfaces et types en named exports

- [x] **Task 2 : Creer le dossier et le fichier registre** (AC: 2, 3, 4, 5)
  - [x] 2.1 Creer le dossier `frontend/app/lib/guided-tours/`
  - [x] 2.2 Creer `frontend/app/lib/guided-tours/registry.ts`
  - [x] 2.3 Importer `GuidedTourDefinition` depuis `~/types/guided-tour`
  - [x] 2.4 Definir et exporter `tourRegistry: Record<string, GuidedTourDefinition>` contenant les 6 parcours (voir Dev Notes pour le contenu exact)
  - [x] 2.5 Verifier que tous les selectors utilisent la convention `[data-guide-target="xxx"]` — JAMAIS de classes CSS ou IDs
  - [x] 2.6 Verifier que les textes sont en francais avec accents et contiennent des placeholders `{{...}}` la ou pertinent

- [x] **Task 3 : Tests unitaires Vitest** (AC: 2, 3, 5, 6)
  - [x] 3.1 Creer `frontend/tests/lib/guided-tours/registry.test.ts`
  - [x] 3.2 Test : `tourRegistry` contient exactement 6 parcours
  - [x] 3.3 Test : chaque parcours a un `id` unique suivant la convention `show_*`
  - [x] 3.4 Test : chaque parcours a au moins un step avec un `selector` valide (format `[data-guide-target="xxx"]`)
  - [x] 3.5 Test : tous les selectors utilisent le format `[data-guide-target="..."]`, aucun ne commence par `.` ou `#`
  - [x] 3.6 Test : les 6 ids attendus sont presents (`show_esg_results`, `show_carbon_results`, `show_financing_catalog`, `show_credit_score`, `show_action_plan`, `show_dashboard_overview`)
  - [x] 3.7 Test : un ajout de 7eme parcours fonctionne (extensibilite)
  - [x] 3.8 Test : les types exportes sont corrects (compilation TypeScript sans erreur)

- [x] **Task 4 : Verification finale** (AC: 6)
  - [x] 4.1 `npx vitest run` — tous les tests passent, zero regression (191/191)
  - [x] 4.2 `npx nuxi typecheck` — zero nouvelle erreur de type (erreurs pre-existantes non liees a cette story)
  - [x] 4.3 Couverture >= 80% sur `registry.ts` (100%); `guided-tour.ts` est types-only (pas de code executable)

## Dev Notes

### Portee de cette story

Cette story est STRICTEMENT frontend — aucune modification backend. Elle cree les types et le registre de parcours qui seront consommes par :
- Story 4.3 : les `data-guide-target` correspondront aux selectors definis ici
- Story 5.1 : `useGuidedTour.ts` importera les types et le registre
- Epic 6 : le tool backend `trigger_guided_tour` enverra un `tour_id` qui correspondra a une cle du registre

### Fichiers a creer

| Fichier | Action | Detail |
|---------|--------|--------|
| `frontend/app/types/guided-tour.ts` | Nouveau | Interfaces TypeScript du systeme de guidage |
| `frontend/app/lib/guided-tours/registry.ts` | Nouveau | Registre des 6 parcours pre-definis |
| `frontend/tests/lib/guided-tours/registry.test.ts` | Nouveau | Tests unitaires du registre |

### Fichiers a NE PAS modifier

- `frontend/app/composables/useDriverLoader.ts` — Deja cree Story 4.1, ne pas toucher
- `frontend/app/composables/useGuidedTour.ts` — N'existe pas encore, sera cree Story 5.1
- `frontend/app/assets/css/main.css` — Deja modifie Story 4.1
- `frontend/app/components/copilot/FloatingChatWidget.vue` — Deja modifie Story 4.1
- `backend/**` — Aucune modification backend
- `frontend/app/stores/ui.ts` — Pas de nouveaux champs (Story 5.1)
- Aucun composant existant dans `components/` — c'est la Story 4.3 qui ajoutera les `data-guide-target`

### Code exact de `types/guided-tour.ts`

```typescript
// frontend/app/types/guided-tour.ts

/**
 * Types du systeme de guidage visuel (parcours guides Driver.js).
 * Consomme par lib/guided-tours/registry.ts et composables/useGuidedTour.ts.
 */

export interface GuidedTourPopover {
  title: string
  description: string
  side?: 'top' | 'bottom' | 'left' | 'right'
  countdown?: number
}

export interface GuidedTourStep {
  /** Route cible si l'etape necessite une navigation (ex: '/carbon/results') */
  route?: string
  /** Selecteur CSS — TOUJOURS au format [data-guide-target="xxx"] */
  selector: string
  /** Configuration du popover Driver.js */
  popover: GuidedTourPopover
}

export interface GuidedTourEntryStep {
  /** Selecteur de l'element sidebar a pointer avant navigation */
  selector: string
  /** Configuration du popover avec countdown optionnel */
  popover: GuidedTourPopover
  /** Route vers laquelle naviguer apres le countdown */
  targetRoute: string
}

export interface GuidedTourDefinition {
  /** Identifiant unique — convention show_[module]_[page] en snake_case */
  id: string
  /** Etapes du parcours dans l'ordre d'affichage */
  steps: GuidedTourStep[]
  /** Etape d'entree optionnelle pour les parcours multi-pages (navigation initiale) */
  entryStep?: GuidedTourEntryStep
}

/** Contexte dynamique envoye par le LLM pour personnaliser les textes */
export type TourContext = Record<string, unknown>

/** Etats de la machine a etats du parcours guide */
export type TourState =
  | 'idle'
  | 'loading'
  | 'ready'
  | 'navigating'
  | 'waiting_dom'
  | 'highlighting'
  | 'complete'
  | 'interrupted'
```

### Code exact de `lib/guided-tours/registry.ts`

```typescript
// frontend/app/lib/guided-tours/registry.ts

import type { GuidedTourDefinition } from '~/types/guided-tour'

/**
 * Registre extensible des parcours guides pre-definis.
 * Convention ids : show_[module]_[page] en snake_case.
 * Convention selectors : [data-guide-target="xxx"] uniquement.
 * Les placeholders {{...}} sont interpoles par useGuidedTour (Story 5.1).
 *
 * Pour ajouter un parcours : ajouter une entree ici + les data-guide-target
 * correspondants sur les composants cibles. Zero modification du moteur.
 */
export const tourRegistry: Record<string, GuidedTourDefinition> = {
  show_esg_results: {
    id: 'show_esg_results',
    steps: [
      {
        route: '/esg',
        selector: '[data-guide-target="esg-score-circle"]',
        popover: {
          title: 'Score ESG global',
          description: 'Votre score ESG est de {{esg_score}}/100. Ce cercle montre votre performance environnementale, sociale et de gouvernance.',
          side: 'bottom',
        },
      },
      {
        selector: '[data-guide-target="esg-strengths-badges"]',
        popover: {
          title: 'Points forts identifiés',
          description: 'Vos meilleures pratiques ESG sont affichées ici. Elles valorisent votre entreprise auprès des bailleurs.',
          side: 'right',
        },
      },
      {
        selector: '[data-guide-target="esg-recommendations"]',
        popover: {
          title: 'Recommandations personnalisées',
          description: 'Ces actions prioritaires vous permettront d\'améliorer votre score et d\'accéder à davantage de financements verts.',
          side: 'top',
        },
      },
    ],
    entryStep: {
      selector: '[data-guide-target="sidebar-esg-link"]',
      popover: {
        title: 'Résultats ESG',
        description: 'Cliquez ici pour voir votre évaluation ESG détaillée.',
        countdown: 8,
      },
      targetRoute: '/esg',
    },
  },

  show_carbon_results: {
    id: 'show_carbon_results',
    steps: [
      {
        route: '/carbon/results',
        selector: '[data-guide-target="carbon-donut-chart"]',
        popover: {
          title: 'Répartition de vos émissions',
          description: 'Votre empreinte est de {{total_tco2}} tCO2e. Ce graphique montre la répartition par catégorie — {{top_category}} représente {{top_category_pct}}% du total.',
          side: 'bottom',
        },
      },
      {
        selector: '[data-guide-target="carbon-benchmark"]',
        popover: {
          title: 'Comparaison sectorielle',
          description: 'Votre position par rapport à la moyenne de votre secteur ({{sector}}).',
          side: 'right',
        },
      },
      {
        selector: '[data-guide-target="carbon-reduction-plan"]',
        popover: {
          title: 'Plan de réduction',
          description: 'Les actions recommandées pour réduire votre empreinte carbone, classées par impact.',
          side: 'top',
        },
      },
    ],
    entryStep: {
      selector: '[data-guide-target="sidebar-carbon-link"]',
      popover: {
        title: 'Résultats Empreinte Carbone',
        description: 'Cliquez ici pour voir vos résultats détaillés.',
        countdown: 8,
      },
      targetRoute: '/carbon/results',
    },
  },

  show_financing_catalog: {
    id: 'show_financing_catalog',
    steps: [
      {
        route: '/financing',
        selector: '[data-guide-target="financing-fund-list"]',
        popover: {
          title: 'Catalogue des fonds disponibles',
          description: 'Voici les fonds de financement vert compatibles avec votre profil et votre secteur d\'activité.',
          side: 'bottom',
        },
      },
    ],
    entryStep: {
      selector: '[data-guide-target="sidebar-financing-link"]',
      popover: {
        title: 'Financements verts',
        description: 'Cliquez ici pour explorer les fonds disponibles.',
        countdown: 8,
      },
      targetRoute: '/financing',
    },
  },

  show_credit_score: {
    id: 'show_credit_score',
    steps: [
      {
        route: '/credit',
        selector: '[data-guide-target="credit-score-gauge"]',
        popover: {
          title: 'Score de crédit vert',
          description: 'Votre score de crédit alternatif est de {{credit_score}}/100. Il combine solvabilité traditionnelle et impact environnemental.',
          side: 'bottom',
        },
      },
    ],
    entryStep: {
      selector: '[data-guide-target="sidebar-credit-link"]',
      popover: {
        title: 'Score Crédit Vert',
        description: 'Cliquez ici pour consulter votre score de crédit alternatif.',
        countdown: 8,
      },
      targetRoute: '/credit',
    },
  },

  show_action_plan: {
    id: 'show_action_plan',
    steps: [
      {
        route: '/action-plan',
        selector: '[data-guide-target="action-plan-timeline"]',
        popover: {
          title: 'Votre plan d\'action',
          description: 'Cette timeline regroupe vos actions prioritaires sur 6, 12 et 24 mois pour améliorer votre performance ESG.',
          side: 'bottom',
        },
      },
    ],
    entryStep: {
      selector: '[data-guide-target="sidebar-action-plan-link"]',
      popover: {
        title: 'Plan d\'action',
        description: 'Cliquez ici pour voir votre feuille de route personnalisée.',
        countdown: 8,
      },
      targetRoute: '/action-plan',
    },
  },

  show_dashboard_overview: {
    id: 'show_dashboard_overview',
    steps: [
      {
        route: '/dashboard',
        selector: '[data-guide-target="dashboard-esg-card"]',
        popover: {
          title: 'Synthèse ESG',
          description: 'Un aperçu rapide de votre score ESG et de vos axes d\'amélioration.',
          side: 'bottom',
        },
      },
      {
        selector: '[data-guide-target="dashboard-carbon-card"]',
        popover: {
          title: 'Synthèse Carbone',
          description: 'Votre empreinte carbone résumée avec les catégories principales.',
          side: 'bottom',
        },
      },
      {
        selector: '[data-guide-target="dashboard-credit-card"]',
        popover: {
          title: 'Synthèse Crédit',
          description: 'Votre score de crédit vert et les facteurs clés.',
          side: 'bottom',
        },
      },
      {
        selector: '[data-guide-target="dashboard-financing-card"]',
        popover: {
          title: 'Synthèse Financements',
          description: 'Les opportunités de financement vert identifiées pour votre entreprise.',
          side: 'bottom',
        },
      },
    ],
    entryStep: {
      selector: '[data-guide-target="sidebar-dashboard-link"]',
      popover: {
        title: 'Tableau de bord',
        description: 'Cliquez ici pour accéder à votre tableau de bord complet.',
        countdown: 8,
      },
      targetRoute: '/dashboard',
    },
  },
}
```

### Pattern de test — Registre

```typescript
// frontend/tests/lib/guided-tours/registry.test.ts
import { describe, it, expect } from 'vitest'
import { tourRegistry } from '~/lib/guided-tours/registry'
import type { GuidedTourDefinition } from '~/types/guided-tour'

const EXPECTED_IDS = [
  'show_esg_results',
  'show_carbon_results',
  'show_financing_catalog',
  'show_credit_score',
  'show_action_plan',
  'show_dashboard_overview',
] as const

describe('tourRegistry', () => {
  it('contient exactement 6 parcours', () => {
    expect(Object.keys(tourRegistry)).toHaveLength(6)
  })

  it('contient les 6 ids attendus', () => {
    for (const id of EXPECTED_IDS) {
      expect(tourRegistry[id]).toBeDefined()
    }
  })

  it('chaque id suit la convention show_*', () => {
    for (const key of Object.keys(tourRegistry)) {
      expect(key).toMatch(/^show_[a-z_]+$/)
    }
  })

  it('chaque parcours a un id coherent avec sa cle', () => {
    for (const [key, tour] of Object.entries(tourRegistry)) {
      expect(tour.id).toBe(key)
    }
  })

  it('chaque parcours a au moins un step', () => {
    for (const tour of Object.values(tourRegistry)) {
      expect(tour.steps.length).toBeGreaterThanOrEqual(1)
    }
  })

  it('tous les selectors utilisent [data-guide-target="..."]', () => {
    for (const tour of Object.values(tourRegistry)) {
      for (const step of tour.steps) {
        expect(step.selector).toMatch(/^\[data-guide-target="[a-z0-9-]+"\]$/)
      }
      if (tour.entryStep) {
        expect(tour.entryStep.selector).toMatch(/^\[data-guide-target="[a-z0-9-]+"\]$/)
      }
    }
  })

  it('aucun selector ne commence par . ou #', () => {
    for (const tour of Object.values(tourRegistry)) {
      for (const step of tour.steps) {
        expect(step.selector).not.toMatch(/^[.#]/)
      }
    }
  })

  it('les ids sont uniques', () => {
    const ids = Object.values(tourRegistry).map(t => t.id)
    expect(new Set(ids).size).toBe(ids.length)
  })

  it('un 7eme parcours peut etre ajoute sans erreur (extensibilite)', () => {
    const extended: Record<string, GuidedTourDefinition> = {
      ...tourRegistry,
      show_custom_demo: {
        id: 'show_custom_demo',
        steps: [
          {
            selector: '[data-guide-target="custom-element"]',
            popover: { title: 'Demo', description: 'Test extensibilite' },
          },
        ],
      },
    }
    expect(Object.keys(extended)).toHaveLength(7)
    expect(extended.show_custom_demo.id).toBe('show_custom_demo')
  })
})
```

### Convention des selectors

Regles **strictes** (ADR5, architecture.md Decision 5) :
- Format : `[data-guide-target="[module]-[element]"]` — kebab-case
- JAMAIS de classes CSS (`.xxx`) ou d'IDs (`#xxx`) comme selectors Driver.js
- Les `data-guide-target` correspondants seront ajoutes sur les composants existants dans la Story 4.3
- Convention nommage : `[module]-[element]` ou `module` est le domaine metier (esg, carbon, financing, credit, dashboard, sidebar) et `element` est l'element specifique (score-circle, donut-chart, fund-list, etc.)

### Convention des ids de parcours

- Format : `show_[module]_[page]` en snake_case
- Exemples : `show_esg_results`, `show_carbon_results`, `show_dashboard_overview`
- Ces ids seront envoyes par le tool backend `trigger_guided_tour` (Epic 6) pour declencher le parcours correspondant

### Placeholders dans les textes

Les textes de description contiennent des placeholders au format `{{variable_name}}`. Exemples :
- `{{esg_score}}` — score ESG sur 100
- `{{total_tco2}}` — empreinte carbone totale en tCO2e
- `{{top_category}}` — categorie d'emission principale
- `{{credit_score}}` — score de credit vert sur 100

La logique d'interpolation sera implementee dans `useGuidedTour.ts` (Story 5.1). Dans cette story, les placeholders sont simplement presents dans les textes bruts du registre.

### Note sur le dossier `lib/`

Le dossier `frontend/app/lib/` n'existe pas encore. Il doit etre cree. C'est le bon emplacement selon l'architecture (Decision 5, lignes 649-651) : `lib/guided-tours/registry.ts` pour le registre, `lib/guided-tours/tours/` pour d'eventuels fichiers separes par parcours (optionnel pour l'instant — les 6 parcours tiennent dans un seul fichier).

### Intelligence de la story precedente (4-1)

**Learnings cles de la Story 4.1 :**
- Driver.js ^1.4.0 installe, lazy loading fonctionne via `useDriverLoader.ts` dans `composables/`
- CSS overrides dark mode en place dans `main.css` (`.dark .driver-popover`)
- Pattern de test : `vi.resetModules()` necessaire pour tester du state module-level — pas directement applicable ici car le registre est un objet statique
- 181 tests frontend au dernier commit — zero regression attendue
- Build reussi, Driver.js isole dans un chunk separe
- Convention du projet : named exports (pas de default export)
- Review findings 4-1 : race condition corrigee dans `prefetchDriverJs`, test manquant ajoute — pattern a suivre pour des tests exhaustifs

**Corrections deferees (deferred-work.md) :**
- Pas de `timeout` sur `requestIdleCallback` — non impactant pour cette story
- Couleurs hexadecimales hardcodees en mode clair — non impactant ici (pas de CSS a modifier)

### Commits recents

```
c1a24d0 3-2-injection-de-la-page-courante-dans-les-prompts-et-adaptation-des-reponses: done
d6889b2 3-2-injection-de-la-page-courante-dans-les-prompts-et-adaptation-des-reponses: done
c94a1e2 3-1-transmission-de-la-page-courante-au-backend: done
c489a6c 2-2-mise-a-jour-de-la-navigation-et-des-liens-internes: done
b7314e2 2-1-suppression-de-la-page-chat-et-de-chatpanel: done
```

### Project Structure Notes

- Frontend : Nuxt 4 SPA (`ssr: false`), structure `app/`, composants PascalCase sans prefixe de dossier (`pathPrefix: false`)
- Types : `frontend/app/types/` contient deja 11 fichiers (actionPlan.ts, carbon.ts, company.ts, etc.) — `guided-tour.ts` s'y integre naturellement
- `lib/` : dossier nouveau a creer — l'architecture prevoit `lib/guided-tours/` pour le registre
- Tests : Vitest 3.0, `@vue/test-utils` 2.4, `happy-dom` — les tests du registre n'ont pas besoin de DOM
- Composables : 17 fichiers existants dans `composables/` — `useGuidedTour.ts` (Story 5.1) viendra s'y ajouter
- Pattern : named exports, pas de default export — a suivre pour types et registre

### References

- [Source: _bmad-output/planning-artifacts/epics.md — Epic 4, Story 4.2, lignes 631-670]
- [Source: _bmad-output/planning-artifacts/architecture.md — ADR5 Decision 5 (registre data-guide-target), lignes 377-461]
- [Source: _bmad-output/planning-artifacts/architecture.md — Types guided-tour.ts, lignes 639-643]
- [Source: _bmad-output/planning-artifacts/architecture.md — Registre et conventions, lignes 646-657]
- [Source: _bmad-output/planning-artifacts/architecture.md — Regles d'enforcement, lignes 757-778]
- [Source: _bmad-output/planning-artifacts/prd.md — FR26 (registre extensible), FR28 (ajout sans modification)]
- [Source: _bmad-output/implementation-artifacts/4-1-installation-driverjs-lazy-loading-et-css-dark-mode.md — Completion Notes, Review Findings]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

Aucun probleme rencontre.

### Completion Notes List

- Task 1 : Types TypeScript crees dans `frontend/app/types/guided-tour.ts` — 5 interfaces/types exportes (GuidedTourPopover, GuidedTourStep, GuidedTourEntryStep, GuidedTourDefinition, TourContext, TourState)
- Task 2 : Registre cree dans `frontend/app/lib/guided-tours/registry.ts` — 6 parcours pre-definis avec selectors `[data-guide-target="..."]`, textes francais avec accents, placeholders `{{...}}`
- Task 3 : 9 tests unitaires Vitest — tous passent. Couverture `registry.ts` = 100%
- Task 4 : 191/191 tests passent (zero regression). Typecheck : zero nouvelle erreur. Erreurs pre-existantes (ScoreHistory.vue, useChat.ts, etc.) non liees a cette story.

### Review Findings

- [x] [Review][Patch] Test "aucun selector..." ne verifiait pas `entryStep.selector` [registry.test.ts:54] — corrige
- [x] [Review][Patch] `countdown: 8` hardcode 6 fois — extrait en constante `DEFAULT_ENTRY_COUNTDOWN` [registry.ts]
- [x] [Review][Patch] `tourRegistry` type `Record<string,...>` → adopte `satisfies` pour securite de type [registry.ts:14]
- [x] [Review][Patch] Placeholders manquants dans `show_financing_catalog`, `show_action_plan`, `show_dashboard_overview` — ajoutes [registry.ts]
- [x] [Review][Defer] `countdown` sans borne min/max — validation dans le moteur Story 5.1
- [x] [Review][Defer] `lib/` pas dans auto-import Nuxt — choix d'architecture (import manuel explicite)
- [x] [Review][Defer] `tsconfig.json` etend `.nuxt/tsconfig.json` — setup pre-existant
- [x] [Review][Defer] `route` non contraint — validation croisee dans Story 5.1
- [x] [Review][Defer] `TourContext` sans contrat d'interpolation — Story 5.1

### Change Log

- 2026-04-13 : Implementation complete Story 4.2 — types et registre de parcours guides
- 2026-04-13 : Code review complete — 4 patches appliques, 5 differes, 7 dismisses. 192/192 tests verts.

### File List

| Fichier | Action |
|---------|--------|
| `frontend/app/types/guided-tour.ts` | Nouveau |
| `frontend/app/lib/guided-tours/registry.ts` | Nouveau |
| `frontend/tests/lib/guided-tours/registry.test.ts` | Nouveau |
