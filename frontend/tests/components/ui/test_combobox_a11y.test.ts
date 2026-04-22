/**
 * Tests a11y ui/Combobox (AC4 + AC14 Story 10.19).
 *
 * Portail Reka UI ComboboxPortal → assertions DOM via document.body.querySelector
 * (Pattern A — leçon 10.16 H-3 capitalisee + piege #28 10.18).
 *
 * Note leçon 10.15 HIGH-2 + 10.18 §4ter.bis : les audits portail-dependants
 * (contraste runtime, focus, animations) sont DELEGUES a Storybook addon-a11y
 * runtime car happy-dom n'evalue pas le layout CSS. Ici : smoke DOM + ARIA.
 */
import { describe, it, expect, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/vue';
import userEvent from '@testing-library/user-event';
import { axe, toHaveNoViolations } from 'jest-axe';
import Combobox from '../../../app/components/ui/Combobox.vue';

expect.extend(toHaveNoViolations);

const AXE_OPTIONS = {
  rules: {
    // happy-dom n'evalue pas le layout CSS → contraste delegue Storybook runtime
    'color-contrast': { enabled: false },
    region: { enabled: false },
    // Artefacts happy-dom sur portails Reka UI coexistant (piege #28 10.18)
    'aria-hidden-focus': { enabled: false },
  },
} as const;

afterEach(() => {
  cleanup();
  document.body
    .querySelectorAll('[role="listbox"]')
    .forEach((el) => el.remove());
});

describe('ui/Combobox : AC4 ARIA DOM (Pattern A)', () => {
  it('role="combobox" present sur l\'input', () => {
    render(Combobox, {
      props: {
        modelValue: null,
        options: [{ value: 'sn', label: 'Sénégal' }],
        label: 'Pays',
      },
    });
    const combobox = screen.getByRole('combobox');
    expect(combobox.getAttribute('role')).toBe('combobox');
  });

  it('aria-expanded passe de "false" a "true" apres ouverture', async () => {
    const user = userEvent.setup();
    render(Combobox, {
      props: {
        modelValue: null,
        options: [{ value: 'sn', label: 'Sénégal' }],
        label: 'Pays',
      },
    });
    const combobox = screen.getByRole('combobox');
    expect(combobox.getAttribute('aria-expanded')).toBe('false');
    combobox.focus();
    await user.keyboard('{ArrowDown}');
    expect(combobox.getAttribute('aria-expanded')).toBe('true');
  });

  it('listbox rendu dans document.body (portal)', async () => {
    const user = userEvent.setup();
    render(Combobox, {
      props: {
        modelValue: null,
        options: [{ value: 'sn', label: 'Sénégal' }],
        label: 'Pays',
      },
    });
    const combobox = screen.getByRole('combobox');
    combobox.focus();
    await user.keyboard('{ArrowDown}');
    // Le listbox est portalise — on peut le localiser soit via screen (qui
    // scanne aussi document.body), soit via querySelector direct body.
    expect(document.body.querySelector('[role="listbox"]')).not.toBeNull();
  });
});

describe('ui/Combobox : vitest-axe smoke (DELEGATED contrast/portal runtime)', () => {
  it('rendu ferme : aucune violation axe hors regles deleguees', async () => {
    const { container } = render(Combobox, {
      props: {
        modelValue: null,
        options: [{ value: 'sn', label: 'Sénégal' }],
        label: 'Pays',
      },
    });
    // DELEGATED TO Storybook ComboboxKeyboardNavigation : contraste runtime + focus visuel
    const results = await axe(container, AXE_OPTIONS);
    expect(results).toHaveNoViolations();
  });
});
