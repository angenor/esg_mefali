/**
 * Tests scan NFR66 `ui/DatePicker.vue` + `DatePicker.stories.ts` (Story 10.20 AC10).
 * Pattern byte-identique 10.17-10.19 scan hex hardcoded.
 *
 * Exigences AC10 :
 *  - 0 hit `#[0-9A-Fa-f]{3,8}` (tokens @theme uniquement dans CSS/Tailwind classes).
 *  - 0 hit `: any\b` / `as unknown` dans DatePicker.vue (strict typing).
 */
import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const ROOT = resolve(__dirname, '../../..');
const DATEPICKER_VUE = resolve(
  ROOT,
  'app/components/ui/DatePicker.vue',
);
const DATEPICKER_STORIES = resolve(
  ROOT,
  'app/components/ui/DatePicker.stories.ts',
);

describe('NFR66 no-hex hardcoded (Story 10.20 AC10)', () => {
  it('DatePicker.vue ne contient aucune couleur hex hardcodee', () => {
    const source = readFileSync(DATEPICKER_VUE, 'utf-8');
    const hexPattern = /#[0-9A-Fa-f]{3,8}\b/g;
    const hits = source.match(hexPattern);
    expect(hits, `hex hits: ${JSON.stringify(hits)}`).toBeNull();
  });

  it('DatePicker.stories.ts ne contient aucune couleur hex hardcodee', () => {
    const source = readFileSync(DATEPICKER_STORIES, 'utf-8');
    const hexPattern = /#[0-9A-Fa-f]{3,8}\b/g;
    const hits = source.match(hexPattern);
    expect(hits, `hex hits: ${JSON.stringify(hits)}`).toBeNull();
  });

  it('DatePicker.vue ne contient ni `: any` ni `as unknown`', () => {
    const source = readFileSync(DATEPICKER_VUE, 'utf-8');
    expect(source).not.toMatch(/:\s*any\b/);
    expect(source).not.toMatch(/\bas\s+unknown\b/);
  });
});
