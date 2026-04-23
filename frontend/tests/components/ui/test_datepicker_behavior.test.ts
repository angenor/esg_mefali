/**
 * Tests comportement ui/DatePicker (AC1-AC9 Story 10.20).
 *
 * Pattern A strict (§4ter.bis 10.18 + §4quinquies 10.19 capitalises) :
 *  - `screen.getByRole` + `user.click/keyboard` (`@testing-library/user-event`),
 *  - AUCUN `wrapper.vm.*`, AUCUN `input.setValue(...)`,
 *  - PopoverPortal → `document.body.querySelector` pour dialog portalise.
 *
 * Pattern L21 §4quater : assertions observables strictes (pas `.toBeDefined()`
 * smoke, pas `.not.toBeNull()` permissif quand structure verifiable).
 *
 * Pattern L22 §4quinquies : displayValue trigger FR (AC6) assertion stricte.
 * Pattern L23 §4quinquies : lifecycle close reset mois (AC7) queryByText null.
 * Pattern L24 §4quinquies : ARIA attribute-strict (AC4) getAttribute strict.
 *
 * Note requetage cells : Reka UI rend un live region sr-only qui duplique le
 * texte « avril 2026 » → on cible `.font-semibold` (CalendarHeading notre
 * template) pour distinguer. Pour les cells, on interroge `data-value` qui
 * est unique par date (ex. `[data-value="2026-04-15"]`).
 */
import { describe, it, expect, afterEach, vi } from 'vitest';
import { render, screen, cleanup, waitFor } from '@testing-library/vue';
import userEvent from '@testing-library/user-event';
import { CalendarDate } from '@internationalized/date';
import DatePicker from '../../../app/components/ui/DatePicker.vue';

afterEach(() => {
  cleanup();
  // Reka UI Portal peut laisser des noeuds orphelins apres unmount happy-dom
  document.body.querySelectorAll('[role="dialog"]').forEach((el) => el.remove());
});

function getTrigger(): HTMLElement {
  const buttons = screen.getAllByRole('button');
  const trigger = buttons.find(
    (b) => b.getAttribute('aria-haspopup') === 'dialog',
  );
  if (!trigger) {
    throw new Error('PopoverTrigger aria-haspopup="dialog" introuvable');
  }
  return trigger;
}

async function openPopover(user: ReturnType<typeof userEvent.setup>) {
  const trigger = getTrigger();
  await user.click(trigger);
  await waitFor(() => {
    const dialog = document.body.querySelector('[role="dialog"]');
    expect(dialog).not.toBeNull();
  });
}

/** Cell date via data-value unique (evite collision regex). */
function getCellByDate(isoDate: string): HTMLElement {
  const cell = document.body.querySelector<HTMLElement>(
    `[role="button"][data-value="${isoDate}"]`,
  );
  if (!cell) {
    throw new Error(`Cell [data-value="${isoDate}"] introuvable`);
  }
  return cell;
}

/** CalendarHeading = notre div .font-semibold (hors live region sr-only Reka). */
function getHeading(): HTMLElement {
  const heading = document.body.querySelector<HTMLElement>(
    '[role="dialog"] .font-semibold',
  );
  if (!heading) {
    throw new Error('CalendarHeading .font-semibold introuvable');
  }
  return heading;
}

// ============================================================================
// AC2 — mode single vs range + emissions update:modelValue
// ============================================================================
describe('ui/DatePicker : AC2 mode single + range (Pattern A strict)', () => {
  it('mode=single : click cell emet update:modelValue avec CalendarDate + ferme popover', async () => {
    const user = userEvent.setup();
    const { emitted } = render(DatePicker, {
      props: {
        modelValue: new CalendarDate(2026, 4, 15),
        label: 'Date deadline',
      },
    });
    await openPopover(user);
    await user.click(getCellByDate('2026-04-20'));
    await waitFor(() => {
      const events = emitted()['update:modelValue'] as unknown[][];
      expect(events).toBeDefined();
      expect(events.length).toBeGreaterThan(0);
    });
    const events = emitted()['update:modelValue'] as unknown[][];
    const last = events[events.length - 1]![0] as CalendarDate;
    expect(last.year).toBe(2026);
    expect(last.month).toBe(4);
    expect(last.day).toBe(20);
  });

  it('mode=range : 2 clicks successifs emettent {start, end}', async () => {
    const user = userEvent.setup();
    const { emitted, rerender } = render(DatePicker, {
      props: {
        mode: 'range',
        modelValue: { start: null, end: null },
        defaultValue: new CalendarDate(2026, 4, 1),
        label: 'Periode',
      },
    });
    await openPopover(user);
    await user.click(getCellByDate('2026-04-05'));
    const events1 = emitted()['update:modelValue'] as unknown[][];
    expect(events1.length).toBeGreaterThan(0);
    const firstEmit = events1[events1.length - 1]![0] as {
      start: CalendarDate | null;
      end: CalendarDate | null;
    };
    expect(firstEmit.start).not.toBeNull();
    await rerender({
      mode: 'range',
      modelValue: firstEmit,
      defaultValue: new CalendarDate(2026, 4, 1),
      label: 'Periode',
    });
    await user.click(getCellByDate('2026-04-10'));
    await waitFor(() => {
      const events = emitted()['update:modelValue'] as unknown[][];
      const latest = events[events.length - 1]![0] as {
        start: CalendarDate | null;
        end: CalendarDate | null;
      };
      expect(latest.start).not.toBeNull();
      expect(latest.end).not.toBeNull();
    });
  });
});

// ============================================================================
// AC3 — Locale FR par default + override EN-US
// ============================================================================
describe('ui/DatePicker : AC3 locale FR default + override', () => {
  it('locale=fr-FR default : CalendarHeading affiche "avril 2026"', async () => {
    const user = userEvent.setup();
    render(DatePicker, {
      props: {
        modelValue: new CalendarDate(2026, 4, 15),
        label: 'Date',
      },
    });
    await openPopover(user);
    await waitFor(() => {
      expect(getHeading().textContent?.toLowerCase()).toContain('avril 2026');
    });
  });

  it('locale=en-US override : CalendarHeading affiche "April 2026"', async () => {
    const user = userEvent.setup();
    render(DatePicker, {
      props: {
        modelValue: new CalendarDate(2026, 4, 15),
        label: 'Date',
        locale: 'en-US',
      },
    });
    await openPopover(user);
    await waitFor(() => {
      expect(getHeading().textContent).toContain('April 2026');
    });
  });

  it('customFormat long : trigger affiche segments "15 avril 2026"', () => {
    render(DatePicker, {
      props: {
        modelValue: new CalendarDate(2026, 4, 15),
        label: 'Date',
        customFormat: {
          weekday: 'long',
          day: 'numeric',
          month: 'long',
          year: 'numeric',
        },
      },
    });
    const trigger = getTrigger();
    expect(trigger.textContent).toMatch(/15/);
    expect(trigger.textContent).toMatch(/avril/i);
    expect(trigger.textContent).toMatch(/2026/);
  });
});

// ============================================================================
// AC4 — ARIA attribute-strict (L24 §4quinquies)
// ============================================================================
describe('ui/DatePicker : AC4 ARIA strict (L24 attribute-strict)', () => {
  it('trigger porte aria-haspopup="dialog" (valeur stricte, pas proxy)', () => {
    render(DatePicker, {
      props: {
        modelValue: null,
        label: 'Date',
      },
    });
    const trigger = getTrigger();
    // L24 strict : attribute value strict (pas absence d'arg ou proxy).
    expect(trigger.getAttribute('aria-haspopup')).toBe('dialog');
  });

  it('trigger aria-expanded passe de "false" a "true" apres click', async () => {
    const user = userEvent.setup();
    render(DatePicker, {
      props: {
        modelValue: null,
        label: 'Date',
      },
    });
    const trigger = getTrigger();
    expect(trigger.getAttribute('aria-expanded')).toBe('false');
    await openPopover(user);
    expect(trigger.getAttribute('aria-expanded')).toBe('true');
  });

  it('CalendarRoot porte role="application" + aria-label Calendrier FR', async () => {
    const user = userEvent.setup();
    render(DatePicker, {
      props: {
        modelValue: new CalendarDate(2026, 4, 15),
        label: 'Date',
      },
    });
    await openPopover(user);
    await waitFor(() => {
      const apps = document.body.querySelectorAll('[role="application"]');
      expect(apps.length).toBeGreaterThanOrEqual(1);
      const calendarRoot = Array.from(apps).find((el) =>
        (el.getAttribute('aria-label') ?? '').includes('Calendrier'),
      );
      expect(calendarRoot).toBeDefined();
      expect(calendarRoot!.getAttribute('aria-label')).toMatch(
        /Calendrier, avril 2026/i,
      );
    });
  });
});

// ============================================================================
// AC5 — Keyboard WAI-ARIA Date Picker Dialog
// ============================================================================
describe('ui/DatePicker : AC5 keyboard WAI-ARIA (Pattern A user-event)', () => {
  it('Escape ferme le popover', async () => {
    const user = userEvent.setup();
    render(DatePicker, {
      props: {
        modelValue: new CalendarDate(2026, 4, 15),
        label: 'Date',
      },
    });
    await openPopover(user);
    await user.keyboard('{Escape}');
    await waitFor(() => {
      expect(document.body.querySelector('[role="dialog"]')).toBeNull();
    });
  });

  // H-3 post-review 10.20 + Leçon 26 §4sexies : délégation per-path explicite,
  // pas de faux positif dispatchEvent + assertion permissive /(avril|mai)/.
  // Le test original passait même si PageDown ne faisait rien (heading restait
  // avril 2026 = match du regex). La navigation clavier PageDown est couverte
  // runtime par Storybook `DatePickerKeyboardNavigation--page-down` (happy-dom
  // limite le focus bubbling keyboard vers le handler interne Reka UI).
  // Fallback observable strict : voir test `CalendarNext click` ci-dessous
  // (mois suivant observé via UI équivalente).
  it.skip('keyboard PageDown — DELEGATED Storybook DatePickerKeyboardNavigation--page-down (happy-dom focus bubbling limit)', () => {
    // Intentionnellement vide : couverture runtime Storybook per-path.
  });

  it('CalendarNext click navigue au mois suivant', async () => {
    const user = userEvent.setup();
    render(DatePicker, {
      props: {
        modelValue: new CalendarDate(2026, 4, 15),
        label: 'Date',
      },
    });
    await openPopover(user);
    const nextBtn = screen.getByRole('button', { name: /Mois suivant/i });
    await user.click(nextBtn);
    await waitFor(() =>
      expect(getHeading().textContent?.toLowerCase()).toContain('mai 2026'),
    );
  });

  it('CalendarPrev click navigue au mois precedent', async () => {
    const user = userEvent.setup();
    render(DatePicker, {
      props: {
        modelValue: new CalendarDate(2026, 4, 15),
        label: 'Date',
      },
    });
    await openPopover(user);
    const prevBtn = screen.getByRole('button', { name: /Mois précédent/i });
    await user.click(prevBtn);
    await waitFor(() =>
      expect(getHeading().textContent?.toLowerCase()).toContain('mars 2026'),
    );
  });

  it('Click cell (equivalent Enter) emet update:modelValue + ferme popover', async () => {
    const user = userEvent.setup();
    const { emitted } = render(DatePicker, {
      props: {
        modelValue: new CalendarDate(2026, 4, 15),
        label: 'Date',
      },
    });
    await openPopover(user);
    await user.click(getCellByDate('2026-04-22'));
    await waitFor(() => {
      const events = emitted()['update:modelValue'] as unknown[][];
      expect(events).toBeDefined();
      const last = events[events.length - 1]![0] as CalendarDate;
      expect(last.day).toBe(22);
    });
  });
});

// ============================================================================
// AC5 keyboard — M-1 post-review 10.20 + Leçon 26 §4sexies
// Délégation per-path Storybook (9/12 chemins). Chaque `it.todo` nomme sa
// story runtime. Happy-dom ne route pas le focus bubbling keyboard au handler
// Reka UI Calendar interne → validation runtime obligatoire.
// ============================================================================
describe.skip('ui/DatePicker : AC5 keyboard — DELEGATED Storybook per-path (Leçon 26 §4sexies)', () => {
  it.todo('ArrowLeft/ArrowRight (jour ±1) — Storybook DatePickerKeyboardNavigation--arrow-left-right');
  it.todo('ArrowUp/ArrowDown (semaine ±1) — Storybook DatePickerKeyboardNavigation--arrow-up-down');
  it.todo('PageUp (mois -1) — Storybook DatePickerKeyboardNavigation--page-up');
  it.todo('Shift+PageDown (année +1) — Storybook DatePickerKeyboardNavigation--shift-page-down');
  it.todo('Shift+PageUp (année -1) — Storybook DatePickerKeyboardNavigation--shift-page-up');
  it.todo('Home (début semaine lundi) — Storybook DatePickerKeyboardNavigation--home');
  it.todo('End (fin semaine dimanche) — Storybook DatePickerKeyboardNavigation--end');
  it.todo('Enter (sélection date focusée) — Storybook DatePickerKeyboardNavigation--enter-select');
  it.todo('Focus retour trigger après Escape — Storybook DatePickerKeyboardNavigation--escape-focus-return');
});

// ============================================================================
// H-2 post-review 10.20 — Réactivité modelValue externe (watch modelValue)
// ============================================================================
describe('ui/DatePicker : H-2 réactivité modelValue externe (watch)', () => {
  it('parent mute modelValue null → popover rouvre et heading affiche today (reset via initialMonth)', async () => {
    const user = userEvent.setup();
    const initial = new CalendarDate(2026, 4, 15);
    const { rerender } = render(DatePicker, {
      props: { modelValue: initial, label: 'Date' },
    });
    // 1. Ouvre : avril 2026
    await openPopover(user);
    await waitFor(() =>
      expect(getHeading().textContent?.toLowerCase()).toContain('avril 2026'),
    );
    // 2. Ferme
    await user.keyboard('{Escape}');
    await waitFor(() =>
      expect(document.body.querySelector('[role="dialog"]')).toBeNull(),
    );
    // 3. Parent reset modelValue → null pendant popover fermé
    await rerender({ modelValue: null, label: 'Date' });
    // 4. Reopen : heading affiche mois today() (pas avril 2026 ancien)
    await openPopover(user);
    const now = new Date();
    const frMonth = new Intl.DateTimeFormat('fr-FR', { month: 'long' })
      .format(now)
      .toLowerCase();
    await waitFor(() =>
      expect(getHeading().textContent?.toLowerCase()).toContain(frMonth),
    );
  });

  it('parent mute modelValue vers nouvelle date → heading reflète le nouveau mois', async () => {
    const user = userEvent.setup();
    const { rerender } = render(DatePicker, {
      props: { modelValue: new CalendarDate(2026, 4, 15), label: 'Date' },
    });
    await openPopover(user);
    await waitFor(() =>
      expect(getHeading().textContent?.toLowerCase()).toContain('avril 2026'),
    );
    await user.keyboard('{Escape}');
    await waitFor(() =>
      expect(document.body.querySelector('[role="dialog"]')).toBeNull(),
    );
    // Parent change modelValue → septembre 2026
    await rerender({
      modelValue: new CalendarDate(2026, 9, 10),
      label: 'Date',
    });
    await openPopover(user);
    await waitFor(() =>
      expect(getHeading().textContent?.toLowerCase()).toContain(
        'septembre 2026',
      ),
    );
    expect(getHeading().textContent?.toLowerCase()).not.toContain(
      'avril 2026',
    );
  });
});

// ============================================================================
// M-3 post-review 10.20 — displayValue range edge states (empty + partial end-only)
// ============================================================================
describe('ui/DatePicker : M-3 displayValue range edge states', () => {
  it('range {start:null, end:null} : trigger affiche placeholder (pas " — ")', () => {
    render(DatePicker, {
      props: {
        mode: 'range',
        modelValue: { start: null, end: null },
        label: 'Periode',
      },
    });
    const trigger = screen
      .getAllByRole('button')
      .find((b) => b.getAttribute('aria-haspopup') === 'dialog')!;
    // Pas d'em-dash quand les 2 bornes sont vides : fallback placeholder
    expect(trigger.textContent).not.toMatch(/—/);
    expect(trigger.textContent).toMatch(/Sélectionner une date/);
  });

  it('range {start:null, end:DateValue} : trigger affiche "Fin ? — 30/04/2026" sémantique préservé', () => {
    render(DatePicker, {
      props: {
        mode: 'range',
        modelValue: { start: null, end: new CalendarDate(2026, 4, 30) },
        label: 'Periode',
      },
    });
    const trigger = screen
      .getAllByRole('button')
      .find((b) => b.getAttribute('aria-haspopup') === 'dialog')!;
    // Gate review M-3 : startStr = rangePartialLabel, endStr = date formatée
    expect(trigger.textContent).toMatch(/Fin \?\s*—\s*30\/04\/2026/);
  });
});

// ============================================================================
// M-2 post-review 10.20 — Range auto-swap (piège #45 validation defensive dev)
// Reka UI RangeCalendarRoot normalise transparent si l'utilisateur clique
// end avant start. Défense supplémentaire : dev-only warn si parent passe
// une plage inversée via v-model (ex. Zod loose schema).
// ============================================================================
describe('ui/DatePicker : M-2 range inversé → dev-only warn (piège #45)', () => {
  it('modelValue {start: 30/04, end: 01/04} → console.warn en DEV (pas throw, pas crash)', () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    try {
      render(DatePicker, {
        props: {
          mode: 'range',
          modelValue: {
            start: new CalendarDate(2026, 4, 30),
            end: new CalendarDate(2026, 4, 1),
          },
          label: 'Periode',
        },
      });
      // DEV warn attendu (import.meta.env.DEV default true en test)
      const calls = warnSpy.mock.calls.flat().join(' ');
      expect(calls).toMatch(/DatePicker.*range.*end.*start/i);
    } finally {
      warnSpy.mockRestore();
    }
  });
});

// ============================================================================
// M-4 post-review 10.20 — Range mode initialMonth avec defaultValue seul
// Couverture branche initialMonth() range : modelValue.start null + defaultValue fourni
// ============================================================================
describe('ui/DatePicker : M-4 range initialMonth fallback defaultValue (branch coverage)', () => {
  it('mode=range + modelValue.start=null + defaultValue=juin 2026 : heading juin 2026', async () => {
    const user = userEvent.setup();
    render(DatePicker, {
      props: {
        mode: 'range',
        modelValue: { start: null, end: null },
        defaultValue: new CalendarDate(2026, 6, 1),
        label: 'Periode',
      },
    });
    await openPopover(user);
    await waitFor(() =>
      expect(getHeading().textContent?.toLowerCase()).toContain('juin 2026'),
    );
  });
});

// ============================================================================
// AC6 — displayValue trigger (L22 §4quinquies)
// ============================================================================
describe('ui/DatePicker : AC6 displayValue trigger (L22 label format FR)', () => {
  it('single : trigger affiche "15/04/2026" format FR (pas clé ISO)', () => {
    render(DatePicker, {
      props: {
        modelValue: new CalendarDate(2026, 4, 15),
        label: 'Date',
      },
    });
    const trigger = getTrigger();
    expect(trigger.textContent).toMatch(/15\/04\/2026/);
    expect(trigger.textContent).not.toMatch(/2026-04-15T/);
    expect(trigger.textContent).not.toMatch(/\[object Object\]/);
  });

  it('single null : trigger affiche placeholder "Sélectionner une date"', () => {
    render(DatePicker, {
      props: {
        modelValue: null,
        label: 'Date',
      },
    });
    const trigger = getTrigger();
    expect(trigger.textContent).toMatch(/Sélectionner une date/);
  });

  it('range complet : trigger affiche em-dash strict entre les 2 dates', () => {
    render(DatePicker, {
      props: {
        mode: 'range',
        modelValue: {
          start: new CalendarDate(2026, 4, 1),
          end: new CalendarDate(2026, 4, 30),
        },
        label: 'Periode',
      },
    });
    const trigger = getTrigger();
    // em-dash strict (U+2014), pas hyphen-minus (U+002D)
    expect(trigger.textContent).toMatch(
      /01\/04\/2026\s*—\s*30\/04\/2026/,
    );
  });

  it('range partial : trigger affiche "01/04/2026 — Fin ?"', () => {
    render(DatePicker, {
      props: {
        mode: 'range',
        modelValue: {
          start: new CalendarDate(2026, 4, 1),
          end: null,
        },
        label: 'Periode',
      },
    });
    const trigger = getTrigger();
    expect(trigger.textContent).toMatch(/01\/04\/2026\s*—\s*Fin \?/);
  });
});

// ============================================================================
// AC7 — Lifecycle close sans selection reset mois courant (L23 §4quinquies)
// ============================================================================
describe('ui/DatePicker : AC7 lifecycle close reset (L23 §4quinquies)', () => {
  it('nav CalendarNext × 3 puis Escape + reouvre : heading revient au mois de modelValue', async () => {
    const user = userEvent.setup();
    render(DatePicker, {
      props: {
        modelValue: new CalendarDate(2026, 4, 15),
        label: 'Date',
      },
    });
    // 1. Ouvre : mois = avril
    await openPopover(user);
    await waitFor(() =>
      expect(getHeading().textContent?.toLowerCase()).toContain('avril 2026'),
    );
    // 2. Nav 3× CalendarNext → juillet 2026 (avril → mai → juin → juillet)
    const nextBtn = screen.getByRole('button', { name: /Mois suivant/i });
    await user.click(nextBtn);
    await user.click(nextBtn);
    await user.click(nextBtn);
    await waitFor(() =>
      expect(getHeading().textContent?.toLowerCase()).toContain('juillet 2026'),
    );
    // 3. Ferme sans selectionner (Escape)
    await user.keyboard('{Escape}');
    await waitFor(() =>
      expect(document.body.querySelector('[role="dialog"]')).toBeNull(),
    );
    // 4. Reouvre : heading doit revenir a avril (L23 reset sans selection)
    await openPopover(user);
    await waitFor(() =>
      expect(getHeading().textContent?.toLowerCase()).toContain('avril 2026'),
    );
    // L21 strict : le mois abandonne "juillet" ne doit plus apparaitre
    expect(getHeading().textContent?.toLowerCase()).not.toContain(
      'juillet 2026',
    );
  });

  it('modelValue null + defaultValue fourni : reset au mois de defaultValue', async () => {
    const user = userEvent.setup();
    render(DatePicker, {
      props: {
        modelValue: null,
        defaultValue: new CalendarDate(2026, 6, 1),
        label: 'Date',
      },
    });
    await openPopover(user);
    await waitFor(() =>
      expect(getHeading().textContent?.toLowerCase()).toContain('juin 2026'),
    );
  });
});

// ============================================================================
// AC8 — Bornes min/max + isDateDisabled + readonly + disabled
// ============================================================================
describe('ui/DatePicker : AC8 bornes + etats (disabled/readonly)', () => {
  it("disabled: true empeche l'ouverture du popover", async () => {
    const user = userEvent.setup();
    render(DatePicker, {
      props: {
        modelValue: null,
        label: 'Date',
        disabled: true,
      },
    });
    const trigger = getTrigger();
    expect(trigger.hasAttribute('disabled')).toBe(true);
    await user.click(trigger);
    // Aucun dialog ne doit apparaitre (attendons 50ms pour s'en assurer)
    await new Promise((r) => setTimeout(r, 50));
    expect(document.body.querySelector('[role="dialog"]')).toBeNull();
  });

  it('minValue : jour anterieur a min est aria-disabled (parent gridcell)', async () => {
    const user = userEvent.setup();
    render(DatePicker, {
      props: {
        modelValue: new CalendarDate(2026, 4, 15),
        minValue: new CalendarDate(2026, 4, 10),
        label: 'Date',
      },
    });
    await openPopover(user);
    // Cell 5 avril - doit etre disabled (anterieur a min 10 avril)
    const cell5 = getCellByDate('2026-04-05');
    const parent = cell5.closest('[role="gridcell"]');
    expect(parent?.getAttribute('aria-disabled')).toBe('true');
  });

  it('isDateDisabled custom : samedi grisé (4 avril 2026 = samedi)', async () => {
    const user = userEvent.setup();
    render(DatePicker, {
      props: {
        modelValue: new CalendarDate(2026, 4, 15),
        label: 'Date ouvrable',
        isDateDisabled: (date) => {
          const d = date.toDate('UTC');
          return d.getUTCDay() === 0 || d.getUTCDay() === 6;
        },
      },
    });
    await openPopover(user);
    const cell4 = getCellByDate('2026-04-04');
    const parent = cell4.closest('[role="gridcell"]');
    expect(parent?.getAttribute('aria-disabled')).toBe('true');
  });

  it('isDateDisabled : lundi (6 avril 2026) reste enabled', async () => {
    const user = userEvent.setup();
    render(DatePicker, {
      props: {
        modelValue: new CalendarDate(2026, 4, 15),
        label: 'Date ouvrable',
        isDateDisabled: (date) => {
          const d = date.toDate('UTC');
          return d.getUTCDay() === 0 || d.getUTCDay() === 6;
        },
      },
    });
    await openPopover(user);
    const cell6 = getCellByDate('2026-04-06');
    const parent = cell6.closest('[role="gridcell"]');
    expect(parent?.getAttribute('aria-disabled')).toBe('false');
  });
});

// ============================================================================
// AC9 — clearLabel + showClear (pattern L-4 10.19 cancelLabel)
// ============================================================================
describe('ui/DatePicker : AC9 clearLabel + showClear', () => {
  it('showClear: true + value : bouton "Effacer" + clic emet null + event clear', async () => {
    const user = userEvent.setup();
    const { emitted } = render(DatePicker, {
      props: {
        modelValue: new CalendarDate(2026, 4, 15),
        label: 'Date',
        showClear: true,
      },
    });
    await openPopover(user);
    const clearBtn = await waitFor(() =>
      screen.getByRole('button', { name: /^Effacer$/ }),
    );
    await user.click(clearBtn);
    const events = emitted()['update:modelValue'] as unknown[][];
    expect(events).toBeDefined();
    const last = events[events.length - 1]![0];
    expect(last).toBeNull();
    expect(emitted().clear).toBeDefined();
  });

  it('showClear: false (default) : bouton clear absent', async () => {
    const user = userEvent.setup();
    render(DatePicker, {
      props: {
        modelValue: new CalendarDate(2026, 4, 15),
        label: 'Date',
      },
    });
    await openPopover(user);
    expect(screen.queryByRole('button', { name: /^Effacer$/ })).toBeNull();
  });

  it('clearLabel custom "Réinitialiser" override le default', async () => {
    const user = userEvent.setup();
    render(DatePicker, {
      props: {
        modelValue: new CalendarDate(2026, 4, 15),
        label: 'Date',
        showClear: true,
        clearLabel: 'Réinitialiser',
      },
    });
    await openPopover(user);
    const btn = await waitFor(() =>
      screen.getByRole('button', { name: /^Réinitialiser$/ }),
    );
    expect(btn.textContent?.trim()).toBe('Réinitialiser');
    expect(screen.queryByRole('button', { name: /^Effacer$/ })).toBeNull();
  });

  it('range showClear : clic emet {start:null, end:null}', async () => {
    const user = userEvent.setup();
    const { emitted } = render(DatePicker, {
      props: {
        mode: 'range',
        modelValue: {
          start: new CalendarDate(2026, 4, 1),
          end: new CalendarDate(2026, 4, 30),
        },
        label: 'Periode',
        showClear: true,
      },
    });
    await openPopover(user);
    const clearBtn = await waitFor(() =>
      screen.getByRole('button', { name: /^Effacer$/ }),
    );
    await user.click(clearBtn);
    const events = emitted()['update:modelValue'] as unknown[][];
    const last = events[events.length - 1]![0] as {
      start: CalendarDate | null;
      end: CalendarDate | null;
    };
    expect(last.start).toBeNull();
    expect(last.end).toBeNull();
  });
});

// ============================================================================
// L-5 post-review 10.20 — Attributs ARIA complémentaires et focus retour trigger
// ============================================================================
describe('ui/DatePicker : L-5 ARIA aria-modal + focus retour Escape', () => {
  it('PopoverContent porte aria-modal="false" (popover non-bloquant)', async () => {
    const user = userEvent.setup();
    render(DatePicker, {
      props: { modelValue: null, label: 'Date' },
    });
    await openPopover(user);
    const dialog = document.body.querySelector<HTMLElement>('[role="dialog"]');
    expect(dialog).not.toBeNull();
    expect(dialog!.getAttribute('aria-modal')).toBe('false');
  });

  it('Escape ferme le popover et le focus revient sur le trigger', async () => {
    const user = userEvent.setup();
    render(DatePicker, {
      props: { modelValue: null, label: 'Date' },
    });
    const trigger = getTrigger();
    await user.click(trigger);
    await waitFor(() =>
      expect(document.body.querySelector('[role="dialog"]')).not.toBeNull(),
    );
    await user.keyboard('{Escape}');
    await waitFor(() =>
      expect(document.body.querySelector('[role="dialog"]')).toBeNull(),
    );
    // WAI-ARIA Dialog : focus retour sur l'élément qui a ouvert le popover
    expect(document.activeElement).toBe(trigger);
  });
});

// ============================================================================
// M-2 review findings — maxValue bound disabled sur CalendarNext + readonly
// (Auditor A2 — AC8 couverture manquante complétée en batch Fix-All)
// ============================================================================
describe('ui/DatePicker : AC8 maxValue + readonly (couverture additionnelle)', () => {
  it('maxValue : jour postérieur à max est aria-disabled (parent gridcell)', async () => {
    const user = userEvent.setup();
    render(DatePicker, {
      props: {
        modelValue: new CalendarDate(2026, 4, 15),
        maxValue: new CalendarDate(2026, 4, 20),
        label: 'Date',
      },
    });
    await openPopover(user);
    const cell25 = getCellByDate('2026-04-25');
    const parent = cell25.closest('[role="gridcell"]');
    expect(parent?.getAttribute('aria-disabled')).toBe('true');
  });

  it('readonly: true — popover ouvre mais click cell no-op (aucune émission modelValue)', async () => {
    const user = userEvent.setup();
    const { emitted } = render(DatePicker, {
      props: {
        modelValue: new CalendarDate(2026, 4, 15),
        readonly: true,
        label: 'Date',
      },
    });
    await openPopover(user);
    await user.click(getCellByDate('2026-04-22'));
    // Pas d'émission update:modelValue — readonly bloque la sélection
    const events = emitted()['update:modelValue'] as unknown[][] | undefined;
    expect(events).toBeUndefined();
    // Popover reste ouvert
    expect(document.body.querySelector('[role="dialog"]')).not.toBeNull();
  });
});

// ============================================================================
// L-3 post-review 10.20 — clearLabel locale anglaise (couverture story EN)
// ============================================================================
describe('ui/DatePicker : L-3 clearLabel locale EN', () => {
  it('locale=en-US + clearLabel="Clear" : bouton rendu avec label anglais', async () => {
    const user = userEvent.setup();
    render(DatePicker, {
      props: {
        modelValue: new CalendarDate(2026, 4, 15),
        label: 'Date',
        locale: 'en-US',
        showClear: true,
        clearLabel: 'Clear',
      },
    });
    await openPopover(user);
    const clearBtn = await waitFor(() =>
      screen.getByRole('button', { name: /^Clear$/ }),
    );
    expect(clearBtn.textContent?.trim()).toBe('Clear');
  });
});

// ============================================================================
// Couverture branches additionnelles (M-4 remontée ≥95%)
// ============================================================================
describe('ui/DatePicker : branches edge additionnelles (M-4 coverage)', () => {
  it('displayValue single null + placeholder custom : trigger affiche placeholder custom', () => {
    render(DatePicker, {
      props: {
        modelValue: null,
        label: 'Date',
        placeholder: 'Choisir une date',
      },
    });
    const trigger = screen
      .getAllByRole('button')
      .find((b) => b.getAttribute('aria-haspopup') === 'dialog')!;
    expect(trigger.textContent).toMatch(/Choisir une date/);
  });

  it('hasValue range partial (start seul) : bouton Effacer visible', async () => {
    const user = userEvent.setup();
    render(DatePicker, {
      props: {
        mode: 'range',
        modelValue: { start: new CalendarDate(2026, 4, 1), end: null },
        label: 'Periode',
        showClear: true,
      },
    });
    await openPopover(user);
    // hasValue = true car start existe même si end null → clear visible
    await waitFor(() =>
      expect(
        screen.queryByRole('button', { name: /^Effacer$/ }),
      ).not.toBeNull(),
    );
  });

  it('hasValue range partial (end seul) : bouton Effacer visible (branch r.end fallback)', async () => {
    const user = userEvent.setup();
    render(DatePicker, {
      props: {
        mode: 'range',
        modelValue: { start: null, end: new CalendarDate(2026, 4, 30) },
        label: 'Periode',
        showClear: true,
      },
    });
    await openPopover(user);
    // hasValue = !!(r.start || r.end) : couverture branche r.end seul
    await waitFor(() =>
      expect(
        screen.queryByRole('button', { name: /^Effacer$/ }),
      ).not.toBeNull(),
    );
  });

  it('Required=true : asterisque rouge rendu + aria-hidden', () => {
    render(DatePicker, {
      props: { modelValue: null, label: 'Date', required: true },
    });
    // L'asterisque est dans le label (before trigger)
    const asterisk = document.querySelector('span[aria-hidden="true"]');
    expect(asterisk).not.toBeNull();
    expect(asterisk!.textContent?.trim()).toBe('*');
  });
});
