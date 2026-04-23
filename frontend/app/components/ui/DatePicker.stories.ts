import type { Meta, StoryObj } from '@storybook/vue3';
import { CalendarDate, getLocalTimeZone, today } from '@internationalized/date';
import DatePicker from './DatePicker.vue';
import { asStorybookComponent } from '../../types/storybook';

/* ===========================================================================
 * DatePicker.stories.ts — Story 10.20 (pattern co-localisation 10.14-10.19).
 * CSF 3.0 + autodocs + a11y runtime (delegation portail lecon 10.15 HIGH-2
 * + piege #28 10.18 + §4quinquies L22-24 10.19 capitalises).
 *
 * Pattern B (comptage runtime OBLIGATOIRE jq storybook-static) — voir Dev
 * Agent Record Completion Notes pour le chiffre exact.
 *
 * DELEGATED TO Storybook runtime :
 *  - DatePickerDarkMode : contraste AA post-darken (brand-green brand-green)
 *  - DatePickerKeyboardNavigation : keyboard WAI-ARIA Date Picker Dialog complet
 *  - DatePickerFocusVisible : focus ring :focus-visible brand-green
 * =========================================================================*/

type DatePickerStoryArgs = {
  modelValue: CalendarDate | null | { start: CalendarDate | null; end: CalendarDate | null };
  label: string;
  mode?: 'single' | 'range';
  locale?: string;
  disabled?: boolean;
  readonly?: boolean;
  showClear?: boolean;
  clearLabel?: string;
  placeholder?: string;
  required?: boolean;
};

const meta: Meta<DatePickerStoryArgs> = {
  title: 'UI/DatePicker',
  component: asStorybookComponent<DatePickerStoryArgs>(DatePicker),
  tags: ['autodocs'],
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component:
          'Wrapper Reka UI `<PopoverRoot>` + `<CalendarRoot>` (ou `<RangeCalendarRoot>`) ' +
          'avec locale FR par defaut (format d/M/yyyy), L22 displayValue trigger, ' +
          'L23 lifecycle close reset mois, L24 ARIA attribute-strict.',
      },
    },
  },
  argTypes: {
    mode: {
      control: 'radio',
      options: ['single', 'range'],
      description: 'Mode single (default) ou range (plage start-end)',
    },
    locale: {
      control: 'radio',
      options: ['fr-FR', 'en-US'],
      description: 'Locale Intl — FR default (CLAUDE.md §Contexte Metier UEMOA/CEDEAO)',
    },
    disabled: { control: 'boolean' },
    readonly: { control: 'boolean' },
    showClear: { control: 'boolean' },
  },
};

export default meta;
type Story = StoryObj<DatePickerStoryArgs>;

/**
 * Cas default : single date selectionnee en avril 2026.
 * Trigger affiche `15/04/2026` format FR (L22 displayValue obligatoire).
 */
export const Single: Story = {
  args: {
    modelValue: new CalendarDate(2026, 4, 15),
    label: 'Date deadline validation dossier',
  },
};

/**
 * Cas range : plage 1-30 avril 2026 (FA echeance bailleur Epic 9).
 * Trigger affiche `01/04/2026 — 30/04/2026` em-dash strict (L22 range).
 */
export const Range: Story = {
  args: {
    mode: 'range',
    modelValue: {
      start: new CalendarDate(2026, 4, 1),
      end: new CalendarDate(2026, 4, 30),
    },
    label: 'Periode echeance bailleur',
  },
};

/**
 * Cas bornes min/max : 3 prochains mois uniquement (entreprise attestation Epic 10).
 * Jours hors range grayed out + CalendarNext desactive apres maxValue.
 */
export const MinMax: Story = {
  args: {
    modelValue: null,
    label: 'Date dans les 3 prochains mois',
    placeholder: 'Choisir une date',
  },
  render: (args) => ({
    components: { DatePicker },
    setup() {
      const tz = getLocalTimeZone();
      const minValue = today(tz);
      const maxValue = today(tz).add({ months: 3 });
      return { args, minValue, maxValue };
    },
    template: `
      <DatePicker
        v-bind="args"
        :min-value="minValue"
        :max-value="maxValue"
      />
    `,
  }),
};

/**
 * Cas disabled : trigger non interactif + aria-disabled="true".
 */
export const Disabled: Story = {
  args: {
    modelValue: new CalendarDate(2026, 4, 15),
    label: 'Date (lecture seule legale)',
    disabled: true,
  },
};

/**
 * Cas readonly : popover ouvrable + cells non-cliquables (nav keyboard OK).
 * Use case « date validee hierarchiquement N2 » Epic 19 peer-review.
 */
export const ReadOnly: Story = {
  args: {
    modelValue: new CalendarDate(2026, 4, 15),
    label: 'Date validee (N2)',
    readonly: true,
  },
};

/**
 * Cas bouton Effacer : showClear true + value -> bouton rouge "Effacer" footer.
 * Pattern cohérent closeLabel 10.18 M-1 + cancelLabel 10.19 L-4.
 */
export const WithClear: Story = {
  args: {
    modelValue: new CalendarDate(2026, 4, 15),
    label: 'Date (effacable)',
    showClear: true,
  },
};

/**
 * Cas label custom "Reinitialiser" : override i18n (AC9).
 */
export const WithClearCustomLabel: Story = {
  args: {
    modelValue: new CalendarDate(2026, 4, 15),
    label: 'Date',
    showClear: true,
    clearLabel: 'Réinitialiser',
  },
};

/**
 * Cas label i18n anglais "Clear" : démonstration override locale consommateur
 * (L-3 post-review 10.20 — couverture explicite clearLabel EN manquante).
 */
export const WithClearEnglishLabel: Story = {
  args: {
    modelValue: new CalendarDate(2026, 4, 15),
    label: 'Date',
    locale: 'en-US',
    showClear: true,
    clearLabel: 'Clear',
  },
};

/**
 * Cas dark mode : decorator html.classList.add('dark').
 * DELEGATED TO runtime : contraste AA brand-green darken (10.15 HIGH-2).
 */
export const DarkMode: Story = {
  args: {
    modelValue: new CalendarDate(2026, 4, 15),
    label: 'Date',
  },
  decorators: [
    (story) => ({
      components: { story },
      template: '<div class="dark bg-dark-bg p-6"><story /></div>',
    }),
  ],
};

/**
 * Cas locale fr-FR (default) : mois "Avril 2026" + jours "L M M J V S D".
 */
export const French: Story = {
  args: {
    modelValue: new CalendarDate(2026, 4, 15),
    label: 'Date (FR)',
    locale: 'fr-FR',
  },
};

/**
 * Cas locale en-US : mois "April 2026" + jours "S M T W T F S".
 */
export const English: Story = {
  args: {
    modelValue: new CalendarDate(2026, 4, 15),
    label: 'Date (EN)',
    locale: 'en-US',
  },
};

/**
 * Cas isDateDisabled custom : jours ouvrables uniquement (samedi/dimanche grises).
 */
export const IsDateDisabledWeekends: Story = {
  args: {
    modelValue: null,
    label: 'Jour ouvrable uniquement',
    placeholder: 'Lundi au vendredi',
  },
  render: (args) => ({
    components: { DatePicker },
    setup() {
      const tz = getLocalTimeZone();
      const isDateDisabled = (date: CalendarDate) => {
        const d = date.toDate(tz);
        return d.getDay() === 0 || d.getDay() === 6;
      };
      return { args, isDateDisabled };
    },
    template: `
      <DatePicker
        v-bind="args"
        :is-date-disabled="isDateDisabled"
      />
    `,
  }),
};

/**
 * Cas required : etoile rouge * affichee apres label.
 */
export const Required: Story = {
  args: {
    modelValue: null,
    label: 'Date obligatoire',
    required: true,
  },
};
