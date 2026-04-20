# Story 4.3 : Marquage data-guide-target sur les composants existants

Status: done

## Story

En tant qu'utilisateur,
je veux que les elements importants de l'interface soient identifiables par le systeme de guidage,
afin que l'assistant puisse me les montrer visuellement.

## Acceptance Criteria

1. **AC1 — Sidebar : 6 attributs data-guide-target sur les liens de navigation**
   - **Given** le composant `AppSidebar.vue` avec un `v-for` sur `navItems`
   - **When** le developpeur ajoute un champ `guideTarget` dans chaque objet `navItems` et le bind sur le `<NuxtLink>`
   - **Then** les 6 liens de navigation cibles portent l'attribut `data-guide-target` correspondant :
     - `sidebar-dashboard-link` sur `/dashboard`
     - `sidebar-action-plan-link` sur `/action-plan`
     - `sidebar-esg-link` sur `/esg`
     - `sidebar-carbon-link` sur `/carbon`
     - `sidebar-financing-link` sur `/financing`
     - `sidebar-credit-link` sur `/credit-score`
   - **And** les 4 autres liens (Dossiers, Rapports, Documents, Profil) n'ont PAS de `data-guide-target` (pas de parcours defini pour eux)

2. **AC2 — ESG : 3 attributs data-guide-target sur la page resultats**
   - **Given** la page `pages/esg/results.vue`
   - **When** le developpeur ajoute les attributs
   - **Then** les elements suivants sont marques :
     - `data-guide-target="esg-score-circle"` sur le conteneur du composant `EsgScoreCircle`
     - `data-guide-target="esg-strengths-badges"` sur le conteneur de la section "Points forts"
     - `data-guide-target="esg-recommendations"` sur le conteneur de la section "Recommandations"

3. **AC3 — Carbon : 3 attributs data-guide-target sur la page resultats**
   - **Given** la page `pages/carbon/results.vue`
   - **When** le developpeur ajoute les attributs
   - **Then** les elements suivants sont marques :
     - `data-guide-target="carbon-donut-chart"` sur le conteneur du graphique Doughnut
     - `data-guide-target="carbon-benchmark"` sur le conteneur de la section "Comparaison sectorielle"
     - `data-guide-target="carbon-reduction-plan"` sur le conteneur de la section "Plan de reduction"

4. **AC4 — Financing : 1 attribut data-guide-target sur la page catalogue**
   - **Given** la page `pages/financing/index.vue`
   - **When** le developpeur ajoute l'attribut
   - **Then** `data-guide-target="financing-fund-list"` est place sur le conteneur de la grille de fonds (onglet actif — la liste visible, pas un onglet specifique)

5. **AC5 — Credit : 1 attribut data-guide-target sur la page score**
   - **Given** la page `pages/credit-score/index.vue`
   - **When** le developpeur ajoute l'attribut
   - **Then** `data-guide-target="credit-score-gauge"` est place sur le conteneur du composant `ScoreGauge`

6. **AC6 — Action Plan : 1 attribut data-guide-target sur la page plan**
   - **Given** la page `pages/action-plan/index.vue`
   - **When** le developpeur ajoute l'attribut
   - **Then** `data-guide-target="action-plan-timeline"` est place sur le composant `<Timeline>` (ou son conteneur direct)

7. **AC7 — Dashboard : 4 attributs data-guide-target sur les cartes**
   - **Given** la page `pages/dashboard.vue`
   - **When** le developpeur ajoute les attributs
   - **Then** les cartes suivantes sont marquees :
     - `data-guide-target="dashboard-esg-card"` sur le `<ScoreCard>` ESG
     - `data-guide-target="dashboard-carbon-card"` sur le `<ScoreCard>` Carbone
     - `data-guide-target="dashboard-credit-card"` sur le `<ScoreCard>` Credit
     - `data-guide-target="dashboard-financing-card"` sur le `<FinancingCard>`

8. **AC8 — Coherence registre-DOM : chaque selector du registre a un data-guide-target correspondant**
   - **Given** les 20 selectors definis dans `lib/guided-tours/registry.ts` (13 steps + 6 entrySteps + verification des doublons = 20 uniques)
   - **When** on compare les selectors du registre aux `data-guide-target` ajoutes dans le DOM
   - **Then** chaque `[data-guide-target="xxx"]` du registre a un element HTML correspondant dans les composants/pages modifies

9. **AC9 — Zero regression**
   - **Given** les modifications sont terminees
   - **When** on execute les tests frontend (`npx vitest run`)
   - **Then** zero regression sur les tests existants (192+ tests)
   - **And** les nouveaux tests verifient la presence des attributs dans les composants modifies

## Tasks / Subtasks

- [x] **Task 1 : Ajouter les data-guide-target dans AppSidebar.vue** (AC: 1)
  - [x] 1.1 Ajouter un champ `guideTarget?: string` aux objets du tableau `navItems`
  - [x] 1.2 Renseigner `guideTarget` pour les 6 liens cibles (dashboard, action-plan, esg, carbon, financing, credit-score)
  - [x] 1.3 Binder l'attribut sur le `<NuxtLink>` : `:data-guide-target="item.guideTarget"` (ne rendra pas l'attribut si `undefined`, donc les 4 autres liens sont proteges)

- [x] **Task 2 : Ajouter les data-guide-target dans pages/esg/results.vue** (AC: 2)
  - [x] 2.1 `data-guide-target="esg-score-circle"` sur le `<div class="relative">` entourant `<EsgScoreCircle>`
  - [x] 2.2 `data-guide-target="esg-strengths-badges"` sur le `<div>` conteneur "Points forts"
  - [x] 2.3 `data-guide-target="esg-recommendations"` sur le `<div>` conteneur "Recommandations"

- [x] **Task 3 : Ajouter les data-guide-target dans pages/carbon/results.vue** (AC: 3)
  - [x] 3.1 `data-guide-target="carbon-donut-chart"` sur le `<div>` conteneur du graphique Doughnut
  - [x] 3.2 `data-guide-target="carbon-reduction-plan"` sur le `<div>` conteneur "Plan de reduction"
  - [x] 3.3 `data-guide-target="carbon-benchmark"` sur le `<div>` conteneur "Comparaison sectorielle"

- [x] **Task 4 : Ajouter le data-guide-target dans pages/financing/index.vue** (AC: 4)
  - [x] 4.1 `data-guide-target="financing-fund-list"` sur le conteneur principal de la grille de fonds

- [x] **Task 5 : Ajouter le data-guide-target dans pages/credit-score/index.vue** (AC: 5)
  - [x] 5.1 `data-guide-target="credit-score-gauge"` sur le `<div>` conteneur du `<ScoreGauge>`

- [x] **Task 6 : Ajouter le data-guide-target dans pages/action-plan/index.vue** (AC: 6)
  - [x] 6.1 Attribut ajoute directement sur le composant `<Timeline>` via Vue 3 fallthrough attrs (single root element confirme)

- [x] **Task 7 : Ajouter les data-guide-target dans pages/dashboard.vue** (AC: 7)
  - [x] 7.1 Verifie : ScoreCard, FinancingCard et Timeline ont tous un seul element racine et pas de `inheritAttrs: false` — Option A (fallthrough attrs) utilisee
  - [x] 7.2 `data-guide-target="dashboard-esg-card"` sur ScoreCard ESG
  - [x] 7.3 `data-guide-target="dashboard-carbon-card"` sur ScoreCard Carbone
  - [x] 7.4 `data-guide-target="dashboard-credit-card"` sur ScoreCard Credit
  - [x] 7.5 `data-guide-target="dashboard-financing-card"` sur FinancingCard

- [x] **Task 8 : Tests de coherence registre-DOM** (AC: 8, 9)
  - [x] 8.1 Cree `frontend/tests/components/data-guide-targets.test.ts`
  - [x] 8.2 Test : importe `tourRegistry` et extrait TOUS les selectors (steps + entrySteps)
  - [x] 8.3 Test : verifie que chaque selector respecte la convention `[data-guide-target="xxx"]`
  - [x] 8.4 Test : liste les 19 valeurs attendues et verifie qu'elles sont toutes presentes dans le registre
  - [x] 8.5 Test : monte AppSidebar avec `@vue/test-utils` et verifie la presence des 6 `data-guide-target` sur les liens cibles + absence sur les 4 autres liens

- [x] **Task 9 : Verification finale** (AC: 9)
  - [x] 9.1 `npx vitest run` — 198 tests passent (192 existants + 6 nouveaux), zero regression
  - [x] 9.2 `npx nuxi typecheck` — zero nouvelle erreur de type (7 erreurs pre-existantes non liees a cette story)
  - [x] 9.3 Verification : les attributs `data-guide-target` sont des attributs HTML purs sans impact visuel

## Dev Notes

### Portee de cette story

Cette story est **STRICTEMENT frontend** — aucune modification backend. Elle ajoute UNIQUEMENT des attributs HTML `data-guide-target` sur des elements existants. Aucune modification de logique, style ou comportement.

**Regle fondamentale** : chaque `data-guide-target` ajoute ici DOIT correspondre exactement a un selector dans `tourRegistry` (Story 4.2). Ni plus, ni moins.

### Convention des attributs (ADR5, architecture.md Decision 5)

- Format : `data-guide-target="[module]-[element]"` — **kebab-case**
- JAMAIS de classes CSS (`.xxx`) ou d'IDs (`#xxx`) comme selectors Driver.js
- Les selecteurs dans le registre utilisent `[data-guide-target="xxx"]` — le `data-guide-target="xxx"` dans le HTML correspond a ce format

### Les 20 selectors a couvrir

| # | Selector value | Composant/Page cible | Type |
|---|---------------|----------------------|------|
| 1 | `sidebar-dashboard-link` | `AppSidebar.vue` | entryStep |
| 2 | `sidebar-esg-link` | `AppSidebar.vue` | entryStep |
| 3 | `sidebar-carbon-link` | `AppSidebar.vue` | entryStep |
| 4 | `sidebar-financing-link` | `AppSidebar.vue` | entryStep |
| 5 | `sidebar-credit-link` | `AppSidebar.vue` | entryStep |
| 6 | `sidebar-action-plan-link` | `AppSidebar.vue` | entryStep |
| 7 | `esg-score-circle` | `pages/esg/results.vue` | step |
| 8 | `esg-strengths-badges` | `pages/esg/results.vue` | step |
| 9 | `esg-recommendations` | `pages/esg/results.vue` | step |
| 10 | `carbon-donut-chart` | `pages/carbon/results.vue` | step |
| 11 | `carbon-benchmark` | `pages/carbon/results.vue` | step |
| 12 | `carbon-reduction-plan` | `pages/carbon/results.vue` | step |
| 13 | `financing-fund-list` | `pages/financing/index.vue` | step |
| 14 | `credit-score-gauge` | `pages/credit-score/index.vue` | step |
| 15 | `action-plan-timeline` | `pages/action-plan/index.vue` | step |
| 16 | `dashboard-esg-card` | `pages/dashboard.vue` | step |
| 17 | `dashboard-carbon-card` | `pages/dashboard.vue` | step |
| 18 | `dashboard-credit-card` | `pages/dashboard.vue` | step |
| 19 | `dashboard-financing-card` | `pages/dashboard.vue` | step |
| 20 | *(aucun 20e — les entryStep selectors sont les sidebar-* qui sont deja dans la liste)* | | |

**Total unique : 19 selectors** repartis sur **8 fichiers**.

### Fichiers a modifier

| Fichier | Action | Nb attributs | Detail |
|---------|--------|-------------|--------|
| `frontend/app/components/layout/AppSidebar.vue` | Modifier | 6 | Ajouter `guideTarget` aux navItems + binding `:data-guide-target` |
| `frontend/app/pages/esg/results.vue` | Modifier | 3 | Attributs sur les conteneurs score/forces/recommandations |
| `frontend/app/pages/carbon/results.vue` | Modifier | 3 | Attributs sur les conteneurs donut/benchmark/reduction |
| `frontend/app/pages/financing/index.vue` | Modifier | 1 | Attribut sur le conteneur de la grille de fonds |
| `frontend/app/pages/credit-score/index.vue` | Modifier | 1 | Attribut sur le conteneur du ScoreGauge |
| `frontend/app/pages/action-plan/index.vue` | Modifier | 1 | Attribut sur le Timeline ou son conteneur |
| `frontend/app/pages/dashboard.vue` | Modifier | 4 | Attributs sur les 4 cartes (3 ScoreCard + 1 FinancingCard) |
| `frontend/tests/components/data-guide-targets.test.ts` | Nouveau | — | Tests de coherence registre-DOM |

### Fichiers a NE PAS modifier

- `frontend/app/types/guided-tour.ts` — Types deja crees (Story 4.2)
- `frontend/app/lib/guided-tours/registry.ts` — Registre deja cree (Story 4.2)
- `frontend/tests/lib/guided-tours/registry.test.ts` — Tests registre deja crees (Story 4.2)
- `frontend/app/composables/useDriverLoader.ts` — Loader Driver.js (Story 4.1)
- `frontend/app/composables/useGuidedTour.ts` — N'existe pas encore (Story 5.1)
- `frontend/app/assets/css/main.css` — Pas de CSS a modifier
- `backend/**` — Aucune modification backend

### Approche technique pour AppSidebar.vue

Le composant utilise un `v-for` sur un tableau `navItems`. L'approche recommandee :

```typescript
// Dans le tableau navItems existant, ajouter guideTarget aux items concernes
const navItems = [
  { to: '/dashboard', label: 'Tableau de bord', icon: '...', guideTarget: 'sidebar-dashboard-link' },
  { to: '/action-plan', label: "Plan d'action", icon: '...', guideTarget: 'sidebar-action-plan-link' },
  { to: '/esg', label: 'Evaluation ESG', icon: '...', guideTarget: 'sidebar-esg-link' },
  { to: '/carbon', label: 'Empreinte Carbone', icon: '...', guideTarget: 'sidebar-carbon-link' },
  { to: '/financing', label: 'Financement', icon: '...', guideTarget: 'sidebar-financing-link' },
  { to: '/credit-score', label: 'Credit Vert', icon: '...', guideTarget: 'sidebar-credit-link' },
  // Les items suivants n'ont PAS de guideTarget (pas de parcours defini)
  { to: '/applications', label: 'Dossiers', icon: '...' },
  // ...
]
```

```vue
<!-- Dans le template, ajouter le binding -->
<NuxtLink
  v-for="item in navItems"
  :key="item.to"
  :to="item.to"
  :data-guide-target="item.guideTarget"
  ...
>
```

Vue 3 ne rend pas les attributs dont la valeur est `undefined` — les items sans `guideTarget` n'auront pas l'attribut dans le DOM.

### Approche technique pour les composants enfants (ScoreCard, FinancingCard, Timeline)

Deux options pour ajouter `data-guide-target` sur un composant Vue :

**Option A — Fallthrough attrs (preferee si composant a un seul root element) :**
```vue
<ScoreCard data-guide-target="dashboard-esg-card" label="Score ESG" ... />
```
Vue 3 transmet automatiquement l'attribut au root element du composant enfant. Verifier que `ScoreCard`, `FinancingCard` et `Timeline` ont un seul element racine et n'ont pas `inheritAttrs: false`.

**Option B — Wrapper div (si composant a multiple roots ou inheritAttrs: false) :**
```vue
<div data-guide-target="dashboard-esg-card">
  <ScoreCard label="Score ESG" ... />
</div>
```

**Recommandation : privilegier l'Option A**, verifier `inheritAttrs` dans chaque composant avant implementation.

### Intelligence de la story precedente (4-2)

**Learnings cles de la Story 4.2 :**
- Les 6 parcours sont dans `tourRegistry` avec 19 selectors `[data-guide-target="xxx"]` uniques
- Constante `DEFAULT_ENTRY_COUNTDOWN = 8` extraite — pas impactant ici
- `satisfies Record<string, GuidedTourDefinition>` utilise pour typage — pas impactant ici
- Review findings : test `entryStep.selector` ajoute, placeholders completes — confirme que le registre est complet et stable
- 192 tests frontend au dernier commit — zero regression attendue
- Convention : named exports, pas de default export

**Corrections deferees (deferred-work.md) pertinentes :**
- `lib/` pas dans auto-import Nuxt — imports manuels necessaires pour le registre dans les tests
- `route` non contraint dans `GuidedTourStep` — pas impactant pour cette story (on ne touche pas aux types)

### Commits recents

```
c1a24d0 3-2-injection-de-la-page-courante-dans-les-prompts-et-adaptation-des-reponses: done
d6889b2 3-2-injection-de-la-page-courante-dans-les-prompts-et-adaptation-des-reponses: done
c94a1e2 3-1-transmission-de-la-page-courante-au-backend: done
c489a6c 2-2-mise-a-jour-de-la-navigation-et-des-liens-internes: done
b7314e2 2-1-suppression-de-la-page-chat-et-de-chatpanel: done
```

### Anti-patterns a eviter

1. **NE PAS utiliser de classes CSS** (`.score-circle`) ou d'IDs (`#esg-score`) comme selectors — convention ADR5
2. **NE PAS modifier la logique** des composants — ajout d'attributs HTML UNIQUEMENT
3. **NE PAS ajouter de style** lie aux `data-guide-target` — ces attributs sont invisibles
4. **NE PAS ajouter de `data-guide-target` sur des elements qui n'ont pas de selector dans le registre** — coherence stricte
5. **NE PAS dupliquer de `data-guide-target`** — chaque valeur est unique dans le DOM
6. **NE PAS creer de nouveau composant** — on modifie les composants existants uniquement

### Project Structure Notes

- Frontend : Nuxt 4 SPA (`ssr: false`), structure `app/`, composants PascalCase sans prefixe de dossier (`pathPrefix: false`)
- Tests : Vitest 3.0, `@vue/test-utils` 2.4, `happy-dom`
- `AppSidebar.vue` est dans `components/layout/` — les navItems sont definis directement dans le composant
- Les pages sont dans `pages/` avec routing automatique Nuxt
- Les composants (ScoreCard, FinancingCard, Timeline, EsgScoreCircle, etc.) sont auto-importes par Nuxt

### References

- [Source: _bmad-output/planning-artifacts/epics-019-floating-copilot.md — Epic 4, Story 4.3]
- [Source: _bmad-output/planning-artifacts/architecture-019-floating-copilot.md — ADR5 Decision 5, registre data-guide-target, conventions naming]
- [Source: _bmad-output/implementation-artifacts/4-2-types-et-registre-de-parcours-guides.md — Registre complet, 19 selectors, conventions]
- [Source: frontend/app/lib/guided-tours/registry.ts — Selectors exacts a matcher]
- [Source: frontend/app/components/layout/AppSidebar.vue — Structure v-for navItems]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

Aucun debug necessaire — implementation directe sans blocage.

### Completion Notes List

- 19 attributs `data-guide-target` ajoutes sur 7 fichiers Vue, correspondant exactement aux 19 selectors du `tourRegistry` (Story 4.2)
- AppSidebar : champ `guideTarget` ajoute aux 6 premiers navItems + binding `:data-guide-target="item.guideTarget"` sur le `<NuxtLink>`. Les 4 items sans parcours (Dossiers, Rapports, Documents, Profil) n'ont pas de `guideTarget` — Vue 3 ne rend pas l'attribut si `undefined`
- Pages ESG/Carbon/Financing/Credit/Action-Plan/Dashboard : attributs `data-guide-target` ajoutes sur les conteneurs existants. Pour les composants enfants (ScoreCard, FinancingCard, Timeline), Option A (fallthrough attrs) utilisee apres verification qu'ils ont un seul root element et pas de `inheritAttrs: false`
- 6 nouveaux tests dans `data-guide-targets.test.ts` : coherence registre (19 targets attendus), convention selectors, absence doublons, montage AppSidebar avec verification des 6 targets presents et des 4 liens sans target
- 198 tests au total (192 existants + 6 nouveaux), zero regression
- Typecheck : zero nouvelle erreur (7 erreurs pre-existantes non liees a cette story)

### File List

- `frontend/app/components/layout/AppSidebar.vue` — Modifie (6 guideTarget + binding)
- `frontend/app/pages/esg/results.vue` — Modifie (3 data-guide-target)
- `frontend/app/pages/carbon/results.vue` — Modifie (3 data-guide-target)
- `frontend/app/pages/financing/index.vue` — Modifie (1 data-guide-target)
- `frontend/app/pages/credit-score/index.vue` — Modifie (1 data-guide-target)
- `frontend/app/pages/action-plan/index.vue` — Modifie (1 data-guide-target)
- `frontend/app/pages/dashboard.vue` — Modifie (4 data-guide-target)
- `frontend/tests/components/data-guide-targets.test.ts` — Nouveau (6 tests)

### Review Findings

- [x] [Review][Defer] Route mismatch `show_esg_results` : registre declare `route: '/esg'` mais `esg-score-circle` est sur `/esg/results` — bug du registre (Story 4.2), corriger dans Story 5.1 [frontend/app/lib/guided-tours/registry.ts:22]
- [x] [Review][Defer] 8 elements `data-guide-target` dans des blocs `v-if` (esg-strengths-badges, esg-recommendations, carbon-donut-chart, carbon-benchmark, carbon-reduction-plan, action-plan-timeline, credit-score-gauge, dashboard cards) — le moteur `useGuidedTour` (Story 5.1) devra gerer les elements absents du DOM (skip/attente/fallback) — deferred, pre-existant par design

### Change Log

- 2026-04-13 : Implementation Story 4.3 — 19 attributs data-guide-target ajoutes sur 7 fichiers Vue, 6 tests de coherence registre-DOM, zero regression (198 tests verts)
- 2026-04-13 : Code review Story 4.3 — 1 decision_needed (route mismatch registre), 1 defer (v-if pattern x8), 5 dismissed
