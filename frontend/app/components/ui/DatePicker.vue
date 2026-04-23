<script setup lang="ts">
/**
 * `ui/DatePicker.vue` (Story 10.20 AC1-AC9) — wrapper typé strict de Reka UI
 * `<PopoverRoot>` + `<CalendarRoot>` (mode single) OU `<RangeCalendarRoot>`
 * (mode range) offrant :
 *  - sélection date single OU plage via prop `mode: 'single' | 'range'`,
 *  - locale FR par défaut (format `d/M/yyyy`) via `DateFormatter` Intl natif,
 *  - displayValue trigger obligatoire (L22 §4quinquies 10.19) — label
 *    formaté `15/04/2026` pas clé ISO brute,
 *  - lifecycle close sans sélection (L23 §4quinquies 10.19) — reset mois
 *    courant au mois de modelValue / defaultValue / today() au close,
 *  - ARIA strict attribute (L24 §4quinquies 10.19) — `aria-haspopup='dialog'`
 *    + `aria-expanded` + `aria-controls` délégué Reka UI (Leçon 25 §4sexies
 *    post-10.20 : ne jamais injecter d'`id` custom sur primitives slot-forwarded)
 *    + `role='application'` Calendar,
 *  - keyboard WAI-ARIA Date Picker Dialog complet (Arrow/Page/Home/End/
 *    Enter/Escape) natif Reka UI,
 *  - bornes `minValue` + `maxValue` + `isDateDisabled` fonction custom,
 *  - bouton clear optionnel (`showClear`) avec label i18n `clearLabel`
 *    (pattern closeLabel 10.18 M-1 + cancelLabel 10.19 L-4).
 *
 * Pattern wrapper Reka UI stabilisé post-10.18/10.19 — 4ᵉ itération
 * byte-identique. 14+ primitives consommées (Popover* + Calendar* +
 * RangeCalendar* conditionnel via v-if mode).
 *
 * Voir :
 *  - docs/CODEMAPS/ui-primitives.md §3.8 DatePicker (exemples Vue + pièges 41-44)
 *  - registry.ts DATEPICKER_MODES + DatePickerMode type
 *  - tests/components/ui/test_datepicker_behavior.test.ts (Pattern A user-event)
 */
import { computed, ref, useId, watch } from 'vue';
import {
  CalendarCell,
  CalendarCellTrigger,
  CalendarGrid,
  CalendarGridBody,
  CalendarGridHead,
  CalendarGridRow,
  CalendarHeadCell,
  CalendarHeader,
  CalendarHeading,
  CalendarNext,
  CalendarPrev,
  CalendarRoot,
  PopoverContent,
  PopoverPortal,
  PopoverRoot,
  PopoverTrigger,
  RangeCalendarCell,
  RangeCalendarCellTrigger,
  RangeCalendarGrid,
  RangeCalendarGridBody,
  RangeCalendarGridHead,
  RangeCalendarGridRow,
  RangeCalendarHeadCell,
  RangeCalendarHeader,
  RangeCalendarHeading,
  RangeCalendarNext,
  RangeCalendarPrev,
  RangeCalendarRoot,
} from 'reka-ui';
import {
  DateFormatter,
  getLocalTimeZone,
  today,
  type DateValue,
} from '@internationalized/date';

/**
 * Plage de dates (mode='range'). Chaque bornure est optionnelle (null autorisé
 * pour sélection partielle `{start: ..., end: null}` en cours de saisie AC2).
 */
export interface DateRange {
  start: DateValue | null;
  end: DateValue | null;
}

/**
 * Props communes single + range. Discrimination via `mode` (L22 L23 L24
 * §4quinquies 10.19 appliquées proactivement).
 */
export interface DatePickerSingleProps {
  mode?: 'single';
  modelValue: DateValue | null;
  /** Mois initial si modelValue null (AC7 lifecycle reset L23). */
  defaultValue?: DateValue;
  /** Label obligatoire a11y (aria-labelledby). */
  label: string;
  /** Placeholder trigger vide. Default 'Sélectionner une date'. */
  placeholder?: string;
  minValue?: DateValue;
  maxValue?: DateValue;
  /** Fonction custom de désactivation jour par jour (AC8). */
  isDateDisabled?: (date: DateValue) => boolean;
  /** Locale Intl. Default 'fr-FR' (CLAUDE.md §Contexte Métier UEMOA/CEDEAO). */
  locale?: string;
  disabled?: boolean;
  /** Popover ouvrable mais cells non-cliquables (nav clavier OK). */
  readonly?: boolean;
  required?: boolean;
  /** Active le bouton Effacer en footer PopoverContent. Default false. */
  showClear?: boolean;
  /** Label i18n bouton clear. Default 'Effacer' (AC9 L-4 10.19 pattern). */
  clearLabel?: string;
  /** Override DateFormatter options (ex. {weekday:'long', day:'numeric', ...}). */
  customFormat?: Intl.DateTimeFormatOptions;
  /** Label placeholder range partial (AC6). Default 'Fin ?'. */
  rangePartialLabel?: string;
}

export interface DatePickerRangeProps
  extends Omit<DatePickerSingleProps, 'mode' | 'modelValue'> {
  mode: 'range';
  modelValue: DateRange;
}

export type DatePickerProps = DatePickerSingleProps | DatePickerRangeProps;

const props = withDefaults(defineProps<DatePickerProps>(), {
  mode: 'single',
  locale: 'fr-FR',
  disabled: false,
  readonly: false,
  required: false,
  showClear: false,
  clearLabel: 'Effacer',
  placeholder: 'Sélectionner une date',
  rangePartialLabel: 'Fin ?',
});

const emit = defineEmits<{
  (e: 'update:modelValue', value: DateValue | DateRange | null): void;
  (e: 'update:open', value: boolean): void;
  (e: 'clear'): void;
}>();

const isOpen = ref(false);
const labelId = useId();

/**
 * Mois initial affiche au premier rendu + au reset close (L23).
 * Ordre de fallback : modelValue (single/range.start) → defaultValue → today().
 */
function initialMonth(): DateValue {
  if (props.mode === 'range') {
    const range = props.modelValue as DateRange;
    if (range.start) return range.start;
  } else {
    const val = props.modelValue as DateValue | null;
    if (val) return val;
  }
  return props.defaultValue ?? today(getLocalTimeZone());
}

const currentMonth = ref<DateValue>(initialMonth());

// M-2 post-review 10.20 (piège #45) — dev-only warn si le parent passe une
// plage inversée via v-model (ex. Zod schema loose côté form). Reka UI
// RangeCalendarRoot normalise transparent lors d'une sélection utilisateur,
// mais rien ne protège contre une mutation programmatique incohérente. Warn
// sans throw : le consommateur peut continuer à rendre, Reka UI affichera
// la plage telle quelle ou swappera à la prochaine interaction.
function warnIfRangeInverted(val: unknown): void {
  if (!import.meta.env.DEV) return;
  if (props.mode !== 'range') return;
  const range = val as DateRange | null | undefined;
  if (!range || !range.start || !range.end) return;
  if (range.end.compare(range.start) < 0) {
    // eslint-disable-next-line no-console
    console.warn(
      '[DatePicker] modelValue range end < start — Reka UI auto-swaps en sélection utilisateur, mais la plage programmatique est incohérente.',
    );
  }
}

warnIfRangeInverted(props.modelValue);

// L23 §4quinquies — reset mois courant au close sans sélection.
// Si l'utilisateur navigue PageDown plusieurs mois puis ferme sans sélectionner,
// le mois courant revient au mois de modelValue (ou fallback). Évite le bug
// capitalisé 10.19 Combobox searchTerm non-cleared (piège #42 codemap §5).
watch(isOpen, (newValue: boolean) => {
  if (!newValue) {
    currentMonth.value = initialMonth();
  }
  emit('update:open', newValue);
});

// H-2 post-review 10.20 — réactivité modelValue parent→composant.
// Si le consommateur mute modelValue via v-model (reset formulaire, correction
// programmatique) pendant que le popover est fermé, le DatePicker doit
// afficher le mois de la nouvelle valeur à la prochaine ouverture. Le watcher
// isOpen seul ne suffit pas : il se déclenche au close, pas au modelValue change
// externe. Deep watcher pour gérer le cas range {start, end} objet muté.
watch(
  () => props.modelValue,
  (newVal) => {
    warnIfRangeInverted(newVal);
    if (!isOpen.value) {
      currentMonth.value = initialMonth();
    }
  },
  { deep: true },
);

const formatter = computed(
  () =>
    new DateFormatter(
      props.locale,
      props.customFormat ?? { day: '2-digit', month: '2-digit', year: 'numeric' },
    ),
);

// L22 §4quinquies — displayValue trigger. Label formaté utilisateur FR pas
// clé ISO brute 2026-04-15T00:00:00.000Z (AC6). Range : em-dash strict —.
const displayValue = computed<string | null>(() => {
  if (props.mode === 'range') {
    const { start, end } = props.modelValue as DateRange;
    if (!start && !end) return null;
    const startStr = start
      ? formatter.value.format(start.toDate(getLocalTimeZone()))
      : props.rangePartialLabel;
    const endStr = end
      ? formatter.value.format(end.toDate(getLocalTimeZone()))
      : props.rangePartialLabel;
    return `${startStr} — ${endStr}`;
  }
  const val = props.modelValue as DateValue | null;
  return val ? formatter.value.format(val.toDate(getLocalTimeZone())) : null;
});

const hasValue = computed(() => {
  if (props.mode === 'range') {
    const r = props.modelValue as DateRange;
    return !!(r.start || r.end);
  }
  return props.modelValue !== null;
});

function handleSingleChange(newValue: DateValue | null | undefined) {
  const val = newValue ?? null;
  emit('update:modelValue', val);
  if (val) {
    currentMonth.value = val;
    isOpen.value = false;
  }
}

function handleRangeChange(newValue: DateRange | null | undefined) {
  const range: DateRange = newValue ?? { start: null, end: null };
  emit('update:modelValue', range);
  if (range.start) {
    currentMonth.value = range.start;
  }
  if (range.start && range.end) {
    isOpen.value = false;
  }
}

function handleClear() {
  const cleared: DateValue | DateRange | null =
    props.mode === 'range' ? { start: null, end: null } : null;
  emit('update:modelValue', cleared);
  emit('clear');
  isOpen.value = false;
}

const calendarAriaLabel = computed(
  () =>
    `Calendrier, ${new DateFormatter(props.locale, {
      month: 'long',
      year: 'numeric',
    }).format(currentMonth.value.toDate(getLocalTimeZone()))}`,
);
</script>

<template>
  <div>
    <label
      :id="labelId"
      class="block text-sm font-medium text-surface-text dark:text-surface-dark-text mb-1"
    >
      {{ label }}
      <span v-if="required" class="text-brand-red" aria-hidden="true">*</span>
    </label>
    <PopoverRoot v-model:open="isOpen">
      <PopoverTrigger
        :disabled="disabled"
        :aria-labelledby="labelId"
        aria-haspopup="dialog"
        :aria-expanded="isOpen ? 'true' : 'false'"
        class="min-h-11 w-full px-3 py-2 text-left border rounded-md bg-white dark:bg-dark-input border-gray-300 dark:border-dark-border focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-green disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center justify-between gap-2"
      >
        <span
          v-if="displayValue"
          class="text-surface-text dark:text-surface-dark-text truncate"
        >
          {{ displayValue }}
        </span>
        <span
          v-else
          class="text-surface-text/40 dark:text-surface-dark-text/40 truncate"
        >
          {{ placeholder }}
        </span>
        <svg
          aria-hidden="true"
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="none"
          stroke="currentColor"
          class="flex-shrink-0"
        >
          <rect x="2" y="3" width="12" height="11" rx="1" stroke-width="1.5" />
          <path
            d="M2 6h12M5 1v3M11 1v3"
            stroke-width="1.5"
            stroke-linecap="round"
          />
        </svg>
      </PopoverTrigger>
      <PopoverPortal>
        <PopoverContent
          role="dialog"
          aria-modal="false"
          :aria-labelledby="labelId"
          class="z-50 bg-white dark:bg-dark-card border border-gray-200 dark:border-dark-border rounded-md shadow-lg p-4 mt-1 data-[state=open]:animate-in data-[state=closed]:animate-out motion-reduce:animate-none"
        >
          <CalendarRoot
            v-if="mode === 'single'"
            :model-value="(modelValue as DateValue | null) ?? undefined"
            :placeholder="currentMonth"
            :locale="locale"
            :min-value="minValue"
            :max-value="maxValue"
            :is-date-unavailable="isDateDisabled"
            :readonly="readonly"
            role="application"
            :aria-label="calendarAriaLabel"
            @update:model-value="handleSingleChange"
            @update:placeholder="(p: DateValue) => (currentMonth = p)"
          >
            <template #default="{ weekDays, grid }">
              <CalendarHeader
                class="flex justify-between items-center mb-2"
              >
                <CalendarPrev
                  aria-label="Mois précédent"
                  class="p-2 hover:bg-gray-50 dark:hover:bg-dark-hover rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-green motion-reduce:transition-none"
                >
                  <svg
                    aria-hidden="true"
                    width="16"
                    height="16"
                    viewBox="0 0 16 16"
                    fill="none"
                    stroke="currentColor"
                  >
                    <path
                      d="M10 3l-4 5 4 5"
                      stroke-width="1.5"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    />
                  </svg>
                </CalendarPrev>
                <CalendarHeading
                  class="font-semibold text-surface-text dark:text-surface-dark-text"
                />
                <CalendarNext
                  aria-label="Mois suivant"
                  class="p-2 hover:bg-gray-50 dark:hover:bg-dark-hover rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-green motion-reduce:transition-none"
                >
                  <svg
                    aria-hidden="true"
                    width="16"
                    height="16"
                    viewBox="0 0 16 16"
                    fill="none"
                    stroke="currentColor"
                  >
                    <path
                      d="M6 3l4 5-4 5"
                      stroke-width="1.5"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    />
                  </svg>
                </CalendarNext>
              </CalendarHeader>
              <CalendarGrid
                v-for="month in grid"
                :key="month.value.toString()"
              >
                <CalendarGridHead>
                  <CalendarGridRow>
                    <CalendarHeadCell
                      v-for="day in weekDays"
                      :key="day"
                      class="text-xs font-medium text-surface-text/60 dark:text-surface-dark-text/60 p-2 text-center w-9"
                    >
                      {{ day }}
                    </CalendarHeadCell>
                  </CalendarGridRow>
                </CalendarGridHead>
                <CalendarGridBody>
                  <CalendarGridRow
                    v-for="(weekDates, weekIdx) in month.rows"
                    :key="weekIdx"
                    class="flex"
                  >
                    <CalendarCell
                      v-for="weekDate in weekDates"
                      :key="weekDate.toString()"
                      :date="weekDate"
                      class="p-0.5"
                    >
                      <CalendarCellTrigger
                        :day="weekDate"
                        :month="month.value"
                        class="w-9 h-9 rounded text-sm text-surface-text dark:text-surface-dark-text hover:bg-gray-50 dark:hover:bg-dark-hover data-[selected]:bg-brand-green data-[selected]:text-white data-[disabled]:opacity-50 data-[disabled]:cursor-not-allowed data-[outside-view]:text-surface-text/40 data-[today]:font-bold data-[today]:ring-1 data-[today]:ring-brand-green focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-green motion-reduce:transition-none"
                      />
                    </CalendarCell>
                  </CalendarGridRow>
                </CalendarGridBody>
              </CalendarGrid>
            </template>
          </CalendarRoot>
          <RangeCalendarRoot
            v-else
            :model-value="(modelValue as DateRange)"
            :placeholder="currentMonth"
            :locale="locale"
            :min-value="minValue"
            :max-value="maxValue"
            :is-date-unavailable="isDateDisabled"
            :readonly="readonly"
            role="application"
            :aria-label="calendarAriaLabel"
            @update:model-value="handleRangeChange"
            @update:placeholder="(p: DateValue) => (currentMonth = p)"
          >
            <template #default="{ weekDays, grid }">
              <RangeCalendarHeader
                class="flex justify-between items-center mb-2"
              >
                <RangeCalendarPrev
                  aria-label="Mois précédent"
                  class="p-2 hover:bg-gray-50 dark:hover:bg-dark-hover rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-green motion-reduce:transition-none"
                >
                  <svg
                    aria-hidden="true"
                    width="16"
                    height="16"
                    viewBox="0 0 16 16"
                    fill="none"
                    stroke="currentColor"
                  >
                    <path
                      d="M10 3l-4 5 4 5"
                      stroke-width="1.5"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    />
                  </svg>
                </RangeCalendarPrev>
                <RangeCalendarHeading
                  class="font-semibold text-surface-text dark:text-surface-dark-text"
                />
                <RangeCalendarNext
                  aria-label="Mois suivant"
                  class="p-2 hover:bg-gray-50 dark:hover:bg-dark-hover rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-green motion-reduce:transition-none"
                >
                  <svg
                    aria-hidden="true"
                    width="16"
                    height="16"
                    viewBox="0 0 16 16"
                    fill="none"
                    stroke="currentColor"
                  >
                    <path
                      d="M6 3l4 5-4 5"
                      stroke-width="1.5"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    />
                  </svg>
                </RangeCalendarNext>
              </RangeCalendarHeader>
              <RangeCalendarGrid
                v-for="month in grid"
                :key="month.value.toString()"
              >
                <RangeCalendarGridHead>
                  <RangeCalendarGridRow>
                    <RangeCalendarHeadCell
                      v-for="day in weekDays"
                      :key="day"
                      class="text-xs font-medium text-surface-text/60 dark:text-surface-dark-text/60 p-2 text-center w-9"
                    >
                      {{ day }}
                    </RangeCalendarHeadCell>
                  </RangeCalendarGridRow>
                </RangeCalendarGridHead>
                <RangeCalendarGridBody>
                  <RangeCalendarGridRow
                    v-for="(weekDates, weekIdx) in month.rows"
                    :key="weekIdx"
                    class="flex"
                  >
                    <RangeCalendarCell
                      v-for="weekDate in weekDates"
                      :key="weekDate.toString()"
                      :date="weekDate"
                      class="p-0.5"
                    >
                      <RangeCalendarCellTrigger
                        :day="weekDate"
                        :month="month.value"
                        class="w-9 h-9 rounded text-sm text-surface-text dark:text-surface-dark-text hover:bg-gray-50 dark:hover:bg-dark-hover data-[selected]:bg-brand-green data-[selected]:text-white data-[highlighted]:bg-brand-green/20 dark:data-[highlighted]:bg-brand-green/30 data-[disabled]:opacity-50 data-[disabled]:cursor-not-allowed data-[outside-view]:text-surface-text/40 data-[today]:font-bold data-[today]:ring-1 data-[today]:ring-brand-green focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-green motion-reduce:transition-none"
                      />
                    </RangeCalendarCell>
                  </RangeCalendarGridRow>
                </RangeCalendarGridBody>
              </RangeCalendarGrid>
            </template>
          </RangeCalendarRoot>
          <div
            v-if="showClear && hasValue"
            class="mt-3 flex justify-end border-t border-gray-200 dark:border-dark-border pt-2"
          >
            <button
              type="button"
              class="text-sm text-brand-red hover:underline min-h-11 min-w-11 px-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-green rounded"
              @click="handleClear"
            >
              {{ clearLabel }}
            </button>
          </div>
        </PopoverContent>
      </PopoverPortal>
    </PopoverRoot>
  </div>
</template>
