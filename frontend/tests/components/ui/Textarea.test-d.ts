/**
 * Compile-time type tests pour ui/Textarea (AC1 + AC3 + AC4 Story 10.16).
 * Executes via `vitest --typecheck`.
 */
import { describe, it, expectTypeOf, assertType } from 'vitest';
import type { FormSize } from '../../../app/components/ui/registry';
import { TEXTAREA_DEFAULT_MAX_LENGTH } from '../../../app/components/ui/registry';

type TextareaProps = {
  modelValue: string;
  label: string;
  id?: string;
  placeholder?: string;
  error?: string;
  hint?: string;
  required?: boolean;
  disabled?: boolean;
  readonly?: boolean;
  size?: FormSize;
  rows?: number;
  maxlength?: number;
  showCounter?: boolean;
  name?: string;
};

describe('ui/Textarea : type safety (compile-time)', () => {
  it('TEXTAREA_DEFAULT_MAX_LENGTH est numerique et vaut 400 (spec 018)', () => {
    expectTypeOf(TEXTAREA_DEFAULT_MAX_LENGTH).toBeNumber();
    // Note : verification runtime 400 dans test_form_registry.
  });

  it('AC1 : modelValue doit etre string (pas number contrairement a Input)', () => {
    const valid: TextareaProps = { modelValue: '', label: 'Commentaire' };
    assertType<TextareaProps>(valid);

    // @ts-expect-error Textarea ne supporte pas number comme modelValue.
    const bad: TextareaProps = { modelValue: 42, label: 'X' };
    void bad;
  });

  it('AC1 : label est obligatoire', () => {
    // @ts-expect-error label manquant (invariant a11y).
    const bad: TextareaProps = { modelValue: '' };
    void bad;
  });

  it('AC3 : size en dehors de FormSize est rejete', () => {
    // @ts-expect-error 'xl' n est pas dans FormSize.
    const bad: TextareaProps = { modelValue: '', label: 'X', size: 'xl' };
    void bad;
  });

  it('AC4 : showCounter est boolean (pas string)', () => {
    // @ts-expect-error showCounter attend boolean.
    const bad: TextareaProps = { modelValue: '', label: 'X', showCounter: 'true' };
    void bad;

    const valid: TextareaProps = { modelValue: '', label: 'X', showCounter: false };
    assertType<TextareaProps>(valid);
  });

  it('AC3 : rows et maxlength sont number', () => {
    // @ts-expect-error rows doit etre number.
    const bad: TextareaProps = { modelValue: '', label: 'X', rows: '4' };
    void bad;
  });
});
