import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const DOC_PATH = resolve(__dirname, '../../docs/CODEMAPS/ui-primitives.md');
const INDEX_PATH = resolve(__dirname, '../../docs/CODEMAPS/index.md');

describe('docs/CODEMAPS/ui-primitives.md (AC10 Story 10.15 + AC12 Story 10.16)', () => {
  const content = readFileSync(DOC_PATH, 'utf8');

  it('contient les 5 sections H2 requises (§3 renommee 10.16)', () => {
    const required = [
      '## 1. Contexte',
      '## 2. Arborescence cible',
      '## 3. Utiliser les primitives UI dans un composant',
      '## 4. Ajouter une 8ᵉ primitive UI',
      '## 5. Pièges documentés',
    ];
    for (const heading of required) {
      expect(content).toContain(heading);
    }
  });

  it('AC12 Story 10.16 : §3 contient 3 sous-sections H3 ui/Input + ui/Textarea + ui/Select', () => {
    expect(content).toContain('### 3.0 `ui/Button`');
    expect(content).toContain('### 3.1 `ui/Input`');
    expect(content).toContain('### 3.2 `ui/Textarea`');
    expect(content).toContain('### 3.3 `ui/Select`');
  });

  it('AC12 Story 10.16 : §5 Pièges documentés contient >= 16 entrees numerotees', () => {
    const piegesSection = content.split('## 5. Pièges documentés')[1] ?? '';
    // Delimite avant la section suivante (§6 Ressources / A11y).
    const body = piegesSection.split(/^##\s/m)[0] ?? piegesSection;
    const matches = body.match(/^\d+\.\s/gm) ?? [];
    expect(matches.length).toBeGreaterThanOrEqual(16);
  });

  it('AC10 Story 10.15 : §3.0 (ui/Button) contient >= 4 exemples Vue numerotes', () => {
    const section30 = content.split('### 3.0')[1]?.split('### 3.1')[0] ?? '';
    const numberedExamples = section30.match(/<!--\s*\d+\./g) ?? [];
    expect(numberedExamples.length).toBeGreaterThanOrEqual(4);
  });

  it('AC12 Story 10.16 : chaque sous-section primitive contient des exemples Vue numerotes', () => {
    const section31 = content.split('### 3.1')[1]?.split('### 3.2')[0] ?? '';
    const section32 = content.split('### 3.2')[1]?.split('### 3.3')[0] ?? '';
    const section33 = content.split('### 3.3')[1]?.split(/^##\s/m)[0] ?? '';
    expect((section31.match(/<!--\s*\d+\./g) ?? []).length).toBeGreaterThanOrEqual(2);
    expect((section32.match(/<!--\s*\d+\./g) ?? []).length).toBeGreaterThanOrEqual(2);
    expect((section33.match(/<!--\s*\d+\./g) ?? []).length).toBeGreaterThanOrEqual(1);
  });

  it('AC12 Story 10.16 : §6 A11y mentionne text-brand-orange 3,85:1 rationale auxiliaire', () => {
    expect(content).toMatch(/text-brand-orange/i);
    expect(content).toContain('3,85:1');
  });

  it('docs/CODEMAPS/index.md reference ui-primitives.md', () => {
    const indexContent = readFileSync(INDEX_PATH, 'utf8');
    expect(indexContent).toContain('ui-primitives.md');
  });
});
