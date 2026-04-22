import { describe, it, expect } from 'vitest';
import {
  DRAWER_SIDES,
  DRAWER_SIZES,
} from '../../../app/components/ui/registry';

describe('ui/registry Drawer tuples (pattern CCC-9 Story 10.18)', () => {
  it('DRAWER_SIDES contient exactement 4 entrees (ordre canonique right first)', () => {
    expect(DRAWER_SIDES.length).toBe(4);
    expect(DRAWER_SIDES).toEqual(['right', 'left', 'top', 'bottom']);
  });

  it('DRAWER_SIDES[0] === "right" (default cohérent consommateurs Epic 13/15/19)', () => {
    expect(DRAWER_SIDES[0]).toBe('right');
  });

  it('DRAWER_SIZES contient exactement 3 entrees (sm/md/lg)', () => {
    expect(DRAWER_SIZES.length).toBe(3);
    expect(DRAWER_SIZES).toEqual(['sm', 'md', 'lg']);
  });

  it('DRAWER_SIDES est frozen (Object.isFrozen)', () => {
    expect(Object.isFrozen(DRAWER_SIDES)).toBe(true);
  });

  it('DRAWER_SIZES est frozen', () => {
    expect(Object.isFrozen(DRAWER_SIZES)).toBe(true);
  });

  it('DRAWER_SIDES est dedoublonne (Set.size === length)', () => {
    expect(new Set(DRAWER_SIDES).size).toBe(DRAWER_SIDES.length);
  });

  it('DRAWER_SIZES est dedoublonne', () => {
    expect(new Set(DRAWER_SIZES).size).toBe(DRAWER_SIZES.length);
  });
});
