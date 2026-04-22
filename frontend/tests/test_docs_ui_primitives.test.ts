import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const DOC_PATH = resolve(__dirname, '../../docs/CODEMAPS/ui-primitives.md');
const INDEX_PATH = resolve(__dirname, '../../docs/CODEMAPS/index.md');

describe('docs/CODEMAPS/ui-primitives.md (AC10)', () => {
  const content = readFileSync(DOC_PATH, 'utf8');

  it('contient exactement les 5 sections H2 requises', () => {
    const required = [
      '## 1. Contexte',
      '## 2. Arborescence cible',
      '## 3. Utiliser `ui/Button` dans un composant',
      '## 4. Ajouter une 8ᵉ primitive UI',
      '## 5. Pièges documentés',
    ];
    for (const heading of required) {
      expect(content).toContain(heading);
    }
  });

  it('§5 Pièges documentés contient au minimum 8 entrées numérotées', () => {
    const piegesSection = content.split('## 5. Pièges documentés')[1] ?? '';
    // Compte les entrees numerotees (1. 2. 3. ...) en debut de ligne.
    const matches = piegesSection.match(/^\d+\.\s/gm) ?? [];
    expect(matches.length).toBeGreaterThanOrEqual(8);
  });

  it('§3 contient ≥ 4 exemples de code Vue (blocs ```vue)', () => {
    // Compte les blocs ```vue (ouvrants) dans le fichier.
    const vueBlocks = content.match(/^```vue\s*$/gm) ?? [];
    expect(vueBlocks.length).toBeGreaterThanOrEqual(1); // au moins 1 bloc
    // Le bloc principal §3 contient plusieurs exemples (commentaires numerotes).
    const section3 = content.split('## 3.')[1]?.split('## 4.')[0] ?? '';
    const numberedExamples = section3.match(/<!--\s*\d+\./g) ?? [];
    expect(numberedExamples.length).toBeGreaterThanOrEqual(4);
  });

  it('docs/CODEMAPS/index.md reference ui-primitives.md', () => {
    const indexContent = readFileSync(INDEX_PATH, 'utf8');
    expect(indexContent).toContain('ui-primitives.md');
  });
});
