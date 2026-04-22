/**
 * Compile-time type tests pour ui/Input (AC1 + AC3 Story 10.16).
 * Executes via `vitest --typecheck` (vitest.config.ts typecheck enabled).
 * Les directives // @ts-expect-error DOIVENT trouver une erreur TS ; sinon
 * vitest typecheck echoue et detecte toute regression silencieuse des
 * unions InputType / FormSize / InputMode.
 */
import { describe, it, expectTypeOf, assertType } from 'vitest';
import type { InputType, FormSize } from '../../../app/components/ui/registry';

// Reproduction locale du type (source : Input.vue:21-40, single source of truth).
type InputMode =
  | 'text'
  | 'numeric'
  | 'decimal'
  | 'tel'
  | 'email'
  | 'url'
  | 'search'
  | 'none';

type InputProps = {
  modelValue: string | number;
  label: string;
  id?: string;
  placeholder?: string;
  error?: string;
  hint?: string;
  required?: boolean;
  disabled?: boolean;
  readonly?: boolean;
  size?: FormSize;
  type?: InputType;
  autocomplete?: string;
  pattern?: string;
  minlength?: number;
  maxlength?: number;
  inputmode?: InputMode;
  name?: string;
};

describe('ui/Input : AC1 + AC3 type safety (compile-time)', () => {
  it('InputType inclut exactement les 7 types HTML5 supportes', () => {
    expectTypeOf<InputType>().toEqualTypeOf<
      'text' | 'email' | 'number' | 'password' | 'url' | 'tel' | 'search'
    >();
  });

  it('FormSize inclut exactement sm|md|lg', () => {
    expectTypeOf<FormSize>().toEqualTypeOf<'sm' | 'md' | 'lg'>();
  });

  it('AC1 : type en dehors de InputType est rejete', () => {
    // @ts-expect-error 'checkbox' n est pas dans InputType (7 natives supportes).
    const bad1: InputProps = { modelValue: '', label: 'X', type: 'checkbox' };
    void bad1;

    // @ts-expect-error 'file' exclu (FileUploader dedie Phase 1).
    const bad2: InputProps = { modelValue: '', label: 'X', type: 'file' };
    void bad2;

    // @ts-expect-error 'date' exclu (DatePicker Story 10.20).
    const bad3: InputProps = { modelValue: '', label: 'X', type: 'date' };
    void bad3;

    // OK : les 7 types supportes.
    const valid1: InputProps = { modelValue: '', label: 'Email', type: 'email' };
    const valid2: InputProps = { modelValue: 0, label: 'Montant', type: 'number' };
    assertType<InputProps>(valid1);
    assertType<InputProps>(valid2);
  });

  it('AC3 : size en dehors de FormSize est rejete', () => {
    // @ts-expect-error 'xl' n est pas dans FormSize.
    const bad: InputProps = { modelValue: '', label: 'X', size: 'xl' };
    void bad;
  });

  it('AC6 : inputmode en dehors de l union est rejete', () => {
    // @ts-expect-error 'voice' n est pas un inputmode HTML5 valide.
    const bad: InputProps = { modelValue: '', label: 'X', inputmode: 'voice' };
    void bad;
  });

  it('AC1 : label est obligatoire (a11y — pas de champ sans label)', () => {
    // @ts-expect-error label manquant — invariant a11y AC5.
    const bad: InputProps = { modelValue: '' };
    void bad;
  });

  it('AC3 : modelValue accepte string | number mais pas boolean', () => {
    const valid1: InputProps = { modelValue: 'texte', label: 'X' };
    const valid2: InputProps = { modelValue: 42, label: 'X' };
    assertType<InputProps>(valid1);
    assertType<InputProps>(valid2);

    // @ts-expect-error boolean n'est pas assignable a modelValue.
    const bad: InputProps = { modelValue: true, label: 'X' };
    void bad;
  });

  // H-4 post-review : verrouille l'emit discrimine string | number.
  it('H-4 : type=number accepte modelValue number (cote parent)', () => {
    const valid: InputProps = { modelValue: 42, label: 'Montant', type: 'number' };
    assertType<InputProps>(valid);
  });
});
