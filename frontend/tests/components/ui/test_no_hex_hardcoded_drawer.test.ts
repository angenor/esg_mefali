import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const UI_DIR = resolve(__dirname, '../../../app/components/ui');
// Scope Story 10.18 : primitive Drawer + sa story (tokens @theme exclusifs).
const SCANNED_FILES = ['Drawer.vue', 'Drawer.stories.ts'] as const;

function stripComments(source: string): string {
  return source
    .replace(/<!--[\s\S]*?-->/g, '')
    .replace(/\/\*[\s\S]*?\*\//g, '')
    .replace(/(^|\s)\/\/[^\n]*/g, '$1');
}

describe('ui/Drawer : 0 hex hardcode (AC1 Story 10.18)', () => {
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
