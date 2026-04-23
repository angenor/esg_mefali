/**
 * Tests a11y ui/DatePicker (AC4 + AC10 Story 10.20).
 *
 * Portail Reka UI PopoverPortal → assertions DOM via document.body
 * (Pattern A — leçon 10.16 H-3 + piege #28 10.18 + §4quinquies 10.19 capitalise).
 *
 * Pattern L24 §4quinquies ARIA attribute-strict :
 *  - `getAttribute('aria-haspopup')` === `'dialog'` valeur stricte (pas proxy),
 *  - `getAttribute('aria-expanded')` === `'false'` | `'true'` (pas sans 2e arg),
 *  - `getAttribute('aria-controls')` matches regex /^[a-z0-9-]+$/ (Reka useId).
 *
 * Note leçon 10.15 HIGH-2 + 10.18 §4ter.bis : les audits portail-dependants
 * (contraste runtime, focus visible, animations) sont DELEGUES a Storybook
 * addon-a11y runtime (happy-dom n'evalue pas le layout CSS).
 *
 * DELEGATED TO Storybook DatePickerDarkMode + DatePickerKeyboardNavigation
 * pour les audits contraste AA + focus visible runtime.
 */
import { describe, it, expect, afterEach } from 'vitest';
import { render, screen, cleanup, waitFor } from '@testing-library/vue';
import userEvent from '@testing-library/user-event';
import { axe, toHaveNoViolations } from 'jest-axe';
import { CalendarDate } from '@internationalized/date';
import DatePicker from '../../../app/components/ui/DatePicker.vue';

expect.extend(toHaveNoViolations);

const AXE_OPTIONS = {
  rules: {
    // happy-dom n'evalue pas le layout CSS → contraste delegue Storybook runtime
    'color-contrast': { enabled: false },
    region: { enabled: false },
    // Artefacts happy-dom sur portails Reka UI (piege #28 10.18)
    'aria-hidden-focus': { enabled: false },
  },
} as const;

afterEach(() => {
  cleanup();
  document.body.querySelectorAll('[role="dialog"]').forEach((el) => el.remove());
});

function getTrigger(): HTMLElement {
  const buttons = screen.getAllByRole('button');
  const trigger = buttons.find(
    (b) => b.getAttribute('aria-haspopup') === 'dialog',
  );
  if (!trigger) {
    throw new Error('PopoverTrigger introuvable');
  }
  return trigger;
}

describe('ui/DatePicker : AC4 ARIA attribute-strict (L24 §4quinquies)', () => {
  it('trigger porte aria-haspopup="dialog" valeur stricte', () => {
    render(DatePicker, {
      props: {
        modelValue: null,
        label: 'Date',
      },
    });
    const trigger = getTrigger();
    // L24 STRICT : getAttribute('aria-haspopup') === 'dialog' pas absence.
    expect(trigger.getAttribute('aria-haspopup')).toBe('dialog');
  });

  it('trigger porte aria-expanded="false" initial puis "true" apres click', async () => {
    const user = userEvent.setup();
    render(DatePicker, {
      props: {
        modelValue: null,
        label: 'Date',
      },
    });
    const trigger = getTrigger();
    // Valeur stricte initiale
    expect(trigger.getAttribute('aria-expanded')).toBe('false');
    await user.click(trigger);
    await waitFor(() => {
      expect(trigger.getAttribute('aria-expanded')).toBe('true');
    });
  });

  it('trigger aria-controls === content.id (cohérence DOM Reka UI délégué)', async () => {
    const user = userEvent.setup();
    render(DatePicker, {
      props: {
        modelValue: null,
        label: 'Date',
      },
    });
    const trigger = getTrigger();
    await user.click(trigger);
    await waitFor(() => {
      expect(document.body.querySelector('[role="dialog"]')).not.toBeNull();
    });
    const ariaControls = trigger.getAttribute('aria-controls');
    // L24 strict + Leçon 25 §4sexies (post-10.20 H-1) : ne pas asserter une
    // regex opaque /reka-popover-content-/ (code mort si wrapper injecte un
    // id custom qui est écrasé par rootContext.contentId). On asserte la
    // cohérence DOM observable : aria-controls === content.id.
    expect(ariaControls).not.toBeNull();
    const dialog = document.body.querySelector<HTMLElement>('[role="dialog"]');
    expect(dialog).not.toBeNull();
    expect(dialog!.id).toBe(ariaControls!);
    expect(dialog!.getAttribute('role')).toBe('dialog');
  });

  it('trigger porte aria-labelledby pointant sur le label externe', () => {
    render(DatePicker, {
      props: {
        modelValue: null,
        label: 'Date deadline dossier',
      },
    });
    const trigger = getTrigger();
    const labelledBy = trigger.getAttribute('aria-labelledby');
    expect(labelledBy).not.toBeNull();
    const label = document.getElementById(labelledBy!);
    expect(label).not.toBeNull();
    expect(label!.textContent).toContain('Date deadline dossier');
  });

  it('CalendarRoot porte role="application" + aria-label FR "Calendrier, ..."', async () => {
    const user = userEvent.setup();
    render(DatePicker, {
      props: {
        modelValue: new CalendarDate(2026, 4, 15),
        label: 'Date',
      },
    });
    await user.click(getTrigger());
    await waitFor(() => {
      expect(document.body.querySelector('[role="dialog"]')).not.toBeNull();
    });
    const apps = document.body.querySelectorAll('[role="application"]');
    const calendarRoot = Array.from(apps).find((el) =>
      (el.getAttribute('aria-label') ?? '').includes('Calendrier'),
    );
    expect(calendarRoot).toBeDefined();
    expect(calendarRoot!.getAttribute('aria-label')).toMatch(
      /^Calendrier, avril 2026$/i,
    );
  });

  it('CalendarCellTrigger porte aria-label format FR complet', async () => {
    const user = userEvent.setup();
    render(DatePicker, {
      props: {
        modelValue: new CalendarDate(2026, 4, 15),
        label: 'Date',
      },
    });
    await user.click(getTrigger());
    await waitFor(() => {
      expect(document.body.querySelector('[role="dialog"]')).not.toBeNull();
    });
    const cell15 = document.body.querySelector<HTMLElement>(
      '[role="button"][data-value="2026-04-15"]',
    );
    expect(cell15).not.toBeNull();
    // Format FR complet : "mercredi 15 avril 2026"
    expect(cell15!.getAttribute('aria-label')).toMatch(
      /^\S+ 15 avril 2026$/i,
    );
  });
});

describe('ui/DatePicker : vitest-axe smoke (DELEGATED contrast/portal runtime)', () => {
  it('rendu ferme : aucune violation axe hors regles deleguees', async () => {
    const { container } = render(DatePicker, {
      props: {
        modelValue: new CalendarDate(2026, 4, 15),
        label: 'Date deadline',
      },
    });
    // DELEGATED TO Storybook DatePickerDarkMode : contraste runtime + focus visuel
    const results = await axe(container, AXE_OPTIONS);
    expect(results).toHaveNoViolations();
  });
});
