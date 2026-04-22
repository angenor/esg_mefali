/**
 * Audits vitest/jest-axe Badge.vue (AC8 Story 10.17).
 * 20 configurations : 4 verdict × 2 sizes + 9 lifecycle + 3 admin + 2 dark mode.
 * La regle `color-contrast` est desactivee (happy-dom ne calcule pas le CSS compile) ;
 * le contraste AA est valide manuellement §6 codemap + Storybook runtime DEF-10.15-4.
 */
import { describe, it, expect, afterEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { axe, toHaveNoViolations } from 'jest-axe';
import { h } from 'vue';
import Badge from '../../../app/components/ui/Badge.vue';
import {
  VERDICT_STATES,
  LIFECYCLE_STATES,
  ADMIN_CRITICALITIES,
} from '../../../app/components/ui/registry';

expect.extend(toHaveNoViolations);

const AXE_OPTIONS = {
  rules: {
    'color-contrast': { enabled: false },
    'color-contrast-enhanced': { enabled: false },
    region: { enabled: false },
  },
} as const;

const IconStub = () =>
  h('svg', { viewBox: '0 0 24 24', 'aria-hidden': 'true' }, [
    h('circle', { cx: 12, cy: 12, r: 6 }),
  ]);

function mountBadge(props: Record<string, unknown>, label = 'Statut') {
  return mount(Badge, {
    attachTo: document.body,
    props,
    slots: {
      icon: () => h(IconStub),
      default: () => label,
    },
  });
}

afterEach(() => {
  // Reset dark class au cas ou un test l'aurait mise.
  document.documentElement.classList.remove('dark');
});

describe('ui/Badge : 0 violation WCAG 2.1 AA — verdict × 2 sizes (AC8)', () => {
  for (const state of VERDICT_STATES) {
    for (const size of ['sm', 'md'] as const) {
      it(`variant=verdict state=${state} size=${size} : 0 violation`, async () => {
        const w = mountBadge({ variant: 'verdict', state, size });
        const results = await axe(document.body, AXE_OPTIONS);
        expect(results).toHaveNoViolations();
        w.unmount();
      });
    }
  }
});

describe('ui/Badge : 0 violation WCAG 2.1 AA — lifecycle × md', () => {
  for (const state of LIFECYCLE_STATES) {
    it(`variant=lifecycle state=${state} : 0 violation`, async () => {
      const w = mountBadge({ variant: 'lifecycle', state });
      const results = await axe(document.body, AXE_OPTIONS);
      expect(results).toHaveNoViolations();
      w.unmount();
    });
  }
});

describe('ui/Badge : 0 violation WCAG 2.1 AA — admin × md', () => {
  for (const state of ADMIN_CRITICALITIES) {
    it(`variant=admin state=${state} : 0 violation`, async () => {
      const w = mountBadge({ variant: 'admin', state });
      const results = await axe(document.body, AXE_OPTIONS);
      expect(results).toHaveNoViolations();
      w.unmount();
    });
  }
});

describe('ui/Badge : 0 violation WCAG 2.1 AA — dark mode (AC7 + AC8)', () => {
  it('verdict pass en dark mode : 0 violation', async () => {
    document.documentElement.classList.add('dark');
    const w = mountBadge({ variant: 'verdict', state: 'pass' }, 'Validé');
    const results = await axe(document.body, AXE_OPTIONS);
    expect(results).toHaveNoViolations();
    w.unmount();
  });

  it('admin n3 en dark mode : 0 violation', async () => {
    document.documentElement.classList.add('dark');
    const w = mountBadge({ variant: 'admin', state: 'n3' }, 'N3');
    const results = await axe(document.body, AXE_OPTIONS);
    expect(results).toHaveNoViolations();
    w.unmount();
  });
});
