import { describe, it, expect } from 'vitest';
import {
  VERDICT_STATES,
  LIFECYCLE_STATES,
  ADMIN_CRITICALITIES,
  BADGE_SIZES,
} from '../../../app/components/ui/registry';

describe('ui/registry Badge tuples (pattern CCC-9 Story 10.17)', () => {
  it('VERDICT_STATES contient exactement 4 entrees', () => {
    expect(VERDICT_STATES.length).toBe(4);
    expect(VERDICT_STATES).toEqual(['pass', 'fail', 'reported', 'na']);
  });

  it('LIFECYCLE_STATES contient exactement 9 entrees (FR32)', () => {
    expect(LIFECYCLE_STATES.length).toBe(9);
    expect(LIFECYCLE_STATES).toEqual([
      'draft',
      'snapshot_frozen',
      'signed',
      'exported',
      'submitted',
      'in_review',
      'accepted',
      'rejected',
      'withdrawn',
    ]);
  });

  it('ADMIN_CRITICALITIES contient exactement 3 entrees (N1/N2/N3)', () => {
    expect(ADMIN_CRITICALITIES.length).toBe(3);
    expect(ADMIN_CRITICALITIES).toEqual(['n1', 'n2', 'n3']);
  });

  it('BADGE_SIZES contient exactement 3 entrees (Q4 sizes inline 20/24/32)', () => {
    expect(BADGE_SIZES.length).toBe(3);
    expect(BADGE_SIZES).toEqual(['sm', 'md', 'lg']);
  });

  it('VERDICT_STATES est frozen (Object.isFrozen)', () => {
    expect(Object.isFrozen(VERDICT_STATES)).toBe(true);
  });

  it('LIFECYCLE_STATES est frozen', () => {
    expect(Object.isFrozen(LIFECYCLE_STATES)).toBe(true);
  });

  it('ADMIN_CRITICALITIES est frozen', () => {
    expect(Object.isFrozen(ADMIN_CRITICALITIES)).toBe(true);
  });

  it('BADGE_SIZES est frozen', () => {
    expect(Object.isFrozen(BADGE_SIZES)).toBe(true);
  });

  it('VERDICT_STATES est dedoublonne (Set.size === length)', () => {
    expect(new Set(VERDICT_STATES).size).toBe(VERDICT_STATES.length);
  });

  it('LIFECYCLE_STATES est dedoublonne', () => {
    expect(new Set(LIFECYCLE_STATES).size).toBe(LIFECYCLE_STATES.length);
  });

  it('ADMIN_CRITICALITIES est dedoublonne', () => {
    expect(new Set(ADMIN_CRITICALITIES).size).toBe(ADMIN_CRITICALITIES.length);
  });

  it('BADGE_SIZES est dedoublonne', () => {
    expect(new Set(BADGE_SIZES).size).toBe(BADGE_SIZES.length);
  });
});
