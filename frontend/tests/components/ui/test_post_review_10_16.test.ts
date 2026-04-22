/**
 * Tests post-review Story 10.16 (2026-04-22).
 * Couvre les 4 patches HIGH + M-1/M-2/M-4 + L-2/L-6 via render DOM reel (pas mutation imperative).
 *
 * Reference : _bmad-output/implementation-artifacts/10-16-code-review-2026-04-22.md
 */
import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import { nextTick } from 'vue';
import Input from '../../../app/components/ui/Input.vue';
import Textarea from '../../../app/components/ui/Textarea.vue';
import Select from '../../../app/components/ui/Select.vue';

describe('H-1 : aria-describedby combine hint + error (pas override)', () => {
  it('Input : hint + error simultanes → 2 IDs dans aria-describedby + les 2 <p> rendus', () => {
    const w = mount(Input, {
      props: {
        modelValue: 'x',
        label: 'Email',
        hint: 'Utilise pour notifications',
        error: 'Format invalide',
      },
    });
    const input = w.find('input');
    const describedBy = input.attributes('aria-describedby') ?? '';
    const ids = describedBy.split(' ');
    expect(ids.length).toBe(2);
    expect(ids.some((id) => id.endsWith('-hint'))).toBe(true);
    expect(ids.some((id) => id.endsWith('-error'))).toBe(true);

    // Les 2 <p> doivent etre presents dans le DOM (H-1 fix).
    const hintId = ids.find((id) => id.endsWith('-hint'))!;
    const errorId = ids.find((id) => id.endsWith('-error'))!;
    expect(w.find(`#${hintId}`).exists()).toBe(true);
    expect(w.find(`#${errorId}`).exists()).toBe(true);
    w.unmount();
  });

  it('Textarea : hint + error simultanes → 3 IDs (hint + error + counter)', () => {
    const w = mount(Textarea, {
      props: {
        modelValue: 'x',
        label: 'Justification',
        hint: 'Soyez concis',
        error: 'Obligatoire',
      },
    });
    const describedBy = w.find('textarea').attributes('aria-describedby') ?? '';
    const ids = describedBy.split(' ');
    expect(ids.some((id) => id.endsWith('-hint'))).toBe(true);
    expect(ids.some((id) => id.endsWith('-error'))).toBe(true);
    expect(ids.some((id) => id.endsWith('-counter'))).toBe(true);
    const hintId = ids.find((id) => id.endsWith('-hint'))!;
    const errorId = ids.find((id) => id.endsWith('-error'))!;
    expect(w.find(`#${hintId}`).exists()).toBe(true);
    expect(w.find(`#${errorId}`).exists()).toBe(true);
    w.unmount();
  });

  it('Select : hint + error simultanes → les 2 IDs + les 2 <p> rendus', () => {
    const w = mount(Select, {
      props: {
        modelValue: '',
        label: 'Secteur',
        options: [{ value: 'a', label: 'A' }],
        hint: 'Influence scoring ESG',
        error: 'Selection obligatoire',
      },
    });
    const describedBy = w.find('select').attributes('aria-describedby') ?? '';
    const ids = describedBy.split(' ');
    expect(ids.length).toBe(2);
    const hintId = ids.find((id) => id.endsWith('-hint'))!;
    const errorId = ids.find((id) => id.endsWith('-error'))!;
    expect(w.find(`#${hintId}`).exists()).toBe(true);
    expect(w.find(`#${errorId}`).exists()).toBe(true);
    w.unmount();
  });
});

describe('H-2 : Textarea IME composition (CJK + dead-keys FR)', () => {
  it('pendant compositionstart → compositionend, target.value n\'est PAS tronque', async () => {
    const w = mount(Textarea, {
      props: { modelValue: '', label: 'X', maxlength: 400 },
    });
    const ta = w.find('textarea');
    const el = ta.element as HTMLTextAreaElement;

    // Simule composition IME : compositionstart + input intermediaire.
    await ta.trigger('compositionstart');
    el.value = 'a'.repeat(450); // Depasse maxlength mais pendant composition.
    await ta.trigger('input');

    // Pendant composition : emit sans troncature (defense 1 = HTML maxlength
    // bloque user input clavier standard, mais tests programmatique).
    const emittedDuring = w.emitted('update:modelValue');
    expect(emittedDuring).toBeTruthy();
    expect(emittedDuring?.[0]?.[0]).toBe('a'.repeat(450));
    // DOM value intact pendant composition (pas de mutation).
    expect(el.value.length).toBe(450);

    // compositionend : troncature re-appliquee.
    await ta.trigger('compositionend');
    const emittedAfter = w.emitted('update:modelValue');
    expect(emittedAfter?.[emittedAfter.length - 1]?.[0]).toBe('a'.repeat(400));
    w.unmount();
  });

  it('input sans composition : troncature immediate (comportement standard)', async () => {
    const w = mount(Textarea, {
      props: { modelValue: '', label: 'X', maxlength: 400 },
    });
    const ta = w.find('textarea');
    const el = ta.element as HTMLTextAreaElement;
    el.value = 'b'.repeat(410);
    await ta.trigger('input');
    const emitted = w.emitted('update:modelValue');
    expect(emitted?.[0]?.[0]).toBe('b'.repeat(400));
    w.unmount();
  });
});

describe('H-3 : Select multiple → selectedOptions refletent modelValue (pas mutation imperative)', () => {
  it('modelValue tableau → options.selected synchronises depuis DOM reel', async () => {
    const w = mount(Select, {
      attachTo: document.body,
      props: {
        modelValue: ['8', '13'],
        label: 'ODD',
        multiple: true,
        options: [
          { value: '8', label: 'ODD 8' },
          { value: '9', label: 'ODD 9' },
          { value: '13', label: 'ODD 13' },
        ],
      },
    });
    await nextTick();
    await nextTick();
    const el = w.find('select').element as HTMLSelectElement;
    const selected = Array.from(el.selectedOptions).map((o) => o.value);
    expect(selected).toEqual(['8', '13']);
    w.unmount();
  });

  it('modelValue change → re-sync selectedOptions', async () => {
    const w = mount(Select, {
      attachTo: document.body,
      props: {
        modelValue: ['8'],
        label: 'ODD',
        multiple: true,
        options: [
          { value: '8', label: 'ODD 8' },
          { value: '13', label: 'ODD 13' },
        ],
      },
    });
    await nextTick();
    await nextTick();
    await w.setProps({ modelValue: ['13'] });
    await nextTick();
    await nextTick();
    const el = w.find('select').element as HTMLSelectElement;
    expect(Array.from(el.selectedOptions).map((o) => o.value)).toEqual(['13']);
    w.unmount();
  });
});

describe('H-4 : Input type=number emet Number (pas string)', () => {
  it('type=number avec valeur numerique → emit Number', async () => {
    const w = mount(Input, {
      props: { modelValue: 0, label: 'Montant', type: 'number' },
    });
    const el = w.find('input').element as HTMLInputElement;
    el.value = '42';
    await w.find('input').trigger('input');
    const emitted = w.emitted('update:modelValue');
    expect(emitted).toBeTruthy();
    expect(typeof emitted?.[0]?.[0]).toBe('number');
    expect(emitted?.[0]?.[0]).toBe(42);
    w.unmount();
  });

  it('type=number avec valeur vide → emit chaine vide (pas NaN)', async () => {
    const w = mount(Input, {
      props: { modelValue: 10, label: 'Montant', type: 'number' },
    });
    const el = w.find('input').element as HTMLInputElement;
    el.value = '';
    await w.find('input').trigger('input');
    const emitted = w.emitted('update:modelValue');
    expect(emitted?.[0]?.[0]).toBe('');
    w.unmount();
  });

  it('type=text : emit string (comportement inchange)', async () => {
    const w = mount(Input, {
      props: { modelValue: '', label: 'Nom', type: 'text' },
    });
    const el = w.find('input').element as HTMLInputElement;
    el.value = 'hello';
    await w.find('input').trigger('input');
    const emitted = w.emitted('update:modelValue');
    expect(typeof emitted?.[0]?.[0]).toBe('string');
    expect(emitted?.[0]?.[0]).toBe('hello');
    w.unmount();
  });
});

describe('M-1 : Textarea counter aria-live statique (pas toggle dynamique)', () => {
  it('role=status + aria-live=polite + aria-atomic toujours presents', () => {
    // Counter gray (< 350) : region existe deja pour etre prete aux changements.
    const w = mount(Textarea, {
      props: { modelValue: 'a'.repeat(100), label: 'X' },
    });
    const counter = w.findAll('p').find((p) => p.text().includes('100/400'));
    expect(counter?.attributes('role')).toBe('status');
    expect(counter?.attributes('aria-live')).toBe('polite');
    expect(counter?.attributes('aria-atomic')).toBe('true');
    w.unmount();
  });
});

describe('M-2 : Textarea preserve selectionRange lors de troncature', () => {
  it('paste mid-string → caret reste dans la position valide', async () => {
    const w = mount(Textarea, {
      props: { modelValue: 'a'.repeat(380), label: 'X', maxlength: 400 },
      attachTo: document.body,
    });
    const el = w.find('textarea').element as HTMLTextAreaElement;
    el.value = 'a'.repeat(100) + 'PASTE_MIDDLE' + 'a'.repeat(330); // 442 chars
    el.setSelectionRange(112, 112); // caret juste apres "PASTE_MIDDLE"
    await w.find('textarea').trigger('input');
    // Post-troncature : caret doit etre <= 400 (preservation).
    expect(el.selectionStart).toBeLessThanOrEqual(400);
    expect(el.selectionEnd).toBeLessThanOrEqual(400);
    w.unmount();
  });
});

describe('M-4 : Input defense troncature JS (parite avec Textarea)', () => {
  it('type=text maxlength bypass programmatique → troncature JS', async () => {
    const w = mount(Input, {
      props: { modelValue: '', label: 'Nom', type: 'text', maxlength: 50 },
    });
    const el = w.find('input').element as HTMLInputElement;
    el.value = 'x'.repeat(100);
    await w.find('input').trigger('input');
    const emitted = w.emitted('update:modelValue');
    expect(emitted?.[0]?.[0]).toBe('x'.repeat(50));
    // DOM re-sync.
    expect(el.value.length).toBe(50);
    w.unmount();
  });

  it('type=number : pas de troncature JS (slice inapplique)', async () => {
    const w = mount(Input, {
      props: { modelValue: 0, label: 'X', type: 'number' },
    });
    const el = w.find('input').element as HTMLInputElement;
    el.value = '123456';
    await w.find('input').trigger('input');
    const emitted = w.emitted('update:modelValue');
    expect(emitted?.[0]?.[0]).toBe(123456);
    w.unmount();
  });
});

describe('L-2 : Input type=search — clear X natif emet input vide', () => {
  it('clear programmatique → emit string vide', async () => {
    const w = mount(Input, {
      props: { modelValue: 'search term', label: 'Search', type: 'search' },
    });
    const el = w.find('input').element as HTMLInputElement;
    el.value = '';
    await w.find('input').trigger('input');
    expect(w.emitted('update:modelValue')?.[0]?.[0]).toBe('');
    w.unmount();
  });
});

describe('L-6 : Textarea maxlength < ORANGE_THRESHOLD_OFFSET guard', () => {
  it('maxlength=30 → compteur reste gray < 30, rouge @ 30 (jamais orange)', () => {
    const w = mount(Textarea, {
      props: { modelValue: 'a'.repeat(20), label: 'Court', maxlength: 30 },
    });
    const counter = w.findAll('p').find((p) => p.text().includes('20/30'));
    expect(counter?.classes()).toContain('text-gray-500');
    expect(counter?.classes()).not.toContain('text-brand-orange');
    w.unmount();

    const w2 = mount(Textarea, {
      props: { modelValue: 'a'.repeat(30), label: 'Court', maxlength: 30 },
    });
    const counter2 = w2.findAll('p').find((p) => p.text().includes('30/30'));
    expect(counter2?.classes()).toContain('text-brand-red');
    w2.unmount();
  });
});
