/**
 * Tests hygiene couleurs ui/EsgIcon (AC6 + AC10 Story 10.21).
 *
 * Scan runtime `rg` equivalent en lecture fichier : 0 hit hex ≠ tokens
 * `@theme` + 0 hit `: any`/`as unknown`. Application AC6 + AC10.
 *
 * Perimetre :
 *  - EsgIcon.vue (composant)
 *  - EsgIcon.stories.ts (si existante)
 *  - assets/icons/esg/*.svg (SVG custom)
 */
import { describe, it, expect } from 'vitest';
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { join } from 'node:path';

const ROOT = join(__dirname, '..', '..', '..');
const COMPONENT_PATH = join(ROOT, 'app', 'components', 'ui', 'EsgIcon.vue');
const STORIES_PATH = join(ROOT, 'app', 'components', 'ui', 'EsgIcon.stories.ts');
const SVG_DIR = join(ROOT, 'app', 'assets', 'icons', 'esg');

const HEX_REGEX = /#[0-9A-Fa-f]{3,8}\b/g;
const ANY_REGEX = /: any\b|\bas unknown\b/g;

describe('ui/EsgIcon : AC6 + AC10 0 hex hardcoded', () => {
  it('EsgIcon.vue ne contient aucun litteral hex (tokens @theme uniquement)', () => {
    const src = readFileSync(COMPONENT_PATH, 'utf-8');
    const matches = src.match(HEX_REGEX) ?? [];
    expect(matches).toEqual([]);
  });

  it('EsgIcon.stories.ts (si existe) ne contient aucun litteral hex', () => {
    if (!existsSync(STORIES_PATH)) {
      // Story co-localisation optionnelle au moment du test.
      return;
    }
    const src = readFileSync(STORIES_PATH, 'utf-8');
    const matches = src.match(HEX_REGEX) ?? [];
    expect(matches).toEqual([]);
  });

  it('assets/icons/esg/*.svg ne contiennent aucun litteral hex (currentColor only)', () => {
    const files = readdirSync(SVG_DIR).filter((f) => f.endsWith('.svg'));
    expect(files.length).toBeGreaterThanOrEqual(6);
    for (const file of files) {
      const src = readFileSync(join(SVG_DIR, file), 'utf-8');
      const matches = src.match(HEX_REGEX) ?? [];
      expect(matches, `${file} contient des hex hardcoded`).toEqual([]);
    }
  });
});

describe('ui/EsgIcon : AC10 0 any / as unknown', () => {
  it('EsgIcon.vue ne contient ni ": any" ni "as unknown"', () => {
    const src = readFileSync(COMPONENT_PATH, 'utf-8');
    const matches = src.match(ANY_REGEX) ?? [];
    expect(matches).toEqual([]);
  });
});
