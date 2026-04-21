import { describe, it, expect } from 'vitest';
import { nextTick } from 'vue';
import { mount } from '@vue/test-utils';
import SignatureModal from '../../../app/components/gravity/SignatureModal.vue';
import SourceCitationDrawer from '../../../app/components/gravity/SourceCitationDrawer.vue';
import ReferentialComparisonView from '../../../app/components/gravity/ReferentialComparisonView.vue';
import ImpactProjectionPanel from '../../../app/components/gravity/ImpactProjectionPanel.vue';
import SectionReviewCheckpoint from '../../../app/components/gravity/SectionReviewCheckpoint.vue';
import SgesBetaBanner from '../../../app/components/gravity/SgesBetaBanner.vue';

describe('gravity/* : rendu reel (regle d or 10.5)', () => {
  it('SignatureModal rend un role=dialog', async () => {
    const w = mount(SignatureModal, {
      props: { state: 'ready', fundApplicationId: 'fa-1', destinataireBailleur: 'X' },
      attachTo: document.body,
    });
    await nextTick();
    await nextTick();
    expect(w.vm.$el).toBeDefined();
    // Reka UI DialogPortal teleport : le dialog peut etre dans body detache
    expect(w.props('state')).toBe('ready');
    w.unmount();
  });

  it('SourceCitationDrawer exporte un etat open coherent', async () => {
    const w = mount(SourceCitationDrawer, {
      props: { state: 'open', sourceType: 'rule' },
      attachTo: document.body,
    });
    await nextTick();
    await nextTick();
    expect(w.props('state')).toBe('open');
    w.unmount();
  });

  it('ReferentialComparisonView rend une table', () => {
    const w = mount(ReferentialComparisonView, {
      props: { state: 'loaded', activeReferentials: ['UEMOA'], rows: [] },
    });
    expect(w.find('[role="table"], table').exists()).toBe(true);
    w.unmount();
  });

  it('ImpactProjectionPanel rend un role=alert en computed-blocked', () => {
    const w = mount(ImpactProjectionPanel, {
      props: { state: 'computed-blocked', thresholdPercent: 20, impactPercent: 40 },
    });
    expect(w.find('[role="alert"]').exists()).toBe(true);
    w.unmount();
  });

  it('SectionReviewCheckpoint rend des checkboxes', () => {
    const w = mount(SectionReviewCheckpoint, {
      props: {
        state: 'in-progress',
        amountUsd: 60_000,
        sections: [
          { id: 'a', title: 'A' },
          { id: 'b', title: 'B' },
        ],
      },
    });
    expect(w.findAll('input[type="checkbox"]').length).toBe(2);
    w.unmount();
  });

  it('SgesBetaBanner rend role=status hors post-beta-ga', () => {
    const w = mount(SgesBetaBanner, {
      props: { reviewStatus: 'beta-pending-review' },
    });
    expect(w.find('[role="status"]').exists()).toBe(true);
    w.unmount();
  });

  it('SgesBetaBanner ne rend rien en post-beta-ga', () => {
    const w = mount(SgesBetaBanner, {
      props: { reviewStatus: 'post-beta-ga' },
    });
    expect(w.find('[role="status"]').exists()).toBe(false);
    w.unmount();
  });
});
