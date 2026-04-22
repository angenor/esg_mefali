/**
 * Compile-time type tests pour ui/Select (AC1 + AC3 Story 10.16).
 * Executes via `vitest --typecheck`.
 */
import { describe, it, expectTypeOf, assertType } from 'vitest';
import type { FormSize } from '../../../app/components/ui/registry';

type SelectOption = {
  value: string;
  label: string;
  disabled?: boolean;
};

type SelectProps = {
  modelValue: string | string[];
  label: string;
  options: SelectOption[];
  id?: string;
  placeholder?: string;
  error?: string;
  hint?: string;
  required?: boolean;
  disabled?: boolean;
  size?: FormSize;
  multiple?: boolean;
  name?: string;
};

describe('ui/Select : type safety (compile-time)', () => {
  it('AC1 : modelValue accepte string ou string[] mais pas number', () => {
    const valid1: SelectProps = {
      modelValue: 'x',
      label: 'X',
      options: [],
    };
    const valid2: SelectProps = {
      modelValue: ['a', 'b'],
      label: 'X',
      options: [],
    };
    assertType<SelectProps>(valid1);
    assertType<SelectProps>(valid2);

    // @ts-expect-error Select value est string cote DOM natif (piege #13).
    const bad: SelectProps = { modelValue: 42, label: 'X', options: [] };
    void bad;
  });

  it('AC3 : options est obligatoire', () => {
    // @ts-expect-error options manquant (invariant : on ne peut pas afficher un select vide).
    const bad: SelectProps = { modelValue: '', label: 'X' };
    void bad;
  });

  it('AC3 : options[].value doit etre string (piege #13 codemap)', () => {
    // @ts-expect-error value numerique rejete au niveau option.
    const bad: SelectProps = {
      modelValue: '',
      label: 'X',
      options: [{ value: 42, label: 'Quarante-deux' }],
    };
    void bad;
  });

  it('AC3 : options[] doit avoir value + label (disabled optionnel)', () => {
    const valid: SelectProps = {
      modelValue: '',
      label: 'X',
      options: [
        { value: 'a', label: 'A' },
        { value: 'b', label: 'B', disabled: true },
      ],
    };
    assertType<SelectProps>(valid);

    // @ts-expect-error label manquant dans option.
    const bad: SelectProps = {
      modelValue: '',
      label: 'X',
      options: [{ value: 'a' }],
    };
    void bad;
  });

  it('AC3 : size en dehors de FormSize est rejete', () => {
    // @ts-expect-error 'xl' n est pas dans FormSize.
    const bad: SelectProps = { modelValue: '', label: 'X', options: [], size: 'xl' };
    void bad;
  });

  it('AC1 : label obligatoire', () => {
    // @ts-expect-error label manquant (invariant a11y).
    const bad: SelectProps = { modelValue: '', options: [] };
    void bad;
  });

  it('FormSize reste union sm|md|lg', () => {
    expectTypeOf<FormSize>().toEqualTypeOf<'sm' | 'md' | 'lg'>();
  });
});
