import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import { axe, toHaveNoViolations } from 'jest-axe';
import Textarea from '../../../app/components/ui/Textarea.vue';
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

describe('ui/Textarea : compteur 3 seuils + triple defense (AC4)', () => {
  it('AC3 : les 3 sizes appliquent min-h-[XX] correct', () => {
    for (const size of FORM_SIZES) {
      const w = mount(Textarea, {
        props: { modelValue: '', label: 'X', size },
      });
      expect(w.find('textarea').classes()).toContain(SIZE_MIN_H[size]);
      w.unmount();
    }
  });

  it('AC3 : v-model bidirectionnel (input trigger emit update:modelValue)', async () => {
    const w = mount(Textarea, { props: { modelValue: '', label: 'C' } });
    const ta = w.find('textarea').element as HTMLTextAreaElement;
    ta.value = 'bonjour';
    await w.find('textarea').trigger('input');
    expect(w.emitted('update:modelValue')?.[0]?.[0]).toBe('bonjour');
    w.unmount();
  });

  it('AC4 : compteur < 350 -> text-gray-500 (pas d alerte couleur)', () => {
    const w = mount(Textarea, {
      props: { modelValue: 'a'.repeat(100), label: 'X' },
    });
    const counter = w.findAll('p').find((p) => p.text().includes('100/400'));
    expect(counter).toBeDefined();
    expect(counter?.classes()).toContain('text-gray-500');
    w.unmount();
  });

  it('AC4 : compteur >= 350 && < 400 -> text-brand-orange (seuil warn, role=status static M-1)', () => {
    const w = mount(Textarea, {
      props: { modelValue: 'a'.repeat(360), label: 'X' },
    });
    const counter = w.findAll('p').find((p) => p.text().includes('360/400'));
    expect(counter).toBeDefined();
    expect(counter?.classes()).toContain('text-brand-orange');
    // M-1 post-review : role=status + aria-live=polite STATIQUES (region existe
    // avant mutation, sinon NVDA/JAWS ratent la 1ere annonce).
    expect(counter?.attributes('role')).toBe('status');
    w.unmount();
  });

  it('AC4 : compteur >= 400 -> text-brand-red + role=status aria-live=polite + aria-atomic', () => {
    const w = mount(Textarea, {
      props: { modelValue: 'a'.repeat(400), label: 'X' },
    });
    const counter = w.findAll('p').find((p) => p.text().includes('400/400'));
    expect(counter).toBeDefined();
    expect(counter?.classes()).toContain('text-brand-red');
    expect(counter?.classes()).toContain('font-medium');
    expect(counter?.attributes('role')).toBe('status');
    expect(counter?.attributes('aria-live')).toBe('polite');
    expect(counter?.attributes('aria-atomic')).toBe('true');
    w.unmount();
  });

  it('AC4 : frappe > 400 tronquee a 400 exactement (defense en profondeur JS)', async () => {
    const w = mount(Textarea, {
      props: { modelValue: '', label: 'J', maxlength: 400 },
    });
    const ta = w.find('textarea').element as HTMLTextAreaElement;
    // Simule paste programmatique qui bypasse maxlength HTML native.
    ta.value = 'a'.repeat(410);
    await w.find('textarea').trigger('input');
    const emitted = w.emitted('update:modelValue');
    expect(emitted).toBeTruthy();
    const emittedValue = emitted?.[0]?.[0] as string;
    expect(emittedValue.length).toBe(400);
    // DOM value aussi tronquee (re-sync eviter desynchronisation).
    expect(ta.value.length).toBe(400);
    w.unmount();
  });

  it('AC4 : showCounter=false -> compteur pas rendu', () => {
    const w = mount(Textarea, {
      props: { modelValue: 'x', label: 'X', showCounter: false },
    });
    const counter = w.findAll('p').find((p) => p.text().includes('/'));
    expect(counter).toBeUndefined();
    w.unmount();
  });

  it('AC3 + AC5 : rows + maxlength HTML native + error state ARIA', () => {
    const w = mount(Textarea, {
      props: {
        modelValue: 'x',
        label: 'J',
        rows: 6,
        maxlength: 200,
        error: 'Obligatoire',
      },
    });
    const ta = w.find('textarea');
    expect(ta.attributes('rows')).toBe('6');
    expect(ta.attributes('maxlength')).toBe('200');
    expect(ta.attributes('aria-invalid')).toBe('true');
    expect(ta.classes()).toContain('border-brand-red');
    // Message d erreur visible avec role alert.
    expect(w.find('[role="alert"]').text()).toContain('Obligatoire');
    w.unmount();
  });

  it('AC5 : vitest-axe — default / error / disabled 0 violation', async () => {
    const defW = mount(Textarea, {
      props: { modelValue: '', label: 'Default' },
      attachTo: document.body,
    });
    expect(await axe(document.body, AXE_OPTIONS)).toHaveNoViolations();
    defW.unmount();

    const errW = mount(Textarea, {
      props: { modelValue: 'x', label: 'Err', error: 'Invalide' },
      attachTo: document.body,
    });
    expect(await axe(document.body, AXE_OPTIONS)).toHaveNoViolations();
    errW.unmount();

    const disW = mount(Textarea, {
      props: { modelValue: '', label: 'Dis', disabled: true },
      attachTo: document.body,
    });
    expect(await axe(document.body, AXE_OPTIONS)).toHaveNoViolations();
    disW.unmount();
  });
});
