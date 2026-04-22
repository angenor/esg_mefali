import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const UI_DIR = resolve(__dirname, '../../../app/components/ui');
// Scope strict Story 10.15 : Button.vue + registry.ts. Les 2 composants brownfield
// (FullscreenModal.vue, ToastNotification.vue) sont HORS scope migration 10.15.
const SCANNED_FILES = ['Button.vue', 'registry.ts'] as const;

function stripComments(source: string): string {
  return source
    .replace(/<!--[\s\S]*?-->/g, '')
    .replace(/\/\*[\s\S]*?\*\//g, '')
    .replace(/(^|\s)\/\/[^\n]*/g, '$1');
}

describe('ui/Button.vue + registry.ts : 0 hex hardcode (AC2)', () => {
  it.each(SCANNED_FILES)('%s ne contient aucun hex hors commentaires', (file) => {
    const content = stripComments(readFileSync(resolve(UI_DIR, file), 'utf8'));
    const hexPattern = /#[0-9A-Fa-f]{3,8}\b/;
    expect({ file, match: content.match(hexPattern)?.[0] ?? null }).toEqual({
      file,
      match: null,
    });
  });
});
