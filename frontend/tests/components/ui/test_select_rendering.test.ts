import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import { axe, toHaveNoViolations } from 'jest-axe';
import Select from '../../../app/components/ui/Select.vue';
import { FORM_SIZES } from '../../../app/components/ui/registry';

expect.extend(toHaveNoViolations);

const SIZE_MIN_H: Record<(typeof FORM_SIZES)[number], string> = {
  sm: 'min-h-[36px]',
  md: 'min-h-[44px]',
  lg: 'min-h-[48px]',
};

const AXE_OPTIONS = {
  rules: {
    'color-contrast-enhanced': { enabled: false },
    region: { enabled: false },
  },
} as const;

const SECTORS = [
  { value: 'agri', label: 'Agriculture' },
  { value: 'energy', label: 'Energie' },
  { value: 'transport', label: 'Transport', disabled: true },
];

describe('ui/Select : rendu native + options + multiple (AC1 + AC3 + AC5)', () => {
  it('AC3 : options rendues avec label + value + disabled attribut', () => {
    const w = mount(Select, {
      props: { modelValue: '', label: 'Secteur', options: SECTORS },
    });
    const options = w.findAll('option');
    // 3 options (+ pas de placeholder).
    expect(options.length).toBe(3);
    expect(options[0]!.attributes('value')).toBe('agri');
    expect(options[0]!.text()).toBe('Agriculture');
    // Option disabled transmise.
    const transport = options.find((o) => o.attributes('value') === 'transport');
    expect(transport?.attributes('disabled')).toBeDefined();
    w.unmount();
  });

  it('AC3 : les 3 sizes appliquent min-h-[XX]', () => {
    for (const size of FORM_SIZES) {
      const w = mount(Select, {
        props: { modelValue: '', label: 'X', options: SECTORS, size },
      });
      expect(w.find('select').classes()).toContain(SIZE_MIN_H[size]);
      w.unmount();
    }
  });

  it('AC3 : change emit update:modelValue avec value string (single)', async () => {
    const w = mount(Select, {
      props: { modelValue: '', label: 'Secteur', options: SECTORS },
    });
    const sel = w.find('select').element as HTMLSelectElement;
    sel.value = 'energy';
    await w.find('select').trigger('change');
    const emitted = w.emitted('update:modelValue');
    expect(emitted).toBeTruthy();
    expect(emitted?.[0]?.[0]).toBe('energy');
    w.unmount();
  });

  it('AC3 : placeholder rendu comme <option value="" disabled>', () => {
    const w = mount(Select, {
      props: {
        modelValue: '',
        label: 'Secteur',
        options: SECTORS,
        placeholder: '-- Selectionner --',
      },
    });
    const options = w.findAll('option');
    expect(options.length).toBe(4);
    expect(options[0]!.text()).toBe('-- Selectionner --');
    expect(options[0]!.attributes('value')).toBe('');
    expect(options[0]!.attributes('disabled')).toBeDefined();
    w.unmount();
  });

  it('AC3 : multiple=true -> attr multiple + selectedOptions emit array', async () => {
    const w = mount(Select, {
      props: {
        modelValue: [],
        label: 'ODD',
        options: [
          { value: '8', label: 'ODD 8' },
          { value: '9', label: 'ODD 9' },
          { value: '13', label: 'ODD 13' },
        ],
        multiple: true,
      },
    });
    const sel = w.find('select');
    expect(sel.attributes('multiple')).toBeDefined();

    // Selectionne 2 options via DOM direct.
    const el = sel.element as HTMLSelectElement;
    Array.from(el.options).forEach((o) => {
      o.selected = o.value === '8' || o.value === '13';
    });
    await sel.trigger('change');
    const emitted = w.emitted('update:modelValue');
    expect(emitted).toBeTruthy();
    expect(emitted?.[0]?.[0]).toEqual(['8', '13']);
    w.unmount();
  });

  it('AC5 : required + error + disabled — ARIA + attributs HTML', () => {
    const reqW = mount(Select, {
      props: { modelValue: '', label: 'X', options: SECTORS, required: true },
    });
    expect(reqW.find('select').attributes('aria-required')).toBe('true');
    expect(reqW.find('select').attributes('required')).toBeDefined();
    reqW.unmount();

    const errW = mount(Select, {
      props: {
        modelValue: '',
        label: 'X',
        options: SECTORS,
        error: 'Selection obligatoire',
      },
    });
    expect(errW.find('select').attributes('aria-invalid')).toBe('true');
    expect(errW.find('select').classes()).toContain('border-brand-red');
    expect(errW.find('[role="alert"]').text()).toContain('Selection obligatoire');
    errW.unmount();

    const disW = mount(Select, {
      props: {
        modelValue: '',
        label: 'X',
        options: SECTORS,
        disabled: true,
      },
    });
    expect(disW.find('select').attributes('disabled')).toBeDefined();
    disW.unmount();
  });

  it('AC5 : label for + select id associes (useId auto)', () => {
    const w = mount(Select, {
      props: { modelValue: '', label: 'Auto', options: SECTORS },
    });
    const labelFor = w.find('label').attributes('for');
    const selectId = w.find('select').attributes('id');
    expect(labelFor).toBeDefined();
    expect(labelFor).toBe(selectId);
    w.unmount();
  });

  it('AC5 : vitest-axe — default / error / disabled 0 violation', async () => {
    const defW = mount(Select, {
      props: { modelValue: '', label: 'Default', options: SECTORS },
      attachTo: document.body,
    });
    expect(await axe(document.body, AXE_OPTIONS)).toHaveNoViolations();
    defW.unmount();

    const errW = mount(Select, {
      props: { modelValue: '', label: 'Err', options: SECTORS, error: 'X' },
      attachTo: document.body,
    });
    expect(await axe(document.body, AXE_OPTIONS)).toHaveNoViolations();
    errW.unmount();

    const disW = mount(Select, {
      props: { modelValue: '', label: 'Dis', options: SECTORS, disabled: true },
      attachTo: document.body,
    });
    expect(await axe(document.body, AXE_OPTIONS)).toHaveNoViolations();
    disW.unmount();
  });
});
