/**
 * Tests rendu Badge.vue (AC3 + AC4 + AC5 + AC6 + AC8 Story 10.17).
 * Pattern A (10.16 H-3) : assertions DOM reel (`classes()`, `attributes('aria-label')`,
 * `[data-testid]` text) — JAMAIS `wrapper.vm.*` ni mutation state interne.
 */
import { describe, it, expect, vi, afterEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { h, nextTick } from 'vue';
import Badge from '../../../app/components/ui/Badge.vue';
import {
  VERDICT_STATES,
  LIFECYCLE_STATES,
  ADMIN_CRITICALITIES,
  BADGE_SIZES,
} from '../../../app/components/ui/registry';

// Stub SVG icone minimal (Lucide Story 10.21 le remplacera).
const IconStub = () =>
  h('svg', { 'data-testid': 'stub-svg', viewBox: '0 0 24 24' }, [
    h('circle', { cx: 12, cy: 12, r: 6 }),
  ]);

// Helpers de mount concise partages.
function mountBadge(props: Record<string, unknown>, label = 'Statut') {
  return mount(Badge, {
    props,
    slots: {
      icon: () => h(IconStub),
      default: () => label,
    },
  });
}

// Marqueurs classes attendus par variant x state (extrait Badge.vue — AC6).
// Patch 10.17 CRITICAL-1/2 : texte = token `-strong` (800) en light mode pour AA.
const VERDICT_BG: Record<(typeof VERDICT_STATES)[number], string> = {
  pass: 'bg-verdict-pass-soft',
  fail: 'bg-verdict-fail-soft',
  reported: 'bg-verdict-reported-soft',
  na: 'bg-verdict-na-soft',
};
const VERDICT_TEXT: Record<(typeof VERDICT_STATES)[number], string> = {
  pass: 'text-verdict-pass-strong',
  fail: 'text-verdict-fail-strong',
  reported: 'text-verdict-reported-strong',
  na: 'text-verdict-na-strong',
};
const LIFECYCLE_TEXT_MAP: Record<(typeof LIFECYCLE_STATES)[number], string> = {
  draft: 'text-fa-draft-strong',
  snapshot_frozen: 'text-fa-snapshot-frozen-strong',
  signed: 'text-fa-signed-strong',
  exported: 'text-fa-exported-strong',
  submitted: 'text-fa-submitted-strong',
  in_review: 'text-fa-in-review-strong',
  accepted: 'text-fa-accepted-strong',
  rejected: 'text-fa-rejected-strong',
  withdrawn: 'text-fa-withdrawn-strong',
};
const ADMIN_TEXT: Record<(typeof ADMIN_CRITICALITIES)[number], string> = {
  n1: 'text-admin-n1-strong',
  n2: 'text-admin-n2-strong',
  n3: 'text-admin-n3-strong',
};
const SIZE_MIN_H: Record<(typeof BADGE_SIZES)[number], string> = {
  sm: 'min-h-[20px]',
  md: 'min-h-[24px]',
  lg: 'min-h-[32px]',
};

afterEach(() => {
  vi.restoreAllMocks();
});

describe('ui/Badge : rendu verdict x sizes (AC3 + AC5 + AC6)', () => {
  for (const state of VERDICT_STATES) {
    for (const size of BADGE_SIZES) {
      it(`variant=verdict state=${state} size=${size} applique tokens + size`, () => {
        const w = mountBadge({ variant: 'verdict', state, size });
        const span = w.find('span').element as HTMLSpanElement;
        const classes = Array.from(span.classList);
        expect(classes).toContain(VERDICT_BG[state]);
        expect(classes).toContain(VERDICT_TEXT[state]);
        expect(classes).toContain(SIZE_MIN_H[size]);
        w.unmount();
      });
    }
  }
});

describe('ui/Badge : rendu lifecycle x md (AC6 — 9 etats FA)', () => {
  for (const state of LIFECYCLE_STATES) {
    it(`variant=lifecycle state=${state} applique text-fa-*`, () => {
      const w = mountBadge({ variant: 'lifecycle', state });
      const span = w.find('span').element as HTMLSpanElement;
      expect(Array.from(span.classList)).toContain(LIFECYCLE_TEXT_MAP[state]);
      w.unmount();
    });
  }
});

describe('ui/Badge : rendu admin x md (AC6 — N1/N2/N3)', () => {
  for (const state of ADMIN_CRITICALITIES) {
    it(`variant=admin state=${state} applique text-admin-*`, () => {
      const w = mountBadge({ variant: 'admin', state });
      const span = w.find('span').element as HTMLSpanElement;
      expect(Array.from(span.classList)).toContain(ADMIN_TEXT[state]);
      w.unmount();
    });
  }
});

describe('ui/Badge : aria-label FR compose (AC8 + patch 10.17 role="img")', () => {
  it('verdict pass sans conditional → "Verdict Validé"', () => {
    const w = mountBadge({ variant: 'verdict', state: 'pass' });
    expect(w.find('span').attributes('aria-label')).toBe('Verdict Validé');
    w.unmount();
  });

  it('verdict fail → "Verdict Non conforme"', () => {
    const w = mountBadge({ variant: 'verdict', state: 'fail' });
    expect(w.find('span').attributes('aria-label')).toBe('Verdict Non conforme');
    w.unmount();
  });

  it('verdict reported → "Verdict À documenter"', () => {
    const w = mountBadge({ variant: 'verdict', state: 'reported' });
    expect(w.find('span').attributes('aria-label')).toBe('Verdict À documenter');
    w.unmount();
  });

  it('lifecycle signed → "Statut Signé"', () => {
    const w = mountBadge({ variant: 'lifecycle', state: 'signed' });
    expect(w.find('span').attributes('aria-label')).toBe('Statut Signé');
    w.unmount();
  });

  it('lifecycle in_review → "Statut En revue"', () => {
    const w = mountBadge({ variant: 'lifecycle', state: 'in_review' });
    expect(w.find('span').attributes('aria-label')).toBe('Statut En revue');
    w.unmount();
  });

  it('admin n2 → "Criticité admin N2"', () => {
    const w = mountBadge({ variant: 'admin', state: 'n2' });
    expect(w.find('span').attributes('aria-label')).toBe('Criticité admin N2');
    w.unmount();
  });
});

describe('ui/Badge : verdict conditional italique (AC4)', () => {
  it('conditional=true applique italic + suffixe aria-label "(conditionnel)"', () => {
    const w = mountBadge({ variant: 'verdict', state: 'pass', conditional: true }, 'Validé');
    const span = w.find('span').element as HTMLSpanElement;
    expect(Array.from(span.classList)).toContain('italic');
    expect(w.find('span').attributes('aria-label')).toBe('Verdict Validé (conditionnel)');
    w.unmount();
  });

  it('conditional=false ne met PAS italic ni suffixe', () => {
    const w = mountBadge({ variant: 'verdict', state: 'pass', conditional: false });
    const span = w.find('span').element as HTMLSpanElement;
    expect(Array.from(span.classList)).not.toContain('italic');
    expect(w.find('span').attributes('aria-label')).toBe('Verdict Validé');
    w.unmount();
  });
});

describe('ui/Badge : role="img" + slots + a11y (AC3 + AC8 + patch 10.17 MEDIUM-1)', () => {
  it('role="img" present sur span racine (statique — PAS live-region polite)', () => {
    const w = mountBadge({ variant: 'verdict', state: 'pass' });
    // Patch 10.17 MEDIUM-1 : `status` remplace par `img` (Badge statique, dashboard dense
    // ne sature plus le screen reader avec N annonces polite au chargement).
    expect(w.find('span').attributes('role')).toBe('img');
    w.unmount();
  });

  it('slot icon rendu avec aria-hidden="true" (decoratif AC8)', () => {
    const w = mountBadge({ variant: 'admin', state: 'n1' });
    const iconWrapper = w.find('[data-testid="badge-icon-slot"]');
    expect(iconWrapper.exists()).toBe(true);
    expect(iconWrapper.attributes('aria-hidden')).toBe('true');
    // L'icone stub SVG est bien injecte.
    expect(iconWrapper.find('[data-testid="stub-svg"]').exists()).toBe(true);
    w.unmount();
  });

  it('slot default rendu avec label texte FR visible', () => {
    const w = mountBadge({ variant: 'lifecycle', state: 'draft' }, 'Mon brouillon');
    const labelWrapper = w.find('[data-testid="badge-label-slot"]');
    expect(labelWrapper.exists()).toBe(true);
    expect(labelWrapper.text()).toBe('Mon brouillon');
    w.unmount();
  });
});

describe('ui/Badge : Regle 11 UX enforcement (AC3 + patch 10.17 CRITICAL-3 Pattern A DOM)', () => {
  // Patch 10.17 CRITICAL-3 : Pattern A strict — les tests assertent l'effet
  // observable DOM (icon wrapper vide, label wrapper sans textContent) EN PLUS du
  // console spy (defense en profondeur).

  it('slot #icon absent → DOM icon wrapper vide (0 child) + console.error emis', async () => {
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const w = mount(Badge, {
      props: { variant: 'verdict', state: 'pass' },
      slots: { default: () => 'Validé' },
    });
    await nextTick();

    // Assertion DOM Pattern A primaire : l'icon wrapper est vide = user ne voit aucune icone.
    const iconWrapper = w.find('[data-testid="badge-icon-slot"]');
    expect(iconWrapper.exists()).toBe(true);
    expect(iconWrapper.element.childElementCount).toBe(0);

    // Assertion console (defense en profondeur, dev-only via import.meta.dev).
    expect(errorSpy).toHaveBeenCalledWith(
      expect.stringContaining('slot #icon is REQUIRED'),
    );
    w.unmount();
  });

  it('slot #icon empty fragment → DOM icon wrapper vide + console.error emis (HIGH-6 patch)', async () => {
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const w = mount(Badge, {
      props: { variant: 'verdict', state: 'pass' },
      slots: {
        // Slot present mais ne rend aucun VNode element (bypass HIGH-6).
        icon: () => [],
        default: () => 'Validé',
      },
    });
    await nextTick();

    const iconWrapper = w.find('[data-testid="badge-icon-slot"]');
    expect(iconWrapper.element.childElementCount).toBe(0);
    expect(errorSpy).toHaveBeenCalledWith(
      expect.stringContaining('slot #icon is REQUIRED'),
    );
    w.unmount();
  });

  it('slot default absent → DOM label wrapper sans textContent + console.warn emis', async () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const w = mount(Badge, {
      props: { variant: 'verdict', state: 'pass' },
      slots: { icon: () => h(IconStub) },
    });
    await nextTick();

    // Assertion DOM Pattern A primaire : le label wrapper n'a aucun textContent.
    const labelWrapper = w.find('[data-testid="badge-label-slot"]');
    expect(labelWrapper.exists()).toBe(true);
    expect(labelWrapper.text()).toBe('');

    expect(warnSpy).toHaveBeenCalledWith(
      expect.stringContaining('slot default (label FR) is REQUIRED'),
    );
    w.unmount();
  });

  it('slot default avec espaces seulement → DOM text trimmed vide + console.warn emis', async () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const w = mount(Badge, {
      props: { variant: 'verdict', state: 'pass' },
      slots: {
        icon: () => h(IconStub),
        default: () => '   ',
      },
    });
    await nextTick();

    const labelWrapper = w.find('[data-testid="badge-label-slot"]');
    expect(labelWrapper.text().trim()).toBe('');
    expect(warnSpy).toHaveBeenCalledWith(
      expect.stringContaining('slot default (label FR) is REQUIRED'),
    );
    w.unmount();
  });

  it('slots valides → DOM icon + label pleins + AUCUN warn/error', async () => {
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const w = mountBadge({ variant: 'verdict', state: 'pass' }, 'Validé');
    await nextTick();

    expect(w.find('[data-testid="badge-icon-slot"]').element.childElementCount).toBeGreaterThan(0);
    expect(w.find('[data-testid="badge-label-slot"]').text()).toBe('Validé');
    expect(errorSpy).not.toHaveBeenCalled();
    expect(warnSpy).not.toHaveBeenCalled();
    w.unmount();
  });
});

describe('ui/Badge : sizes variant base classes (AC5)', () => {
  it('size sm applique text-xs + gap-1 + min-h-[20px]', () => {
    const w = mountBadge({ variant: 'verdict', state: 'pass', size: 'sm' });
    const classes = Array.from((w.find('span').element as HTMLSpanElement).classList);
    expect(classes).toContain('text-xs');
    expect(classes).toContain('min-h-[20px]');
    w.unmount();
  });

  it('size md (default) applique text-sm + min-h-[24px]', () => {
    const w = mountBadge({ variant: 'verdict', state: 'pass' });
    const classes = Array.from((w.find('span').element as HTMLSpanElement).classList);
    expect(classes).toContain('text-sm');
    expect(classes).toContain('min-h-[24px]');
    w.unmount();
  });

  it('size lg applique text-base + min-h-[32px]', () => {
    const w = mountBadge({ variant: 'verdict', state: 'pass', size: 'lg' });
    const classes = Array.from((w.find('span').element as HTMLSpanElement).classList);
    expect(classes).toContain('text-base');
    expect(classes).toContain('min-h-[32px]');
    w.unmount();
  });

  it('AUCUNE size ne porte min-h-[44px] (Q4 Badge != Button, pas touch target)', () => {
    for (const size of BADGE_SIZES) {
      const w = mountBadge({ variant: 'verdict', state: 'pass', size });
      const classes = Array.from((w.find('span').element as HTMLSpanElement).classList);
      expect(classes).not.toContain('min-h-[44px]');
      w.unmount();
    }
  });
});
