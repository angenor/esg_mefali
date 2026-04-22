/**
 * Contraste WCAG 2.1 AA pour tous les couples (bg, text) rendus par Badge.vue.
 * Patch code-review 10.17 CRITICAL-1/2/3 : test pur JS qui calcule la luminance
 * relative et le ratio (L1+0.05)/(L2+0.05) a partir des hex tokens main.css.
 *
 * Necessaire car `vitest-axe` desactive `color-contrast` sous happy-dom (pas de
 * pipeline CSS). Ce test ne depend ni de DOM ni de browser — il lit les hex
 * directement depuis `main.css` via regex et asserte AA >= 4.5:1 pour tous les
 * text/bg combos emis par `variantClasses` de Badge.vue.
 */
import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const MAIN_CSS_PATH = resolve(__dirname, '../../../app/assets/css/main.css');
const MAIN_CSS = readFileSync(MAIN_CSS_PATH, 'utf8');

// Parse les `--color-*: #XXXXXX;` declarees dans `@theme`.
function extractTokens(): Record<string, string> {
  const tokens: Record<string, string> = {};
  const re = /--color-([a-z0-9-]+):\s*(#[0-9A-Fa-f]{6,8})\s*;/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(MAIN_CSS)) !== null) {
    tokens[m[1]] = m[2].toUpperCase();
  }
  return tokens;
}

const TOKENS = extractTokens();

// sRGB -> luminance relative WCAG 2.1.
function relLuminance(hex: string): number {
  const h = hex.replace('#', '');
  const r = parseInt(h.slice(0, 2), 16) / 255;
  const g = parseInt(h.slice(2, 4), 16) / 255;
  const b = parseInt(h.slice(4, 6), 16) / 255;
  const lin = (c: number) => (c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4));
  return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
}

function contrast(hexA: string, hexB: string): number {
  const la = relLuminance(hexA);
  const lb = relLuminance(hexB);
  const [lighter, darker] = la > lb ? [la, lb] : [lb, la];
  return (lighter + 0.05) / (darker + 0.05);
}

// DARK_BG simule `dark .bg-surface-dark-bg` (panneau dark du projet).
const DARK_BG = '#111827'; // gray-900 par convention Tailwind dark palette.

// Composite couleur + opacite sur un fond (pour simuler `bg-X/20`).
function composite(hex: string, alpha: number, bgHex: string): string {
  const parse = (h: string) => {
    const s = h.replace('#', '');
    return [parseInt(s.slice(0, 2), 16), parseInt(s.slice(2, 4), 16), parseInt(s.slice(4, 6), 16)];
  };
  const [r1, g1, b1] = parse(hex);
  const [r2, g2, b2] = parse(bgHex);
  const r = Math.round(r1 * alpha + r2 * (1 - alpha));
  const g = Math.round(g1 * alpha + g2 * (1 - alpha));
  const b = Math.round(b1 * alpha + b2 * (1 - alpha));
  return '#' + [r, g, b].map((x) => x.toString(16).padStart(2, '0').toUpperCase()).join('');
}

const AA_NORMAL = 4.5;

// Families + states consommes par Badge.vue (variantClasses).
const FAMILIES = [
  { name: 'verdict', states: ['pass', 'fail', 'reported', 'na'] },
  {
    name: 'fa',
    states: [
      'draft',
      'snapshot-frozen',
      'signed',
      'exported',
      'submitted',
      'in-review',
      'accepted',
      'rejected',
      'withdrawn',
    ],
  },
  { name: 'admin', states: ['n1', 'n2', 'n3'] },
];

describe('ui/Badge : tokens presents dans main.css (patch 10.17 CRITICAL)', () => {
  for (const { name, states } of FAMILIES) {
    for (const state of states) {
      it(`${name}-${state} : base + -soft + -strong presents`, () => {
        expect(TOKENS[`${name}-${state}`]).toMatch(/^#[0-9A-F]{6}$/);
        expect(TOKENS[`${name}-${state}-soft`]).toMatch(/^#[0-9A-F]{6}$/);
        expect(TOKENS[`${name}-${state}-strong`]).toMatch(/^#[0-9A-F]{6}$/);
      });
    }
  }
});

describe('ui/Badge : contraste AA light mode (bg-*-soft + text-*-strong) >= 4.5:1', () => {
  for (const { name, states } of FAMILIES) {
    for (const state of states) {
      it(`${name}-${state} light : ratio >= ${AA_NORMAL}:1`, () => {
        const bg = TOKENS[`${name}-${state}-soft`];
        const text = TOKENS[`${name}-${state}-strong`];
        const ratio = contrast(bg, text);
        expect({ state: `${name}-${state}`, mode: 'light', bg, text, ratio: +ratio.toFixed(2) })
          .toMatchObject({ ratio: expect.any(Number) });
        expect(ratio, `${name}-${state} light ${text} on ${bg} = ${ratio.toFixed(2)}:1`)
          .toBeGreaterThanOrEqual(AA_NORMAL);
      });
    }
  }
});

describe('ui/Badge : contraste AA dark mode (bg-*/20 + text-*-soft) >= 4.5:1', () => {
  for (const { name, states } of FAMILIES) {
    for (const state of states) {
      it(`${name}-${state} dark : ratio >= ${AA_NORMAL}:1`, () => {
        const baseColor = TOKENS[`${name}-${state}`];
        const textColor = TOKENS[`${name}-${state}-soft`];
        const compositedBg = composite(baseColor, 0.2, DARK_BG);
        const ratio = contrast(compositedBg, textColor);
        expect(ratio, `${name}-${state} dark ${textColor} on ${compositedBg} = ${ratio.toFixed(2)}:1`)
          .toBeGreaterThanOrEqual(AA_NORMAL);
      });
    }
  }
});

describe('ui/Badge : admin decouple de lifecycle-outcome (patch decision 10.17)', () => {
  it('admin-n1 != fa-accepted (teintes decouplees)', () => {
    expect(TOKENS['admin-n1']).not.toBe(TOKENS['fa-accepted']);
  });

  it('admin-n1 est dans la famille bleue (sky) pas verte', () => {
    // sky-700 #0369A1 : R < G < B avec R faible, B dominant (typique bleu).
    const n1 = TOKENS['admin-n1'].replace('#', '');
    const r = parseInt(n1.slice(0, 2), 16);
    const b = parseInt(n1.slice(4, 6), 16);
    expect(b).toBeGreaterThan(r);
  });
});
