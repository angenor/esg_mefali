/**
 * Scan 0 hex hardcode Combobox + Tabs (Story 10.19 AC14 scan NFR66).
 * Pattern byte-identique test_no_hex_hardcoded_drawer (10.18).
 */
import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const UI_DIR = resolve(__dirname, '../../../app/components/ui');

const SCANNED_FILES = [
  'Combobox.vue',
  'Combobox.stories.ts',
  'Tabs.vue',
  'Tabs.stories.ts',
] as const;

function stripComments(source: string): string {
  return source
    .replace(/<!--[\s\S]*?-->/g, '')
    .replace(/\/\*[\s\S]*?\*\//g, '')
    .replace(/(^|\s)\/\/[^\n]*/g, '$1');
}

describe('ui/Combobox + ui/Tabs : 0 hex hardcode (Story 10.19 AC14)', () => {
  it.each(SCANNED_FILES)(
    '%s ne contient aucun hex hors commentaires',
    (file) => {
      const content = stripComments(
        readFileSync(resolve(UI_DIR, file), 'utf8'),
      );
      const hexPattern = /#[0-9A-Fa-f]{3,8}\b/;
      expect({ file, match: content.match(hexPattern)?.[0] ?? null }).toEqual({
        file,
        match: null,
      });
    },
  );
});
