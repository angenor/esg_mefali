import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import { axe, toHaveNoViolations } from 'jest-axe';
import ReferentialComparisonView from '../../../app/components/gravity/ReferentialComparisonView.vue';
import ImpactProjectionPanel from '../../../app/components/gravity/ImpactProjectionPanel.vue';
import SectionReviewCheckpoint from '../../../app/components/gravity/SectionReviewCheckpoint.vue';
import SgesBetaBanner from '../../../app/components/gravity/SgesBetaBanner.vue';

expect.extend(toHaveNoViolations);

// Rules axe limitees au niveau A + AA (AAA tolere MVP, AC4).
const AXE_OPTIONS = {
  rules: {
    'color-contrast-enhanced': { enabled: false },
    region: { enabled: false },
  },
} as const;

// SignatureModal + SourceCitationDrawer utilisent Reka UI <Teleport> + Portal
// qui requiert un conteneur DOM racine persistant. Ils sont couverts par
// Storybook addon-a11y runtime (voir *.stories.ts) — ici on audite les
// composants non portales qui rendent inline.

describe('gravity/* : aucun viol WCAG 2.1 AA (jest-axe)', () => {
  it('ReferentialComparisonView loaded a 0 violation', async () => {
    const w = mount(ReferentialComparisonView, {
      props: {
        state: 'loaded',
        activeReferentials: ['UEMOA'],
        rows: [
          { id: 'c1', label: 'Politique', verdicts: { UEMOA: 'pass' } },
        ],
      },
      attachTo: document.body,
    });
    const results = await axe(document.body, AXE_OPTIONS);
    expect(results).toHaveNoViolations();
    w.unmount();
  });

  it('ImpactProjectionPanel computed-safe a 0 violation', async () => {
    const w = mount(ImpactProjectionPanel, {
      props: { state: 'computed-safe', impactPercent: 12, thresholdPercent: 20 },
      attachTo: document.body,
    });
    const results = await axe(document.body, AXE_OPTIONS);
    expect(results).toHaveNoViolations();
    w.unmount();
  });

  it('SectionReviewCheckpoint in-progress a 0 violation', async () => {
    const w = mount(SectionReviewCheckpoint, {
      props: {
        state: 'in-progress',
        amountUsd: 60_000,
        sections: [{ id: 's1', title: 'Contexte' }],
      },
      attachTo: document.body,
    });
    const results = await axe(document.body, AXE_OPTIONS);
    expect(results).toHaveNoViolations();
    w.unmount();
  });

  it('SgesBetaBanner beta-pending-review a 0 violation', async () => {
    const w = mount(SgesBetaBanner, {
      props: { reviewStatus: 'beta-pending-review', sgesId: 's-1' },
      attachTo: document.body,
    });
    const results = await axe(document.body, AXE_OPTIONS);
    expect(results).toHaveNoViolations();
    w.unmount();
  });
});
