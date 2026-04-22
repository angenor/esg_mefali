import { describe, it, expect } from 'vitest';
import {
  INPUT_TYPES,
  FORM_SIZES,
  BUTTON_SIZES,
  TEXTAREA_DEFAULT_MAX_LENGTH,
} from '../../../app/components/ui/registry';

describe('ui/registry : INPUT_TYPES + FORM_SIZES (pattern CCC-9 Story 10.16)', () => {
  it('AC2 : INPUT_TYPES contient exactement les 7 types HTML5 supportes', () => {
    expect(INPUT_TYPES.length).toBe(7);
    expect(INPUT_TYPES).toEqual([
      'text',
      'email',
      'number',
      'password',
      'url',
      'tel',
      'search',
    ]);
  });

  it('AC2 : FORM_SIZES contient exactement 3 entrees (sm/md/lg)', () => {
    expect(FORM_SIZES.length).toBe(3);
    expect(FORM_SIZES).toEqual(['sm', 'md', 'lg']);
  });

  it('AC2 : INPUT_TYPES et FORM_SIZES sont frozen (Object.isFrozen)', () => {
    expect(Object.isFrozen(INPUT_TYPES)).toBe(true);
    expect(Object.isFrozen(FORM_SIZES)).toBe(true);
  });

  it('AC2 : INPUT_TYPES et FORM_SIZES sont dedoublonnes', () => {
    expect(new Set(INPUT_TYPES).size).toBe(INPUT_TYPES.length);
    expect(new Set(FORM_SIZES).size).toBe(FORM_SIZES.length);
  });

  it('AC2 : FORM_SIZES est un tuple INDEPENDANT de BUTTON_SIZES (pas re-export)', () => {
    // Meme valeurs mais identite differente — un rebrand futur des formulaires
    // ne doit pas coupler les boutons (piege #11 codemap §5).
    expect(FORM_SIZES).toEqual(BUTTON_SIZES);
    expect(FORM_SIZES).not.toBe(BUTTON_SIZES);
  });

  it('Story 10.16 : TEXTAREA_DEFAULT_MAX_LENGTH = 400 (spec 018 AC5)', () => {
    expect(TEXTAREA_DEFAULT_MAX_LENGTH).toBe(400);
  });
});
