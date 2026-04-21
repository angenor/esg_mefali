import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const DOC = readFileSync(
  resolve(__dirname, '../../docs/CODEMAPS/storybook.md'),
  'utf8'
);
const INDEX = readFileSync(
  resolve(__dirname, '../../docs/CODEMAPS/index.md'),
  'utf8'
);

const EXPECTED_SECTIONS = [
  '## 1. Contexte',
  '## 2. Arborescence cible',
  '## 3. Lancer Storybook en local',
  '## 4. Ajouter un 7ᵉ composant à gravité',
  '## 5. Pièges documentés',
];

describe('docs/CODEMAPS/storybook.md (Story 10.14)', () => {
  it('contient les 5 sections H2 exactes', () => {
    for (const h2 of EXPECTED_SECTIONS) {
      expect(DOC).toContain(h2);
    }
  });

  it('§5 liste au moins 8 pièges (bullets `- **...**`)', () => {
    const section5Start = DOC.indexOf('## 5. Pièges documentés');
    expect(section5Start).toBeGreaterThan(0);
    const section5End = DOC.indexOf('\n---', section5Start);
    const section5 = DOC.slice(section5Start, section5End > 0 ? section5End : undefined);
    const bullets = section5.match(/^- \*\*/gm) ?? [];
    expect(bullets.length).toBeGreaterThanOrEqual(8);
  });

  it('docs/CODEMAPS/index.md reference storybook.md', () => {
    expect(INDEX).toContain('[storybook.md](./storybook.md)');
  });
});
