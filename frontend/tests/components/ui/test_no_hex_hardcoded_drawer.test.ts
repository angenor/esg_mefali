import { describe, it, expect } from 'vitest';
import { readFileSync, readdirSync } from 'node:fs';
import { resolve } from 'node:path';

const UI_DIR = resolve(__dirname, '../../../app/components/ui');

// Scope Story 10.18 : primitive Drawer + sa story (tokens @theme exclusifs).
const SCANNED_FILES = ['Drawer.vue', 'Drawer.stories.ts'] as const;

// L-3 10.18 post-review : scan hex etendu a tout le dossier components/ui/
// (Button, Input, Textarea, Select, Badge, Drawer, ...). Protege contre
// un hex introduit par regression future sur une primitive non-couverte.
// Fichiers `.ts` et `.vue` uniquement (exclure `.test.ts` hors scope).
function listUiSourceFiles(): string[] {
  return readdirSync(UI_DIR, { withFileTypes: true })
    .filter((d) => d.isFile())
    .map((d) => d.name)
    .filter((name) => name.endsWith('.vue') || (name.endsWith('.ts') && !name.endsWith('.test.ts')));
}

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

describe('ui/* : 0 hex hardcode global (L-3 10.18 post-review — scope etendu)', () => {
  const globalFiles = listUiSourceFiles();
  it.each(globalFiles)(
    '%s (components/ui/) ne contient aucun hex hors commentaires',
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
