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
