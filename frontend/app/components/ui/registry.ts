/**
 * Registre central des primitives UI Phase 0 (Story 10.15-10.21).
 * Pattern CCC-9 frozen tuple (heritage Story 10.8+10.10+10.11+10.12+10.13+10.14+10.15).
 * Source unique pour : tests (variants × sizes), stories (matrice showcase), composants .vue (types).
 *
 * Invariants :
 * - BUTTON_VARIANTS.length === 4, BUTTON_SIZES.length === 3 (Story 10.15).
 * - INPUT_TYPES.length === 7, FORM_SIZES.length === 3 (Story 10.16).
 * - Tous les tuples frozen (Object.isFrozen) + dedoublonnes (Set.size === length).
 *
 * Note 10.16 : FORM_SIZES partage ses valeurs avec BUTTON_SIZES (sm/md/lg) mais
 * reste independant semantiquement — un rebrand futur des formulaires ne doit
 * pas coupler les boutons (pas de re-export `BUTTON_SIZES as FORM_SIZES`).
 */

export const BUTTON_VARIANTS = Object.freeze([
  'primary',
  'secondary',
  'ghost',
  'danger',
] as const);

export const BUTTON_SIZES = Object.freeze(['sm', 'md', 'lg'] as const);

export type ButtonVariant = (typeof BUTTON_VARIANTS)[number];
export type ButtonSize = (typeof BUTTON_SIZES)[number];

/**
 * Types HTML5 supportes par `ui/Input.vue` (Story 10.16).
 * 7 types natives : text (default) + email + number + password + url + tel + search.
 * `file` exclu (composant dedie `FileUploader.vue` Phase 1, drag-drop specifique).
 * `date`/`datetime-local`/`time` exclus (Story 10.20 `ui/DatePicker.vue` wrapper).
 * `checkbox`/`radio` exclus (primitives dediees hors Phase 0).
 */
export const INPUT_TYPES = Object.freeze([
  'text',
  'email',
  'number',
  'password',
  'url',
  'tel',
  'search',
] as const);

/**
 * Tailles partagees par les 3 primitives formulaire Story 10.16
 * (Input, Textarea, Select). Valeurs identiques a BUTTON_SIZES mais
 * intentionnellement independantes — evolution future d'un des 2 ne
 * doit pas coupler l'autre (voir pattern shim 10.6 / piege #11 codemap).
 */
export const FORM_SIZES = Object.freeze(['sm', 'md', 'lg'] as const);

export type InputType = (typeof INPUT_TYPES)[number];
export type FormSize = (typeof FORM_SIZES)[number];

/**
 * Maxlength par defaut pour `ui/Textarea.vue` — conforme Spec 018 AC5
 * (copilot justification, triple defense browser + JS + backend).
 */
export const TEXTAREA_DEFAULT_MAX_LENGTH = 400;

/**
 * Registre `ui/Badge.vue` (Story 10.17) — 3 familles semantiques unifiees
 * par une union discriminee `variant x state` (AC1) :
 *
 *  - `VERDICT_STATES`   : 4 etats ESG (pass / fail / reported / na)
 *                         consommes par ComplianceBadge + ScoreGauge (FR40 / Q21 UX Step 8).
 *  - `LIFECYCLE_STATES` : 9 etats FundApplication (FR32)
 *                         consommes par FundApplicationLifecycleBadge + sidebar.
 *  - `ADMIN_CRITICALITIES` : 3 niveaux criticite admin (arbitrage Q11 Mariam).
 *  - `BADGE_SIZES`      : 3 tailles non-interactives adaptees affichage inline
 *                         (Q4 verrouillee — PAS touch target 44 px, Badge = affichage pur).
 *
 * Invariants : length 4 / 9 / 3 / 3 · Object.isFrozen === true · dedoublonne.
 * Pattern CCC-9 frozen tuple byte-identique a Story 10.15 + 10.16.
 */
export const VERDICT_STATES = Object.freeze([
  'pass',
  'fail',
  'reported',
  'na',
] as const);

export const LIFECYCLE_STATES = Object.freeze([
  'draft',
  'snapshot_frozen',
  'signed',
  'exported',
  'submitted',
  'in_review',
  'accepted',
  'rejected',
  'withdrawn',
] as const);

export const ADMIN_CRITICALITIES = Object.freeze([
  'n1',
  'n2',
  'n3',
] as const);

export const BADGE_SIZES = Object.freeze(['sm', 'md', 'lg'] as const);

export type VerdictState = (typeof VERDICT_STATES)[number];
export type LifecycleState = (typeof LIFECYCLE_STATES)[number];
export type AdminCriticality = (typeof ADMIN_CRITICALITIES)[number];
export type BadgeSize = (typeof BADGE_SIZES)[number];

/**
 * Labels FR single source of truth (10.17 code-review MEDIUM-2 DRY fix).
 * Consommes par Badge.vue (composition aria-label) + Badge.stories.ts
 * (slot default). Migration future useI18n() trivialisee a un seul fichier.
 */
export const VERDICT_LABELS_FR: Readonly<Record<VerdictState, string>> = Object.freeze({
  pass: 'Validé',
  fail: 'Non conforme',
  reported: 'À documenter',
  na: 'Non applicable',
});

export const LIFECYCLE_LABELS_FR: Readonly<Record<LifecycleState, string>> = Object.freeze({
  draft: 'Brouillon',
  snapshot_frozen: 'Figé',
  signed: 'Signé',
  exported: 'Exporté',
  submitted: 'Soumis',
  in_review: 'En revue',
  accepted: 'Accepté',
  rejected: 'Refusé',
  withdrawn: 'Retiré',
});

export const ADMIN_LABELS_FR: Readonly<Record<AdminCriticality, string>> = Object.freeze({
  n1: 'N1',
  n2: 'N2',
  n3: 'N3',
});

/**
 * Signature Badge partagee (10.17 code-review MEDIUM-3 DRY fix) :
 * import depuis Badge.vue (defineProps) + Badge.test-d.ts (compile-time).
 * Source unique de verite pour la discrimination variant x state.
 */
export type BadgePropsBase = { size?: BadgeSize };
export type BadgeProps =
  | (BadgePropsBase & { variant: 'verdict'; state: VerdictState; conditional?: boolean })
  | (BadgePropsBase & { variant: 'lifecycle'; state: LifecycleState })
  | (BadgePropsBase & { variant: 'admin'; state: AdminCriticality });

/**
 * Registre `ui/Drawer.vue` (Story 10.18) — panneau lateral accessible
 * wrapper Reka UI DialogRoot + DialogPortal + DialogOverlay + DialogContent
 * avec override ARIA `role="complementary"` + `aria-modal="false"`
 * (lecon 10.14 HIGH-2 capitalisee infra — drawer consultatif != modal bloquant).
 *
 *  - `DRAWER_SIDES` : 4 positions (ordre canonique `right` default first —
 *                     SourceCitationDrawer Epic 13 + IntermediaryComparator Epic 15
 *                     + PeerReviewThreadedPanel Epic 19 consomment side=right).
 *  - `DRAWER_SIZES` : 3 tailles desktop (sm=320px filtre / md=480px default
 *                     sources+peer-review / lg=560px comparaison intermediaires).
 *                     Mobile <md 768 px : fullscreen auto CSS-only (piege #29).
 *
 * Invariants : length 4 / 3 · Object.isFrozen === true · dedoublonne.
 * Pattern CCC-9 frozen tuple byte-identique a 10.15 + 10.16 + 10.17.
 */
export const DRAWER_SIDES = Object.freeze([
  'right',
  'left',
  'top',
  'bottom',
] as const);

export const DRAWER_SIZES = Object.freeze(['sm', 'md', 'lg'] as const);

export type DrawerSide = (typeof DRAWER_SIDES)[number];
export type DrawerSize = (typeof DRAWER_SIZES)[number];

/**
 * Registre `ui/Combobox.vue` + `ui/Tabs.vue` (Story 10.19) — 2ᵉ + 3ᵉ wrappers
 * Reka UI apres Drawer 10.18. Ordre canonique des tuples = default infere
 * (index 0). Changer l'ordre = rupture API tous consommateurs (piege #35
 * codemap `ui-primitives.md#§5`).
 *
 *  - `COMBOBOX_MODES`        : single (default) / multiple — cohérent Select 10.16.
 *  - `TABS_ORIENTATIONS`     : horizontal (default 95% cas UI SaaS) / vertical.
 *  - `TABS_ACTIVATION_MODES` : automatic (default WAI-ARIA) / manual (a11y
 *                              screen reader exploration sans charger contenu).
 *
 * Invariants : length 2/2/2 · Object.isFrozen === true · dedoublonne ·
 * types derivés `typeof TUPLE[number]`. Pattern CCC-9 byte-identique 10.15-10.18.
 */
export const COMBOBOX_MODES = Object.freeze(['single', 'multiple'] as const);

export const TABS_ORIENTATIONS = Object.freeze(['horizontal', 'vertical'] as const);

export const TABS_ACTIVATION_MODES = Object.freeze(['automatic', 'manual'] as const);

export type ComboboxMode = (typeof COMBOBOX_MODES)[number];
export type TabsOrientation = (typeof TABS_ORIENTATIONS)[number];
export type TabsActivationMode = (typeof TABS_ACTIVATION_MODES)[number];
