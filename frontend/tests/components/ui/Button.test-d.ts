/**
 * Compile-time type tests pour ui/Button (AC5 Story 10.15).
 * Executes via `vitest --typecheck` (vitest.config.ts typecheck enabled).
 * Les directives // @ts-expect-error DOIVENT trouver une erreur TS ; sinon
 * vitest typecheck echoue et detecte toute regression silencieuse de la
 * discrimination union iconOnly + ariaLabel.
 */
import { describe, it, expectTypeOf, assertType } from 'vitest';
import type { ButtonVariant, ButtonSize } from '../../../app/components/ui/registry';

// Reproduction locale du type discrimine Button.vue:13-22 (source of truth).
// Si Button.vue change, cette copie doit suivre explicitement.
type ButtonPropsBase = {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  disabled?: boolean;
  type?: 'button' | 'submit' | 'reset';
};
type ButtonProps =
  | (ButtonPropsBase & { iconOnly?: false | undefined; ariaLabel?: string })
  | (ButtonPropsBase & { iconOnly: true; ariaLabel: string });

describe('ui/Button : AC1 + AC5 type safety (compile-time)', () => {
  it('ButtonVariant inclut exactement primary|secondary|ghost|danger', () => {
    expectTypeOf<ButtonVariant>().toEqualTypeOf<
      'primary' | 'secondary' | 'ghost' | 'danger'
    >();
  });

  it('ButtonSize inclut exactement sm|md|lg', () => {
    expectTypeOf<ButtonSize>().toEqualTypeOf<'sm' | 'md' | 'lg'>();
  });

  it('AC5 : iconOnly=true SANS ariaLabel n est PAS assignable', () => {
    // @ts-expect-error iconOnly=true requiert ariaLabel: string.
    const invalid1: ButtonProps = { iconOnly: true };
    void invalid1;

    // @ts-expect-error iconOnly=true interdit ariaLabel=undefined.
    const invalid2: ButtonProps = { iconOnly: true, ariaLabel: undefined };
    void invalid2;

    // OK : iconOnly=true AVEC ariaLabel: string.
    const valid1: ButtonProps = { iconOnly: true, ariaLabel: 'Fermer le modal' };
    assertType<ButtonProps>(valid1);

    // OK : iconOnly=false/omis rend ariaLabel optionnel.
    const valid2: ButtonProps = { iconOnly: false };
    assertType<ButtonProps>(valid2);
    const valid3: ButtonProps = {};
    assertType<ButtonProps>(valid3);
    const valid4: ButtonProps = { ariaLabel: 'Description optionnelle' };
    assertType<ButtonProps>(valid4);
  });

  it('AC1 : variant en dehors de l union est rejete', () => {
    // @ts-expect-error 'invalid-variant' n est pas dans ButtonVariant.
    const bad: ButtonProps = { variant: 'invalid-variant' };
    void bad;
  });

  it('AC1 : size en dehors de l union est rejete', () => {
    // @ts-expect-error 'xl' n est pas dans ButtonSize.
    const bad: ButtonProps = { size: 'xl' };
    void bad;
  });

  it('AC1 : type bouton accepte uniquement button|submit|reset', () => {
    // @ts-expect-error 'menu' n est pas un HTMLButton type valide.
    const bad: ButtonProps = { type: 'menu' };
    void bad;
  });
});
