/**
 * Tests registre `DATEPICKER_MODES` (Story 10.20 AC1).
 * Pattern CCC-9 frozen tuple byte-identique 10.15-10.19.
 */
import { describe, it, expect } from 'vitest';
import { DATEPICKER_MODES } from '../../../app/components/ui/registry';

describe('ui/registry DATEPICKER_MODES (Story 10.20 AC1)', () => {
  it('contient exactement 2 entrees', () => {
    expect(DATEPICKER_MODES.length).toBe(2);
    expect(DATEPICKER_MODES).toEqual(['single', 'range']);
  });

  it("index 0 est 'single' (ordre canonique single-first, piege #42)", () => {
    expect(DATEPICKER_MODES[0]).toBe('single');
  });

  it('est frozen', () => {
    expect(Object.isFrozen(DATEPICKER_MODES)).toBe(true);
  });

  it('est dedoublonne', () => {
    expect(new Set(DATEPICKER_MODES).size).toBe(DATEPICKER_MODES.length);
  });
});
