import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import { axe, toHaveNoViolations } from 'jest-axe';
import Input from '../../../app/components/ui/Input.vue';
import {
  INPUT_TYPES,
  FORM_SIZES,
} from '../../../app/components/ui/registry';

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

describe('ui/Input : rendu 7 types x 3 sizes (AC1 + AC3 + AC6)', () => {
  it('AC3 : les 7 types HTML5 rendent l attribut type correct', () => {
    for (const type of INPUT_TYPES) {
      const w = mount(Input, {
        props: { modelValue: '', label: `Label ${type}`, type },
      });
      expect(w.find('input').attributes('type')).toBe(type);
      w.unmount();
    }
  });

  it('AC6 : les 3 sizes appliquent min-h-[XX] correct (touch target)', () => {
    for (const size of FORM_SIZES) {
      const w = mount(Input, {
        props: { modelValue: '', label: 'X', size },
      });
      expect(w.find('input').classes()).toContain(SIZE_MIN_H[size]);
      w.unmount();
    }
  });

  it('AC3 : v-model bidirectionnel — input DOM declenche update:modelValue', async () => {
    const w = mount(Input, { props: { modelValue: '', label: 'Email' } });
    const inputEl = w.find('input').element as HTMLInputElement;
    inputEl.value = 'abc@example.com';
    await w.find('input').trigger('input');
    const emitted = w.emitted('update:modelValue');
    expect(emitted).toBeTruthy();
    expect(emitted?.[0]?.[0]).toBe('abc@example.com');
    w.unmount();
  });

  it('AC3 + AC5 : required + error + disabled + readonly — attributs HTML + ARIA', () => {
    // required
    const reqW = mount(Input, {
      props: { modelValue: '', label: 'Nom', required: true },
    });
    const reqInput = reqW.find('input');
    expect(reqInput.attributes('required')).toBeDefined();
    expect(reqInput.attributes('aria-required')).toBe('true');
    // Asterisque rouge apres le label, aria-hidden (AC5).
    expect(reqW.find('label span.text-brand-red').exists()).toBe(true);
    expect(reqW.find('label span.text-brand-red').attributes('aria-hidden')).toBe('true');
    reqW.unmount();

    // error
    const errW = mount(Input, {
      props: { modelValue: 'x', label: 'Email', error: 'Format invalide' },
    });
    const errInput = errW.find('input');
    expect(errInput.attributes('aria-invalid')).toBe('true');
    const describedBy = errInput.attributes('aria-describedby');
    expect(describedBy).toBeDefined();
    // Element decrit par aria-describedby existe et contient le message.
    const errorPara = errW.find('[role="alert"]');
    expect(errorPara.exists()).toBe(true);
    expect(errorPara.text()).toContain('Format invalide');
    expect(errInput.classes()).toContain('border-brand-red');
    errW.unmount();

    // disabled
    const disW = mount(Input, {
      props: { modelValue: '', label: 'X', disabled: true },
    });
    expect(disW.find('input').attributes('disabled')).toBeDefined();
    disW.unmount();

    // readonly
    const roW = mount(Input, {
      props: { modelValue: 'fixed', label: 'X', readonly: true },
    });
    expect(roW.find('input').attributes('readonly')).toBeDefined();
    roW.unmount();
  });

  it('AC5 : aria-describedby combine hint + error (les 2 IDs)', () => {
    const w = mount(Input, {
      props: {
        modelValue: '',
        label: 'Email',
        hint: 'Utilise pour les notifications',
        error: 'Format invalide',
      },
    });
    const describedBy = w.find('input').attributes('aria-describedby') ?? '';
    const ids = describedBy.split(' ');
    expect(ids.length).toBe(2);
    expect(ids.some((id) => id.endsWith('-hint'))).toBe(true);
    expect(ids.some((id) => id.endsWith('-error'))).toBe(true);
    w.unmount();
  });

  it('Q5 : slots #iconLeft et #iconRight rendus avec aria-hidden + padding ajuste', () => {
    const w = mount(Input, {
      props: { modelValue: '', label: 'Search' },
      slots: {
        iconLeft: '<span class="stub-left">L</span>',
        iconRight: '<span class="stub-right">R</span>',
      },
    });
    const leftWrap = w.find('span.stub-left')?.element?.parentElement;
    const rightWrap = w.find('span.stub-right')?.element?.parentElement;
    expect(leftWrap?.getAttribute('aria-hidden')).toBe('true');
    expect(rightWrap?.getAttribute('aria-hidden')).toBe('true');
    // Padding ajuste pour faire place aux icones.
    const inputClasses = w.find('input').classes();
    expect(inputClasses).toContain('pl-10');
    expect(inputClasses).toContain('pr-10');
    w.unmount();
  });

  it('AC6 : inputmode auto pour type email/tel/search/url + override explicite', () => {
    const emailW = mount(Input, {
      props: { modelValue: '', label: 'X', type: 'email' },
    });
    expect(emailW.find('input').attributes('inputmode')).toBe('email');
    emailW.unmount();

    const telW = mount(Input, {
      props: { modelValue: '', label: 'X', type: 'tel' },
    });
    expect(telW.find('input').attributes('inputmode')).toBe('tel');
    telW.unmount();

    // Override explicite : type=number + inputmode=numeric (piege #11 codemap).
    const numW = mount(Input, {
      props: {
        modelValue: 0,
        label: 'Montant',
        type: 'number',
        inputmode: 'numeric',
      },
    });
    expect(numW.find('input').attributes('inputmode')).toBe('numeric');
    numW.unmount();
  });

  it('AC5 : label for + input id associes (useId auto si prop id absente)', () => {
    const w = mount(Input, { props: { modelValue: '', label: 'Auto' } });
    const labelFor = w.find('label').attributes('for');
    const inputId = w.find('input').attributes('id');
    expect(labelFor).toBeDefined();
    expect(inputId).toBeDefined();
    expect(labelFor).toBe(inputId);
    w.unmount();

    // Prop id explicite preservee.
    const w2 = mount(Input, {
      props: { modelValue: '', label: 'Explicit', id: 'my-input-x' },
    });
    expect(w2.find('label').attributes('for')).toBe('my-input-x');
    expect(w2.find('input').attributes('id')).toBe('my-input-x');
    w2.unmount();
  });

  it('AC5 : vitest-axe — default / error / disabled 0 violation (jest-axe fallback)', async () => {
    // Default
    const defW = mount(Input, {
      props: { modelValue: '', label: 'Default' },
      attachTo: document.body,
    });
    expect(await axe(document.body, AXE_OPTIONS)).toHaveNoViolations();
    defW.unmount();

    // Error state
    const errW = mount(Input, {
      props: { modelValue: 'x', label: 'Err', error: 'Invalide' },
      attachTo: document.body,
    });
    expect(await axe(document.body, AXE_OPTIONS)).toHaveNoViolations();
    errW.unmount();

    // Disabled state
    const disW = mount(Input, {
      props: { modelValue: '', label: 'Dis', disabled: true },
      attachTo: document.body,
    });
    expect(await axe(document.body, AXE_OPTIONS)).toHaveNoViolations();
    disW.unmount();
  });
});
