/**
 * Tests registre `COMBOBOX_MODES` (Story 10.19 AC1).
 * Pattern CCC-9 frozen tuple byte-identique 10.15-10.18.
 */
import { describe, it, expect } from 'vitest';
import { COMBOBOX_MODES } from '../../../app/components/ui/registry';

describe('ui/registry COMBOBOX_MODES (Story 10.19 AC1)', () => {
  it('contient exactement 2 entrees', () => {
    expect(COMBOBOX_MODES.length).toBe(2);
    expect(COMBOBOX_MODES).toEqual(['single', 'multiple']);
  });

  it("index 0 est 'single' (ordre canonique — default infere single-first)", () => {
    expect(COMBOBOX_MODES[0]).toBe('single');
  });

  it('est frozen (Object.isFrozen)', () => {
    expect(Object.isFrozen(COMBOBOX_MODES)).toBe(true);
  });

  it('est dedoublonne (Set.size === length)', () => {
    expect(new Set(COMBOBOX_MODES).size).toBe(COMBOBOX_MODES.length);
  });
});
