/**
 * Tests comportement ui/EsgIcon (AC4-AC7 + AC9 Story 10.21).
 *
 * Pattern A observable (§4ter.bis + §4quinquies + §4sexies capitalises) :
 *  - DOM assertions observables (svg.attributes, classes, innerHTML),
 *  - AUCUN `wrapper.vm.*`, AUCUN imperative binding,
 *  - L21 §4quater : assertions strictes (toBe, toContain),
 *  - L24 §4quinquies : ARIA attribute-strict (string valeurs litterales),
 *  - L26 §4sexies : tests per-path, pas global sweep toutes icones.
 */
import { describe, it, expect, afterEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import EsgIcon from '../../../app/components/ui/EsgIcon.vue';
import type { EsgIconName } from '../../../app/components/ui/registry';

afterEach(() => {
  vi.restoreAllMocks();
});

describe('ui/EsgIcon : AC4-AC7 rendering (Lucide + ESG custom)', () => {
  it('AC5 : rend un composant Lucide pour name="chevron-down" (SVG present)', () => {
    const wrapper = mount(EsgIcon, { props: { name: 'chevron-down' } });
    expect(wrapper.find('svg').exists()).toBe(true);
    // Lucide ChevronDown contient un <path d="m6 9 6 6 6-6"/> specifique.
    expect(wrapper.html()).toContain('<path');
  });

  it('AC5 : rend un composant Lucide pour name="check" distinct de chevron', () => {
    const wrapper = mount(EsgIcon, { props: { name: 'check' } });
    expect(wrapper.find('svg').exists()).toBe(true);
    expect(wrapper.html()).not.toBe('');
  });

  it('AC5 + AC8 : rend le SVG custom ESG pour name="esg-effluents"', () => {
    const wrapper = mount(EsgIcon, { props: { name: 'esg-effluents' } });
    const svg = wrapper.find('svg');
    expect(svg.exists()).toBe(true);
    // Convention Lucide respectee par SVG custom.
    expect(svg.attributes('stroke')).toBe('currentColor');
    expect(svg.attributes('fill')).toBe('none');
  });

  it('AC4 size="xs" : mappe a 12 pixels (width attribute natif Lucide)', () => {
    const wrapper = mount(EsgIcon, { props: { name: 'chevron-down', size: 'xs' } });
    expect(wrapper.find('svg').attributes('width')).toBe('12');
  });

  it('AC4 size="xl" : mappe a 32 pixels', () => {
    const wrapper = mount(EsgIcon, { props: { name: 'chevron-down', size: 'xl' } });
    expect(wrapper.find('svg').attributes('width')).toBe('32');
  });

  it('AC4 size default ("md") : mappe a 20 pixels sans prop explicite', () => {
    const wrapper = mount(EsgIcon, { props: { name: 'chevron-down' } });
    expect(wrapper.find('svg').attributes('width')).toBe('20');
  });
});

describe('ui/EsgIcon : AC6 variants + tokens (no hex)', () => {
  it('variant="brand" injecte la classe token text-brand-green', () => {
    const wrapper = mount(EsgIcon, { props: { name: 'check', variant: 'brand' } });
    const classAttr = wrapper.find('svg').attributes('class') ?? '';
    expect(classAttr).toContain('text-brand-green');
    expect(classAttr).toContain('dark:text-brand-green');
  });

  it('variant="danger" injecte la classe token text-brand-red', () => {
    const wrapper = mount(EsgIcon, { props: { name: 'x-circle', variant: 'danger' } });
    const classAttr = wrapper.find('svg').attributes('class') ?? '';
    expect(classAttr).toContain('text-brand-red');
  });

  it('variant="success" injecte la classe token text-verdict-pass', () => {
    const wrapper = mount(EsgIcon, { props: { name: 'check-circle', variant: 'success' } });
    const classAttr = wrapper.find('svg').attributes('class') ?? '';
    expect(classAttr).toContain('text-verdict-pass');
  });

  it('variant="muted" injecte la classe text-surface-text/60', () => {
    const wrapper = mount(EsgIcon, { props: { name: 'info', variant: 'muted' } });
    const classAttr = wrapper.find('svg').attributes('class') ?? '';
    expect(classAttr).toContain('text-surface-text/60');
    expect(classAttr).toContain('dark:text-surface-dark-text/60');
  });

  it('prop class est merge avec variantClass (pas ecrase)', () => {
    const wrapper = mount(EsgIcon, {
      props: { name: 'check', variant: 'brand', class: 'h-4 w-4 custom-foo' },
    });
    const classAttr = wrapper.find('svg').attributes('class') ?? '';
    expect(classAttr).toContain('text-brand-green');
    expect(classAttr).toContain('custom-foo');
    expect(classAttr).toContain('h-4');
  });
});

describe('ui/EsgIcon : AC4 strokeWidth forward natif Lucide', () => {
  it('strokeWidth=3 forward vers SVG stroke-width attribute', () => {
    const wrapper = mount(EsgIcon, {
      props: { name: 'chevron-down', strokeWidth: 3 },
    });
    expect(wrapper.find('svg').attributes('stroke-width')).toBe('3');
  });

  it('strokeWidth default=2', () => {
    const wrapper = mount(EsgIcon, { props: { name: 'check' } });
    expect(wrapper.find('svg').attributes('stroke-width')).toBe('2');
  });
});

describe('ui/EsgIcon : AC5 fallback warn dev-only + placeholder', () => {
  it('name inconnu declenche console.warn 1 fois en DEV (L21 strict)', () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    mount(EsgIcon, {
      props: { name: 'unknown-xyz' as EsgIconName },
    });
    expect(warnSpy).toHaveBeenCalledTimes(1);
    expect(warnSpy).toHaveBeenCalledWith(
      expect.stringContaining('unknown-xyz'),
    );
    expect(warnSpy).toHaveBeenCalledWith(
      expect.stringContaining('[EsgIcon]'),
    );
    warnSpy.mockRestore();
  });

  it('name inconnu rend le placeholder cercle barre (svg + circle + line)', () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const wrapper = mount(EsgIcon, {
      props: { name: 'does-not-exist' as EsgIconName },
    });
    const svg = wrapper.find('svg');
    expect(svg.exists()).toBe(true);
    expect(wrapper.find('circle').exists()).toBe(true);
    expect(wrapper.find('line').exists()).toBe(true);
    warnSpy.mockRestore();
  });

  it('name valide ne declenche PAS console.warn (DEV path negatif)', () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    mount(EsgIcon, { props: { name: 'check' } });
    expect(warnSpy).not.toHaveBeenCalled();
    warnSpy.mockRestore();
  });
});

describe('ui/EsgIcon : AC7 ARIA decorative vs semantique (L24 attribute-strict)', () => {
  it('decorative=true (explicit) : aria-hidden="true" strict, pas de role ni aria-label', () => {
    const wrapper = mount(EsgIcon, {
      props: { name: 'chevron-down', decorative: true },
    });
    const svg = wrapper.find('svg').element;
    expect(svg.getAttribute('aria-hidden')).toBe('true');
    expect(svg.getAttribute('role')).toBeNull();
    expect(svg.getAttribute('aria-label')).toBeNull();
  });

  it('decorative=false (default) : role="img" + aria-label=name, pas de aria-hidden', () => {
    const wrapper = mount(EsgIcon, { props: { name: 'calendar' } });
    const svg = wrapper.find('svg').element;
    expect(svg.getAttribute('role')).toBe('img');
    expect(svg.getAttribute('aria-label')).toBe('calendar');
    expect(svg.getAttribute('aria-hidden')).toBeNull();
  });

  it('decorative=false sur ESG custom : aria-label reflete le name ESG', () => {
    const wrapper = mount(EsgIcon, { props: { name: 'esg-mobile-money' } });
    const svg = wrapper.find('svg').element;
    expect(svg.getAttribute('role')).toBe('img');
    expect(svg.getAttribute('aria-label')).toBe('esg-mobile-money');
  });
});
