import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import { axe, toHaveNoViolations } from 'jest-axe';
import Button from '../../../app/components/ui/Button.vue';
import { BUTTON_VARIANTS } from '../../../app/components/ui/registry';

expect.extend(toHaveNoViolations);

// A + AA uniquement (AAA tolere MVP, pattern 10.14 byte-identique).
const AXE_OPTIONS = {
  rules: {
    'color-contrast-enhanced': { enabled: false },
    region: { enabled: false },
  },
} as const;

describe('ui/Button : aucune violation WCAG 2.1 AA (jest-axe)', () => {
  for (const variant of BUTTON_VARIANTS) {
    it(`variant=${variant} default : 0 violation`, async () => {
      const w = mount(Button, {
        props: { variant },
        slots: { default: `Action ${variant}` },
        attachTo: document.body,
      });
      const results = await axe(document.body, AXE_OPTIONS);
      expect(results).toHaveNoViolations();
      w.unmount();
    });

    it(`variant=${variant} loading : 0 violation (aria-busy documente)`, async () => {
      const w = mount(Button, {
        props: { variant, loading: true },
        slots: { default: `Action ${variant}` },
        attachTo: document.body,
      });
      const results = await axe(document.body, AXE_OPTIONS);
      expect(results).toHaveNoViolations();
      w.unmount();
    });
  }
});
