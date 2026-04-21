import { describe, it, expect } from 'vitest';
import { readFileSync, readdirSync } from 'node:fs';
import { resolve } from 'node:path';

const GRAVITY_DIR = resolve(__dirname, '../../../app/components/gravity');
const VUE_FILES = readdirSync(GRAVITY_DIR).filter((f) => f.endsWith('.vue'));

/**
 * Supprime les commentaires HTML <!-- ... --> et les commentaires JS //... + bloc.
 * Les tokens @theme exposant des hex vivent dans main.css (pas dans gravity/).
 */
function stripComments(source: string): string {
  return source
    .replace(/<!--[\s\S]*?-->/g, '')
    .replace(/\/\*[\s\S]*?\*\//g, '')
    .replace(/(^|\s)\/\/[^\n]*/g, '$1');
}

describe('gravity/*.vue : 0 hex hardcode (AC6)', () => {
  it('chaque composant gravity ne contient aucun hex hors commentaires', () => {
    expect(VUE_FILES.length).toBe(6);
    const hexPattern = /#[0-9A-Fa-f]{3,8}\b/;
    for (const file of VUE_FILES) {
      const content = stripComments(readFileSync(resolve(GRAVITY_DIR, file), 'utf8'));
      expect({ file, match: content.match(hexPattern)?.[0] ?? null }).toEqual({
        file,
        match: null,
      });
    }
  });
});
