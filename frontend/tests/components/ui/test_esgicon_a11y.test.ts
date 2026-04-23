/**
 * Tests a11y ui/EsgIcon (AC7 + AC10 Story 10.21).
 *
 * L24 §4quinquies 10.19 — ARIA attribute-strict valeurs litterales stringifiees
 * (`aria-hidden="true"` string, pas boolean ; role="img" strict).
 * L26 §4sexies 10.20 — tests par-variant delegues Storybook (describe.skip +
 *   it.todo per-path) pour contraste/hover dark mode, pas global sweep.
 * L21 §4quater — assertions strictes observables, pas smoke existence.
 */
import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import EsgIcon from '../../../app/components/ui/EsgIcon.vue';

describe('ui/EsgIcon : AC7 ARIA L24 attribute-strict', () => {
  it('aria-hidden="true" valeur stricte string (pas boolean, pas vide)', () => {
    const wrapper = mount(EsgIcon, {
      props: { name: 'x', decorative: true },
    });
    const svg = wrapper.find('svg').element;
    expect(svg.getAttribute('aria-hidden')).toBe('true');
    expect(svg.getAttribute('aria-hidden')).not.toBe('');
  });

  it('role="img" valeur stricte (pas "image" ni vide)', () => {
    const wrapper = mount(EsgIcon, { props: { name: 'calendar' } });
    const svg = wrapper.find('svg').element;
    expect(svg.getAttribute('role')).toBe('img');
    expect(svg.getAttribute('role')).not.toBe('image');
  });

  it('aria-label valeur stricte = prop name', () => {
    const wrapper = mount(EsgIcon, { props: { name: 'calendar' } });
    expect(wrapper.find('svg').element.getAttribute('aria-label')).toBe('calendar');
  });

  it('aria-label reflete le name custom ESG exact', () => {
    const wrapper = mount(EsgIcon, { props: { name: 'esg-biodiversite' } });
    expect(wrapper.find('svg').element.getAttribute('aria-label')).toBe(
      'esg-biodiversite',
    );
  });

  it('aria-hidden absent quand decorative=false (attribut absent strict)', () => {
    const wrapper = mount(EsgIcon, { props: { name: 'check' } });
    expect(wrapper.find('svg').element.getAttribute('aria-hidden')).toBeNull();
  });

  it('role absent et aria-label absent quand decorative=true', () => {
    const wrapper = mount(EsgIcon, { props: { name: 'x', decorative: true } });
    const svg = wrapper.find('svg').element;
    expect(svg.getAttribute('role')).toBeNull();
    expect(svg.getAttribute('aria-label')).toBeNull();
  });
});

// L26 §4sexies : delegation per-path explicite vs global sweep.
// Contraste AA post-darken, hover states, focus-visible dark mode sont
// valides via Storybook addon-a11y snapshots, pas dans Vitest happy-dom.
describe.skip('AC6 variant contrast dark mode — DELEGATED Storybook per-path', () => {
  it.todo('variant=brand dark mode AA post-darken — ui-esgicon--dark-mode--brand');
  it.todo('variant=danger dark mode AA — ui-esgicon--dark-mode--danger');
  it.todo('variant=success dark mode — ui-esgicon--dark-mode--success');
  it.todo('variant=muted dark mode — ui-esgicon--dark-mode--muted');
  it.todo('hover brand+dark mode — ui-esgicon--variants-hover-dark');
  it.todo('focus-visible keyboard — ui-esgicon--focus-keyboard');
});
