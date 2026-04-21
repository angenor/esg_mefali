import { describe, it, expect } from 'vitest';
import { nextTick } from 'vue';
import { mount } from '@vue/test-utils';
import { axe, toHaveNoViolations } from 'jest-axe';
import ReferentialComparisonView from '../../../app/components/gravity/ReferentialComparisonView.vue';
import ImpactProjectionPanel from '../../../app/components/gravity/ImpactProjectionPanel.vue';
import SectionReviewCheckpoint from '../../../app/components/gravity/SectionReviewCheckpoint.vue';
import SgesBetaBanner from '../../../app/components/gravity/SgesBetaBanner.vue';
import SignatureModal from '../../../app/components/gravity/SignatureModal.vue';
import SourceCitationDrawer from '../../../app/components/gravity/SourceCitationDrawer.vue';

expect.extend(toHaveNoViolations);

// Rules axe limitees au niveau A + AA (AAA tolere MVP, AC4).
const AXE_OPTIONS = {
  rules: {
    'color-contrast-enhanced': { enabled: false },
    region: { enabled: false },
  },
} as const;

// SignatureModal (Reka UI Dialog portalise) + SourceCitationDrawer (Teleport natif) :
// couverture jest-axe renforcee via double tick apres mount (post-review 10.14 MEDIUM-3).
// Le runtime Storybook addon-a11y reste complementaire en CI.

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

  it('SignatureModal ready a 0 violation (portal Reka UI Dialog)', async () => {
    const w = mount(SignatureModal, {
      props: {
        state: 'ready',
        fundApplicationId: 'fa-1',
        destinataireBailleur: 'GCF',
        snapshotPreview: '{"ok": true}',
      },
      attachTo: document.body,
    });
    await nextTick();
    await nextTick();
    const results = await axe(document.body, AXE_OPTIONS);
    expect(results).toHaveNoViolations();
    w.unmount();
  });

  it('SourceCitationDrawer open a 0 violation (role=complementary)', async () => {
    const w = mount(SourceCitationDrawer, {
      props: {
        state: 'open',
        sourceType: 'rule',
        sourceTitle: 'Decret UEMOA 2023-045',
        sourceUrl: 'https://uemoa.int/fr/textes/decret-2023-045',
        sourceAccessedAt: '2026-04-21T09:12:00Z',
      },
      attachTo: document.body,
    });
    await nextTick();
    await nextTick();
    const results = await axe(document.body, AXE_OPTIONS);
    expect(results).toHaveNoViolations();
    w.unmount();
  });
});
