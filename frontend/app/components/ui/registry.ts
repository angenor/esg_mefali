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
