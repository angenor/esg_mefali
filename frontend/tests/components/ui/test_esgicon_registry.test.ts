import { describe, it, expect } from 'vitest';
import {
  ICON_SIZES,
  ICON_VARIANTS,
  ESG_ICON_NAMES,
  type IconSize,
  type IconVariant,
  type EsgIconName,
} from '~/components/ui/registry';

// Story 10.21 — Registry CCC-9 EsgIcon : 3 tuples frozen dedoublonnes.
// Pattern 10.8+10.14-10.20 byte-identique (7e extension).

describe('ICON_SIZES (Story 10.21 AC4)', () => {
  it('contient exactement 5 tailles dans l ordre canonique xs..xl', () => {
    expect(ICON_SIZES.length).toBe(5);
    expect(ICON_SIZES[0]).toBe('xs');
    expect(ICON_SIZES[1]).toBe('sm');
    expect(ICON_SIZES[2]).toBe('md');
    expect(ICON_SIZES[3]).toBe('lg');
    expect(ICON_SIZES[4]).toBe('xl');
  });

  it('est frozen et dedoublonne', () => {
    expect(Object.isFrozen(ICON_SIZES)).toBe(true);
    expect(new Set(ICON_SIZES).size).toBe(ICON_SIZES.length);
  });
});

describe('ICON_VARIANTS (Story 10.21 AC6)', () => {
  it('contient exactement 5 variants default-first', () => {
    expect(ICON_VARIANTS.length).toBe(5);
    expect(ICON_VARIANTS[0]).toBe('default');
    expect(ICON_VARIANTS).toEqual(['default', 'brand', 'danger', 'success', 'muted']);
  });

  it('est frozen et dedoublonne', () => {
    expect(Object.isFrozen(ICON_VARIANTS)).toBe(true);
    expect(new Set(ICON_VARIANTS).size).toBe(ICON_VARIANTS.length);
  });
});

describe('ESG_ICON_NAMES (Story 10.21 AC2 + AC8)', () => {
  it('contient au moins 30 entrees (20 Lucide + 6 ESG + marge)', () => {
    expect(ESG_ICON_NAMES.length).toBeGreaterThanOrEqual(30);
  });

  it('est frozen et dedoublonne', () => {
    expect(Object.isFrozen(ESG_ICON_NAMES)).toBe(true);
    expect(new Set(ESG_ICON_NAMES).size).toBe(ESG_ICON_NAMES.length);
  });

  it('contient au moins 20 icones Lucide (non prefixees esg-*) — AC2', () => {
    const lucideNames = ESG_ICON_NAMES.filter((n) => !n.startsWith('esg-'));
    expect(lucideNames.length).toBeGreaterThanOrEqual(20);
  });

  it('contient au moins 6 icones ESG custom (prefixe esg-*) — AC8', () => {
    const esgNames = ESG_ICON_NAMES.filter((n) => n.startsWith('esg-'));
    expect(esgNames.length).toBeGreaterThanOrEqual(6);
    expect(esgNames).toContain('esg-effluents');
    expect(esgNames).toContain('esg-biodiversite');
    expect(esgNames).toContain('esg-audit-social');
    expect(esgNames).toContain('esg-mobile-money');
    expect(esgNames).toContain('esg-taxonomie-uemoa');
    expect(esgNames).toContain('esg-sges-beta-seal');
  });

  it('expose les icones Lucide whitelist critiques (chevron-down, check, x, calendar, loader)', () => {
    expect(ESG_ICON_NAMES).toContain('chevron-down');
    expect(ESG_ICON_NAMES).toContain('check');
    expect(ESG_ICON_NAMES).toContain('x');
    expect(ESG_ICON_NAMES).toContain('calendar');
    expect(ESG_ICON_NAMES).toContain('loader');
  });
});

describe('Types derives (typeof TUPLE[number])', () => {
  it('IconSize accepte md', () => {
    const size: IconSize = 'md';
    expect(ICON_SIZES).toContain(size);
  });

  it('IconVariant accepte default', () => {
    const variant: IconVariant = 'default';
    expect(ICON_VARIANTS).toContain(variant);
  });

  it('EsgIconName accepte chevron-down et esg-effluents', () => {
    const lucideName: EsgIconName = 'chevron-down';
    const esgName: EsgIconName = 'esg-effluents';
    expect(ESG_ICON_NAMES).toContain(lucideName);
    expect(ESG_ICON_NAMES).toContain(esgName);
  });
});
