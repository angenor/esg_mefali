import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import Button from '../../../app/components/ui/Button.vue';
import {
  BUTTON_VARIANTS,
  BUTTON_SIZES,
} from '../../../app/components/ui/registry';

// Regle d or 10.5 : effet observable sur DOM reel, pas de mock.
// Classes attendues par variant (extrait AC2, tokens @theme).
const VARIANT_CLASS_MARKERS: Record<(typeof BUTTON_VARIANTS)[number], string> = {
  primary: 'bg-brand-green',
  secondary: 'border-gray-300',
  ghost: 'bg-transparent',
  danger: 'bg-brand-red',
};

const SIZE_MIN_H_MARKERS: Record<(typeof BUTTON_SIZES)[number], string> = {
  sm: 'min-h-[32px]',
  md: 'min-h-[44px]',
  lg: 'min-h-[48px]',
};

describe('ui/Button : rendu 4 variants x 3 sizes (AC2 + AC3)', () => {
  for (const variant of BUTTON_VARIANTS) {
    for (const size of BUTTON_SIZES) {
      it(`variant=${variant} size=${size} rend les classes tokens attendues`, () => {
        const w = mount(Button, {
          props: { variant, size },
          slots: { default: 'Action' },
        });
        const classes = w.find('button').classes();
        expect(classes).toContain(VARIANT_CLASS_MARKERS[variant]);
        expect(classes).toContain(SIZE_MIN_H_MARKERS[size]);
        w.unmount();
      });
    }
  }

  it('defaults : variant=primary + size=md + type=button', () => {
    const w = mount(Button, { slots: { default: 'Default' } });
    const btn = w.find('button');
    expect(btn.classes()).toContain('bg-brand-green');
    expect(btn.classes()).toContain('min-h-[44px]');
    expect(btn.attributes('type')).toBe('button');
    w.unmount();
  });

  it('focus-visible ring applique via focus-visible:ring-2 sur tous variants', () => {
    const w = mount(Button, { slots: { default: 'Focus' } });
    expect(w.find('button').classes()).toContain('focus-visible:ring-2');
    w.unmount();
  });
});
