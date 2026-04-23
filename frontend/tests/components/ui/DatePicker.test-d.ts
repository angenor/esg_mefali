/**
 * Compile-time type tests pour ui/DatePicker (AC1 Story 10.20).
 * Pattern byte-identique 10.15-10.19 HIGH-1 compile-time enforcement.
 *
 * Union discriminee DatePickerProps = DatePickerSingleProps | DatePickerRangeProps
 * via prop `mode: 'single' | 'range'` + modelValue coherent.
 *
 * Piege #43 : @internationalized/date CalendarDate vs Date native.
 * Reka UI Calendar n'accepte PAS `new Date(...)` → utiliser `CalendarDate` /
 * `parseDate` / `today(getLocalTimeZone())`.
 */
import { describe, it, expectTypeOf } from 'vitest';
import { CalendarDate, type DateValue } from '@internationalized/date';
import type { DatePickerMode } from '../../../app/components/ui/registry';

// Signatures publiques reflet byte-identique (DatePicker.vue).
// Declarees localement pour eviter import d'un .vue en typecheck.
interface DateRange {
  start: DateValue | null;
  end: DateValue | null;
}

interface DatePickerSingleProps {
  mode?: 'single';
  modelValue: DateValue | null;
  defaultValue?: DateValue;
  label: string;
  placeholder?: string;
  minValue?: DateValue;
  maxValue?: DateValue;
  isDateDisabled?: (date: DateValue) => boolean;
  locale?: string;
  disabled?: boolean;
  readonly?: boolean;
  required?: boolean;
  showClear?: boolean;
  clearLabel?: string;
  customFormat?: Intl.DateTimeFormatOptions;
  rangePartialLabel?: string;
}

interface DatePickerRangeProps
  extends Omit<DatePickerSingleProps, 'mode' | 'modelValue'> {
  mode: 'range';
  modelValue: DateRange;
}

type DatePickerProps = DatePickerSingleProps | DatePickerRangeProps;

describe('ui/DatePicker : AC1 type safety (compile-time)', () => {
  it("DatePickerMode inclut exactement 'single' | 'range'", () => {
    expectTypeOf<DatePickerMode>().toEqualTypeOf<'single' | 'range'>();
  });

  it('modelValue: CalendarDate valide (single default)', () => {
    const ok: DatePickerProps = {
      modelValue: new CalendarDate(2026, 4, 15),
      label: 'Date deadline',
    };
    void ok;
  });

  it('modelValue: null valide (pas de selection)', () => {
    const ok: DatePickerProps = {
      modelValue: null,
      label: 'Date',
    };
    void ok;
  });

  it('range: {start, end} CalendarDate valide', () => {
    const ok: DatePickerProps = {
      mode: 'range',
      modelValue: {
        start: new CalendarDate(2026, 4, 1),
        end: new CalendarDate(2026, 4, 30),
      },
      label: 'Periode',
    };
    void ok;
  });

  it("mode: 'invalid' est rejete (hors union 'single' | 'range')", () => {
    // @ts-expect-error mode 'invalid' hors union
    const bad: DatePickerProps = {
      mode: 'invalid',
      modelValue: null,
      label: 'Date',
    };
    void bad;
  });

  it('modelValue: string (ISO) est rejete (DateValue requis)', () => {
    // @ts-expect-error modelValue doit etre DateValue pas string ISO brute
    const bad: DatePickerProps = {
      modelValue: '2026-04-15',
      label: 'Date',
    };
    void bad;
  });

  it('minValue: Date native est rejete (CalendarDate requis piege #43)', () => {
    // @ts-expect-error minValue doit etre DateValue, pas Date native JS
    const bad: DatePickerProps = {
      modelValue: null,
      label: 'Date',
      minValue: new Date(),
    };
    void bad;
  });

  it('range: modelValue null (sans {start, end}) est rejete', () => {
    // @ts-expect-error mode='range' exige modelValue: DateRange pas null
    const bad: DatePickerProps = {
      mode: 'range',
      modelValue: null,
      label: 'Periode',
    };
    void bad;
  });

  it("showClear: 'yes' est rejete (boolean strict)", () => {
    // @ts-expect-error showClear doit etre boolean
    const bad: DatePickerProps = {
      modelValue: null,
      label: 'Date',
      showClear: 'yes',
    };
    void bad;
  });

  it('isDateDisabled: null est rejete (fonction requise si present)', () => {
    // @ts-expect-error isDateDisabled doit etre fonction, pas null
    const bad: DatePickerProps = {
      modelValue: null,
      label: 'Date',
      isDateDisabled: null,
    };
    void bad;
  });

  it('label manquant est rejete (requis a11y aria-labelledby)', () => {
    // @ts-expect-error label requis pour aria-labelledby
    const bad: DatePickerProps = {
      modelValue: null,
    };
    void bad;
  });

  it('isDateDisabled: (date) => boolean valide', () => {
    const ok: DatePickerProps = {
      modelValue: null,
      label: 'Date',
      isDateDisabled: (date: DateValue) => date.day === 15,
    };
    void ok;
  });

  it('clearLabel: string override valide', () => {
    const ok: DatePickerProps = {
      modelValue: null,
      label: 'Date',
      showClear: true,
      clearLabel: 'Reinitialiser',
    };
    void ok;
  });

  it("clearLabel: number est rejete (string strict AC9)", () => {
    // @ts-expect-error clearLabel doit etre string
    const bad: DatePickerProps = {
      modelValue: null,
      label: 'Date',
      clearLabel: 42,
    };
    void bad;
  });
});
