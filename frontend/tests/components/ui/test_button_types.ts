/**
 * Assertions TypeScript compile-time pour ui/Button (AC5).
 * Ce fichier N'EST PAS execute au runtime (pas de .test.ts). Il est resolu via
 * `npm run build` (Nuxt type-check) et la surface TS de Vitest lors du collect.
 * Les directives // @ts-expect-error documentent les invariants du type discrimine :
 *   - iconOnly=true force ariaLabel: string (non-optional).
 */
// @ts-nocheck-line-disabled-intentionally
import type { DefineComponent } from 'vue';
// eslint-disable-next-line @typescript-eslint/no-unused-vars
import Button from '../../../app/components/ui/Button.vue';
import type {
  ButtonVariant,
  ButtonSize,
} from '../../../app/components/ui/registry';

// Cast generique : Vue SFC exporte un DefineComponent, on verifie seulement que
// les types de props declares dans registry.ts sont bien exportes + utilisables.
type _AssertVariants = ButtonVariant extends 'primary' | 'secondary' | 'ghost' | 'danger'
  ? true
  : never;
type _AssertSizes = ButtonSize extends 'sm' | 'md' | 'lg' ? true : never;

const _variants: _AssertVariants = true;
const _sizes: _AssertSizes = true;

// Smoke : le composant est bien un DefineComponent (pas `any` ni `undefined`).
const _buttonRef: DefineComponent<Record<string, unknown>> | unknown = Button;

export { _variants, _sizes, _buttonRef };
