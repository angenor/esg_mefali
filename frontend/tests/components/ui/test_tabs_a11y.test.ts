/**
 * Tests a11y ui/Tabs (AC10 + AC14 Story 10.19).
 *
 * Tabs n'est PAS portalise (contrairement a Combobox) → scan DOM standard
 * via @testing-library/vue `screen.*`.
 */
import { describe, it, expect, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/vue';
import { axe, toHaveNoViolations } from 'jest-axe';
import Tabs from '../../../app/components/ui/Tabs.vue';

expect.extend(toHaveNoViolations);

const AXE_OPTIONS = {
  rules: {
    'color-contrast': { enabled: false },
    region: { enabled: false },
  },
} as const;

afterEach(() => {
  cleanup();
});

const TABS_FIXTURE = [
  { value: 't1', label: 'Onglet 1' },
  { value: 't2', label: 'Onglet 2' },
  { value: 't3', label: 'Onglet 3' },
];

describe('ui/Tabs : AC10 ARIA DOM (Pattern A)', () => {
  it('role="tablist" + aria-orientation correct', () => {
    render(Tabs, {
      props: { modelValue: 't1', tabs: TABS_FIXTURE },
    });
    const list = screen.getByRole('tablist');
    expect(list.getAttribute('aria-orientation')).toBe('horizontal');
  });

  it('tabs avec role="tab" et aria-selected differencies', () => {
    render(Tabs, {
      props: { modelValue: 't2', tabs: TABS_FIXTURE },
    });
    const tabs = screen.getAllByRole('tab');
    expect(tabs.length).toBe(3);
    expect(tabs[0].getAttribute('aria-selected')).toBe('false');
    expect(tabs[1].getAttribute('aria-selected')).toBe('true');
    expect(tabs[2].getAttribute('aria-selected')).toBe('false');
  });

  it('tabpanel actif a role="tabpanel" + aria-labelledby pointant un id existant', () => {
    render(Tabs, {
      props: { modelValue: 't1', tabs: TABS_FIXTURE },
    });
    const panel = screen.getByRole('tabpanel');
    expect(panel.getAttribute('role')).toBe('tabpanel');
    const labelledby = panel.getAttribute('aria-labelledby');
    expect(labelledby).not.toBeNull();
    expect(document.getElementById(labelledby!)).not.toBeNull();
  });

  it('prop label fournit aria-label explicite sur tablist', () => {
    render(Tabs, {
      props: {
        modelValue: 't1',
        tabs: TABS_FIXTURE,
        label: 'Sections admin',
      },
    });
    expect(screen.getByRole('tablist').getAttribute('aria-label')).toBe(
      'Sections admin',
    );
  });
});

describe('ui/Tabs : vitest-axe smoke', () => {
  it('rendu horizontal : aucune violation axe hors regles deleguees', async () => {
    const { container } = render(Tabs, {
      props: {
        modelValue: 't1',
        tabs: TABS_FIXTURE,
        label: 'Navigation',
      },
    });
    const results = await axe(container, AXE_OPTIONS);
    expect(results).toHaveNoViolations();
  });

  it('rendu vertical : aucune violation axe', async () => {
    const { container } = render(Tabs, {
      props: {
        modelValue: 't1',
        tabs: TABS_FIXTURE,
        orientation: 'vertical',
        label: 'Nav verticale',
      },
    });
    const results = await axe(container, AXE_OPTIONS);
    expect(results).toHaveNoViolations();
  });
});
