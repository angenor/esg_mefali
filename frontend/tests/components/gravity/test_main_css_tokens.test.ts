import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const CSS = readFileSync(
  resolve(__dirname, '../../../app/assets/css/main.css'),
  'utf8'
);

describe('main.css : tokens @theme semantiques (Story 10.14)', () => {
  it('expose les 8 tokens verdict', () => {
    for (const name of [
      '--color-verdict-pass',
      '--color-verdict-pass-soft',
      '--color-verdict-fail',
      '--color-verdict-fail-soft',
      '--color-verdict-reported',
      '--color-verdict-reported-soft',
      '--color-verdict-na',
      '--color-verdict-na-soft',
    ]) {
      expect(CSS).toContain(name);
    }
  });

  it('expose les 9 tokens FundApplication lifecycle', () => {
    for (const name of [
      '--color-fa-draft',
      '--color-fa-snapshot-frozen',
      '--color-fa-signed',
      '--color-fa-exported',
      '--color-fa-submitted',
      '--color-fa-in-review',
      '--color-fa-accepted',
      '--color-fa-rejected',
      '--color-fa-withdrawn',
    ]) {
      expect(CSS).toContain(name);
    }
  });

  it('expose les 3 tokens admin criticite', () => {
    for (const name of ['--color-admin-n1', '--color-admin-n2', '--color-admin-n3']) {
      expect(CSS).toContain(name);
    }
  });
});
