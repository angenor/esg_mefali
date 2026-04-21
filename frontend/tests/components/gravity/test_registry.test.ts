import { describe, it, expect } from 'vitest';
import { GRAVITY_COMPONENT_REGISTRY } from '../../../app/components/gravity/registry';

describe('GRAVITY_COMPONENT_REGISTRY (pattern CCC-9)', () => {
  it('contient exactement 6 entrees', () => {
    expect(GRAVITY_COMPONENT_REGISTRY.length).toBe(6);
  });

  it('est frozen (Object.isFrozen) et chaque entry aussi', () => {
    expect(Object.isFrozen(GRAVITY_COMPONENT_REGISTRY)).toBe(true);
    for (const entry of GRAVITY_COMPONENT_REGISTRY) {
      expect(Object.isFrozen(entry)).toBe(true);
      expect(Object.isFrozen(entry.states)).toBe(true);
    }
  });

  it('a des noms uniques', () => {
    const names = GRAVITY_COMPONENT_REGISTRY.map((e) => e.name);
    expect(new Set(names).size).toBe(names.length);
  });

  it('a des states non vides pour chaque entree', () => {
    for (const entry of GRAVITY_COMPONENT_REGISTRY) {
      expect(entry.states.length).toBeGreaterThan(0);
      expect(entry.fr.length).toBeGreaterThan(0);
    }
  });
});
