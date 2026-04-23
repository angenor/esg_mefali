/**
 * Compile-time type tests pour ui/EsgIcon (AC4 Story 10.21).
 * Pattern byte-identique 10.15-10.20 HIGH-1 compile-time enforcement.
 *
 * Union literale EsgIconName derivee du tuple frozen ESG_ICON_NAMES
 * (≥ 30 entrees). Rejet compile-time de tout `name` hors registry,
 * `size` hors ICON_SIZES, `variant` hors ICON_VARIANTS, et coercions
 * non-strictes (`decorative: 'true'`, `strokeWidth: '2'`).
 *
 * Signature publique EsgIconProps refletee localement (byte-identique avec
 * EsgIcon.vue) pour eviter d'importer un .vue en typecheck (typecheck
 * vitest : tests typecheck include glob test-d.ts inclus, .vue exclus).
 */
import { describe, it, expectTypeOf, assertType } from 'vitest';
import type { EsgIconName, IconSize, IconVariant } from '../../../app/components/ui/registry';

interface EsgIconProps {
  name: EsgIconName;
  size?: IconSize;
  variant?: IconVariant;
  decorative?: boolean;
  strokeWidth?: number;
  class?: string;
}

describe('ui/EsgIcon : AC4 type safety (compile-time)', () => {
  it('IconSize inclut exactement xs|sm|md|lg|xl', () => {
    expectTypeOf<IconSize>().toEqualTypeOf<'xs' | 'sm' | 'md' | 'lg' | 'xl'>();
  });

  it('IconVariant inclut exactement default|brand|danger|success|muted', () => {
    expectTypeOf<IconVariant>().toEqualTypeOf<
      'default' | 'brand' | 'danger' | 'success' | 'muted'
    >();
  });

  it('EsgIconName inclut au moins les icones Lucide MVP + 6 ESG custom', () => {
    // echantillon : verifie assignabilite des constantes critiques.
    const lucide: EsgIconName = 'chevron-down';
    const lucide2: EsgIconName = 'check';
    const esg: EsgIconName = 'esg-effluents';
    const esg2: EsgIconName = 'esg-sges-beta-seal';
    void lucide;
    void lucide2;
    void esg;
    void esg2;
  });

  it('props valides cas nominal (name seul, Lucide)', () => {
    const ok: EsgIconProps = { name: 'chevron-down' };
    assertType<EsgIconProps>(ok);
  });

  it('props valides cas complet (size + variant + decorative + strokeWidth + class)', () => {
    const ok: EsgIconProps = {
      name: 'esg-mobile-money',
      size: 'md',
      variant: 'brand',
      decorative: true,
      strokeWidth: 2,
      class: 'h-4 w-4',
    };
    assertType<EsgIconProps>(ok);
  });

  it('AC4 : name hors registry rejete', () => {
    // @ts-expect-error name "does-not-exist" hors ESG_ICON_NAMES
    const bad: EsgIconProps = { name: 'does-not-exist' };
    void bad;
  });

  it('AC4 : size hors ICON_SIZES rejete', () => {
    // @ts-expect-error size "xxl" hors ICON_SIZES
    const bad: EsgIconProps = { name: 'check', size: 'xxl' };
    void bad;
  });

  it('AC4 : variant hors ICON_VARIANTS rejete', () => {
    // @ts-expect-error variant "rainbow" hors ICON_VARIANTS
    const bad: EsgIconProps = { name: 'check', variant: 'rainbow' };
    void bad;
  });

  it('AC4 : decorative string au lieu de boolean rejete', () => {
    // @ts-expect-error decorative: 'true' (string) au lieu de boolean
    const bad: EsgIconProps = { name: 'check', decorative: 'true' };
    void bad;
  });

  it('AC4 : strokeWidth string au lieu de number rejete', () => {
    // @ts-expect-error strokeWidth: '2' (string) au lieu de number
    const bad: EsgIconProps = { name: 'check', strokeWidth: '2' };
    void bad;
  });

  it('AC4 : name manquant rejete (propriete required)', () => {
    // @ts-expect-error name est required (pas d'default)
    const bad: EsgIconProps = {};
    void bad;
  });

  it('AC4 : name boolean rejete', () => {
    // @ts-expect-error name: true (boolean) au lieu de EsgIconName
    const bad: EsgIconProps = { name: true };
    void bad;
  });

  it('AC4 : class number rejete', () => {
    // @ts-expect-error class: 123 (number) au lieu de string
    const bad: EsgIconProps = { name: 'check', class: 123 };
    void bad;
  });

  it('AC4 : esg-* prefix seul accepte cote custom (marge extensibilite)', () => {
    // esg-effluents OK
    const ok: EsgIconProps = { name: 'esg-effluents' };
    assertType<EsgIconProps>(ok);

    // @ts-expect-error esg-typo non publie rejete
    const bad: EsgIconProps = { name: 'esg-typo-non-existant' };
    void bad;
  });
});
