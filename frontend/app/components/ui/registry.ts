/**
 * Registre central des primitives UI Phase 0 (Story 10.15-10.21).
 * Pattern CCC-9 frozen tuple (heritage Story 10.8+10.10+10.11+10.12+10.13+10.14).
 * Source unique pour : tests (variants × sizes), stories (matrice showcase), Button.vue (types).
 * Invariants : BUTTON_VARIANTS.length === 4, BUTTON_SIZES.length === 3, les 2 tuples frozen.
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
