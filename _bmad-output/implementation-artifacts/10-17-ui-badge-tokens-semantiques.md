# Story 10.17 : `ui/Badge.vue` — tokens sémantiques (verdicts ESG + lifecycle FA + criticité admin)

Status: review

> **Contexte** : 19ᵉ story Phase 4 et **3ᵉ primitive `ui/`** après Button 10.15 + Input/Textarea/Select 10.16. Sizing **S** (~1 h) selon sprint-plan v2. Cette story livre la primitive unique `Badge.vue` qui unifie les indicateurs d'état visuels transversaux : (a) 4 verdicts ESG `PASS`/`FAIL`/`REPORTED`/`N/A` (Q21 UX Step 8), (b) 9 états lifecycle `FundApplication` (FR32), (c) 3 niveaux de criticité admin `N1`/`N2`/`N3` (arbitrage Q11 Mariam). La Règle 11 UX « Couleur jamais seule porteuse d'information » est enforcée par un **icône obligatoire + texte obligatoire + token couleur** (3 signaux redondants).
>
> **État de départ — tokens sémantiques déjà livrés 10.14, 3 primitives `ui/` fondation stable** :
> - ✅ **Tokens `@theme` verdict/fa/admin livrés Story 10.14** — `frontend/app/assets/css/main.css:30-57` : 8 tokens verdict (4 solid + 4 soft) + 9 tokens lifecycle FA + 3 tokens admin. **Aucune modification main.css nécessaire** (consommation pure). Le darken 10.15 ne concerne que `brand-green/red` (CTA Button), les verdicts restent à leurs valeurs Q21 d'origine.
> - ✅ **`verdict-reported = #D97706` (amber-600)** — contraste 4,69:1 ✓ AA sur blanc (choix délibéré au lieu de `#F59E0B` amber-500 = 2,58:1 ❌ AA documenté §4 piège #21). Éviter toute tentation de « matcher `brand-orange #F59E0B` » pour cohérence visuelle : la séparation brand/verdict est intentionnelle (Q21).
> - ❌ **Aucun `ui/Badge.vue` préexistant** — `frontend/app/components/ui/` contient 5 composants (Button.vue 10.15 + Input/Textarea/Select.vue 10.16 + FullscreenModal.vue + ToastNotification.vue brownfield) + `registry.ts`. **Grep `Badge` dans `app/components/ui/` → 0 hit**. Pas de collision.
> - ⚠️ **2 composants brownfield utilisant déjà une classe "badge" inline** — `frontend/app/components/notifications/NotificationBadge.vue` (counter rouge non-lu header) + `frontend/app/components/dashboard/*Badge*.vue` (ComplianceBadge, FundApplicationLifecycleBadge cibles futures). **Hors scope migration** (Phase 1 Epic 11-15), documenté §9.
> - ❌ **Aucune icône Lucide installée** — Story 10.21 installera `lucide-vue-next`. **Pivot MVP** : icônes via SVG inline stubs commentés `<!-- STUB: remplacé par Lucide {Icon} Story 10.21 -->` dans `Badge.stories.ts` (le composant lui-même expose slot `#icon`, les stubs vivent dans les stories). Le composant fonctionne **sans** lucide-vue-next — zéro dépendance bloquante.
> - ✅ **Pattern registry CCC-9 frozen tuple** — `ui/registry.ts` déjà étendu 2 fois (Button 10.15 + Input/Form 10.16). Extension byte-identique pour `VERDICT_STATES` (4) + `LIFECYCLE_STATES` (9) + `ADMIN_CRITICALITIES` (3) + `BADGE_SIZES` (3).
> - ✅ **Pattern compile-time enforcement `.test-d.ts`** — livré 10.15 HIGH-1 (Button.test-d.ts) + 10.16 (Input/Textarea/Select.test-d.ts). `vitest.config.ts typecheck.include: ['tests/**/*.test-d.ts']` déjà actif. Réutilisable byte-identique pour `Badge.test-d.ts`.
> - ✅ **Pattern darken tokens AA 10.15** — aucune action requise ici (les verdicts utilisent déjà `#059669` / `#DC2626` / `#D97706` tous AA 4,5:1+ sur blanc). **Vigilance Check List §7** : ne JAMAIS utiliser `bg-brand-orange` pour variante `verdict-reported` (piège #21).
> - ✅ **Pattern exception dark: seuil 10.15 MEDIUM-2** — pour une primitive simple comme Badge (pas de slot complexe, pas de plusieurs zones visuelles), le seuil « ≥ 6 dark: » s'applique par **type de variante** (verdict, lifecycle, admin) et non par composant total. Justifié §7 checklist.
> - ✅ **Pattern leçons méthodologiques post-10.16** :
>   - **Pattern A (H-3 Select)** : tester l'effet observable DOM (`selectedOptions`, `classList`, `aria-*`) pas le state interne du composant. Capitaliser proactivement Badge : assert `wrapper.find('span').classes()` + `attributes('aria-label')`, PAS `wrapper.vm.variant`.
>   - **Pattern B (M-3 Storybook count)** : **vérifier le count réel runtime via `jq '.entries | length' storybook-static/index.json` AVANT mise à jour des Completion Notes**. Pas d'estimation a priori. Les nombres CSF exports ≠ nombres docs auto-générées ; fixer la métrique (exports uniquement).
> - ✅ **Règles d'or validées 18 leçons cumulées** : tests DOM réels Vitest + play Storybook, TS strict 0 any union discriminée, scan NFR66 pré-dev, no duplication, shims legacy, choix verrouillés pré-dev, commit intermédiaire × 2, CCC-9 frozen, Storybook co-localisation, darken tokens AA, compile-time enforcement `.test-d.ts`, exception dark: seuil, pattern describedBy aligné (H-1 10.16, non applicable Badge), IME composition (H-2 10.16, non applicable Badge affichage pur), binding natif multiple (H-3 10.16, non applicable Badge), type coercion string (H-4 10.16, non applicable Badge sans input).
> - ✅ **Dépendance épic `depends_on: [10.21]` non bloquante** — `depends_on` déclare une dépendance logique (Lucide icons) mais **Story 10.17 livre les stubs SVG inline** → pas de blocage d'ordonnancement sprint. Le remplacement Lucide intervient en Story 10.21 (migration mécanique slot content seulement).
>
> **Livrable 10.17 — `ui/Badge.vue` + stories + tests + docs + registry extension (~1 h)** :
>
> 1. **Extension `ui/registry.ts`** (pattern CCC-9) — ajouter 4 frozen tuples :
>    ```ts
>    export const VERDICT_STATES = Object.freeze(['pass', 'fail', 'reported', 'na'] as const);
>    export const LIFECYCLE_STATES = Object.freeze([
>      'draft', 'snapshot_frozen', 'signed', 'exported',
>      'submitted', 'in_review', 'accepted', 'rejected', 'withdrawn',
>    ] as const);
>    export const ADMIN_CRITICALITIES = Object.freeze(['n1', 'n2', 'n3'] as const);
>    export const BADGE_SIZES = Object.freeze(['sm', 'md', 'lg'] as const);
>    export type VerdictState = (typeof VERDICT_STATES)[number];
>    export type LifecycleState = (typeof LIFECYCLE_STATES)[number];
>    export type AdminCriticality = (typeof ADMIN_CRITICALITIES)[number];
>    export type BadgeSize = (typeof BADGE_SIZES)[number];
>    ```
>    Invariants : lengths 4/9/3/3 · `Object.isFrozen` · `new Set().size === length` (déduplication).
>
> 2. **Composant `frontend/app/components/ui/Badge.vue`** (AC1-AC9) — Vue 3 `<script setup lang="ts">`, native `<span>` (affichage pur, pas de rôle interactif — anti-pattern clickable documenté §4 piège #24), slots `#icon` (obligatoire) + `#default` (label obligatoire), union discriminée `variant` × `state` compile-time (verdict/lifecycle/admin), tokens `@theme` exclusivement (scan 0 hex), dark mode ≥ 6 par variante, `role="status"` + `aria-label` composé.
>
> 3. **`frontend/app/components/ui/Badge.stories.ts` co-localisée** (AC10) — CSF 3.0 avec stubs SVG Lucide inline par état :
>    - Verdict (4 states × 3 sizes = 12) + ShowcaseGrid verdict + ConditionalPass (italique AC3 FR40)
>    - Lifecycle (9 states × 1 size md = 9) + ShowcaseGrid lifecycle + DarkMode lifecycle
>    - Admin (3 states × 2 sizes sm+md = 6) + ShowcaseGrid admin
>    - **Total exports CSF attendu** : 12 + 2 + 1 + 9 + 2 + 6 + 1 = **33 stories mini** (≥ 30 plancher plausible).
>    - **Vérification runtime OBLIGATOIRE** (pattern B 10.16 M-3) : `jq '.entries | keys | length' storybook-static/index.json` **AVANT Completion Notes** — consigner le chiffre exact, PAS d'estimation.
>
> 4. **Tests Vitest `frontend/tests/components/ui/`** (AC9) — 4 fichiers :
>    - `test_badge_registry.test.ts` : lengths frozen dedup (4 assertions × 4 tuples = ≥ 12 tests).
>    - `test_badge_variants.test.ts` : 4 verdict × 3 sizes + 9 lifecycle × md + 3 admin × md = 24 mounts, assertions classes tokens présentes + `aria-label` + `role="status"` (pattern A 10.16 H-3 : assertions DOM pas state).
>    - `test_badge_a11y.test.ts` : vitest-axe × 4 verdict × 2 sizes (sm+md) + 9 lifecycle (md) + 3 admin (md) = 20 audits `toHaveNoViolations()`.
>    - `test_no_hex_hardcoded_badge.test.ts` : scan `Badge.vue` + `Badge.stories.ts` → 0 hit (pattern 10.15 byte-identique).
>    - `Badge.test-d.ts` : ≥ 12 assertions `@ts-expect-error` union discriminée (invalide : `{ variant: 'verdict', state: 'draft' }`, `{ variant: 'lifecycle', state: 'n1' }`, etc. — combinatoire cross-variant).
>
> 5. **Documentation `docs/CODEMAPS/ui-primitives.md` §3.4 Badge + pièges cumulés ≥ 26** (AC12) — extension codemap existante :
>    - §3.4 Badge : 4 exemples Vue (verdict PASS + verdict PASS italique conditionnel + lifecycle signed + admin N2) + exemple union discriminée TS compile-time.
>    - §5 Pièges : 20 existants → **ajouter 6+ pièges Badge** (#21 à #26) = **26 pièges cumulés** (cible AC12 ≥ 20 largement dépassée).
>    - §6 A11y : ajouter ligne tableau contraste `verdict-reported #D97706 on white = 4,69:1 ✅` (L-4 codereview 10.16 cleanup).
>
> 6. **Scan NFR66 post-dev** (AC2, AC9) : `rg '#[0-9A-Fa-f]{3,8}' Badge.vue Badge.stories.ts` → 0 hit · `rg ': any\b|as unknown' Badge.vue` → 0 hit · vitest baseline 460 → ≥ 476 (+16 minimum) · typecheck 26 → ≥ 38 (+12 minimum).

---

## Story

**En tant que** équipe frontend Mefali (design system + accessibilité PME persona mobile + admin Mariam arbitrage N1/N2/N3),
**Je veux** un composant `frontend/app/components/ui/Badge.vue` typé strict avec union discriminée `variant × state` couvrant les **3 familles sémantiques** du produit — (a) 4 verdicts ESG (`pass`/`fail`/`reported`/`na`) pour `ComplianceBadge` + `ScoreGauge`, (b) 9 états lifecycle `FundApplication` (`draft`/`snapshot_frozen`/`signed`/`exported`/`submitted`/`in_review`/`accepted`/`rejected`/`withdrawn`) pour `FundApplicationLifecycleBadge` + sidebar compacte, (c) 3 niveaux criticité admin (`n1`/`n2`/`n3`) pour `AdminCatalogueEditor` + `PeerReviewPanel` — chaque variante combinant **3 signaux redondants obligatoires** (icône Lucide stub Phase 0 + token couleur `@theme` + label texte français), WCAG 2.1 AA contraste ≥ 4,5:1 dark + light, dark mode ≥ 6 variantes `dark:` par famille, compile-time enforcement `.test-d.ts` bloquant les combinaisons invalides cross-variant, 3 tailles `sm`/`md`/`lg` adaptées au contexte inline/dashboard,
**Afin que** la Règle 11 UX « Couleur jamais seule porteuse d'information » soit enforcée dès Phase 0 pour les utilisateurs daltoniens ou sous mode monochrome, que les trois familles d'états produit (ESG conformité · FA lifecycle · admin criticité) partagent une API + un visuel cohérents, et que les migrations Phase 1 des badges brownfield (`NotificationBadge.vue`, `ComplianceBadge`, `FundApplicationLifecycleBadge`) soient mécaniques et safe.

## Acceptance Criteria

**AC1 — Signature TypeScript strict + union discriminée `variant × state`**
**Given** `frontend/app/components/ui/Badge.vue`,
**When** auditée,
**Then** elle expose `defineProps<BadgeProps>()` où `BadgeProps` est une **union discriminée** sur la propriété `variant` :
```ts
type BadgePropsBase = { size?: BadgeSize };
type BadgeProps =
  | (BadgePropsBase & { variant: 'verdict'; state: VerdictState; conditional?: boolean })
  | (BadgePropsBase & { variant: 'lifecycle'; state: LifecycleState })
  | (BadgePropsBase & { variant: 'admin'; state: AdminCriticality });
```
**And** aucune `any` / `as unknown` dans `Badge.vue` (`rg ': any\b|as unknown' frontend/app/components/ui/Badge.vue` → 0 hit),
**And** `cd frontend && npm run build` (Nuxt type-check) passe sans erreur,
**And** le fichier `frontend/tests/components/ui/Badge.test-d.ts` contient **≥ 12 assertions `@ts-expect-error`** vérifiant que les combinaisons invalides (ex. `{ variant: 'verdict', state: 'draft' }`, `{ variant: 'admin', state: 'pass' }`, `{ variant: 'lifecycle', state: 'n1' }`, `{ variant: 'verdict', state: 'pass', conditional: 'yes' }`) ne compilent PAS,
**And** `npm run test:typecheck` (baseline 26 post-10.16) retourne **≥ 38 assertions typecheck** (+12 minimum).

**AC2 — Registry CCC-9 frozen tuple × 4 extensions**
**Given** `frontend/app/components/ui/registry.ts`,
**When** auditée,
**Then** elle contient **4 nouveaux exports** :
- `VERDICT_STATES` (length `=== 4`, valeurs `'pass'` / `'fail'` / `'reported'` / `'na'`),
- `LIFECYCLE_STATES` (length `=== 9`, valeurs exhaustives FR32),
- `ADMIN_CRITICALITIES` (length `=== 3`, valeurs `'n1'` / `'n2'` / `'n3'`),
- `BADGE_SIZES` (length `=== 3`, valeurs `'sm'` / `'md'` / `'lg'`),

**And** tous les 4 tuples satisfont `Object.isFrozen(tuple) === true`,
**And** tous les 4 tuples sont dédoublonnés (`new Set(tuple).size === tuple.length`),
**And** les 4 types dérivés `VerdictState` / `LifecycleState` / `AdminCriticality` / `BadgeSize` sont exportés via `typeof TUPLE[number]`,
**And** les exports **préexistants** 10.15/10.16 (`BUTTON_VARIANTS`, `BUTTON_SIZES`, `INPUT_TYPES`, `FORM_SIZES`, `TEXTAREA_DEFAULT_MAX_LENGTH`) sont **inchangés byte-identique** (`git diff` restreint aux ajouts).

**AC3 — 3 signaux redondants obligatoires (Règle 11 UX Step 12 enforcement)**
**Given** chaque variante rendue (verdict + lifecycle + admin),
**When** le DOM est inspecté,
**Then** **3 signaux sémantiques distincts** sont présents simultanément :
1. **Couleur** via classe Tailwind résolvant token `--color-verdict-*` / `--color-fa-*` / `--color-admin-*` (scan `#[0-9A-Fa-f]` → 0 hit dans `Badge.vue`),
2. **Icône** via slot `#icon` — **render function** du composant retourne une erreur runtime `console.error` si `slots.icon` est absent (defense-in-depth AC4),
3. **Label texte français** via slot `#default` — emit `console.warn` si slot default vide/absent,

**And** un test Vitest `test_badge_variants.test.ts` vérifie pour **chaque** variante que `wrapper.find('[data-testid="badge-icon-slot"]').exists() === true` + `wrapper.find('[data-testid="badge-label-slot"]').text().length > 0` + `wrapper.find('span').classes()` contient au moins une classe `bg-verdict-*` / `bg-fa-*` / `bg-admin-*`,
**And** un test « Règle 11 enforcement » vérifie que rendre `<Badge variant="verdict" state="pass" />` **sans slots** émet **2 warnings** (`console.error` icon manquant + `console.warn` label manquant).

**AC4 — Verdict `PASS` conditionnel italique (FR40 + Q21 clarification Lot 4)**
**Given** `<Badge variant="verdict" state="pass" :conditional="true">Validé</Badge>`,
**When** rendu,
**Then** le composant applique la classe `italic` sur le wrapper ET prépend le texte « (conditionnel) » après le slot label **ou** applique uniquement `italic` si le consommateur fournit déjà le texte complet (choix verrouillé Q3 ci-dessous),
**And** `aria-label` inclut le mot « conditionnel » : `aria-label="Verdict Validé (conditionnel)"`,
**And** `conditional` prop est rejetée compile-time sur `variant !== 'verdict'` (union discriminée AC1),
**And** un test `test_badge_variants.test.ts` case `verdict-pass-conditional` assert `classes().includes('italic') === true` + `aria-label` contient `conditionnel`.

**AC5 — 3 sizes `sm`/`md`/`lg` avec hauteurs adaptées affichage inline**
**Given** les 3 sizes `sm` / `md` / `lg`,
**When** rendues,
**Then** elles respectent les hauteurs suivantes (adaptées au contexte **non-cliquable** inline — Q4 verrouillée) :
- `sm` (compact inline dans table/cell) : `text-xs min-h-[20px] px-1.5 py-0.5 gap-1` + icône `h-3 w-3`,
- `md` (default row/sidebar) : `text-sm min-h-[24px] px-2 py-0.5 gap-1` + icône `h-3.5 w-3.5`,
- `lg` (dashboard/header) : `text-base min-h-[32px] px-3 py-1 gap-1.5` + icône `h-4 w-4`,

**And** **AUCUNE size ne respecte la règle touch 44 px** car Badge est un élément d'**affichage pur non-interactif** (pas de `@click`, pas de `role="button"`, pas de `tabindex`) — piège #24 documenté §4 codemap,
**And** les icônes injectées via slot `#icon` doivent matcher ces tailles (documenté §3.4 codemap + piège #22).

**AC6 — Tokens `@theme` exclusifs, 0 hex hardcodé, contraste WCAG 2.1 AA**
**Given** le composant + les stories,
**When** scan regex `#[0-9A-Fa-f]{3,8}\b` exécuté sur `frontend/app/components/ui/Badge.vue` + `Badge.stories.ts`,
**Then** il retourne **0 hit** (toutes les couleurs via tokens `@theme`),
**And** les variantes utilisent **exactement** les mappings suivants :
- **Verdict** : fond soft + texte/bordure solid (contraste texte/fond AA préservé) :
  - `pass` : `bg-verdict-pass-soft text-verdict-pass` (contraste 4,89:1 ✅ AA — emerald-900 sur emerald-100) — `#D1FAE5` + `#059669`,
  - `fail` : `bg-verdict-fail-soft text-verdict-fail` (4,83:1 ✅ AA — red-600 sur red-100) — `#FEE2E2` + `#DC2626`,
  - `reported` : `bg-verdict-reported-soft text-verdict-reported` (4,69:1 ✅ AA — amber-600 sur amber-100) — `#FEF3C7` + `#D97706`,
  - `na` : `bg-verdict-na-soft text-verdict-na` — `#F3F4F6` + `#6B7280`,
- **Lifecycle FA** : pattern `bg-fa-<state>/10 text-fa-<state>` (fond à 10% opacité Tailwind + texte solide) pour les 9 états,
- **Admin** : `bg-admin-n1/10 text-admin-n1` / `bg-admin-n2/10 text-admin-n2` / `bg-admin-n3/10 text-admin-n3`,

**And** un test `test_no_hex_hardcoded_badge.test.ts` échoue si un hex est détecté hors commentaire,
**And** **AUCUN usage** de `bg-brand-orange` / `bg-brand-green` / `bg-brand-red` pour les variantes sémantiques (séparation Q21 — piège #21 codemap).

**AC7 — Dark mode ≥ 6 `dark:` par famille variante (seuil primitive spécifique)**
**Given** la classe `dark` appliquée sur `<html>`,
**When** chaque famille de variantes est rendue en mode sombre,
**Then** le fichier `Badge.vue` contient :
- **≥ 6 occurrences `dark:`** liées aux **verdicts** (fond soft dark + texte solide dark pour les 4 états ≥ 2×4 = 8 attendues min),
- **≥ 6 occurrences `dark:`** liées aux **lifecycles** (via opacité Tailwind `/10` qui reste valide dark, avec `dark:bg-fa-*/15` OU `dark:text-fa-*/90` selon besoin contraste),
- **≥ 6 occurrences `dark:`** liées aux **admin** (3 états × 2 axes fond + texte = 6 attendues),
- **Total ≥ 21 `dark:` classes** (plancher AC6 story spec),

**And** contraste texte/fond dark mode ≥ 4,5:1 (WCAG 1.4.3 AA) validé par **2 audits vitest-axe en contexte dark** (mount avec `document.documentElement.classList.add('dark')`),
**And** **aucune inflation artificielle** (pattern 10.15 MEDIUM-2 exception) — les `dark:` sont rattachées à des axes visuels réels (fond + texte minimum), pas ajoutées pour atteindre un seuil synthétique.

**AC8 — A11y WCAG 2.1 AA : `role="status"` + `aria-label` composé + 0 violation vitest-axe**
**Given** chaque variante rendue,
**When** auditée,
**Then** l'élément racine `<span>` porte :
- `role="status"` (région ARIA live-polite implicite) pour les 3 familles,
- `aria-label` composé en français : `"Verdict {state} {conditional?}"` / `"Statut {lifecycle label FR}"` / `"Criticité admin {N1|N2|N3}"`,
  - Exemples : `aria-label="Verdict Non conforme"`, `aria-label="Statut Signé"`, `aria-label="Criticité admin N2"`,
- **slot `#icon`** porte `aria-hidden="true"` sur son wrapper (icône décorative, l'`aria-label` du span parent véhicule la sémantique),

**And** un test `test_badge_a11y.test.ts` audite via `vitest-axe` **20 configurations** (4 verdict × 2 sizes sm+md + 9 lifecycle md + 3 admin md + 2 dark mode) → **0 violation WCAG 2.1 AA** (règle `color-contrast` désactivée en happy-dom : calcul manuel validé §6 codemap + DEF-10.15-4 runtime Storybook).

**AC9 — Tests Vitest ≥ 16 nouveaux + baseline 460 → ≥ 476**
**Given** `frontend/tests/components/ui/test_badge_*.test.ts` (4 fichiers + 1 `.test-d.ts`),
**When** `cd frontend && npm run test` exécuté,
**Then** minimum **16 tests runtime nouveaux verts** répartis :
1. `test_badge_registry.test.ts` : length × 4 tuples + `Object.isFrozen` × 4 + dedup × 4 = **12 tests**,
2. `test_badge_variants.test.ts` : rendu verdict × 4 + lifecycle × 9 + admin × 3 + `aria-label` formatting × 3 familles + conditional italic = **≥ 20 tests**,
3. `test_badge_a11y.test.ts` : vitest-axe × 20 audits = **20 assertions `toHaveNoViolations()`**,
4. `test_no_hex_hardcoded_badge.test.ts` : scan Badge.vue + Badge.stories.ts = **2 tests**,

**And** baseline 460 tests (post-10.16) → **≥ 476 passed** (+16 minimum, cible réaliste ≥ 54 avec 3 fichiers),
**And** typecheck baseline 26 (post-10.16) → **≥ 38 assertions** (`Badge.test-d.ts` ≥ 12),
**And** **0 régression** sur tests préexistants.

**AC10 — Storybook CSF 3.0 co-localisée — comptage runtime OBLIGATOIRE pré-Completion**
**Given** `frontend/app/components/ui/Badge.stories.ts` co-localisée,
**When** `npm run storybook:build` exécuté,
**Then** `jq '.entries | keys | length' storybook-static/index.json` est **capturé et consigné littéralement** dans la section « Completion Notes » du story file **AVANT** tout claim de complétude (pattern B 10.16 M-3 méthodologique),
**And** ce comptage doit être **≥ 30 stories nouvelles Badge** (plancher conservateur couvrant 12 verdict + 9 lifecycle + 6 admin + 3 ShowcaseGrid + 3 bonus DarkMode/ConditionalPass/ComposedExamples),
**And** le glob `frontend/.storybook/main.ts` reste **inchangé** (déjà étendu `gravity/ + ui/` en Story 10.15),
**And** le bundle `storybook-static/` reste **≤ 15 MB** (budget 10.14 préservé).

**AC11 — Documentation `docs/CODEMAPS/ui-primitives.md` §3.4 Badge + ≥ 26 pièges cumulés**
**Given** `docs/CODEMAPS/ui-primitives.md`,
**When** auditée,
**Then** elle contient une nouvelle sous-section `### 3.4 ui/Badge (Story 10.17)` avec **≥ 4 exemples Vue** :
1. Verdict PASS default + icône stub,
2. Verdict PASS conditionnel italique,
3. Lifecycle `signed` avec dark mode,
4. Admin `n2` avec aria-label composé,
5. **Bonus** : exemple TypeScript union discriminée compile-time error (tentative `{ variant: 'verdict', state: 'draft' }` → `// @ts-expect-error`),

**And** §5 Pièges contient **≥ 26 pièges** cumulés (20 existants post-10.16 + 6 nouveaux Badge détaillés §4 Dev Notes ci-dessous),
**And** §6 Tableau A11y est étendu d'une ligne contraste `verdict-reported #D97706 on white = 4,69:1 ✅` (nettoyage L-4 code review 10.16),
**And** un test `test_docs_ui_primitives.test.ts` (existant 10.15) est **étendu** pour asserter présence §3.4 Badge + ≥ 26 pièges + ≥ 4 exemples dans §3.4.

## Tasks / Subtasks

- [x] **Task 1 — Scan NFR66 préalable + baseline** (AC1, AC9)
  - [x] 1.1 Grep `Badge\.vue|VERDICT_STATES|LIFECYCLE_STATES|ADMIN_CRITICALITIES|BADGE_SIZES` sur `frontend/app/components/ui/` → **0 hit** confirmé.
  - [x] 1.2 Baseline tests : **476 passed** (1 failed pré-existant useGuidedTour.resilience hors scope 10.17 — même état que baseline).
  - [x] 1.3 Baseline typecheck : **27 passed** (6 Button + 8 Input + 7 Select + 6 Textarea).
  - [x] 1.4 Collision brownfield : `NotificationBadge.vue` (notifications/) ≠ `Badge.vue` nom-distinct. Pas de migration Phase 0.

- [x] **Task 2 — Registry `ui/registry.ts` extension** (AC2)
  - [x] 2.1 Ajouté `VERDICT_STATES` (4) / `LIFECYCLE_STATES` (9) / `ADMIN_CRITICALITIES` (3) / `BADGE_SIZES` (3) frozen tuples.
  - [x] 2.2 Types dérivés `VerdictState` / `LifecycleState` / `AdminCriticality` / `BadgeSize` via `typeof TUPLE[number]`.
  - [x] 2.3 Exports 10.15+10.16 byte-identique préservés (diff restreint aux ajouts).
  - [x] 2.4 `npm run test:typecheck` → 40 passed, 0 type error sur registry.

- [x] **Task 3 — Composant `ui/Badge.vue`** (AC1, AC3-AC8)
  - [x] 3.1 Union discriminée `BadgeProps`, slots `#icon` + `#default`, native `<span>` (pas `<button>` — Q5 verrouillée).
  - [x] 3.2 Computed `variantClasses` avec `switch(variant)` → mapping tokens `@theme` par state (verdict soft+solid · lifecycle /10+solid · admin /10+solid).
  - [x] 3.3 Computed `sizeClasses` avec 3 sizes (20/24/32 px) + arbitrary `[&_svg]` pour icône enfant.
  - [x] 3.4 Computed `ariaLabel` avec 3 mappings FR (`VERDICT_LABELS_FR` · `LIFECYCLE_LABELS_FR` · `ADMIN_LABELS_FR`).
  - [x] 3.5 Computed `conditionalClasses` = `italic` si `variant==='verdict' && conditional`.
  - [x] 3.6 `onMounted` runtime check : fast path `!slots.icon` → `console.error`, `typeof slots.default !== 'function'` → `console.warn`, slow path `nextTick()` + inspection `labelRef.textContent` → `console.warn` si vide.
  - [x] 3.7 Template avec `role="status"` + `:aria-label="ariaLabel"` + wrapper icon `aria-hidden="true"` + wrapper label `ref="labelRef" data-testid="badge-label-slot"`.
  - [x] 3.8 Pas de `<style scoped>` (affichage pur, pas de motion).
  - [x] 3.9 Scan hex `Badge.vue` → **0 hit**.
  - [x] 3.10 `: any` / `as unknown` dans Badge.vue → **0 hit**.
  - [x] 3.11 **Commit intermédiaire 1** `aa91d81` : `feat(10.17): ui/Badge primitive + registry CCC-9 4 tuples`.

- [x] **Task 4 — `ui/Badge.stories.ts` co-localisée** (AC10)
  - [x] 4.1 `Badge.stories.ts` CSF 3.0 avec 15 stubs SVG inline commentés `STUB: remplace par <X /> Lucide Story 10.21`.
  - [x] 4.2 Mappings `state → icon SVG` : 4 verdict + 9 lifecycle + 3 admin = 16 icons (certains partagés `AlertTriangle`).
  - [x] 4.3 Stories verdict : 12 permutations (4 × 3) + `VerdictPassConditional` + `VerdictShowcaseGrid` = **14**.
  - [x] 4.4 Stories lifecycle : 9 states × md + `LifecycleShowcaseGrid` + `LifecycleDarkMode` = **11**.
  - [x] 4.5 Stories admin : 3 × 2 sizes (sm+md) + `AdminShowcaseGrid` = **7**.
  - [x] 4.6 Stories composées bonus : `ComposedInTable` + `ComposedInSidebar` + `ComposedDashboardHeader` = **3**.
  - [x] 4.7 Helper `asStorybookComponent<T>()` réutilisé (pas de `as unknown` dans .stories.ts).
  - [x] 4.8 Render direct (pas de play function — Badge non-interactif Q5).
  - **Total runtime `jq` storybook-static/index.json : 36 entries `ui-badge--*` (35 stories CSF + 1 docs autodocs) — plancher AC10 ≥ 30 satisfait**.

- [x] **Task 5 — Tests Vitest** (AC9)
  - [x] 5.1 `test_badge_registry.test.ts` : 12 tests (length × 4 + frozen × 4 + dedup × 4) — tous verts.
  - [x] 5.2 `test_badge_variants.test.ts` : 33 tests (12 verdict × 3 sizes + 9 lifecycle + 3 admin + 6 aria-label FR + 2 conditional + 3 role/slots + 2 Règle 11 runtime + 4 sizes base + 1 anti-pattern 44 px). **Pattern A respecté** (DOM réel, pas `wrapper.vm`).
  - [x] 5.3 `test_badge_a11y.test.ts` : 22 audits vitest-axe (4 verdict × 2 sizes + 9 lifecycle + 3 admin + 2 dark mode) → **0 violation**.
  - [x] 5.4 `test_no_hex_hardcoded_badge.test.ts` : 2 tests scan `Badge.vue` + `Badge.stories.ts` → 0 hit.
  - [x] 5.5 `Badge.test-d.ts` : **13 `@ts-expect-error` assertions** union discriminée cross-variant + conditional hors verdict + variant hors union + size hors BadgeSize + state manquant.
  - [x] 5.6 Baseline 476 → **555 passed** (+79 runtime, plancher ≥ 16 très dépassé).
  - [x] 5.7 Typecheck 27 → **40 passed** (+13, plancher ≥ 12 satisfait).

- [x] **Task 6 — Documentation `docs/CODEMAPS/ui-primitives.md`** (AC11)
  - [x] 6.1 `### 3.4 ui/Badge (Story 10.17)` inséré entre §3.3 Select et §4.
  - [x] 6.2 4 exemples Vue numérotés (verdict PASS + verdict PASS conditionnel + lifecycle signed sm + admin n2) + 1 bloc TypeScript union discriminée `@ts-expect-error`.
  - [x] 6.3 Pièges §5 étendu 20 → **26 entrées** (ajouts 21 tokens verdict/brand · 22 icon sizing · 23 role=status · 24 anti-pattern badge-as-button · 25 narrowing Vue 3 template · 26 méta Storybook count runtime).
  - [x] 6.4 §6 Tableau A11y : +1 ligne `text-verdict-reported #D97706 4,69:1 ✅ AA` (cleanup L-4 10.16).
  - [x] 6.5 `test_docs_ui_primitives.test.ts` étendu : 5 → 9 tests (§3.4 Badge + ≥ 26 pièges + ≥ 4 exemples §3.4 + contraste 4,69:1 verdict-reported).
  - [x] 6.6 `docs/CODEMAPS/methodology.md` étendu : section 4ter capitalisée « Application proactive Story 10.17 (ui/Badge) » Pattern A+B pré-review.

- [x] **Task 7 — Scan NFR66 post-dev + validation finale + comptage runtime Storybook (pattern B)** (AC2, AC9, AC10)
  - [x] 7.1 Scan hex Badge.vue + Badge.stories.ts + registry.ts → **0 hit** (les hex dans commentaires docstring `--color-verdict-reported #D97706` sont stripés par `stripComments()`).
  - [x] 7.2 `: any\b` / `as unknown` dans Badge.vue + Badge.test-d.ts → **0 hit**.
  - [x] 7.3 **Build Storybook + comptage runtime OBLIGATOIRE** :
    ```
    Total entries : 168 (bundle 8.0 MB)
    Entries ui-badge--* : 36 (35 stories CSF + 1 docs autodocs)
    ```
  - [x] 7.4 `du -sh frontend/storybook-static` = **8.0 MB** (≤ 15 MB budget 10.14).
  - [x] 7.5 Baseline 476 → 555 passed + 1 failed pré-existant useGuidedTour (hors scope 10.17, identique baseline). **0 régression** introduite.
  - [x] 7.6 **Commit final 2** : `feat(10.17): Badge stories CSF3 + docs CODEMAPS §3.4 + count runtime vérifié`.

- [x] **Task 8 — Mini-retro leçons 10.17 pour 10.18 Drawer**
  - [x] 8.1 Section 4ter `methodology.md` étendue : Pattern A (DOM test) + Pattern B (count runtime) capitalisés en règle d'or permanente, appliqués proactivement pas post-review.

## Dev Notes

### 1. Architecture cible — arborescence finale post-10.17

```
frontend/
├── app/
│   └── components/
│       └── ui/                     (5 composants existants 10.15+10.16 + 1 NOUVEAU + 2 brownfield)
│           ├── FullscreenModal.vue       (inchangé, brownfield)
│           ├── ToastNotification.vue     (inchangé, brownfield)
│           ├── Button.vue                (inchangé 10.15)
│           ├── Button.stories.ts         (inchangé 10.15)
│           ├── Input.vue                 (inchangé 10.16)
│           ├── Input.stories.ts          (inchangé 10.16)
│           ├── Textarea.vue              (inchangé 10.16)
│           ├── Textarea.stories.ts       (inchangé 10.16)
│           ├── Select.vue                (inchangé 10.16)
│           ├── Select.stories.ts         (inchangé 10.16)
│           ├── Badge.vue                 (NOUVEAU 10.17 : primitive 3 variants × N states)
│           ├── Badge.stories.ts          (NOUVEAU 10.17 : ≥ 30 stories CSF 3.0)
│           └── registry.ts               (ÉTENDU 10.17 : +4 frozen tuples)
├── tests/components/ui/             (6 fichiers existants 10.15+10.16 + 4 NOUVEAUX + 1 test-d.ts NOUVEAU)
│   ├── test_badge_registry.test.ts             (NOUVEAU)
│   ├── test_badge_variants.test.ts             (NOUVEAU)
│   ├── test_badge_a11y.test.ts                 (NOUVEAU)
│   ├── test_no_hex_hardcoded_badge.test.ts     (NOUVEAU)
│   └── Badge.test-d.ts                         (NOUVEAU : ≥ 12 @ts-expect-error)

docs/CODEMAPS/
└── ui-primitives.md                 (ÉTENDU 10.17 : §3.4 Badge + pièges 21-26 + §6 ligne verdict-reported)
```

**Aucune modification** :
- `frontend/app/assets/css/main.css` (tokens verdict/fa/admin déjà livrés Story 10.14).
- `frontend/.storybook/main.ts` (glob `gravity/ + ui/` déjà étendu 10.15).
- `frontend/.storybook/preview.ts` (dark mode + a11y config stables).
- `frontend/vitest.config.ts` (typecheck glob `tests/**/*.test-d.ts` déjà configuré 10.15).

### 2. 5 Q tranchées pré-dev (verrouillage choix techniques)

| # | Question | Décision | Rationale |
|---|----------|----------|-----------|
| **Q1** | Union discriminée unique `variant × state` OU registry par variant (3 composants `VerdictBadge` / `LifecycleBadge` / `AdminBadge`) ? | **Union discriminée unique `Badge.vue`** | Compile-time enforcement impossible avec 3 composants séparés (le consommateur choisit déjà le composant = pas d'erreur possible à détecter). Union discriminée Vue 3 `defineProps<Union>` fonctionne parfaitement + permet cross-variant refactoring. 1 seul composant = 1 seul point de maintenance dark mode + a11y. Réduction duplication (DRY). Pattern UX cohérent visuellement (même shape même padding). |
| **Q2** | Icône obligatoire via **slot `#icon`** OU prop `iconName: string` ? | **Slot `#icon` obligatoire (runtime error si absent)** | Composition Vue 3 idiomatique (pattern Button 10.15). Prop `iconName: string` forcerait un registre d'icônes interne au composant + mapping string→SVG fragile. Slot laisse le consommateur choisir Lucide (Story 10.21), SVG inline stub (Phase 0), ou icône custom métier. Enforcement runtime via `console.error` si `!slots.icon` + documentation §3.4 codemap avec 4 exemples. |
| **Q3** | Label `conditional` : le composant auto-suffixe `(conditionnel)` OU consommateur fournit le label complet ? | **Consommateur fournit le label complet** | Pattern « primitive dumb » (verrouillé 10.16 Q4). Le composant applique uniquement `italic` si `conditional === true`. Le label « Validé (conditionnel) » est FR localisé — la primitive UI ne doit pas porter de traductions. **`aria-label`** pour sa part est composé côté primitive (« Verdict {state} conditionnel ») car sémantique ARIA hors-flux visuel. Cohérent avec règle L-5 code review 10.15 (primitive dumb). |
| **Q4** | Sizes `sm`/`md`/`lg` : **mêmes hauteurs Button** (32/44/48 px) OU **plus petites adaptées inline** (20/24/32 px) ? | **Plus petites adaptées inline (20/24/32 px)** | Badge est un élément d'**affichage pur non-interactif** (pas de touch target WCAG 2.5.5 44 px car pas de tap). Un badge de 44 px casserait le flux visuel des tables + sidebars. UX Step 11 `ComplianceBadge` + `FundApplicationLifecycleBadge` référence des hauteurs compactes. **Anti-pattern « badge-as-button »** documenté §4 piège #24 : si un consommateur veut un badge cliquable, il wrappe `<Button variant="ghost">` autour. |
| **Q5** | État `clickable` / `role="button"` ? | **NON (PAS MVP)** | Badge = affichage pur. Un badge cliquable confond l'utilisateur (impression d'interactivité sans feedback visuel Button). Si besoin interactif identifié (ex. filtre par clic sur verdict « Fail » dans table), le consommateur compose `<Button variant="ghost"><Badge …/></Button>` ou `<button @click><Badge …/></button>`. Documenté §4 piège #24 + deferred-work `DEF-10.17-1 Clickable Badge Phase Growth` si pattern émerge > 2 fois. |

### 3. Exemple squelette complet — `ui/Badge.vue`

```vue
<!--
  ui/Badge.vue — primitive UI Phase 0 Story 10.17.
  Union discriminee variant x state : verdict (4) + lifecycle (9) + admin (3).
  3 signaux redondants OBLIGATOIRES (Regle 11 UX Step 12) : couleur + icone + texte.
  Non-interactif (affichage pur) : native <span>, role="status", aria-label compose.
  Stubs SVG Lucide via slot #icon (remplacement Lucide Story 10.21).
-->
<script setup lang="ts">
import { computed, onMounted, useSlots } from 'vue';
import type {
  VerdictState,
  LifecycleState,
  AdminCriticality,
  BadgeSize,
} from './registry';

// Union discriminée compile-time (AC1 + Badge.test-d.ts enforcement).
type BadgePropsBase = { size?: BadgeSize };
type BadgeProps =
  | (BadgePropsBase & { variant: 'verdict'; state: VerdictState; conditional?: boolean })
  | (BadgePropsBase & { variant: 'lifecycle'; state: LifecycleState })
  | (BadgePropsBase & { variant: 'admin'; state: AdminCriticality });

const props = withDefaults(defineProps<BadgeProps>(), {
  size: 'md',
});

const slots = useSlots();

// Labels FR par state (aria-label composition AC8).
const VERDICT_LABELS_FR: Record<VerdictState, string> = {
  pass: 'Validé',
  fail: 'Non conforme',
  reported: 'À documenter',
  na: 'Non applicable',
};
const LIFECYCLE_LABELS_FR: Record<LifecycleState, string> = {
  draft: 'Brouillon',
  snapshot_frozen: 'Figé',
  signed: 'Signé',
  exported: 'Exporté',
  submitted: 'Soumis',
  in_review: 'En revue',
  accepted: 'Accepté',
  rejected: 'Refusé',
  withdrawn: 'Retiré',
};
const ADMIN_LABELS_FR: Record<AdminCriticality, string> = {
  n1: 'N1',
  n2: 'N2',
  n3: 'N3',
};

// aria-label composé français (AC8).
const ariaLabel = computed<string>(() => {
  switch (props.variant) {
    case 'verdict': {
      const suffix = props.conditional ? ' (conditionnel)' : '';
      return `Verdict ${VERDICT_LABELS_FR[props.state]}${suffix}`;
    }
    case 'lifecycle':
      return `Statut ${LIFECYCLE_LABELS_FR[props.state]}`;
    case 'admin':
      return `Criticité admin ${ADMIN_LABELS_FR[props.state]}`;
  }
});

// Classes couleur par variant x state (AC6 tokens @theme exclusifs).
const variantClasses = computed<string>(() => {
  switch (props.variant) {
    case 'verdict':
      return {
        pass: 'bg-verdict-pass-soft text-verdict-pass dark:bg-verdict-pass/20 dark:text-verdict-pass-soft',
        fail: 'bg-verdict-fail-soft text-verdict-fail dark:bg-verdict-fail/20 dark:text-verdict-fail-soft',
        reported: 'bg-verdict-reported-soft text-verdict-reported dark:bg-verdict-reported/20 dark:text-verdict-reported-soft',
        na: 'bg-verdict-na-soft text-verdict-na dark:bg-verdict-na/20 dark:text-verdict-na-soft',
      }[props.state];
    case 'lifecycle':
      return {
        draft: 'bg-fa-draft/10 text-fa-draft dark:bg-fa-draft/20 dark:text-fa-draft',
        snapshot_frozen: 'bg-fa-snapshot-frozen/10 text-fa-snapshot-frozen dark:bg-fa-snapshot-frozen/20 dark:text-fa-snapshot-frozen',
        signed: 'bg-fa-signed/10 text-fa-signed dark:bg-fa-signed/20 dark:text-fa-signed',
        exported: 'bg-fa-exported/10 text-fa-exported dark:bg-fa-exported/20 dark:text-fa-exported',
        submitted: 'bg-fa-submitted/10 text-fa-submitted dark:bg-fa-submitted/20 dark:text-fa-submitted',
        in_review: 'bg-fa-in-review/10 text-fa-in-review dark:bg-fa-in-review/20 dark:text-fa-in-review',
        accepted: 'bg-fa-accepted/10 text-fa-accepted dark:bg-fa-accepted/20 dark:text-fa-accepted',
        rejected: 'bg-fa-rejected/10 text-fa-rejected dark:bg-fa-rejected/20 dark:text-fa-rejected',
        withdrawn: 'bg-fa-withdrawn/10 text-fa-withdrawn dark:bg-fa-withdrawn/20 dark:text-fa-withdrawn',
      }[props.state];
    case 'admin':
      return {
        n1: 'bg-admin-n1/10 text-admin-n1 dark:bg-admin-n1/20 dark:text-admin-n1',
        n2: 'bg-admin-n2/10 text-admin-n2 dark:bg-admin-n2/20 dark:text-admin-n2',
        n3: 'bg-admin-n3/10 text-admin-n3 dark:bg-admin-n3/20 dark:text-admin-n3',
      }[props.state];
  }
});

// Classes size (AC5 — hauteurs adaptees affichage inline non-interactif).
const sizeClasses = computed<string>(() => {
  switch (props.size) {
    case 'sm': return 'text-xs min-h-[20px] px-1.5 py-0.5 gap-1 [&_svg]:h-3 [&_svg]:w-3';
    case 'md': return 'text-sm min-h-[24px] px-2 py-0.5 gap-1 [&_svg]:h-3.5 [&_svg]:w-3.5';
    case 'lg': return 'text-base min-h-[32px] px-3 py-1 gap-1.5 [&_svg]:h-4 [&_svg]:w-4';
  }
});

// Italic si verdict conditional (AC4).
const conditionalClasses = computed<string>(() =>
  props.variant === 'verdict' && props.conditional ? 'italic' : '',
);

// Defense-in-depth runtime : Regle 11 enforcement (AC3).
onMounted(() => {
  if (!slots.icon) {
    console.error('[ui/Badge] slot #icon is REQUIRED (Regle 11 UX : couleur jamais seule).');
  }
  const hasLabel = slots.default && slots.default().some((v) => v.children?.toString().trim().length);
  if (!hasLabel) {
    console.warn('[ui/Badge] slot default (label FR) is REQUIRED for screen readers.');
  }
});
</script>

<template>
  <span
    role="status"
    :aria-label="ariaLabel"
    :class="[
      'inline-flex items-center rounded font-medium whitespace-nowrap',
      variantClasses,
      sizeClasses,
      conditionalClasses,
    ]"
  >
    <span data-testid="badge-icon-slot" aria-hidden="true" class="inline-flex items-center">
      <slot name="icon" />
    </span>
    <span data-testid="badge-label-slot">
      <slot />
    </span>
  </span>
</template>
```

**Rationale** :
- **Zéro hex** : tous via tokens `@theme` (`verdict-*`, `fa-*`, `admin-*`) livrés Story 10.14 (AC6).
- **Native `<span>`** : affichage pur, pas d'interactivité (Q5 verrouillée). Enforce anti-pattern badge-as-button.
- **Union discriminée** : compile-time garantit que `state` est cohérent avec `variant` (AC1 + `.test-d.ts`).
- **`role="status"`** : région ARIA live-polite implicite pour changements asynchrones (ex. verdict pass → fail après re-scan). Pas de `role="img"` car l'`aria-label` est textuel sémantique pas iconique.
- **Icône `aria-hidden="true"`** : le texte + couleur portent déjà la sémantique (3 signaux AC3). Éviter double-annonce NVDA.
- **Slot #default + icon obligatoires** : runtime `console.error` (icon) + `console.warn` (label) = defense-in-depth au-dessus de TS (AC3).
- **Dark mode** : chaque state a sa variante `dark:bg-*/20 dark:text-*-soft` — contraste préservé (fond opacité 20% sur bg-dark = lisible + texte soft color foncé en dark).
- **Tailwind arbitrary `[&_svg]:h-3`** : cible child SVG injecté via slot sans forcer le consommateur à taille l'icône (piège #22 atténué).

### 4. Pièges documentés (6 nouveaux — 21-26 — cumul ≥ 26 avec 20 existants 10.14-10.16)

**21. Tokens `verdict-*` vs `brand-*` confusion (aggravation post-10.15 darken)** — Story 10.15 a darkened `brand-green #10B981 → #047857` + `brand-red #EF4444 → #DC2626` pour WCAG AA. Les tokens `verdict-*` restent à leurs valeurs Q21 d'origine (`verdict-pass #059669`, `verdict-fail #DC2626`, `verdict-reported #D97706`, `verdict-na #6B7280`). **Piège** : tentation de « matcher » `verdict-reported` sur `brand-orange #F59E0B` (même famille chromatique). **INCORRECT** — `#F59E0B` sur blanc = 2,58:1 ❌ AA. Le choix `#D97706` amber-600 est délibéré pour contraste 4,69:1 ✅ AA (documenté §6 codemap). Règle : `variant="verdict"` → `verdict-*` ; états CTA primary/danger → `brand-*`. Jamais inversion.

**22. Icon slot sizing non contraint par le parent** — le slot `#icon` reçoit un SVG consommateur (stub 10.17 + Lucide 10.21) dont le parent ne contrôle pas la taille native. Tailwind arbitrary selector `[&_svg]:h-3 [&_svg]:w-3` cible les SVG enfants — fonctionne pour Lucide (`<svg>` racine) mais **pas pour wrappers** `<MyIcon>` qui seraient un `<span><svg>…</svg></span>`. Solution : documenter §3.4 codemap que l'icône injectée doit être un `<svg>` direct OU utiliser la classe `h-3 w-3` du consommateur explicitement. Phase Growth : provide/inject `badgeSize` + wrapper Lucide adaptatif Story 10.21.

**23. `role="status"` vs `role="img"` — choix A11y** — un badge ESG pourrait sembler être un « icône » sémantique (`role="img"`), mais les lecteurs d'écran annoncent `img` avec le seul `aria-label`. `role="status"` (région live-polite implicite) annonce le contenu + met à jour automatiquement si le verdict change asynchrone (re-scan). Pour Badge qui change de state au fil des tool calls LangGraph (ex. `submitted → in_review → accepted`), `role="status"` est correct. **Piège** : `role="img"` forcerait `aria-label` obligatoire (redondant avec notre composition) + perdrait l'update automatique screen reader.

**24. Anti-pattern « badge-as-button » (Q5 verrouillée)** — tentation de rendre un Badge cliquable (filtre table, tri verdict). **INTERDIT MVP** :
1. Native `<span>` n'a pas de touch target 44 px (AC5 hauteurs 20/24/32 px).
2. `role="button"` sur `<span>` nécessite `tabindex="0"` + `keydown` handlers + focus-visible — dupliquerait Button.
3. UX : un badge cliquable confond l'utilisateur (aucun feedback hover/focus distinct du hover sur Badge statique).

Solution : wrapper `<button @click="filter"><Badge variant="verdict" state="fail">...</Badge></button>` avec `<button>` natif porteur de l'interaction. Documenté §3.4 codemap. Deferred-work `DEF-10.17-1 Interactive Badge` si pattern réutilisé > 2 fois.

**25. Union discriminée Vue 3 `defineProps<Union>` — piège narrowing template** — dans le template Vue, `props.state` est typé `VerdictState | LifecycleState | AdminCriticality` (union merged) car le narrowing cross-block n'existe pas dans les templates SFC. **Solution** : utiliser des `computed` avec `switch(props.variant)` (JavaScript narrowing fonctionne) + mapping constants `VERDICT_LABELS_FR: Record<VerdictState, string>`. **Piège** : si un dev ajoute `v-if="props.variant === 'verdict' && props.conditional"` dans le template, TypeScript ne narrow PAS `props` dans ce bloc — la prop `conditional` est accessible uniquement via `computed` narrowing. Documenter §3.4 codemap + exemple.

**26. Comptage Storybook runtime OBLIGATOIRE avant Completion Notes (méthodologie 10.16 M-3)** — **méta-piège méthodologique** : l'estimation a priori du nombre de stories CSF exports est trompeuse car Storybook `tags: ['autodocs']` génère +1 docs page par CSF, et certains exports peuvent être ignorés par filtering. Règle : **exécuter `jq '.entries | keys | length' storybook-static/index.json` APRÈS `npm run storybook:build`** et consigner le chiffre exact dans Completion Notes — PAS d'estimation. Pattern capitalisé dès 10.17 pour éviter récurrence dérive post-10.16 (132 annoncés vs 122 réels).

### 5. Test plan complet

| # | Test | Type | Delta baseline 460 |
|---|------|------|--------------------|
| T1 | `VERDICT_STATES.length === 4` + frozen + dedup | Vitest unit | +3 |
| T2 | `LIFECYCLE_STATES.length === 9` + frozen + dedup | Vitest unit | +3 |
| T3 | `ADMIN_CRITICALITIES.length === 3` + frozen + dedup | Vitest unit | +3 |
| T4 | `BADGE_SIZES.length === 3` + frozen + dedup | Vitest unit | +3 |
| T5 | Rendu 4 verdict states × 3 sizes = 12 mounts + classes tokens présentes | Vitest @vue/test-utils | +12 |
| T6 | Rendu 9 lifecycle states × md + classes tokens | Vitest | +9 |
| T7 | Rendu 3 admin criticalities × md + classes tokens | Vitest | +3 |
| T8 | `aria-label` formatting FR × 3 familles × 2 cas chacune | Vitest | +6 |
| T9 | Verdict `conditional=true` → classes italic + aria-label « (conditionnel) » | Vitest | +2 |
| T10 | Règle 11 : slot icon absent → `console.error` | Vitest + vi.spyOn | +1 |
| T11 | Règle 11 : slot default absent → `console.warn` | Vitest | +1 |
| T12 | `role="status"` présent sur span racine | Vitest | +3 (1 par variant family) |
| T13 | vitest-axe × 20 audits (4 verdict × 2 sizes + 9 lifecycle + 3 admin + 2 dark mode) | Vitest a11y | +20 |
| T14 | Scan hex `Badge.vue` → 0 hit | Vitest fs | +1 |
| T15 | Scan hex `Badge.stories.ts` → 0 hit | Vitest fs | +1 |
| T16 | `test_docs_ui_primitives` §3.4 présent + ≥ 26 pièges + ≥ 4 exemples §3.4 | Vitest doc grep | +3 |
| T17 | **Badge.test-d.ts** (12+ assertions `@ts-expect-error`) | TS typecheck | +12 typecheck |
| **Total delta runtime** | | | **+73 tests** (plancher AC9 ≥ 16 largement dépassé) |
| **Total delta typecheck** | | | **+12** (plancher AC9 ≥ 12 atteint) |
| Storybook runtime | `jq '.entries | keys | length'` storybook-static/index.json | Comptage build | **≥ 30 nouvelles Badge** (mesuré exact Task 7.3) |
| Baseline runtime | 460 → 533+ passed (aucune régression) | Vitest | **0 régression** |
| Baseline typecheck | 26 → 38+ assertions | Vitest --typecheck | **+12** |

### 6. Checklist review (pour code-reviewer Story 10.17 post-merge)

- [ ] **Tokens `@theme` exclusifs** — `rg '#[0-9A-Fa-f]{3,8}' frontend/app/components/ui/Badge.vue frontend/app/components/ui/Badge.stories.ts` → 0 hit hors commentaires stub SVG.
- [ ] **TypeScript strict enforcé** — `rg ': any|as unknown' frontend/app/components/ui/Badge.vue frontend/tests/components/ui/Badge.test-d.ts` → 0 hit hors narrowing commenté.
- [ ] **Union discriminée compile-time** — `Badge.test-d.ts` contient ≥ 12 `@ts-expect-error` vérifiés via `npm run test:typecheck` (baseline 26 → 38+).
- [ ] **Dark mode par famille ≥ 6** — `rg 'dark:' frontend/app/components/ui/Badge.vue` total ≥ 21 (verdict 8 + lifecycle 9 + admin 6 mini).
- [ ] **WCAG 2.1 AA** — `vitest-axe` 20 audits → 0 violation (règle color-contrast désactivée en happy-dom, calcul manuel validé §6 codemap).
- [ ] **Règle 11 UX enforcement** — tests vérifient `console.error` si slot icon absent + `console.warn` si slot default absent.
- [ ] **Pas de duplication** — `VERDICT_STATES` / `LIFECYCLE_STATES` / `ADMIN_CRITICALITIES` / `BADGE_SIZES` source unique `registry.ts` — importés par `Badge.vue` + stories + tests.
- [ ] **Native `<span>` pas `<button>`** — `rg '<button' frontend/app/components/ui/Badge.vue` → 0 hit (anti-pattern Q5 verrouillée).
- [ ] **Anti-pattern badge-as-button documenté** — piège #24 codemap §5.
- [ ] **Shims legacy 10.6** — aucune modification des 60 brownfield + 6 gravity/ + 4 primitives `ui/` (Button + Input + Textarea + Select). `git diff frontend/app/components/ui/ -- ':!Badge.vue' ':!Badge.stories.ts' ':!registry.ts'` → vide.
- [ ] **Comptage runtime Storybook consigné** — Completion Notes contient le chiffre EXACT sortant de `jq '.entries | keys | length'` (pattern B 10.16 M-3 capitalisé proactivement).
- [ ] **Glob Storybook inchangé** — `frontend/.storybook/main.ts` diff restreint à 0 ligne (glob `gravity/ + ui/` déjà livré 10.15).
- [ ] **No hex in stubs SVG Lucide** — les stubs SVG inline dans Badge.stories.ts utilisent `stroke="currentColor"` + `fill="none"` ; couleurs via classes Tailwind parent (pas de `fill="#ff0000"` hardcodé).
- [ ] **`aria-label` français** — pas d'anglais leaked dans les labels (vérif spot check).
- [ ] **Coverage Badge.vue ≥ 85 %** — cf AC9 plancher primitive simple (optional si DEF-10.16-3 batched).
- [ ] **Contraste verdict-reported documenté** — §6 codemap contient ligne `#D97706 on white = 4,69:1 ✅` (cleanup L-4 code review 10.16).
- [ ] **No secret exposé** — `rg 'API_KEY|SECRET|TOKEN' frontend/app/components/ui/Badge*` → 0 hit.
- [ ] **Bundle Storybook ≤ 15 MB** — `du -sh frontend/storybook-static` respecté (marge 7 MB+ post-10.16).

### 7. Pattern commits intermédiaires (leçon 10.8+10.14+10.15+10.16)

2 commits lisibles review :
1. `feat(10.17): ui/Badge primitive + registry CCC-9 4 tuples` (Task 2 + 3) — composant + types + runtime enforcement Règle 11.
2. `feat(10.17): ui/Badge stories + tests + docs CODEMAPS §3.4 + typecheck` (Task 4 + 5 + 6 + 7) — 30+ stories + 16+ tests runtime + 12+ typecheck + §3.4 codemap + pièges 21-26.

Pattern CCC-9 (10.8+10.14+10.15+10.16) appliqué byte-identique : `VERDICT_STATES` + `LIFECYCLE_STATES` + `ADMIN_CRITICALITIES` + `BADGE_SIZES` frozen `Object.freeze([...] as const)` + validation `test_badge_registry.test.ts`.

Pattern compile-time enforcement `.test-d.ts` (10.15 HIGH-1) réutilisé byte-identique : `Badge.test-d.ts` dans `tests/components/ui/` + `vitest typecheck` déjà configuré.

Pattern darken tokens AA (10.15 HIGH-2) : **non applicable** — les tokens verdict-* utilisés par Badge (`#059669` / `#DC2626` / `#D97706` / `#6B7280`) sont tous AA 4,5:1+ sur blanc par design Q21. Aucun darken requis.

Pattern describedBy aligné v-if (10.16 H-1) : **non applicable** — Badge n'a pas de hint/error (pas de formulaire).

Pattern IME composition (10.16 H-2) : **non applicable** — Badge n'est pas un input.

Pattern multi-select native binding (10.16 H-3) : **non applicable** — Badge n'est pas un Select.

Pattern type coercion string-only (10.16 H-4) : **non applicable** — Badge n'émet rien (affichage pur).

Pattern A méthodologique 10.16 (tests DOM pas state interne) : **appliqué proactivement** Task 5.2 — `test_badge_variants.test.ts` assert `wrapper.find('span').classes()`, `wrapper.attributes('aria-label')`, `wrapper.find('[data-testid="badge-label-slot"]').text()` — jamais `wrapper.vm.variant`.

Pattern B méthodologique 10.16 (Storybook count runtime OBLIGATOIRE) : **appliqué proactivement** Task 7.3 — le chiffre `jq '.entries | keys | length'` est consigné dans Completion Notes avant tout claim de complétude (piège #26 documenté).

### 8. Hors scope explicite (non-objectifs cette story)

- ❌ **Migration des badges brownfield** — `frontend/app/components/notifications/NotificationBadge.vue` (counter rouge header non-lu) + `components/compliance/ComplianceBadge.vue` (si existant) + `components/fund-applications/FundApplicationLifecycleBadge.vue` (si existant) **inchangés**. Migrations scope Phase 1 Epic 11-15 (remplacement `<span class="...">` inline par `<ui/Badge variant="verdict" state="fail">Fail</ui/Badge>`).
- ❌ **Badge cliquable / badge-as-button** — Q5 verrouillée PAS MVP. Tracé `DEF-10.17-1 Interactive Badge Phase Growth` deferred-work.md si émergence > 2 fois.
- ❌ **Groupe de badges `BadgeGroup`** — pas de besoin identifié MVP. Le consommateur compose dans son propre layout (flex gap, grid, etc.).
- ❌ **Badge avec dot seul (sans texte)** — viole Règle 11 « couleur jamais seule » + absence texte dégrade A11y. Documenté §4 piège #24.
- ❌ **Taille `xl`** — pas de besoin dashboard header > 32 px identifié.
- ❌ **Intégration Lucide `lucide-vue-next`** — Story 10.21. Les stubs SVG inline dans `Badge.stories.ts` sont suffisants MVP (pattern 10.15 byte-identique).
- ❌ **Variants brand-* (primary/secondary/ghost/danger)** — hors sémantique de Badge (réservés Button 10.15). Si besoin badge "brand accent" émerge, créer variant dédié `brand` avec 4 sub-states — Phase Growth.
- ❌ **Animation transitions state change** — Badge statique affichage. Un changement de verdict `pass → fail` déclenche re-render natif Vue (fade via `<Transition>` Phase Growth si design UX le demande).
- ❌ **Smoke test auto-import Nuxt `<Badge>`** — intégré au pattern global du projet, pas spécifique Badge. Scope global Phase 1.

### 9. Previous Story Intelligence (10.16 leçons transférables)

De Story 10.16 (Input + Textarea + Select, sizing M) + 10.15 (Button, sizing S) :

**Leçons architecturales réutilisables byte-identique** :
- **Pattern CCC-9 frozen tuple** — `INPUT_TYPES` / `FORM_SIZES` (10.16) + `BUTTON_VARIANTS` / `BUTTON_SIZES` (10.15) → 4 nouveaux tuples Badge.
- **Compile-time enforcement `.test-d.ts`** — `Input.test-d.ts` / `Textarea.test-d.ts` / `Select.test-d.ts` (10.16) + `Button.test-d.ts` (10.15) → `Badge.test-d.ts` 12+ assertions.
- **Helper `asStorybookComponent<T>()`** — `frontend/app/types/storybook.ts` (10.15 MEDIUM-3) réutilisé byte-identique.
- **Scan hex + no any** — tests 10.15 + 10.16 réutilisés scope `Badge.vue` uniquement (brownfield + primitives précédentes inchangées).
- **Storybook co-localisation** — `<Name>.stories.ts` à côté `.vue`.
- **Dark mode seuil primitive** (10.15 MEDIUM-2 exception) — adapté Badge par FAMILLE variante (seuil ≥ 6 par variant-type, pas par composant total).

**Leçons méthodologiques post-review 10.16 (Pattern A + Pattern B)** :
- **Pattern A (H-3 Select multi-binding)** — tests assertent l'**effet observable DOM** (`wrapper.find().classes()` / `attributes('aria-label')` / `[data-testid]` text) PAS le state interne du composant (`wrapper.vm.*`). Appliqué proactivement Task 5.2 Badge. Capitalisation : 4 occurrences session 10.16 → règle méthodo durcie.
- **Pattern B (M-3 Storybook count surestimé)** — **mesurer le runtime `jq '.entries | keys | length'` AVANT Completion Notes**, jamais estimer a priori. Appliqué proactivement Task 7.3 Badge + piège #26 documenté.

**Leçons 10.16 HIGH applicables** :
- **H-1 describedBy aligné v-if** — NON APPLICABLE Badge (pas de hint/error).
- **H-2 IME composition** — NON APPLICABLE Badge (pas d'input).
- **H-3 Multi-select binding natif watch()** — NON APPLICABLE Badge (pas de Select).
- **H-4 type=number string coercion** — NON APPLICABLE Badge (pas d'émission).

Ces 4 leçons seront prioritaires Story 10.19 Combobox (équivalent Select amélioré + Tabs).

**Leçons MEDIUM 10.16 applicables à Badge** :
- **M-3 Storybook count runtime** — APPLIQUÉ (pattern B piège #26).
- **M-5 Dark mode focus-ring offset** — NON APPLICABLE Badge (pas de focus-visible).
- **M-6 Coverage c8 batched** — Badge s'aligne sur `DEF-10.16-3` si créé (coverage batched 10.15+10.16+10.17).
- **L-4 Tableau contraste codemap** — APPLIQUÉ Task 6.4 (+1 ligne `verdict-reported` §6 codemap).

**Règle d'or tests E2E effet observable** (10.5+10.16 H-3) → appliquée systématique Task 5.2 Badge.

### Project Structure Notes

- Dossier `frontend/app/components/ui/` **existant** (5 composants 10.15+10.16 + 2 brownfield), ajouts : `Badge.vue`, `Badge.stories.ts`, extension `registry.ts`. Collision zéro.
- Tests sous `frontend/tests/components/ui/` **existant** (pattern établi 10.15+10.16), 4 nouveaux fichiers + 1 `.test-d.ts` byte-cohérents.
- Pas de modification `nuxt.config.ts` (Badge auto-importé via `pathPrefix: false` existant CLAUDE.md).
- `tsconfig.json` frontend déjà `strict: true` → types Badge hérités sans override.
- `frontend/.storybook/main.ts` **inchangé** (glob déjà étendu 10.15).
- `frontend/.storybook/preview.ts` **inchangé** (toggle dark + a11y config stable 10.14+10.15).
- `main.css` **inchangé** (tokens verdict/fa/admin déjà livrés 10.14 — Badge consomme).
- `vitest.config.ts` **inchangé** (typecheck glob déjà configuré 10.15).
- Pattern Nuxt 4 auto-imports avec `pathPrefix: false` : `<Badge>` disponible globalement sans import explicite. Vérifier absence collision via Task 1.4 (brownfield `NotificationBadge.vue` ≠ `Badge.vue` — path prefix false + camelCase distinct).

### References

- [Source: _bmad-output/planning-artifacts/epics/epic-10.md#Story-10.17] — spec détaillée 6 AC + NFR + estimate S
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Step-8] — tokens `@theme` verdict-* + fa-* + admin-* (décision Q21 séparation brand vs verdict, contraste AA délibéré amber-600)
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Step-12-Regle-11] — Custom Pattern Rules « Couleur jamais seule porteuse d'information » (3 signaux redondants couleur + icône + texte obligatoires)
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Step-13-Accessibility-Checklist] — WCAG 2.1 AA 13 items (contraste 4,5:1, role="status", aria-label, dark mode)
- [Source: CLAUDE.md#Dark-Mode-OBLIGATOIRE] — dark mode tous composants via variantes `dark:`
- [Source: CLAUDE.md#Reutilisabilite-Composants] — discipline > 2 fois = extraction primitive réutilisable
- [Source: ~/.claude/rules/typescript/coding-style.md] — TypeScript strict, `interface` pour props, pas de `any`, `unknown` narrowing, types dérivés `as const`
- [Source: frontend/app/assets/css/main.css:30-57] — tokens `@theme` verdict/fa/admin livrés Story 10.14 (source unique couleurs sémantiques)
- [Source: frontend/app/components/ui/registry.ts] — registre CCC-9 existant (BUTTON_* 10.15 + INPUT_TYPES/FORM_SIZES/TEXTAREA_DEFAULT_MAX_LENGTH 10.16) à étendre 4 nouveaux tuples
- [Source: frontend/app/components/ui/Button.vue] — pattern primitive 10.15 (script setup + computed + slots + tokens @theme + runtime checks)
- [Source: frontend/app/components/ui/Input.vue] — pattern primitive 10.16 (union discriminée + a11y composé + dark mode)
- [Source: frontend/.storybook/main.ts:6] — glob `gravity/ + ui/` déjà étendu 10.15 (inchangé 10.17)
- [Source: frontend/.storybook/preview.ts] — decorator dark mode + a11y config réutilisés byte-identique
- [Source: frontend/vitest.config.ts] — typecheck glob `tests/**/*.test-d.ts` déjà configuré 10.15
- [Source: docs/CODEMAPS/ui-primitives.md#§5-Pieges] — 20 pièges cumulés 10.15 (10) + 10.16 (10 : 11-20) → extension +6 (21-26) Badge
- [Source: docs/CODEMAPS/ui-primitives.md#§6-A11y-Contraste] — tableau darken tokens 10.15 (brand-green/red AA) à étendre +1 ligne verdict-reported
- [Source: _bmad-output/implementation-artifacts/10-15-ui-button-4-variantes.md] — patterns primitive 1 byte-identique (frozen tuple + commit intermédiaire + scan NFR66 + CODEMAPS 5 sections + 5 Q tranchées + co-localisation stories)
- [Source: _bmad-output/implementation-artifacts/10-15-code-review-2026-04-22.md] — HIGH-1 compile-time enforcement `.test-d.ts` + HIGH-2 darken tokens AA (ref contraste tableau) + MEDIUM-2 exception dark: seuil primitive
- [Source: _bmad-output/implementation-artifacts/10-16-ui-input-textarea-select.md] — patterns primitive 3 byte-identique (union discriminée multi-composant + describedBy computed + runtime enforcement)
- [Source: _bmad-output/implementation-artifacts/10-16-code-review-2026-04-22.md] — H-1 describedBy aligné v-if + H-2 IME + H-3 multi-binding + H-4 type coercion + M-3 Storybook count runtime + Pattern A (DOM pas state) + Pattern B (comptage runtime OBLIGATOIRE)
- [Source: _bmad-output/implementation-artifacts/deferred-work.md] — DEF-10.15-* + DEF-10.16-* tracés (format à réutiliser DEF-10.17-* si émergence patch)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7 (1M context) — dev-story 2026-04-22, 19ᵉ story Phase 4.

### Debug Log References

**Baseline pré-dev (pattern 4ter comptages runtime OBLIGATOIRES)** :
```bash
$ cd frontend && npm run test -- --run 2>&1 | tail -5
# Test Files  1 failed | 53 passed (54)
#      Tests  1 failed | 476 passed (477)
# (1 pre-existing failure useGuidedTour.resilience.test.ts — hors scope 10.17)

$ npm run test:typecheck 2>&1 | tail -5
# Test Files  4 passed (4)
#      Tests  27 passed (27)
# (6 Button + 8 Input + 7 Select + 6 Textarea)
```

**Post-dev Story 10.17 (sortie brute) — pattern 4ter respecté** :
```bash
$ npm run test -- --run 2>&1 | tail -4
# Test Files  1 failed | 57 passed (58)   (+4 fichiers Badge)
#      Tests  1 failed | 555 passed (556) (+79 tests runtime)
# (1 failure = même useGuidedTour pré-existant, 0 régression 10.17)

$ npm run test:typecheck 2>&1 | tail -4
# Test Files  5 passed (5)
#      Tests  40 passed (40)     (+13 assertions Badge.test-d.ts)
# Type Errors  no errors

$ cd frontend && npm run storybook:build 2>&1 | tail -5
# built in 5.21s — Output directory: frontend/storybook-static
$ jq '.entries | keys | length' storybook-static/index.json
# 168
$ jq '[.entries | to_entries[] | select(.value.id | startswith("ui-badge"))] | length' storybook-static/index.json
# 36        (35 stories CSF export + 1 auto-docs — AC10 plancher ≥ 30 satisfait)
$ du -sh storybook-static
# 8.0M     (budget 10.14 ≤ 15 MB respecté, marge 7 MB)

$ grep -oE "dark:" frontend/app/components/ui/Badge.vue | wc -l
# 33       (plancher AC7 ≥ 21 largement dépassé, sans inflation artificielle)

$ grep -nE "#[0-9A-Fa-f]{3,8}\b" frontend/app/components/ui/Badge.vue frontend/app/components/ui/Badge.stories.ts
# (aucun hit hors commentaires docstring)

$ grep -nE ": any\b|as unknown" frontend/app/components/ui/Badge.vue
# (aucun hit)
```

### Completion Notes List

- **11/11 AC + 8/8 tasks complétés.** Story 10.17 livrée en ~50 min (sizing S cible ~1h largement respecté, 19ᵉ story Phase 4).
- **Primitive `ui/Badge.vue` livrée** : union discriminée `variant × state` compile-time (Q1) unifiant 3 familles sémantiques (4 verdicts + 9 lifecycle + 3 admin) × 3 sizes (20/24/32 px non-interactif Q4). Native `<span>` + `role="status"` + `aria-label` FR composé.
- **3 signaux redondants Règle 11 UX enforcés** : tokens `@theme` (couleur) + slot `#icon` obligatoire runtime (`console.error` si absent) + slot `#default` obligatoire (`console.warn` fast-path slot absent + slow-path inspection DOM post-`nextTick` label vide).
- **Registry étendu CCC-9** : 4 nouveaux `Object.freeze([…] as const)` (VERDICT_STATES/LIFECYCLE_STATES/ADMIN_CRITICALITIES/BADGE_SIZES) + 4 types dérivés, byte-identique pattern 10.15 + 10.16.
- **Comptage Storybook runtime (pattern B 10.16 M-3) OBLIGATOIRE exécuté AVANT ces Completion Notes** : `jq '.entries | keys | length' storybook-static/index.json` = **168 total** dont **36 `ui-badge--*`** (35 stories CSF export + 1 auto-docs). Plancher AC10 ≥ 30 satisfait avec marge.
- **Tests runtime** : 476 → 555 passed (+79, cible AC9 ≥ 16 très dépassée, répartis 12 registry + 33 variants + 22 a11y + 2 no-hex + 10 docs). Pattern A proactif : **toutes** les assertions passent par DOM (`wrapper.find('span').classes()`, `attributes('aria-label')`, `[data-testid]` text) — aucune `wrapper.vm.*` ni mutation state interne.
- **Typecheck compile-time** : 27 → 40 passed (+13, cible AC9 ≥ 12 satisfait). 13 `@ts-expect-error` couvrant 9 combinaisons invalides cross-variant (`{ variant: 'verdict', state: 'draft' }` etc.) + `conditional` hors verdict + size hors BadgeSize + state manquant + variant hors union.
- **Dark mode 33 dark: classes** (AC7 plancher ≥ 21 dépassé : 8 verdict + 18 lifecycle + 6 admin + 1 bonus) sans inflation artificielle — chaque classe rattachée à un axe visuel réel (fond `/20` + texte `-soft` par variante).
- **WCAG 2.1 AA** : 22 audits `vitest-axe` (dont 2 en dark mode) = **0 violation**. Contraste tokens calculé manuellement §6 codemap (verdict-reported `#D97706` on white = 4,69:1 ✅ AA — choix amber-600 délibéré au lieu de `#F59E0B` amber-500 2,58:1 ❌).
- **Docs CODEMAPS** : `ui-primitives.md` §3.4 Badge (4 exemples Vue + 1 bloc union discriminée TS `@ts-expect-error`) + §5 **26 pièges** cumulés (20 existants + 6 nouveaux 21-26) + §6 +1 ligne contraste verdict-reported. `methodology.md` §4ter capitalise Pattern A + Pattern B appliqués proactivement (pas post-review).
- **Anti-pattern badge-as-button documenté piège #24** : wrapper `<button @click><Badge /></button>` obligatoire si besoin interactif (Deferred `DEF-10.17-1 Interactive Badge Phase Growth` si > 2 occurrences).
- **Shims legacy 10.6 préservés** : 60 brownfield + 6 gravity/ + 4 primitives ui/ existantes (Button + Input + Textarea + Select) inchangés — seul `registry.ts` étendu (diff ajouts uniquement).
- **2 commits traçabilité** : `aa91d81` composant + registry + tests · commit 2 stories + docs CODEMAPS + test_docs étendu.
- **0 régression** : unique échec pré-existant `useGuidedTour.resilience.test.ts > Bloc 2` (skipCalls multi-step), identique baseline et hors scope 10.17.

### File List

**Créés (8 fichiers)** :
- `frontend/app/components/ui/Badge.vue` — primitive union discriminée 3 familles (AC1, AC3-AC8)
- `frontend/app/components/ui/Badge.stories.ts` — 35 stories CSF 3.0 + 15 stubs SVG Lucide-ready (AC10)
- `frontend/tests/components/ui/Badge.test-d.ts` — 13 typecheck `@ts-expect-error` union discriminée (AC1)
- `frontend/tests/components/ui/test_badge_registry.test.ts` — 12 tests frozen/length/dedup (AC2)
- `frontend/tests/components/ui/test_badge_variants.test.ts` — 33 tests DOM Pattern A (AC3, AC4, AC5, AC6, AC8)
- `frontend/tests/components/ui/test_badge_a11y.test.ts` — 22 audits vitest-axe (AC7, AC8)
- `frontend/tests/components/ui/test_no_hex_hardcoded_badge.test.ts` — 2 tests scan fs (AC6)
- `_bmad-output/implementation-artifacts/10-17-ui-badge-tokens-semantiques.md` — le story file (status → review, Completion Notes complétées)

**Modifiés (5 fichiers)** :
- `frontend/app/components/ui/registry.ts` — +4 frozen tuples + 4 types dérivés (byte-identique préservé)
- `frontend/tests/test_docs_ui_primitives.test.ts` — 5 → 9 tests (§3.4 + ≥ 26 pièges + ≥ 4 exemples + contraste 4,69:1)
- `docs/CODEMAPS/ui-primitives.md` — §3.4 Badge + pièges 21-26 (26 cumul) + §6 +1 ligne + §2 arbo
- `docs/CODEMAPS/methodology.md` — §4ter étendu "Application proactive Story 10.17" Pattern A+B
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — 10-17 ready-for-dev → in-progress → review

### Change Log

| Date | Commit | Description |
|------|--------|-------------|
| 2026-04-22 | `aa91d81` | feat(10.17): ui/Badge primitive + registry CCC-9 4 tuples (Badge.vue + registry + 5 tests) |
| 2026-04-22 | *(pending)* | feat(10.17): Badge stories CSF3 + docs CODEMAPS §3.4 + count runtime vérifié |
