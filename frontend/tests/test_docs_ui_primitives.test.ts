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

  it('AC14 Story 10.19 : §3 contient 7 sous-sections H3 (Button + Input + Textarea + Select + Badge + Drawer + Combobox + Tabs)', () => {
    expect(content).toContain('### 3.0 `ui/Button`');
    expect(content).toContain('### 3.1 `ui/Input`');
    expect(content).toContain('### 3.2 `ui/Textarea`');
    expect(content).toContain('### 3.3 `ui/Select`');
    expect(content).toContain('### 3.4 `ui/Badge`');
    expect(content).toContain('### 3.5 `ui/Drawer`');
    expect(content).toContain('### 3.6 `ui/Combobox`');
    expect(content).toContain('### 3.7 `ui/Tabs`');
  });

  it('AC14 Story 10.19 : §5 Pièges documentés contient >= 40 entrees numerotees (34 -> 40 cumul Combobox/Tabs)', () => {
    const piegesSection = content.split('## 5. Pièges documentés')[1] ?? '';
    const body = piegesSection.split(/^##\s/m)[0] ?? piegesSection;
    const matches = body.match(/^\d+\.\s/gm) ?? [];
    expect(matches.length).toBeGreaterThanOrEqual(40);
  });

  it('AC14 Story 10.19 : §3.6 Combobox contient >= 4 exemples Vue numerotes', () => {
    const section36 = content.split('### 3.6')[1]?.split('### 3.7')[0] ?? '';
    const numberedExamples = section36.match(/<!--\s*\d+\./g) ?? [];
    expect(numberedExamples.length).toBeGreaterThanOrEqual(4);
  });

  it('AC14 Story 10.19 : §3.7 Tabs contient >= 4 exemples Vue numerotes', () => {
    const section37 = content.split('### 3.7')[1]?.split(/^##\s/m)[0] ?? '';
    const numberedExamples = section37.match(/<!--\s*\d+\./g) ?? [];
    expect(numberedExamples.length).toBeGreaterThanOrEqual(4);
  });

  it('AC14 Story 10.19 : §3.6 Combobox mentionne IME composition guard + ignore-filter', () => {
    const section36 = content.split('### 3.6')[1]?.split('### 3.7')[0] ?? '';
    expect(section36).toMatch(/IME composition/i);
    expect(section36).toMatch(/ignore-filter|ignoreFilter/i);
  });

  it('AC14 Story 10.19 : §3.7 Tabs mentionne orientation + activationMode + forceMount', () => {
    const section37 = content.split('### 3.7')[1]?.split(/^##\s/m)[0] ?? '';
    expect(section37).toMatch(/orientation/i);
    expect(section37).toMatch(/activation[mM]ode/);
    expect(section37).toMatch(/forceMount|force-mount/);
  });

  it('AC14 Story 10.18 : §3.5 Drawer contient >= 4 exemples Vue numerotes', () => {
    const section35 = content.split('### 3.5')[1]?.split(/^##\s/m)[0] ?? '';
    const numberedExamples = section35.match(/<!--\s*\d+\./g) ?? [];
    expect(numberedExamples.length).toBeGreaterThanOrEqual(4);
  });

  it('AC14 Story 10.18 : §3.5 Drawer mentionne role="complementary" override', () => {
    const section35 = content.split('### 3.5')[1]?.split(/^##\s/m)[0] ?? '';
    expect(section35).toMatch(/role="complementary"/);
    expect(section35).toMatch(/aria-modal="false"|Reka UI/i);
  });

  it('AC10 Story 10.15 : §3.0 (ui/Button) contient >= 4 exemples Vue numerotes', () => {
    const section30 = content.split('### 3.0')[1]?.split('### 3.1')[0] ?? '';
    const numberedExamples = section30.match(/<!--\s*\d+\./g) ?? [];
    expect(numberedExamples.length).toBeGreaterThanOrEqual(4);
  });

  it('AC12 Story 10.16 : chaque sous-section primitive contient des exemples Vue numerotes', () => {
    const section31 = content.split('### 3.1')[1]?.split('### 3.2')[0] ?? '';
    const section32 = content.split('### 3.2')[1]?.split('### 3.3')[0] ?? '';
    const section33 = content.split('### 3.3')[1]?.split('### 3.4')[0] ?? '';
    expect((section31.match(/<!--\s*\d+\./g) ?? []).length).toBeGreaterThanOrEqual(2);
    expect((section32.match(/<!--\s*\d+\./g) ?? []).length).toBeGreaterThanOrEqual(2);
    expect((section33.match(/<!--\s*\d+\./g) ?? []).length).toBeGreaterThanOrEqual(1);
  });

  it('AC11 Story 10.17 : §3.4 Badge contient >= 4 exemples Vue numerotes', () => {
    const section34 = content.split('### 3.4')[1]?.split(/^##\s/m)[0] ?? '';
    const numberedExamples = section34.match(/<!--\s*\d+\./g) ?? [];
    expect(numberedExamples.length).toBeGreaterThanOrEqual(4);
  });

  it('AC12 Story 10.16 : §6 A11y mentionne text-brand-orange 3,85:1 rationale auxiliaire', () => {
    expect(content).toMatch(/text-brand-orange/i);
    expect(content).toContain('3,85:1');
  });

  it('AC11 Story 10.17 : §6 A11y mentionne verdict-reported D97706 4,69:1 (cleanup L-4 10.16)', () => {
    expect(content).toMatch(/text-verdict-reported|verdict-reported/i);
    expect(content).toContain('4,69:1');
  });

  it('Patch code-review 10.17 : §6bis documente le soft-bg pattern AA compliance', () => {
    expect(content).toMatch(/6bis\.\s+Soft-background/i);
    expect(content).toContain('Decoupling admin');
    // La table §6bis cite au moins 3 ratios calcules text-strong sur bg-soft.
    expect(content).toMatch(/10,08:1|10\.08:1/); // verdict-pass strong on soft
    expect(content).toMatch(/9,93:1|9\.93:1/); // verdict-fail / admin-n3
  });

  it('Patch code-review 10.17 : §3.4 Badge documente decouplage admin sky vs fa.accepted', () => {
    const section34 = content.split('### 3.4')[1]?.split(/^##\s/m)[0] ?? '';
    expect(section34).toMatch(/sky-700|sky/i);
    expect(section34).toMatch(/d[eé]coupl(age|e)/i);
  });

  it('docs/CODEMAPS/index.md reference ui-primitives.md', () => {
    const indexContent = readFileSync(INDEX_PATH, 'utf8');
    expect(indexContent).toContain('ui-primitives.md');
  });

  it('AC10 Story 10.20 : §3.8 DatePicker present avec wrapper Reka UI PopoverRoot+CalendarRoot', () => {
    expect(content).toContain('### 3.8 `ui/DatePicker`');
    const section38 = content.split('### 3.8')[1]?.split(/^##\s/m)[0] ?? '';
    expect(section38).toMatch(/PopoverRoot/);
    expect(section38).toMatch(/CalendarRoot|RangeCalendarRoot/);
  });

  it('AC10 Story 10.20 : §3.8 DatePicker contient >= 4 exemples Vue numerotes', () => {
    const section38 = content.split('### 3.8')[1]?.split(/^##\s/m)[0] ?? '';
    const numberedExamples = section38.match(/<!--\s*\d+\./g) ?? [];
    expect(numberedExamples.length).toBeGreaterThanOrEqual(4);
  });

  it('AC10 Story 10.20 : §3.8 DatePicker mentionne @internationalized/date + locale FR + L22 displayValue + L23 lifecycle', () => {
    const section38 = content.split('### 3.8')[1]?.split(/^##\s/m)[0] ?? '';
    expect(section38).toMatch(/@internationalized\/date/);
    expect(section38).toMatch(/locale|fr-FR/i);
    expect(section38).toMatch(/L22|displayValue/);
    expect(section38).toMatch(/L23|lifecycle|reset/i);
  });

  it('AC10 Story 10.20 : §5 pieges contient >= 45 entrees numerotees (+4 post-10.19)', () => {
    const piegesSection = content.split('## 5. Pièges documentés')[1] ?? '';
    const body = piegesSection.split(/^##\s/m)[0] ?? piegesSection;
    const matches = body.match(/^\d+\.\s/gm) ?? [];
    expect(matches.length).toBeGreaterThanOrEqual(45);
  });

  it('AC10 Story 10.20 : §5 pieges documente piege #44 CalendarDate vs Date native', () => {
    const piegesSection = content.split('## 5. Pièges documentés')[1] ?? '';
    const body = piegesSection.split(/^##\s/m)[0] ?? piegesSection;
    expect(body).toMatch(/CalendarDate.*Date native|piege.*43|piege.*44/is);
  });
});
