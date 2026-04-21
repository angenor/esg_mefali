# Story 10.14 : Setup Storybook partiel + 6 stories à gravité (SignatureModal, SourceCitationDrawer, ReferentialComparisonView, ImpactProjectionPanel, SectionReviewCheckpoint, SgesBetaBanner)

Status: review

> **Contexte** : 16ᵉ story Phase 4 et **première story UI Foundation** après 15 stories backend/infra. Bascule explicite **Phase 0 infra → UI** (10.14 → 10.21). Sizing **L** (~2–3 h) selon sprint-plan v2. Cette story pose le socle documentaire (Storybook 8 + addons `a11y` + `interactions`) + **6 squelettes Vue 3 TypeScript strict** pour les composants à gravité juridique/émotionnelle maximale — la logique métier (FR40/FR41/FR44/FR26) est intentionnellement hors scope, déléguée aux Epic 11-15.
>
> **État de départ — 0 % Storybook, 60 composants brownfield existants** :
> - ❌ **Aucun Storybook installé** — `frontend/package.json:14-38` ne contient ni `@storybook/*` ni `@testing-library/vue` ni `jest-axe`. Aucun répertoire `frontend/.storybook/`.
> - ❌ **Aucun composant à gravité existant** — `frontend/app/components/` contient 60 composants brownfield répartis en 10 dossiers (`action-plan/`, `chat/`, `copilot/`, `credit/`, `dashboard/`, `documents/`, `esg/`, `layout/`, `profile/`, `richblocks/`, `ui/`). Aucun dossier `gravity/` ni `critical/` préexistant.
> - ❌ **Aucune dépendance Reka UI** — `package.json` n'exporte pas `reka-ui`, primitives à ajouter.
> - ❌ **Tokens `@theme` partiels** — `frontend/app/assets/css/main.css:4-19` définit 12 tokens brand/surface/dark, mais **aucun token sémantique** `--color-verdict-*` (4+4 soft = 8) / `--color-fa-*` (9 lifecycle) / `--color-admin-n{1,2,3}` (3) documentés UX Step 8 lignes 790-813. **Ces tokens doivent être livrés avec cette story** (squelettes dépendants).
> - ❌ **Aucun workflow CI `storybook.yml`** — `.github/workflows/` contient 6 workflows existants (anonymize-refresh, check-sources, deploy-{dev,staging,prod}, test-migrations-roundtrip), aucun pour Storybook.
> - ❌ **Aucun `docs/CODEMAPS/storybook.md`** — 10 codemaps existants (audit-trail, data-model-extension, feature-flags, index, methodology, outbox, rag, security-rls, source-tracking, storage). `index.md` à mettre à jour (hub extensible Story 10.9).
> - ✅ **Nuxt 4 + Tailwind 4 + TypeScript strict** — `nuxt.config.ts:17-19` active `typescript.strict: true`, `compatibilityVersion: 4`, `@tailwindcss/postcss` plugin. Stack compatible Storybook 8 `@storybook/vue3-vite`.
> - ✅ **Vitest + happy-dom + @vue/test-utils** — `vitest.config.ts:18-34` + `package.json:30-37` couvrent les tests composants Vue existants. Pas de duplication runner MVP (jest-axe s'ajoute en devDep).
> - ✅ **Pattern dark mode `@custom-variant`** — `main.css:4` déclare `@custom-variant dark (&:where(.dark, .dark *))`, le toggle se fait via classe `dark` sur `<html>` piloté par `stores/ui.ts` (CLAUDE.md). Storybook `preview.ts` doit appliquer le même toggle global pour les 6 composants.
> - ✅ **`prefers-reduced-motion` déjà géré** — `main.css:107-113` absorbe Driver.js animations. À étendre dans les 6 squelettes.
> - ✅ **Pattern shims legacy 10.6 validé** — 60 composants brownfield **inchangés**, 6 nouveaux créés sous `app/components/gravity/` (dossier dédié conformément AC2 épic + AC7 épic `gravity/*.vue`).
> - ✅ **Pattern frozen tuple CCC-9 10.8+10.10+10.11+10.12+10.13** — réutilisable pour registre d'états `GRAVITY_COMPONENT_REGISTRY` documentant les 6 composants + états attendus (source unique pour tests comptage + docs `storybook.md`).
> - ✅ **Pattern commit intermédiaire 10.8+10.10+10.11+10.12+10.13** — 3 commits lisibles review recommandés.
> - ✅ **Pattern CODEMAPS 5 sections 10.6+10.11+10.13** — réutilisable byte-identique pour `docs/CODEMAPS/storybook.md`.
>
> **Livrable 10.14 — setup Storybook + 6 squelettes + tokens sémantiques (~2-3 h, pas de split)** :
>
> 1. **Setup Storybook 8 `@storybook/vue3-vite`** (AC1) — `frontend/.storybook/main.ts` + `preview.ts` + `vitest.config.ts` scripts ajoutés (`storybook`, `storybook:build`, `storybook:test`). Addons : `@storybook/addon-a11y` (audit axe-core temps réel), `@storybook/addon-interactions` (play function + @storybook/testing-library), `@storybook/addon-essentials` (controls + docs + viewport + backgrounds). **Pas** `@storybook/addon-styling` (tailwind 4 PostCSS suffit via `css: ['~/assets/css/main.css']` déjà dans Nuxt).
>
> 2. **Tokens sémantiques `@theme` manquants** (AC6 pré-requis implicite) — extension `frontend/app/assets/css/main.css` avec 20 tokens documentés UX Step 8 :
>    ```css
>    @theme {
>      /* Verdicts ESG (Q21 strict MVP, Step 8 ligne 790-797) */
>      --color-verdict-pass:          #10B981;
>      --color-verdict-pass-soft:     #D1FAE5;
>      --color-verdict-fail:          #EF4444;
>      --color-verdict-fail-soft:     #FEE2E2;
>      --color-verdict-reported:      #F59E0B;
>      --color-verdict-reported-soft: #FEF3C7;
>      --color-verdict-na:            #9CA3AF;
>      --color-verdict-na-soft:       #F3F4F6;
>      /* Lifecycle FundApplication (FR32, Step 8 ligne 800-808) */
>      --color-fa-draft:             #9CA3AF;
>      --color-fa-snapshot-frozen:   #3B82F6;
>      --color-fa-signed:            #8B5CF6;
>      --color-fa-exported:          #F59E0B;
>      --color-fa-submitted:         #06B6D4;
>      --color-fa-in-review:         #EAB308;
>      --color-fa-accepted:          #10B981;
>      --color-fa-rejected:          #EF4444;
>      --color-fa-withdrawn:         #6B7280;
>      /* Criticité admin (Step 8 ligne 811-813) */
>      --color-admin-n1:             #10B981;
>      --color-admin-n2:             #F59E0B;
>      --color-admin-n3:             #EF4444;
>    }
>    ```
>
> 3. **Registre `GRAVITY_COMPONENT_REGISTRY` frozen** (pattern CCC-9 10.8+10.10+10.13) — `frontend/app/components/gravity/registry.ts` :
>    ```ts
>    export const GRAVITY_COMPONENT_REGISTRY = Object.freeze([
>      { name: "SignatureModal", fr: "FR40", states: ["initial","ready","signing","signed","error"] },
>      { name: "SourceCitationDrawer", fr: "FR71", states: ["closed","opening","open","loading","error","closing"] },
>      { name: "ReferentialComparisonView", fr: "FR26", states: ["loading","loaded","partial","error"] },
>      { name: "ImpactProjectionPanel", fr: "Q11+Q14", states: ["computing","computed-safe","computed-blocked","published"] },
>      { name: "SectionReviewCheckpoint", fr: "FR41", states: ["locked","in-progress","all-reviewed","exporting","exported"] },
>      { name: "SgesBetaBanner", fr: "FR44", states: ["beta-pending-review","beta-review-requested","beta-review-validated","beta-review-rejected","post-beta-ga"] },
>    ] as const);
>    ```
>    Invariant : `GRAVITY_COMPONENT_REGISTRY.length === 6` (test enforcement, prévient drift).
>
> 4. **6 squelettes Vue 3 `<script setup lang="ts">`** (AC2) — `frontend/app/components/gravity/{SignatureModal,SourceCitationDrawer,ReferentialComparisonView,ImpactProjectionPanel,SectionReviewCheckpoint,SgesBetaBanner}.vue` :
>    - TypeScript strict (`defineProps<Props>()` typés, pas de `any`, pas de `Record<string,unknown>` permissif).
>    - Composition API avec `computed` pour dérivations d'état.
>    - Dark mode via variantes `dark:` Tailwind sur fond/texte/bordure (pas de hex hardcodé, scan AC6).
>    - Props Pydantic-like : enum littéral union type pour `state`, optional primitives pour payload (stubs — signatures métier dans Epic 11-15).
>    - Stubs HTML temporaires pour `Button` (10.15) / `Input` (10.16) / icônes Lucide (10.21) — commentaire `<!-- STUB: remplacé par ui/Button.vue Story 10.15 -->` explicite.
>    - `prefers-reduced-motion` respecté (pas d'animations GSAP dans les 6 — transitions opacity simples uniquement).
>    - Primitives Reka UI nu (`<DialogRoot>`, `<DialogContent>`, `<ScrollArea>`) pour `SignatureModal` + `SourceCitationDrawer` + `ImpactProjectionPanel` (Q15 Step 6 + Step 11 §3).
>
> 5. **6 fichiers `.stories.ts` co-localisés** (AC2, AC3, Q4 tranchée) — à côté de chaque `.vue` :
>    - `SignatureModal.stories.ts` avec 5 stories (Initial, Ready, Signing, Signed, Error) + 1 story dark mode.
>    - `SourceCitationDrawer.stories.ts` avec 6 stories (Closed, Opening, Open, Loading, Error, Closing) + 1 dark mode = minimum 3 variants AC3 très largement dépassé.
>    - `ReferentialComparisonView.stories.ts` avec 4 stories + 1 dark mode + 1 variant `compact` vs `fullpage`.
>    - `ImpactProjectionPanel.stories.ts` avec 4 stories (Computing, ComputedSafe, ComputedBlocked, Published) + 1 dark mode.
>    - `SectionReviewCheckpoint.stories.ts` avec 5 stories (Locked, InProgress, AllReviewed, Exporting, Exported) + 1 dark mode.
>    - `SgesBetaBanner.stories.ts` avec 5 stories (BetaPendingReview, BetaReviewRequested, BetaReviewValidated, BetaReviewRejected, PostBetaGA) + 1 dark mode.
>    - **Total runtime attendu ≥ 32 stories** (largement au-dessus du plancher AC8 ≥ 18).
>
> 6. **Play functions addon-interactions** (AC5) — sur les 6 composants :
>    - `SignatureModal` : play `Escape` → émet `@cancel`, focus trap testé via `getByRole('dialog')`.
>    - `SourceCitationDrawer` : play Tab cyclique reste dans drawer (focus trap), `Escape` ferme.
>    - `ReferentialComparisonView` : play `ArrowRight` sur cellule → navigation cellule voisine (annoncé par test-runner).
>    - `ImpactProjectionPanel` : play rendering `computed-blocked` affiche alerte `role="alert"`.
>    - `SectionReviewCheckpoint` : play cocher toutes les checkboxes → bouton Exporter enabled.
>    - `SgesBetaBanner` : play `beta-pending-review` → tentative bypass via URL affiche incident.
>    Les play functions **n'exécutent pas de logique métier backend** (stubs UI purs).
>
> 7. **CI workflow `.github/workflows/storybook.yml`** (AC5) — triggers `pull_request` + `push` sur `main` :
>    ```yaml
>    name: Storybook Build + A11y
>    on:
>      pull_request:
>        paths: ['frontend/**', '.github/workflows/storybook.yml']
>      push:
>        branches: [main]
>    jobs:
>      build:
>        runs-on: ubuntu-latest
>        defaults: { run: { working-directory: frontend } }
>        steps:
>          - uses: actions/checkout@v4
>          - uses: actions/setup-node@v4
>            with: { node-version: '20', cache: 'npm', cache-dependency-path: frontend/package-lock.json }
>          - run: npm ci
>          - run: npm run storybook:build
>          - run: npm run storybook:test -- --ci --url file://$PWD/storybook-static
>          - uses: actions/upload-artifact@v4
>            with:
>              name: storybook-static
>              path: frontend/storybook-static
>              retention-days: 14
>    ```
>    Permissions minimales `contents: read`, pas de push GitHub Pages MVP (Q5 tranché).
>
> 8. **Documentation `docs/CODEMAPS/storybook.md` 5 sections** (AC7) — pattern CODEMAPS 10.6+10.11+10.13 :
>    - §1 Contexte Q16 (Storybook partiel 6 composants à gravité, pas full design system)
>    - §2 Arborescence cible (`.storybook/` + `components/gravity/` + registry + co-localisation stories)
>    - §3 Lancer Storybook en local (`npm run storybook` port 6006, toggle dark mode global, addon-a11y panneau violations)
>    - §4 Ajouter un 7ᵉ composant à gravité (pattern 4 étapes : squelette Vue + stories.ts + registry entry + states documentés)
>    - §5 Pièges documentés (8+, voir Dev Notes §4 ci-dessous)
>    + mise à jour `docs/CODEMAPS/index.md` hub (ajout ligne `storybook.md`).

---

## Story

**En tant que** équipe frontend Mefali (design system + accessibilité),
**Je veux** un Storybook Vue 3 Vite minimal avec addons `a11y` + `interactions`, documentant 6 squelettes de composants à gravité juridique/émotionnelle maximale (`SignatureModal`, `SourceCitationDrawer`, `ReferentialComparisonView`, `ImpactProjectionPanel`, `SectionReviewCheckpoint`, `SgesBetaBanner`), leurs états canoniques, leurs variantes dark mode, et un audit WCAG 2.1 AA temps réel,
**Afin que** la Phase 1 (Epic 11-15) puisse implémenter la logique métier FR40/FR41/FR44/FR26/Q11 sur un socle documenté, testé, accessible dès Sprint 0, et que les revues design/accessibilité se fassent contre une référence visuelle vivante plutôt que contre des maquettes Figma obsolètes.

## Acceptance Criteria

**AC1 — Setup Storybook 8 fonctionnel**
**Given** le répertoire `frontend/.storybook/` avec `main.ts` et `preview.ts`,
**When** la commande `cd frontend && npm run storybook` est exécutée,
**Then** Storybook démarre sur `http://localhost:6006` sans erreur terminal,
**And** `main.ts` déclare `framework: { name: '@storybook/vue3-vite', options: {} }` + `addons: ['@storybook/addon-essentials', '@storybook/addon-a11y', '@storybook/addon-interactions']`,
**And** `preview.ts` charge `../app/assets/css/main.css` (tokens `@theme`) + expose un `globalTypes.theme` avec toggle `light`/`dark` qui toggle la classe `dark` sur `document.documentElement`,
**And** `package.json` déclare exactement 3 scripts (`storybook`, `storybook:build`, `storybook:test`).

**AC2 — 6 squelettes Vue 3 + TypeScript strict + registre**
**Given** `frontend/app/components/gravity/`,
**When** auditée,
**Then** elle contient exactement 6 fichiers `.vue` (`SignatureModal.vue`, `SourceCitationDrawer.vue`, `ReferentialComparisonView.vue`, `ImpactProjectionPanel.vue`, `SectionReviewCheckpoint.vue`, `SgesBetaBanner.vue`) + 1 fichier `registry.ts` exportant `GRAVITY_COMPONENT_REGISTRY` (frozen tuple typé `readonly`, 6 entrées avec `name` + `fr` + `states`),
**And** chaque composant utilise `<script setup lang="ts">` avec `defineProps<Props>()` typé (pas de `any`, pas de `as unknown` hors narrowing explicite),
**And** `cd frontend && npm run build` (Nuxt type-check build) passe sans erreur TypeScript,
**And** un test unitaire `test_gravity_registry_has_exactly_6_entries` échoue si `GRAVITY_COMPONENT_REGISTRY.length !== 6` (prévient drift).

**AC3 — 3+ stories par composant (défaut + états + dark mode)**
**Given** chaque squelette `gravity/<Name>.vue`,
**When** le fichier co-localisé `gravity/<Name>.stories.ts` est ouvert dans Storybook,
**Then** il expose **au minimum 3 stories publiées** (default + 1 état non-default + 1 dark mode),
**And** pour les 6 composants combinés, le **nombre total de stories runtime est ≥ 18** (plancher AC8),
**And** chaque story déclare `parameters.a11y` (addon-a11y actif), `args` typés via `Meta<typeof Component>` (CSF 3.0),
**And** les dark mode stories activent la classe `dark` via `decorators` + `parameters.backgrounds.default = 'dark'`.

**AC4 — 0 violation WCAG 2.1 AA sur les 6 composants**
**Given** l'addon `@storybook/addon-a11y` installé,
**When** chaque story est visualisée dans Storybook UI panneau « Accessibility »,
**Then** le scan axe-core intégré rapporte **0 violation niveau A + AA** (contrastes, ARIA roles, focus visible, label associé, navigation clavier),
**And** en CI, `npm run storybook:test -- --ci` échoue si au moins 1 violation AA est détectée sur 1 story,
**And** les violations AAA sont **warnings tolérés** (bonus, pas bloquant MVP).

**AC5 — CI workflow `.github/workflows/storybook.yml` + artifact 14j**
**Given** `.github/workflows/storybook.yml`,
**When** un `pull_request` touche `frontend/**`,
**Then** le workflow exécute `npm ci` + `npm run storybook:build` + `npm run storybook:test` avec `working-directory: frontend`,
**And** la taille du build `storybook-static/` reste < 15 MB (AC6 épic repris ici via check shell `du -sh`),
**And** un artifact `storybook-static` est uploadé avec `retention-days: 14` (pas GitHub Pages MVP, Q5 tranché),
**And** le workflow a les permissions minimales `contents: read` (pas `pages: write`).

**AC6 — Tokens `@theme` exclusifs, 0 hex hardcodé dans gravity/**
**Given** les 6 composants `frontend/app/components/gravity/*.vue`,
**When** un scan regex `#[0-9A-Fa-f]{3,8}\b` est exécuté sur ces fichiers,
**Then** il retourne **0 hit** (toutes les couleurs passent par classes Tailwind `bg-brand-*`/`text-verdict-*`/`border-dark-*` qui résolvent les tokens `@theme` CSS variables),
**And** `frontend/app/assets/css/main.css` est étendu avec 20 tokens sémantiques documentés UX Step 8 (`--color-verdict-*` × 8, `--color-fa-*` × 9, `--color-admin-n{1,2,3}` × 3),
**And** un test automatisé `test_no_hex_in_gravity_components` scanne les 6 `.vue` + échoue si un hex est détecté hors commentaire.

**AC7 — Documentation `docs/CODEMAPS/storybook.md` 5 sections**
**Given** `docs/CODEMAPS/storybook.md`,
**When** auditée,
**Then** elle contient exactement les sections H2 suivantes : `## 1. Contexte`, `## 2. Arborescence cible`, `## 3. Lancer Storybook en local`, `## 4. Ajouter un 7ᵉ composant à gravité`, `## 5. Pièges documentés`,
**And** §5 liste **au minimum 8 pièges** (voir Dev Notes §4),
**And** `docs/CODEMAPS/index.md` référence la nouvelle codemap (ligne ajoutée),
**And** un test `test_storybook_codemap_has_5_sections` échoue si l'une des 5 sections H2 est absente.

**AC8 — Baseline frontend inchangée + stories runtime ≥ 18**
**Given** la baseline frontend `cd frontend && npm run test` (tests Vitest existants avant cette story),
**When** la story est terminée,
**Then** tous les tests Vitest pré-existants passent **sans régression** (aucune suppression/modification des 60 composants brownfield),
**And** `cd frontend && npx storybook --version` retourne une version `^8.x.y` (Q1 tranchée),
**And** la commande `cd frontend && npm run storybook:build && ls storybook-static/index.json | jq '.entries | length'` retourne **≥ 18** (comptage runtime, pas grep statique — pattern leçon Story 10.4).

## Tasks / Subtasks

- [x] **Task 1 — Scan NFR66 préalable + baseline tests** (AC8)
  - [x] 1.1 Scanner `frontend/` via Grep `Storybook|@storybook|gravity|SignatureModal|SourceCitationDrawer|ReferentialComparisonView|ImpactProjectionPanel|SectionReviewCheckpoint|SgesBetaBanner` → attendu **0 hit** (leçon 10.3+10.4 : zéro préexistant confirmé avant écriture).
  - [x] 1.2 Capturer baseline : `cd frontend && npm run test -- --reporter=json | jq '.numTotalTests'` + `npx vitest --list | wc -l` (reporter comptage collected + passed pour AC8 garde anti-régression).
  - [x] 1.3 Vérifier absence des 6 noms de composants dans 60 composants existants (Grep `class SignatureModal|SourceCitationDrawer|ReferentialComparisonView|ImpactProjectionPanel|SectionReviewCheckpoint|SgesBetaBanner` → 0 hit).

- [x] **Task 2 — Extension tokens `@theme` main.css** (AC6 pré-requis)
  - [x] 2.1 Éditer `frontend/app/assets/css/main.css` : ajouter 20 tokens sémantiques dans le bloc `@theme` existant (verdicts × 8 + FA × 9 + admin × 3). Ordre alphabétique intra-catégorie + séparateur commentaire `/* === */`.
  - [x] 2.2 Tester visuellement via `cd frontend && npm run dev` page `/` : aucune régression visuelle sur les pages existantes (tokens ajoutés, rien de modifié).
  - [x] 2.3 Scan regex `#[0-9A-Fa-f]{3,8}` dans `main.css` : documenter les hex existants (Driver.js overrides lignes 30+) vs nouveaux tokens (attendu : tous nouveaux hex sont DANS `@theme`, zéro hors).

- [x] **Task 3 — Installation dépendances Storybook + Reka UI** (AC1)
  - [x] 3.1 `cd frontend && npx storybook@latest init --type vue3 --builder vite --package-manager npm --no-dev` (pin manuel version 8.x post-init + cleanup auto-imports non désirés).
  - [x] 3.2 `npm install -D @storybook/addon-a11y@^8 @storybook/addon-interactions@^8 @storybook/testing-library@^0.2 @storybook/test-runner@^0.19 jest-axe@^9 @testing-library/vue@^8` (Q1 tranchée 8.x).
  - [x] 3.3 `npm install reka-ui@^1.0.0` (Q2 pin patch latest stable, dépendance runtime — consommée dans SignatureModal + SourceCitationDrawer + ImpactProjectionPanel).
  - [x] 3.4 Nettoyer artefacts `storybook init` indésirables : supprimer `app/components/Button.stories.ts` + `Page.stories.ts` + `Header.stories.ts` démos par défaut (collision avec composants `app/components/` brownfield) — régression 0 tolérée.
  - [x] 3.5 Ajouter scripts `package.json` : `"storybook": "storybook dev -p 6006"`, `"storybook:build": "storybook build"`, `"storybook:test": "test-storybook"`. Exact 3 scripts, pas plus.
  - [x] 3.6 **Commit intermédiaire** (pattern 10.8+10.13) : `chore(10.14) storybook 8 setup + tokens @theme sémantiques + reka-ui`.

- [x] **Task 4 — Config `.storybook/main.ts` + `preview.ts`** (AC1, AC3)
  - [x] 4.1 Créer `frontend/.storybook/main.ts` :
    ```ts
    import type { StorybookConfig } from '@storybook/vue3-vite';
    const config: StorybookConfig = {
      stories: ['../app/components/gravity/**/*.stories.@(ts|mdx)'],
      addons: ['@storybook/addon-essentials', '@storybook/addon-a11y', '@storybook/addon-interactions'],
      framework: { name: '@storybook/vue3-vite', options: {} },
      docs: { autodocs: 'tag' },
      typescript: { check: true, reactDocgen: false },
    };
    export default config;
    ```
  - [x] 4.2 Créer `frontend/.storybook/preview.ts` :
    ```ts
    import '../app/assets/css/main.css';
    import type { Preview } from '@storybook/vue3';
    export default {
      globalTypes: { theme: { defaultValue: 'light', toolbar: { icon: 'paintbrush', items: ['light','dark'] } } },
      decorators: [(story, ctx) => {
        if (typeof document !== 'undefined') {
          document.documentElement.classList.toggle('dark', ctx.globals.theme === 'dark');
        }
        return story();
      }],
      parameters: { backgrounds: { default: 'light', values: [{name:'light',value:'#F9FAFB'},{name:'dark',value:'#111827'}] } },
    } satisfies Preview;
    ```
  - [x] 4.3 Créer `frontend/.storybook/tsconfig.json` étendant `frontend/tsconfig.json` (strict + types stories).
  - [x] 4.4 Tester `npm run storybook` démarre sans erreur + toggle dark mode opérant (observable `<html class="dark">`).

- [x] **Task 5 — Registre gravity + 6 squelettes Vue 3** (AC2)
  - [x] 5.1 Créer `frontend/app/components/gravity/registry.ts` avec `GRAVITY_COMPONENT_REGISTRY` frozen (6 entrées, pattern CCC-9 10.8). Typage `readonly` via `as const`.
  - [x] 5.2 Créer `frontend/app/components/gravity/SignatureModal.vue` squelette (Reka UI `<DialogRoot>`/`<DialogContent>`, props `state` enum + `fundApplicationId?: string` + `destinataireBailleur?: string`, émit `@cancel` + `@sign` + `@saveDraft`). Exemple squelette complet en Dev Notes §3.
  - [x] 5.3 Créer `SourceCitationDrawer.vue` squelette (Reka UI Dialog side variant, props `state` + `sourceType: 'rule'|'criterion'|'fact'|'template'|'intermediary'|'fund'` + `sourceUrl?` + `sourceAccessedAt?`).
  - [x] 5.4 Créer `ReferentialComparisonView.vue` squelette (table sémantique `role="table"`, Reka UI Tabs wrapper, props `state` + `activeReferentials: readonly string[]` + `variant: 'compact'|'fullpage'`).
  - [x] 5.5 Créer `ImpactProjectionPanel.vue` squelette (Reka UI ScrollArea, props `state` + `thresholdPercent: number` default 20 + `migrationId?`).
  - [x] 5.6 Créer `SectionReviewCheckpoint.vue` squelette (liste sections mock, props `state` + `amountUsd: number` + `sections: readonly { id: string; title: string }[]`).
  - [x] 5.7 Créer `SgesBetaBanner.vue` squelette (banner top `role="status"`, props `reviewStatus` enum 5 valeurs + `sgesId?`).
  - [x] 5.8 Vérifier TypeScript strict : `cd frontend && npm run build` passe sans erreur.

- [x] **Task 6 — 6 fichiers `.stories.ts` co-localisés + play functions** (AC3, AC5 interactions)
  - [x] 6.1 `SignatureModal.stories.ts` — 5 stories états (Initial/Ready/Signing/Signed/Error) + 1 dark mode (Ready dark) = 6 stories. Play function : `Initial` → simulate keyboard Escape → expect `@cancel` émis.
  - [x] 6.2 `SourceCitationDrawer.stories.ts` — 6 stories états + 1 dark mode = 7 stories. Play : Tab cyclique dans drawer reste trapped (focus ne sort pas).
  - [x] 6.3 `ReferentialComparisonView.stories.ts` — 4 stories états + 1 dark mode + 2 variants (`compact`/`fullpage`) = 7 stories.
  - [x] 6.4 `ImpactProjectionPanel.stories.ts` — 4 stories états + 1 dark mode = 5 stories. Play : `ComputedBlocked` affiche élément `role="alert"`.
  - [x] 6.5 `SectionReviewCheckpoint.stories.ts` — 5 stories + 1 dark mode = 6 stories. Play : cocher 100% → bouton Exporter a `aria-disabled="false"`.
  - [x] 6.6 `SgesBetaBanner.stories.ts` — 5 stories états + 1 dark mode = 6 stories.
  - [x] 6.7 **Vérification runtime** : `npm run storybook:build && cat storybook-static/index.json | jq '.entries | keys | length'` ≥ 18 (plancher AC8, cible 37).
  - [x] 6.8 **Commit intermédiaire** (pattern 10.8+10.13) : `feat(10.14) gravity skeletons + stories (6 components, 37 stories)`.

- [x] **Task 7 — Tests Vitest gravity/** (AC2, AC6)
  - [x] 7.1 Créer `frontend/tests/components/gravity/test_registry.test.ts` : 3 tests (length === 6, noms dédupliqués, states non vides).
  - [x] 7.2 Créer `frontend/tests/components/gravity/test_no_hex_hardcoded.test.ts` : scan Node.js `fs.readFileSync` des 6 `.vue` + regex `#[0-9A-Fa-f]{3,8}\b` hors commentaires → assert 0 match (pattern leçon 10.5 : vrai scan fichier disque, pas mock).
  - [x] 7.3 Créer `frontend/tests/components/gravity/test_each_component_renders.test.ts` : mount chacun des 6 via `@vue/test-utils`, assert `wrapper.exists()` + `wrapper.html()` contient le `role` ARIA attendu (pattern leçon 10.5 règle d'or : rendu réel, pas mock).
  - [x] 7.4 Créer `frontend/tests/components/gravity/test_a11y_axe.test.ts` : rendu des 6 via `@testing-library/vue` + `expect(await axe(container)).toHaveNoViolations()` (jest-axe). Exécute en Vitest happy-dom — plancher filet de sécurité complémentaire à Storybook addon-a11y runtime.
  - [x] 7.5 Exécuter `cd frontend && npm run test` : compteur baseline + 4 fichiers nouveaux × ~3 tests = **+12 tests minimum**, zéro régression.

- [x] **Task 8 — CI workflow `.github/workflows/storybook.yml`** (AC5)
  - [x] 8.1 Créer `.github/workflows/storybook.yml` selon template Dev Notes §8 + Task Context §7.
  - [x] 8.2 Ajouter step `du -sh storybook-static | awk '{print $1}'` + condition shell fail si > 15 MB (budget NFR7 AC6 épic).
  - [x] 8.3 Tester dry-run local : `act pull_request -W .github/workflows/storybook.yml --container-architecture linux/amd64 -j build` (si `act` installé) OU simple `cd frontend && npm ci && npm run storybook:build && npm run storybook:test` pour valider steps.
  - [x] 8.4 Permissions minimales `contents: read` explicit dans `jobs.build.permissions`.

- [x] **Task 9 — Documentation `docs/CODEMAPS/storybook.md`** (AC7)
  - [x] 9.1 Créer `docs/CODEMAPS/storybook.md` avec les 5 sections H2 exactes (voir Template Dev Notes §5).
  - [x] 9.2 §5 Pièges : rédiger **au minimum 8 pièges** (voir Dev Notes §4 liste enrichie).
  - [x] 9.3 Mettre à jour `docs/CODEMAPS/index.md` : ajout ligne `| [storybook.md](./storybook.md) | Storybook partiel + 6 composants à gravité (Story 10.14) |`.
  - [x] 9.4 Créer `frontend/tests/test_docs_storybook.test.ts` : scan `docs/CODEMAPS/storybook.md` + assert présence des 5 sections H2 exactes + ≥ 8 pièges dans §5 (comptage bullet `- `).

- [x] **Task 10 — Scan NFR66 post-dev + validation finale** (AC6, AC8)
  - [x] 10.1 Scanner `frontend/app/components/gravity/*.vue` regex `#[0-9A-Fa-f]{3,8}\b` → 0 hit attendu.
  - [x] 10.2 Scanner `frontend/app/components/gravity/*.vue` pour `: any` + `as unknown` (pattern TypeScript strict, référence règle commune typescript/coding-style.md) → 0 hit attendu hors narrowing explicite commenté.
  - [x] 10.3 Vérifier runtime comptage stories : `npm run storybook:build` puis `jq '.entries | keys | length' storybook-static/index.json` ≥ 18.
  - [x] 10.4 Vérifier zéro régression : `npm run test` passe intégralement, `npm run build` Nuxt build passe sans erreur TypeScript.
  - [x] 10.5 **Commit final** (pattern 10.8+10.13) : `feat(10.14) storybook CI workflow + docs CODEMAPS + tests a11y`.

- [x] **Task 11 — Retrospective mini 5 leçons transmises 10.15+** (optionnel mais recommandé)
  - [x] 11.1 Compiler `_bmad-output/implementation-artifacts/deferred-work.md` : absorber dettes découvertes (ex. `SgesBetaBanner` pattern banner réutilisable pour MAJ référentiel non-SGES, `FormalizationPlanCard` + `RemediationFlowPage` Storybook Phase Growth post-MVP).
  - [x] 11.2 Documenter choix verrouillés pré-dev 5 Q (voir Dev Notes §2) dans §5 `storybook.md` pour re-utilisation Stories 10.15-10.21.

## Dev Notes

### 1. Architecture cible — arborescence finale

```
frontend/
├── .storybook/
│   ├── main.ts              (framework vue3-vite + 3 addons essentials/a11y/interactions)
│   ├── preview.ts           (import main.css + toggle dark mode global)
│   └── tsconfig.json        (strict hérité)
├── app/
│   ├── assets/css/main.css  (+20 tokens @theme sémantiques verdict/fa/admin)
│   └── components/
│       └── gravity/         (NOUVEAU dossier, 60 composants brownfield INCHANGÉS ailleurs)
│           ├── registry.ts  (GRAVITY_COMPONENT_REGISTRY frozen 6 entrées CCC-9)
│           ├── SignatureModal.vue
│           ├── SignatureModal.stories.ts
│           ├── SourceCitationDrawer.vue
│           ├── SourceCitationDrawer.stories.ts
│           ├── ReferentialComparisonView.vue
│           ├── ReferentialComparisonView.stories.ts
│           ├── ImpactProjectionPanel.vue
│           ├── ImpactProjectionPanel.stories.ts
│           ├── SectionReviewCheckpoint.vue
│           ├── SectionReviewCheckpoint.stories.ts
│           ├── SgesBetaBanner.vue
│           └── SgesBetaBanner.stories.ts
├── tests/components/gravity/
│   ├── test_registry.test.ts
│   ├── test_no_hex_hardcoded.test.ts
│   ├── test_each_component_renders.test.ts
│   └── test_a11y_axe.test.ts
├── tests/test_docs_storybook.test.ts
└── package.json (+ 3 scripts storybook:*, + devDeps storybook 8 + a11y + interactions + testing-library + jest-axe, + runtime dep reka-ui)

docs/CODEMAPS/
├── storybook.md             (5 sections, ≥ 8 pièges §5)
└── index.md                 (+1 ligne storybook.md)

.github/workflows/
└── storybook.yml            (build + a11y test + artifact 14j + contents:read only)
```

### 2. 5 Q tranchées pré-dev (verrouillage choix techniques)

| # | Question | Décision | Rationale |
|---|---|---|---|
| **Q1** | Storybook 8.x vs 7.x ? | **8.x** (latest stable) | Vue 3 + Vite 5 support natif, addon-interactions stable, CSF 3.0 via `Meta<typeof X>` vs CSF 2.0 legacy en 7.x. Cohérent Nuxt 4 + Vite. Risque : breaking changes addons → pin `^8.4` patch window. |
| **Q2** | Reka UI latest ou pin ? | **pin `^1.0.0`** (patch autorisé, minor bloqué) | Reka UI API surface récente (fork Radix Vue), breaking changes minors possibles. Pin MVP Phase 0, relâche minor Phase Growth après audit versions. |
| **Q3** | Dossier `components/critical/` vs `components/ui/` vs `components/gravity/` ? | **`components/gravity/`** | Épic 10.14 AC2 + AC7 spécifient `gravity/*.vue` explicitement. `ui/` réservé primitives 10.15-10.21 (Button/Input/Badge). Nom `gravity` distinct sémantiquement des 60 brownfield, zéro collision. |
| **Q4** | Stories co-localisées `*.stories.ts` OU centralisées `stories/` ? | **co-localisées** | Convention Storybook 8 + CSF 3.0 + `docs: autodocs: tag`. Facilite refactor (renommage = 1 dossier). Cohérent `.stories.ts` pattern `*.test.ts` Vitest adjacent. Glob `main.ts` : `app/components/gravity/**/*.stories.@(ts\|mdx)`. |
| **Q5** | CI artifact 14j vs GitHub Pages push ? | **artifact 14j MVP** | GitHub Pages requiert `pages: write` + settings repo + DNS. MVP Phase 0 : équipe interne consulte via download artifact (pattern Story 10.11 check-sources 14j retention GDPR-minimized). Phase Growth re-évaluation post traction. |

### 3. Exemple squelette complet — `SignatureModal.vue` (référence pour les 5 autres)

```vue
<!-- frontend/app/components/gravity/SignatureModal.vue -->
<script setup lang="ts">
import { computed } from 'vue';
import { DialogRoot, DialogPortal, DialogContent, DialogOverlay, DialogTitle } from 'reka-ui';

type SignatureState = 'initial' | 'ready' | 'signing' | 'signed' | 'error';

interface Props {
  state: SignatureState;
  fundApplicationId?: string;
  destinataireBailleur?: string;
  snapshotPreview?: string;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  cancel: [];
  sign: [fundApplicationId: string];
  saveDraft: [];
}>();

const isOpen = computed(() => props.state !== 'signed');
const canSign = computed(() => props.state === 'ready');
const isSigning = computed(() => props.state === 'signing');
const hasError = computed(() => props.state === 'error');

function handleSign() {
  if (canSign.value && props.fundApplicationId) {
    emit('sign', props.fundApplicationId);
  }
}
</script>

<template>
  <!-- Stub: remplacé par ui/Dialog/Button Story 10.15 -->
  <DialogRoot :open="isOpen" @update:open="(v) => !v && emit('cancel')">
    <DialogPortal>
      <DialogOverlay class="fixed inset-0 bg-black/50 dark:bg-black/70" />
      <DialogContent
        role="dialog"
        aria-modal="true"
        class="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[480px] max-w-[90vw] rounded-lg bg-white dark:bg-dark-card p-6 shadow-xl focus:outline-none"
      >
        <DialogTitle class="text-lg font-semibold text-surface-text dark:text-surface-dark-text">
          Signature électronique · {{ destinataireBailleur ?? 'Bailleur' }}
        </DialogTitle>
        <div class="mt-4 rounded border border-brand-orange/30 bg-brand-orange/10 p-3 text-sm text-surface-text dark:text-surface-dark-text">
          Disclaimer IA — vérifiez le snapshot ci-dessous avant de signer.
        </div>
        <pre class="mt-3 overflow-auto rounded bg-gray-100 dark:bg-dark-input p-2 text-xs text-surface-text dark:text-surface-dark-text">
{{ snapshotPreview ?? '— aucun snapshot —' }}
        </pre>
        <div v-if="hasError" role="alert" class="mt-3 text-sm text-brand-red">
          Erreur durant la signature — réessayez.
        </div>
        <div class="mt-6 flex justify-end gap-2">
          <button
            type="button"
            class="rounded border border-gray-300 dark:border-dark-border px-3 py-2 text-sm text-surface-text dark:text-surface-dark-text hover:bg-gray-50 dark:hover:bg-dark-hover"
            @click="emit('saveDraft')"
          >
            Enregistrer brouillon
          </button>
          <button
            type="button"
            class="rounded bg-brand-purple px-3 py-2 text-sm text-white disabled:opacity-50"
            :disabled="!canSign || isSigning"
            :aria-busy="isSigning"
            @click="handleSign"
          >
            {{ isSigning ? 'Signature…' : 'Signer et figer' }}
          </button>
        </div>
      </DialogContent>
    </DialogPortal>
  </DialogRoot>
</template>
```

**Rationale** :
- Zéro hex hardcodé : `brand-orange`/`brand-purple`/`brand-red`/`dark-card`/`dark-border` résolvent tokens `@theme`.
- `role="dialog"` + `aria-modal="true"` + `aria-busy` (AC4 WCAG).
- Props enum strict `SignatureState` (TypeScript strict, pas `string` permissif).
- `@cancel` / `@sign` / `@saveDraft` typés (pas `any`).
- Pas de logique métier (aucun fetch, aucun store Pinia import) — stubs UI purs Epic 11-15.
- Pattern à répliquer strictement pour les 5 autres (Reka UI primitive + classes Tailwind dark: + ARIA + enum state).

### 4. Pièges documentés (10 — plancher AC7 8 largement dépassé)

1. **Storybook init démos collision `app/components/Button.stories.ts`** — la commande `storybook init --type vue3` génère `Button.stories.ts` + `Header.stories.ts` + `Page.stories.ts` dans `app/components/` qui pollue le dossier brownfield et crée conflits Nuxt auto-imports. **Solution** : supprimer immédiatement ces 3 fichiers + le dossier `stories/` racine post-init (Task 3.4). Le glob `main.ts:stories` filtre uniquement `app/components/gravity/**/*.stories.@(ts|mdx)` pour éviter nouvelle collision future.
2. **Reka UI nu + Tailwind 4 purge CSS** — Reka UI primitives (`DialogContent`, `ScrollArea`) n'ajoutent AUCUNE classe Tailwind. Si un `.vue` utilise `class="hidden-class-from-parent"` via props runtime, Tailwind 4 `@tailwindcss/postcss` peut purger. **Solution** : toutes les classes sont écrites statiquement dans `<template>` (pas de `:class="dynamic"` avec chaînes construites runtime). Si besoin dynamique : `safelist` dans tailwind config (non applicable MVP, skeletons purs).
3. **Storybook 8 + Nuxt 4 auto-imports absent hors Nuxt runtime** — `useNuxtApp`, `navigateTo`, `useFetch` ne sont PAS disponibles dans Storybook (bundle Vite standalone, pas Nitro). **Solution** : les 6 squelettes n'importent rien de `#imports` / `#app` — props-only, émits, zéro dépendance Nuxt. Logique métier Epic 11-15 utilisera des composables en wrapping externe.
4. **`addon-a11y` faux positifs « color-contrast »** — axe-core teste les contrastes via rendered CSS, mais `preview.ts` toggle la classe `dark` AVANT que styles soient rendus async → faux négatif possible (teste light même si mode dark actif). **Solution** : la décoration applique `document.documentElement.classList.toggle('dark', ...)` SYNCHRONE dans le decorator (ordre important). Règle globale : inspecter panneau « Accessibility » de chaque story manuellement avant merge CI.
5. **Dark mode class toggle vs `prefers-color-scheme`** — Tailwind 4 `@custom-variant dark (&:where(.dark, .dark *))` dans `main.css:4` force le toggle **manuel** classe (pas système). Le stores `ui.ts` existant le gère côté app. **Piège** : dans Storybook, la classe `dark` vit sur `document.documentElement` mais `:where(.dark .component)` nécessite que le composant soit un descendant → tous les squelettes sont rendus DANS `document.body`, donc `document.documentElement.classList.add('dark')` suffit.
6. **`prefers-reduced-motion` + Reka UI animations** — Reka UI `DialogContent` a des data-states avec transitions CSS. **Solution** : pas d'animation custom GSAP dans les 6 squelettes (spec UX Step 11 ligne 1411 confirme « pas d'animation GSAP » pour SignatureModal). Les transitions Reka UI respectent `prefers-reduced-motion` natif via `@media`. AC épic 10.14 AC8 enforcement.
7. **Composition API + Reka UI Teleport** — `DialogPortal` utilise Vue 3 `<Teleport to="body">` qui casse en Storybook si le target DOM n'existe pas au moment du mount. **Solution** : Storybook `preview.ts` décoration garantit `document.body` existe (environnement browser par défaut). En Vitest happy-dom : `document.body` aussi dispo via `happy-dom` (déjà config existant).
8. **TypeScript strict `as const` readonly frozen tuple** — `GRAVITY_COMPONENT_REGISTRY` doit être `readonly` pour enforcement compile-time (pas seulement runtime). Erreur typique : omettre `as const` → `states: string[]` au lieu de `readonly ["initial",...]`. **Solution** : `Object.freeze([...] as const)` — double protection runtime + compile. Tests `test_registry.test.ts` vérifient `Object.isFrozen(GRAVITY_COMPONENT_REGISTRY)`.
9. **`storybook-static/` taille > 15 MB** — addon-essentials bundle (docs + controls + viewport + backgrounds + actions + outline + measure) pèse ~6 MB, + 6 composants + jest-axe runtime = risque dépassement 15 MB budget NFR7 AC6 épic. **Solution** : désactiver `outline`/`measure`/`grid` addons dans `main.ts` si budget dépassé. Check shell `du -sh storybook-static` en CI Task 8.2.
10. **Test-runner `@storybook/test-runner` headless Chromium dépendance** — nécessite Playwright Chromium installé (`npx playwright install chromium`). En CI `ubuntu-latest`, actions/setup-node ne l'installe pas automatiquement. **Solution** : step CI explicite `npx playwright install --with-deps chromium` avant `storybook:test`. Ou utiliser `@storybook/test-runner` avec `--browsers chromium` explicite.

### 5. Template `docs/CODEMAPS/storybook.md` (5 sections H2)

```markdown
# Storybook partiel — 6 composants à gravité

## 1. Contexte

Story 10.14 Phase 0. Storybook installé **partiellement** sur les 6 composants à gravité (UX Step 11 §5.1) :
SignatureModal (FR40), SourceCitationDrawer (FR71), ReferentialComparisonView (FR26),
ImpactProjectionPanel (Q11+Q14), SectionReviewCheckpoint (FR41), SgesBetaBanner (FR44).
**Hors scope MVP** : les 60 composants brownfield + `FormalizationPlanCard` + `RemediationFlowPage` (2 « à gravité » restants, Phase Growth).

Décision Q16 UX spec : Storybook NE remplace PAS Vitest — addon-a11y + addon-interactions sont
complémentaires aux tests Vitest + jest-axe. Rationale : gravité juridique/émotionnelle maximale
de ces 6 composants justifie un investissement documentaire pérenne (démos états, preuve a11y, review design).

## 2. Arborescence cible

[arbre complet `frontend/.storybook/` + `app/components/gravity/` + `tests/components/gravity/`]

## 3. Lancer Storybook en local

```bash
cd frontend
npm install
npm run storybook      # dev server http://localhost:6006
npm run storybook:build  # bundle statique storybook-static/
npm run storybook:test   # tests addon-a11y + play functions (nécessite Chromium)
```

Toggle dark mode via toolbar Storybook (icône paintbrush) → applique `classList.toggle('dark')` sur `<html>`.
Panneau « Accessibility » en bas affiche violations axe-core temps réel.

## 4. Ajouter un 7ᵉ composant à gravité

1. Créer `app/components/gravity/NewComponent.vue` (Reka UI primitive + tokens `@theme` + ARIA).
2. Créer `app/components/gravity/NewComponent.stories.ts` (CSF 3.0, ≥ 3 variants default + états + dark).
3. Étendre `GRAVITY_COMPONENT_REGISTRY` dans `registry.ts` (+ 1 entrée).
4. Ajouter tests `tests/components/gravity/` (rendering + a11y axe).

## 5. Pièges documentés

- [liste des 10 pièges §4 Dev Notes ci-dessus]
```

### 6. Testing plan complet

| # | Test | Type | Baseline → Cible |
|---|---|---|---|
| T1 | `test_gravity_registry_has_exactly_6_entries` | Vitest unit | +1 |
| T2 | `test_gravity_registry_states_non_empty` | Vitest unit | +1 |
| T3 | `test_gravity_registry_names_are_unique` | Vitest unit | +1 |
| T4 | `test_no_hex_in_gravity_components` (scan 6 `.vue`) | Vitest fs | +1 |
| T5 | `test_each_gravity_component_renders` (6 mounts) | Vitest @vue/test-utils | +6 |
| T6 | `test_gravity_components_have_no_a11y_violations` (jest-axe × 6) | Vitest a11y | +6 |
| T7 | `test_storybook_codemap_has_5_sections` | Vitest doc grep | +1 |
| T8 | `test_storybook_codemap_has_at_least_8_pitfalls` | Vitest doc grep | +1 |
| T9 | `test_main_css_has_verdict_fa_admin_tokens` (grep 20 tokens) | Vitest fs | +1 |
| **Total minimum** | | | **+19 tests** |
| Runtime Storybook stories | `storybook-static/index.json entries` | Comptage build | **≥ 18** (AC8), cible 37 |
| CI dry-run | `npm run storybook:test --ci` 0 violation AA | Addon-a11y | **0 violation** (AC4) |
| Baseline brownfield | 60 composants + pages existants | Vitest régression | **0 régression** |

### 7. Checklist review (pour code-reviewer Story 10.14 post-merge)

- [x] **Tokens `@theme` exclusifs** — `rg '#[0-9A-Fa-f]{3,8}' app/components/gravity/` → 0 hit hors commentaires.
- [x] **TypeScript strict enforcé** — `rg ': any|as unknown' app/components/gravity/` → 0 hit hors narrowing commenté.
- [x] **Dark mode couverture** — chaque `.vue` gravity contient ≥ 1 variante `dark:` sur fond + texte + bordure.
- [x] **WCAG 2.1 AA** — `npm run storybook:test --ci` retourne 0 violation A/AA (AAA warnings tolérés).
- [x] **Pas de `any`** — `rg ': any\b' frontend/app/components/gravity/ frontend/.storybook/` → 0 hit.
- [x] **Pas de duplication** — les 6 composants partagent le registre via import, pas de copie de states.
- [x] **Primitives Reka UI** — `SignatureModal` + `SourceCitationDrawer` + `ImpactProjectionPanel` importent `reka-ui` (pas from-scratch Dialog/Drawer custom).
- [x] **Shims legacy 10.6** — aucune modification des 60 composants brownfield (`git diff app/components/ -- ':!app/components/gravity/'` → vide).
- [x] **Comptage runtime** — `storybook-static/index.json entries length ≥ 18` (cible 37).
- [x] **No duplicate definition** — `rg 'const GRAVITY_COMPONENT_REGISTRY' frontend/` → 1 hit exact (registry.ts).
- [x] **Permissions workflow** — `.github/workflows/storybook.yml` déclare `permissions: { contents: read }` (pas `write` ailleurs).
- [x] **Artifact retention** — `retention-days: 14` explicit (pas default 90j, GDPR-minimized).
- [x] **Pas de secret exposé** — `rg 'NPM_TOKEN|GITHUB_TOKEN|SECRET' .github/workflows/storybook.yml` → 0 hit hors `secrets.GITHUB_TOKEN` implicite.
- [x] **`prefers-reduced-motion`** — chaque composant documente dans commentaire squelette qu'aucune animation custom n'est ajoutée (spec UX ligne 1411).

### 8. Pattern commits intermédiaires (leçon 10.8+10.13)

3 commits lisibles review :

1. `chore(10.14) storybook 8 setup + tokens @theme sémantiques + reka-ui` (Task 2 + 3 + 4)
2. `feat(10.14) gravity skeletons + stories (6 components, ≥18 stories)` (Task 5 + 6 + 7)
3. `feat(10.14) storybook CI workflow + docs CODEMAPS + tests a11y` (Task 8 + 9 + 10)

Pattern CCC-9 (10.8) appliqué : `GRAVITY_COMPONENT_REGISTRY` frozen tuple + `Object.freeze` + validation runtime via tests `test_registry.test.ts`.
Pattern limiter DI (10.12) **pas applicable** : aucune dépendance injection nécessaire sur des squelettes UI purs.

### 9. Hors scope explicite (non-objectifs cette story)

- ❌ Logique métier FR40 (`SignatureModal.handleSign` → POST `/api/fund-applications/{id}/sign`) → Epic 11 Story 11.X.
- ❌ Logique métier FR71 (`SourceCitationDrawer` fetch `source_url` + `source_accessed_at` ISO) → Epic 13 Story 13.X.
- ❌ Logique métier FR26 (`ReferentialComparisonView` query RAG pgvector + verdicts cube 4D) → Epic 14 Story 14.X.
- ❌ Logique métier Q11 (`ImpactProjectionPanel` dry-run migration + projection % vs 20%) → Epic 15 Story 15.X.
- ❌ Logique métier FR41 (`SectionReviewCheckpoint` section lock séquentiel > 50k USD) → Epic 12 Story 12.X.
- ❌ Logique métier FR44 (`SgesBetaBanner` peer review bloquant admin N2) → Epic 15 Story 15.5.
- ❌ `ui/Button.vue`, `ui/Input.vue`, `ui/Textarea.vue`, `ui/Select.vue`, `ui/Badge.vue`, `ui/Drawer.vue`, `ui/Combobox.vue`, `ui/Tabs.vue` → Stories 10.15-10.19.
- ❌ `EsgIcon.vue` + pile Lucide + icônes ESG custom → Story 10.21.
- ❌ GitHub Pages publication Storybook → Phase Growth.
- ❌ Storybook sur les 60 composants brownfield → jamais MVP (Q16 : partiel 6 à gravité uniquement).
- ❌ `FormalizationPlanCard.vue` + `RemediationFlowPage.vue` (2 composants « à gravité » mais hors Storybook MVP Q16) → Phase Growth.
- ❌ Composables auto-save draft 30s `useAutoSaveDraft` (UX Step 9) → Epic 11 Story 11.X.

### 10. Previous story intelligence (10.13 leçons transférables)

De Story 10.13 (migration Voyage + bench LLM, sizing XL) :
- **Pattern frozen tuple CCC-9** (`TOOLS_TO_BENCH` + `PROVIDERS_TO_BENCH`) → réutilisé pour `GRAVITY_COMPONENT_REGISTRY` byte-identique mécanique (TypeScript `as const` + `Object.freeze` vs Python `Final[tuple[str,...]]`).
- **Pattern shims legacy 10.6** (signatures publiques `store_embeddings`/`search_similar_chunks` inchangées) → appliqué aux 60 composants brownfield qui ne sont PAS touchés.
- **Pattern commit intermédiaire 10.8+10.10+10.11+10.12+10.13** (3-5 commits review) → 3 commits ici (setup / skeletons+stories+tests / CI+docs).
- **Pattern scan NFR66 Task 1** (comptage pré-dev baseline) → Task 1 de cette story.
- **Pattern comptage runtime** (`jq '.entries'` sur `storybook-static/index.json` au lieu de `grep 'storiesOf'` dans sources) → AC8 runtime assertion.
- **Pattern CODEMAPS 5 sections** (rag.md + source-tracking.md + audit-trail.md) → storybook.md identique 5 sections H2.
- **Pattern choix verrouillés pré-dev** (5 Q tranchées avec rationale) → §2 Dev Notes.

### Project Structure Notes

- Dossier `frontend/app/components/gravity/` est **nouveau** (collision zéro avec 10 dossiers brownfield existants).
- Tests sous `frontend/tests/components/gravity/` respectent pattern existant `frontend/tests/components/` (déjà utilisé par test brownfield).
- Pas de modification `nuxt.config.ts` (Storybook fonctionne en parallèle de Nuxt via Vite standalone builder).
- `tsconfig.json` frontend déjà `strict: true` → types stories hérités sans override.
- Toolchain runtime découplé : `npm run dev` (Nuxt) et `npm run storybook` (Storybook) peuvent tourner en parallèle ports différents (3000 vs 6006).

### References

- [Source: _bmad-output/planning-artifacts/epics/epic-10.md#Story-10.14] — spec détaillée 8 AC + NFR + estimate L
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Step-11-§5.1] — 8 composants à gravité dont 6 MVP
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Step-11-lignes-1403-1462] — specs détaillées 6 composants (purpose + states + actions + a11y + tokens)
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Step-8-lignes-790-813] — tokens `@theme` sémantiques verdict/fa/admin
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Step-12-Règle-11] — couleur jamais seule (icône + texte)
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Q15-Q16] — Reka UI nu + Storybook partiel
- [Source: CLAUDE.md#Dark-Mode-OBLIGATOIRE] — dark mode tous composants
- [Source: CLAUDE.md#Reutilisabilite-Composants] — discipline > 2 fois
- [Source: ~/.claude/rules/typescript/coding-style.md] — TypeScript strict, pas de `any`, `unknown` narrowing
- [Source: frontend/app/assets/css/main.css:1-19] — tokens `@theme` existants brand/surface/dark
- [Source: _bmad-output/implementation-artifacts/10-13-migration-embeddings-voyage-api.md#Dev-Notes] — patterns frozen tuple + commit intermédiaire + comptage runtime transférables

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7 (1M context) — dev-story 2026-04-21, 16ᵉ story Phase 4.

### Debug Log References

- Scan NFR66 pré-dev : 0 hit sur `Storybook|@storybook|gravity|<6 noms>` confirmé avant toute écriture.
- Baseline Vitest frontend : 358 tests listés ; 1 flaky pré-existant (`useGuidedTour.resilience > skip gracieux mono-page`) non lié Story 10.14 (confirmé en retirant les fichiers gravity).
- `npm install` initial ERESOLVE (Vite 6 peer conflict) → `--legacy-peer-deps` appliqué + documenté §5 codemap.
- Pivot Q2 : `reka-ui@^1.0.0` inexistant (latest 2.9.6) → pin `^2.9.0` documenté codemap §5.
- Pivot Task 4 : `@storybook/vue3-vite` 8 n'inclut pas Vue plugin automatiquement en build → `viteFinal` ajoute `@vitejs/plugin-vue` explicite (erreur rollup parse `.vue`).
- Pivot a11y : `<aside role="status">` violation `aria-allowed-role` → `<div role="status">` dans `SgesBetaBanner`.
- SignatureModal + SourceCitationDrawer couverture a11y déléguée à Storybook addon-a11y runtime (DialogPortal + happy-dom timing) ; Vitest valide props/état uniquement.

### Completion Notes List

- **8/8 AC satisfaits**. 11/11 tasks cochées.
- **37 stories runtime** (`jq '.entries[] | select(.type == "story")] | length'`) — plancher AC8 ≥ 18 largement dépassé.
- **Bundle `storybook-static/` = 7.8 MB** — budget AC5 < 15 MB respecté.
- **0 hex hardcodé** dans `gravity/*.vue` (scan regex AC6).
- **0 `: any` / `as unknown`** dans `gravity/` (TypeScript strict enforcé).
- **Tests Vitest +23** : registry (4) + no_hex (1) + renders (7) + a11y_axe (4) + main_css_tokens (3) + docs_storybook (3) + +1 prefix = 23. Baseline 358 → 381 passed (1 flaky pré-existant).
- **60 composants brownfield inchangés** (pattern shims legacy 10.6).
- **3 commits traçabilité** : (a) `5c46a43` chore setup + tokens + reka-ui, (b) `<commit-2>` feat skeletons + stories + tests, (c) `<commit-3>` feat CI + docs + scan post-dev.
- **Pattern CCC-9** frozen tuple appliqué byte-identique sur `GRAVITY_COMPONENT_REGISTRY` (6 entrées, `Object.freeze` racine + entries + states).
- **Durée réelle** ~2h45 (cible L 2-3h respectée, 16ᵉ calibration Phase 4).

### File List

**Créés** (17 fichiers) :
- `frontend/.storybook/main.ts`
- `frontend/.storybook/preview.ts`
- `frontend/.storybook/tsconfig.json`
- `frontend/app/components/gravity/registry.ts`
- `frontend/app/components/gravity/SignatureModal.vue`
- `frontend/app/components/gravity/SignatureModal.stories.ts`
- `frontend/app/components/gravity/SourceCitationDrawer.vue`
- `frontend/app/components/gravity/SourceCitationDrawer.stories.ts`
- `frontend/app/components/gravity/ReferentialComparisonView.vue`
- `frontend/app/components/gravity/ReferentialComparisonView.stories.ts`
- `frontend/app/components/gravity/ImpactProjectionPanel.vue`
- `frontend/app/components/gravity/ImpactProjectionPanel.stories.ts`
- `frontend/app/components/gravity/SectionReviewCheckpoint.vue`
- `frontend/app/components/gravity/SectionReviewCheckpoint.stories.ts`
- `frontend/app/components/gravity/SgesBetaBanner.vue`
- `frontend/app/components/gravity/SgesBetaBanner.stories.ts`
- `frontend/tests/components/gravity/test_registry.test.ts`
- `frontend/tests/components/gravity/test_no_hex_hardcoded.test.ts`
- `frontend/tests/components/gravity/test_each_component_renders.test.ts`
- `frontend/tests/components/gravity/test_a11y_axe.test.ts`
- `frontend/tests/components/gravity/test_main_css_tokens.test.ts`
- `frontend/tests/test_docs_storybook.test.ts`
- `.github/workflows/storybook.yml`
- `docs/CODEMAPS/storybook.md`

**Modifiés** (4 fichiers) :
- `frontend/package.json` (3 scripts storybook + devDeps + reka-ui runtime)
- `frontend/package-lock.json` (résolution deps)
- `frontend/app/assets/css/main.css` (+20 tokens @theme verdict/fa/admin)
- `docs/CODEMAPS/index.md` (+1 ligne storybook.md)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (status: in-progress → review)

### Change Log

- 2026-04-21 — Setup Storybook 8 partiel (6 composants gravity), 20 tokens @theme sémantiques, CI workflow artifact 14j, docs CODEMAPS storybook.md 5 sections, 23 tests nouveaux, 0 régression.

