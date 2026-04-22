/**
 * Tests registres `TABS_ORIENTATIONS` + `TABS_ACTIVATION_MODES` (Story 10.19 AC7).
 * Pattern CCC-9 frozen tuple byte-identique 10.15-10.18.
 */
import { describe, it, expect } from 'vitest';
import {
  TABS_ACTIVATION_MODES,
  TABS_ORIENTATIONS,
} from '../../../app/components/ui/registry';

describe('ui/registry TABS_ORIENTATIONS (Story 10.19 AC7)', () => {
  it('contient exactement 2 entrees', () => {
    expect(TABS_ORIENTATIONS.length).toBe(2);
    expect(TABS_ORIENTATIONS).toEqual(['horizontal', 'vertical']);
  });

  it("index 0 est 'horizontal' (ordre canonique WAI-ARIA default)", () => {
    expect(TABS_ORIENTATIONS[0]).toBe('horizontal');
  });

  it('est frozen', () => {
    expect(Object.isFrozen(TABS_ORIENTATIONS)).toBe(true);
  });

  it('est dedoublonne', () => {
    expect(new Set(TABS_ORIENTATIONS).size).toBe(TABS_ORIENTATIONS.length);
  });
});

describe('ui/registry TABS_ACTIVATION_MODES (Story 10.19 AC9)', () => {
  it('contient exactement 2 entrees', () => {
    expect(TABS_ACTIVATION_MODES.length).toBe(2);
    expect(TABS_ACTIVATION_MODES).toEqual(['automatic', 'manual']);
  });

  it("index 0 est 'automatic' (ordre canonique WAI-ARIA default)", () => {
    expect(TABS_ACTIVATION_MODES[0]).toBe('automatic');
  });

  it('est frozen', () => {
    expect(Object.isFrozen(TABS_ACTIVATION_MODES)).toBe(true);
  });

  it('est dedoublonne', () => {
    expect(new Set(TABS_ACTIVATION_MODES).size).toBe(
      TABS_ACTIVATION_MODES.length,
    );
  });
});
