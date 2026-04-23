/**
 * Compile-time type tests pour ui/Combobox (AC1 Story 10.19).
 * Pattern byte-identique 10.15-10.18 HIGH-1 compile-time enforcement.
 *
 * Note generic : `ComboboxProps<T>` est parametree par T extends string | number.
 * TypeScript 5.x ne supporte pas nativement la discriminated union
 * `{multiple:true, modelValue:T[]}` via defineProps (DEF-10.19-1 deferred) →
 * fallback permissif `T | T[] | null` accepte Phase 0.
 */
import { describe, it, expectTypeOf } from 'vitest';
import type { ComboboxMode } from '../../../app/components/ui/registry';

// Signature publique reflet byte-identique de ComboboxProps (Combobox.vue).
// Declaree localement pour eviter import d'un .vue en typecheck.
interface ComboboxOption<TValue extends string | number> {
  value: TValue;
  label: string;
  disabled?: boolean;
  group?: string;
}

interface ComboboxProps<TValue extends string | number = string> {
  modelValue: TValue | TValue[] | null;
  options: Array<ComboboxOption<TValue>>;
  label: string;
  multiple?: boolean;
  placeholder?: string;
  emptyLabel?: string;
  searchable?: boolean;
  disabled?: boolean;
  required?: boolean;
  open?: boolean;
  /** L-4 patch — label i18n du bouton d'effacement de la recherche. */
  cancelLabel?: string;
}

describe('ui/Combobox : AC1 type safety (compile-time)', () => {
  it("ComboboxMode inclut exactement 'single' | 'multiple'", () => {
    expectTypeOf<ComboboxMode>().toEqualTypeOf<'single' | 'multiple'>();
  });

  it('modelValue: string valide (generic default string)', () => {
    const ok: ComboboxProps = {
      modelValue: 'sn',
      options: [{ value: 'sn', label: 'Sénégal' }],
      label: 'Pays',
    };
    void ok;
  });

  it('modelValue: string[] valide pour multi-select', () => {
    const ok: ComboboxProps = {
      modelValue: ['sn', 'ci'],
      options: [
        { value: 'sn', label: 'Sénégal' },
        { value: 'ci', label: "Côte d'Ivoire" },
      ],
      label: 'Pays',
      multiple: true,
    };
    void ok;
  });

  it('modelValue: null valide (aucune selection)', () => {
    const ok: ComboboxProps = {
      modelValue: null,
      options: [],
      label: 'Pays',
    };
    void ok;
  });

  it('modelValue: boolean est rejete', () => {
    // @ts-expect-error modelValue doit etre T | T[] | null, pas boolean
    const bad: ComboboxProps = {
      modelValue: true,
      options: [],
      label: 'Pays',
    };
    void bad;
  });

  it('modelValue: 42 est rejete sans instanciation generic <number>', () => {
    // @ts-expect-error generic default string — 42 est un number
    const bad: ComboboxProps = {
      modelValue: 42,
      options: [],
      label: 'Pays',
    };
    void bad;
  });

  it('ComboboxProps<number> accepte modelValue number', () => {
    const ok: ComboboxProps<number> = {
      modelValue: 42,
      options: [{ value: 42, label: 'Quarante-deux' }],
      label: 'Seuil',
    };
    void ok;
  });

  it("multiple: 'yes' est rejete (boolean requis)", () => {
    // @ts-expect-error multiple doit etre boolean, pas string
    const bad: ComboboxProps = {
      modelValue: null,
      options: [],
      label: 'Pays',
      multiple: 'yes',
    };
    void bad;
  });

  it('options sans {value, label} est rejete', () => {
    // @ts-expect-error options[0] manque value + label requis
    const bad: ComboboxProps = {
      modelValue: null,
      options: [{ foo: 'bar' }],
      label: 'Pays',
    };
    void bad;
  });

  it('options[0].value: null est rejete (T requis, null exclue)', () => {
    // @ts-expect-error value doit etre T extends string | number, pas null
    const bad: ComboboxProps = {
      modelValue: null,
      options: [{ value: null, label: 'vide' }],
      label: 'Pays',
    };
    void bad;
  });

  it('label manquant est rejete (requis a11y)', () => {
    // @ts-expect-error label requis (aria-labelledby)
    const bad: ComboboxProps = {
      modelValue: null,
      options: [],
    };
    void bad;
  });

  it("searchable: 'maybe' est rejete (boolean strict)", () => {
    // @ts-expect-error searchable doit etre boolean
    const bad: ComboboxProps = {
      modelValue: null,
      options: [],
      label: 'Pays',
      searchable: 'maybe',
    };
    void bad;
  });

  it('L-4 cancelLabel: string valide', () => {
    const ok: ComboboxProps = {
      modelValue: null,
      options: [],
      label: 'Pays',
      cancelLabel: 'Clear search',
    };
    void ok;
  });

  it('L-4 cancelLabel: number est rejete (string strict)', () => {
    // @ts-expect-error cancelLabel doit etre string
    const bad: ComboboxProps = {
      modelValue: null,
      options: [],
      label: 'Pays',
      cancelLabel: 42,
    };
    void bad;
  });
});
