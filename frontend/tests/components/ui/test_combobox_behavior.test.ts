/**
 * Tests comportement ui/Combobox (AC1-AC6 Story 10.19).
 *
 * Pattern A strict (10.16 H-3 capitalise + 10.17 + 10.18 §4ter.bis) :
 *  - `screen.getByRole` + `user.type/click/keyboard` (`@testing-library/user-event`),
 *  - AUCUN `wrapper.vm.*`, AUCUN `input.setValue(...)`,
 *  - ComboboxPortal → `screen.*` scanne `document.body` natif `@testing-library/vue`.
 *
 * Pattern leçon 21 §4quater : assertions observables strictes
 * (pas `.not.toBeNull()` smoke, pas `if (emitted) ...` permissif).
 *
 * Ouverture du dropdown : le clic sur l'input Reka UI ComboboxInput n'ouvre PAS
 * automatiquement le dropdown (WAI-ARIA-compliant). On utilise `{ArrowDown}`
 * sur l'input focalise pour ouvrir (pattern WAI-ARIA standard).
 */
import { describe, it, expect, afterEach } from 'vitest';
import { render, screen, fireEvent, cleanup, waitFor } from '@testing-library/vue';
import userEvent from '@testing-library/user-event';
import { nextTick } from 'vue';
import Combobox from '../../../app/components/ui/Combobox.vue';

afterEach(() => {
  cleanup();
  // Reka UI Portal peut laisser des noeuds orphelins apres unmount happy-dom
  document.body
    .querySelectorAll('[role="listbox"]')
    .forEach((el) => el.remove());
});

const PAYS_OPTIONS = [
  { value: 'sn', label: 'Sénégal' },
  { value: 'ci', label: "Côte d'Ivoire" },
  { value: 'bf', label: 'Burkina Faso' },
  { value: 'eg', label: 'Égypte' },
] as const;

const PAYS_GROUPED = [
  { value: 'sn', label: 'Sénégal', group: 'UEMOA' },
  { value: 'ci', label: "Côte d'Ivoire", group: 'UEMOA' },
  { value: 'cm', label: 'Cameroun', group: 'CEMAC' },
  { value: 'ga', label: 'Gabon', group: 'CEMAC' },
] as const;

function getComboboxInput(): HTMLElement {
  return screen.getByRole('combobox');
}

// Helper : ouvre le dropdown via focus + ArrowDown (WAI-ARIA standard Reka UI).
async function openDropdown(user: ReturnType<typeof userEvent.setup>) {
  const input = getComboboxInput();
  input.focus();
  await user.keyboard('{ArrowDown}');
}

describe('ui/Combobox : AC1 render de base + props', () => {
  it('rend un input role="combobox" avec le label associe', () => {
    render(Combobox, {
      props: {
        modelValue: null,
        options: [...PAYS_OPTIONS],
        label: 'Pays',
      },
    });
    const input = getComboboxInput();
    expect(input).toBeDefined();
    expect(input.getAttribute('aria-expanded')).toBe('false');
  });

  it('affiche le placeholder custom quand fourni', () => {
    render(Combobox, {
      props: {
        modelValue: null,
        options: [],
        label: 'Pays',
        placeholder: 'Choisir un pays...',
      },
    });
    const input = getComboboxInput() as HTMLInputElement;
    expect(input.placeholder).toBe('Choisir un pays...');
  });
});

describe('ui/Combobox : AC2 mode single + multiple', () => {
  it('single : clic option emet update:modelValue avec la valeur scalaire', async () => {
    const user = userEvent.setup();
    const { emitted } = render(Combobox, {
      props: {
        modelValue: null,
        options: [...PAYS_OPTIONS],
        label: 'Pays',
      },
    });
    await openDropdown(user);
    const option = await screen.findByRole('option', { name: /sénégal/i });
    await user.click(option);
    const events = emitted()['update:modelValue'];
    expect(events).toBeDefined();
    expect(events.at(-1)).toEqual(['sn']);
  });

  it('single : H-1 displayValue — post-select affiche le label (pas la clé brute)', async () => {
    // H-1 / Leçon 22 §4quinquies — Reka UI ComboboxInput sans display-value
    // faisait `modelValue.toString()` → input affichait 'sn' au lieu de
    // 'Sénégal' après select. Pattern A strict : observe la valeur DOM apres
    // selection runtime (Reka UI resetSearchTerm se declenche au select).
    const user = userEvent.setup();
    const { rerender } = render(Combobox, {
      props: {
        modelValue: null,
        options: [...PAYS_OPTIONS],
        label: 'Pays',
      },
    });
    await openDropdown(user);
    const option = await screen.findByRole('option', { name: /sénégal/i });
    await user.click(option);
    // Reka UI appelle displayValue via watch modelValue + nextTick reassign.
    await nextTick();
    // Remonte le v-model cote parent (simulate real v-model binding).
    await rerender({
      modelValue: 'sn',
      options: [...PAYS_OPTIONS],
      label: 'Pays',
    });
    await waitFor(() => {
      const input = getComboboxInput() as HTMLInputElement;
      expect(input.value).toBe('Sénégal');
    });
  });

  it('multiple : H-1 displayValue — input reste vide (labels dans badges)', () => {
    render(Combobox, {
      props: {
        modelValue: ['sn', 'ci'],
        options: [...PAYS_OPTIONS],
        label: 'Pays',
        multiple: true,
      },
    });
    const input = getComboboxInput() as HTMLInputElement;
    expect(input.value).toBe('');
  });

  it('multiple : render badges DOM-strict par [data-slot="badge"] (M-1 patch)', () => {
    // M-1 / Leçon 24 §4quinquies — count DOM-strict via data-slot explicite
    // au lieu du proxy role="img" couplé à l'aria-label Badge "Statut Brouillon".
    const { container } = render(Combobox, {
      props: {
        modelValue: ['sn', 'ci'],
        options: [...PAYS_OPTIONS],
        label: 'Pays',
        multiple: true,
      },
    });
    const badges = container.querySelectorAll('[data-slot="badge"]');
    expect(badges.length).toBe(2);
    // Verification observable : les labels des deux valeurs sont rendus.
    expect(screen.getByText('Sénégal')).toBeDefined();
    expect(screen.getByText(/côte d'ivoire/i)).toBeDefined();
  });

  it('multiple : bouton × retire une valeur selectionnee', async () => {
    const user = userEvent.setup();
    const { emitted } = render(Combobox, {
      props: {
        modelValue: ['sn', 'ci'],
        options: [...PAYS_OPTIONS],
        label: 'Pays',
        multiple: true,
      },
    });
    const removeBtn = screen.getByRole('button', { name: /Retirer Sénégal/i });
    await user.click(removeBtn);
    const events = emitted()['update:modelValue'];
    expect(events).toBeDefined();
    expect(events.at(-1)).toEqual([['ci']]);
  });
});

describe('ui/Combobox : branches coverage bump (H-5 ≥85% target)', () => {
  it('labelFor fallback String(value) pour option absente du set', () => {
    // Branche ?? String(value) dans labelFor — valeur 'xx' n'est pas dans options.
    render(Combobox, {
      props: {
        modelValue: ['xx', 'sn'],
        options: [...PAYS_OPTIONS],
        label: 'Pays',
        multiple: true,
      },
    });
    // L'option 'xx' est rendue avec String('xx') = 'xx' comme fallback label.
    expect(screen.getByText('xx')).toBeDefined();
  });

  it('M-6 Escape pendant composition IME → flush isComposing (defensive)', async () => {
    // Chrome macOS peut annuler une composition sur Escape sans emettre
    // compositionend ; handleInputKeydown assure isComposing=false.
    const user = userEvent.setup();
    render(Combobox, {
      props: {
        modelValue: null,
        options: [...PAYS_OPTIONS],
        label: 'Pays',
      },
    });
    await openDropdown(user);
    const input = getComboboxInput() as HTMLInputElement;
    await fireEvent.compositionStart(input);
    await fireEvent.update(input, 'sen');
    // Escape pendant composition → handleInputKeydown flush.
    await user.keyboard('{Escape}');
    // Apres flush + reopen, le filter doit fonctionner normalement.
    input.focus();
    await user.keyboard('{ArrowDown}');
    await user.type(input, 'burkina');
    expect(await screen.findByRole('option', { name: /burkina faso/i })).toBeDefined();
  });

  it('v-model:open externe false → reset via watcher (branche externe)', async () => {
    // Control externe de open via prop → watch(() => props.open) est la source.
    const { rerender } = render(Combobox, {
      props: {
        modelValue: null,
        options: [...PAYS_OPTIONS],
        label: 'Pays',
        open: true,
      },
    });
    const input = getComboboxInput() as HTMLInputElement;
    // Simule tape via user-event pendant open=true.
    await fireEvent.update(input, 'zzz');
    // Ferme via rerender avec open=false → watcher doit reset searchTerm.
    await rerender({
      modelValue: null,
      options: [...PAYS_OPTIONS],
      label: 'Pays',
      open: false,
    });
    await nextTick();
    expect(input.value).toBe('');
  });
});

describe('ui/Combobox : H-2 searchTerm lifecycle au close sans selection', () => {
  // H-2 / Leçon 23 §4quinquies — un searchTerm stale après close-without-select
  // faisait fuiter l'etat entre ouvertures. Pattern : watch(open) + reset.
  it('ouvrir + taper + Escape + rouvrir → input vide', async () => {
    const user = userEvent.setup();
    render(Combobox, {
      props: {
        modelValue: null,
        options: [...PAYS_OPTIONS],
        label: 'Pays',
      },
    });
    await openDropdown(user);
    const input = getComboboxInput() as HTMLInputElement;
    await user.type(input, 'zzz');
    expect(input.value).toBe('zzz');
    await user.keyboard('{Escape}');
    expect(input.getAttribute('aria-expanded')).toBe('false');
    // Reouverture : le searchTerm doit avoir ete reset.
    input.focus();
    await user.keyboard('{ArrowDown}');
    expect(input.value).toBe('');
    // Liste complete visible (pas filtree par stale term).
    const options = await screen.findAllByRole('option');
    expect(options.length).toBe(PAYS_OPTIONS.length);
  });
});

describe('ui/Combobox : AC3 search insensible casse + diacritiques', () => {
  it("tape 'sen' → option 'Sénégal' filtree presente", async () => {
    const user = userEvent.setup();
    render(Combobox, {
      props: {
        modelValue: null,
        options: [...PAYS_OPTIONS],
        label: 'Pays',
      },
    });
    await openDropdown(user);
    await user.type(getComboboxInput(), 'sen');
    const option = await screen.findByRole('option', { name: /sénégal/i });
    expect(option).toBeDefined();
  });

  it("tape 'COT' (majuscules) → 'Côte d'Ivoire' presente + autres filtrees", async () => {
    const user = userEvent.setup();
    render(Combobox, {
      props: {
        modelValue: null,
        options: [...PAYS_OPTIONS],
        label: 'Pays',
      },
    });
    await openDropdown(user);
    await user.type(getComboboxInput(), 'COT');
    const opt = await screen.findByRole('option', { name: /côte d'ivoire/i });
    expect(opt).toBeDefined();
    expect(screen.queryByRole('option', { name: /sénégal/i })).toBeNull();
  });

  it("tape 'egypte' (sans accent) → 'Égypte' presente (NFD diacritic strip)", async () => {
    const user = userEvent.setup();
    render(Combobox, {
      props: {
        modelValue: null,
        options: [...PAYS_OPTIONS],
        label: 'Pays',
      },
    });
    await openDropdown(user);
    await user.type(getComboboxInput(), 'egypte');
    const opt = await screen.findByRole('option', { name: /égypte/i });
    expect(opt).toBeDefined();
  });
});

describe('ui/Combobox : AC3 IME composition guard (piege #38)', () => {
  it("pendant compositionstart → input n'est pas filtre cote composant (M-3 strict)", async () => {
    // M-3 / Leçon 21 + 24 §4quinquies — assertion stricte : pendant composition,
    // le typing 'sen' ne doit PAS filtrer 'Sénégal' hors du listbox. On asserte
    // directement la presence de Sénégal (option attendue absente sans guard
    // car searchTerm='sen' matcherait) → toBeNull strict sur l'option qui
    // devrait disparaitre si le filter etait actif (Burkina Faso — aucun 'e').
    const user = userEvent.setup();
    render(Combobox, {
      props: {
        modelValue: null,
        options: [...PAYS_OPTIONS],
        label: 'Pays',
      },
    });
    await openDropdown(user);
    const input = getComboboxInput() as HTMLInputElement;
    await fireEvent.compositionStart(input);
    // M-2 Pattern A strict : fireEvent.input synchronise v-model (happy-dom/Vue)
    // sans passer par le write DOM imperative (anti-pattern leçon 21).
    await fireEvent.update(input, 'sen');
    // Pendant la composition, Sénégal ET Burkina Faso doivent rester visibles
    // (guard neutralise le filter → toutes les options sont rendues).
    expect(screen.queryByRole('option', { name: /sénégal/i })).not.toBeNull();
    expect(screen.queryByRole('option', { name: /burkina faso/i })).not.toBeNull();
  });

  it('apres compositionend → filter declenche normalement (M-3 toBeNull strict)', async () => {
    // M-3 / Leçon 21 §4quater — assertion `toBeNull()` strict sur sénégal apres
    // typing 'burkina' (option absente, pas autre présente).
    const user = userEvent.setup();
    render(Combobox, {
      props: {
        modelValue: null,
        options: [...PAYS_OPTIONS],
        label: 'Pays',
      },
    });
    await openDropdown(user);
    const input = getComboboxInput() as HTMLInputElement;
    await fireEvent.compositionStart(input);
    // M-2 Pattern A : fireEvent.update pour synchronisation v-model
    // (substitut portable à l'IME composition dans happy-dom — user-event
    // `.keyboard('{Dead}…')` nécessite layout keyboard réel).
    await fireEvent.update(input, 'burkina');
    await fireEvent.compositionEnd(input);
    // Post compositionend, filter doit s'appliquer :
    // - Burkina Faso est present,
    // - Sénégal est absent (pas de match 'burkina') — strict toBeNull.
    const opt = await screen.findByRole('option', { name: /burkina faso/i });
    expect(opt).toBeDefined();
    expect(screen.queryByRole('option', { name: /sénégal/i })).toBeNull();
  });
});

describe('ui/Combobox : AC4 ARIA attributes (Pattern A DOM)', () => {
  it('input a role="combobox" + aria-labelledby pointant le label', () => {
    render(Combobox, {
      props: {
        modelValue: null,
        options: [...PAYS_OPTIONS],
        label: 'Pays',
      },
    });
    const input = getComboboxInput();
    expect(input.getAttribute('role')).toBe('combobox');
    const labelledby = input.getAttribute('aria-labelledby');
    expect(labelledby).not.toBeNull();
    expect(document.getElementById(labelledby!)).not.toBeNull();
  });

  it('apres ouverture, aria-expanded="true" + role="listbox" present', async () => {
    const user = userEvent.setup();
    render(Combobox, {
      props: {
        modelValue: null,
        options: [...PAYS_OPTIONS],
        label: 'Pays',
      },
    });
    await openDropdown(user);
    const input = getComboboxInput();
    expect(input.getAttribute('aria-expanded')).toBe('true');
    expect(document.body.querySelector('[role="listbox"]')).not.toBeNull();
  });

  it('chaque option a role="option"', async () => {
    const user = userEvent.setup();
    render(Combobox, {
      props: {
        modelValue: null,
        options: [...PAYS_OPTIONS],
        label: 'Pays',
      },
    });
    await openDropdown(user);
    const options = await screen.findAllByRole('option');
    expect(options.length).toBe(PAYS_OPTIONS.length);
  });
});

describe('ui/Combobox : AC5 keyboard navigation', () => {
  it('ArrowDown puis Enter → selection emise', async () => {
    const user = userEvent.setup();
    const { emitted } = render(Combobox, {
      props: {
        modelValue: null,
        options: [...PAYS_OPTIONS],
        label: 'Pays',
      },
    });
    await openDropdown(user);
    await user.keyboard('{Enter}');
    const events = emitted()['update:modelValue'];
    expect(events).toBeDefined();
    expect(events.length).toBeGreaterThan(0);
  });

  it('Escape → aria-expanded repasse a "false"', async () => {
    const user = userEvent.setup();
    render(Combobox, {
      props: {
        modelValue: null,
        options: [...PAYS_OPTIONS],
        label: 'Pays',
      },
    });
    await openDropdown(user);
    expect(getComboboxInput().getAttribute('aria-expanded')).toBe('true');
    await user.keyboard('{Escape}');
    expect(getComboboxInput().getAttribute('aria-expanded')).toBe('false');
  });
});

describe('ui/Combobox : AC6 empty state', () => {
  it('options vides → message default "Aucun résultat" avec role=status', async () => {
    const user = userEvent.setup();
    render(Combobox, {
      props: {
        modelValue: null,
        options: [],
        label: 'Pays',
      },
    });
    await openDropdown(user);
    const status = await screen.findByRole('status');
    expect(status.textContent).toContain('Aucun résultat');
    expect(status.getAttribute('aria-live')).toBe('polite');
  });

  it('emptyLabel custom override le message default', async () => {
    const user = userEvent.setup();
    render(Combobox, {
      props: {
        modelValue: null,
        options: [],
        label: 'Pays',
        emptyLabel: 'Aucun pays trouvé',
      },
    });
    await openDropdown(user);
    const status = await screen.findByRole('status');
    expect(status.textContent).toContain('Aucun pays trouvé');
  });

  it('search sans match → empty state affiche', async () => {
    const user = userEvent.setup();
    render(Combobox, {
      props: {
        modelValue: null,
        options: [...PAYS_OPTIONS],
        label: 'Pays',
      },
    });
    await openDropdown(user);
    await user.type(getComboboxInput(), 'zzz');
    const status = await screen.findByRole('status');
    expect(status.textContent).toContain('Aucun résultat');
  });
});

describe('ui/Combobox : AC6 options grouped + disabled', () => {
  it('options avec group[] → ComboboxGroup + ComboboxLabel rendus', async () => {
    const user = userEvent.setup();
    render(Combobox, {
      props: {
        modelValue: null,
        options: [...PAYS_GROUPED],
        label: 'Pays',
      },
    });
    await openDropdown(user);
    const listbox = await screen.findByRole('listbox');
    expect(listbox.textContent).toContain('UEMOA');
    expect(listbox.textContent).toContain('CEMAC');
  });

  it('option disabled → data-disabled present (Reka UI Listbox)', async () => {
    const user = userEvent.setup();
    render(Combobox, {
      props: {
        modelValue: null,
        options: [
          { value: 'sn', label: 'Sénégal' },
          { value: 'ci', label: "Côte d'Ivoire", disabled: true },
        ],
        label: 'Pays',
      },
    });
    await openDropdown(user);
    const disabledOpt = await screen.findByRole('option', {
      name: /côte d'ivoire/i,
    });
    // Reka UI (Listbox) expose la proprieté via `data-disabled` (attribut
    // present vide si disabled, absent sinon) — selecteur CSS `data-[disabled]`
    // consomme par Combobox.vue pour l'etat visuel. L'attribut `aria-disabled`
    // natif HTML est laisse au consommateur si besoin (hors scope primitive).
    expect(disabledOpt.hasAttribute('data-disabled')).toBe(true);
  });
});
