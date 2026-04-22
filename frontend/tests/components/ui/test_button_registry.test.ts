import { describe, it, expect } from 'vitest';
import {
  BUTTON_VARIANTS,
  BUTTON_SIZES,
} from '../../../app/components/ui/registry';

describe('ui/registry BUTTON_VARIANTS + BUTTON_SIZES (pattern CCC-9)', () => {
  it('BUTTON_VARIANTS contient exactement 4 entrees', () => {
    expect(BUTTON_VARIANTS.length).toBe(4);
    expect(BUTTON_VARIANTS).toEqual(['primary', 'secondary', 'ghost', 'danger']);
  });

  it('BUTTON_SIZES contient exactement 3 entrees', () => {
    expect(BUTTON_SIZES.length).toBe(3);
    expect(BUTTON_SIZES).toEqual(['sm', 'md', 'lg']);
  });

  it('BUTTON_VARIANTS et BUTTON_SIZES sont frozen (Object.isFrozen)', () => {
    expect(Object.isFrozen(BUTTON_VARIANTS)).toBe(true);
    expect(Object.isFrozen(BUTTON_SIZES)).toBe(true);
  });

  it('BUTTON_VARIANTS et BUTTON_SIZES ont des noms uniques (dedoublonnes)', () => {
    expect(new Set(BUTTON_VARIANTS).size).toBe(BUTTON_VARIANTS.length);
    expect(new Set(BUTTON_SIZES).size).toBe(BUTTON_SIZES.length);
  });
});
