<script setup lang="ts" generic="T extends string | number">
/**
 * `ui/Combobox.vue` (Story 10.19 AC1-AC6) — wrapper typé strict de Reka UI
 * `<ComboboxRoot>` offrant :
 *  - autocomplete searchable single + multi-select (prop `multiple`),
 *  - search insensible casse + diacritiques (Unicode NFD) + IME composition
 *    safe (compositionstart/end guard — piège #38 codemap, accents FR + CJK),
 *  - ARIA role="combobox"/listbox/option + aria-expanded/controls/activedescendant
 *    fournis natifs Reka UI,
 *  - keyboard ArrowUp/Down/Home/End/Enter/Escape/Tab WAI-ARIA natifs,
 *  - empty state slot configurable + message i18n 'Aucun résultat' default,
 *  - multi-select badges réutilisation `ui/Badge` (10.17) + bouton × touch ≥ 44 px.
 *
 * Pattern wrapper Reka UI stabilisé post-10.18 (Drawer). 14 primitives Reka UI
 * consommées (ComboboxRoot + Anchor + Input + Trigger + Portal + Content +
 * Viewport + Empty + Group + Label + Item + ItemIndicator + Separator + Cancel).
 *
 * Voir :
 *  - docs/CODEMAPS/ui-primitives.md §3.6 Combobox (exemples Vue + pièges 35-40)
 *  - registry.ts COMBOBOX_MODES + ComboboxMode type
 *  - tests/components/ui/test_combobox_behavior.test.ts (Pattern A user-event)
 */
import { computed, ref, useId } from 'vue';
import {
  ComboboxAnchor,
  ComboboxCancel,
  ComboboxContent,
  ComboboxEmpty,
  ComboboxGroup,
  ComboboxInput,
  ComboboxItem,
  ComboboxItemIndicator,
  ComboboxLabel,
  ComboboxPortal,
  ComboboxRoot,
  ComboboxSeparator,
  ComboboxTrigger,
  ComboboxViewport,
} from 'reka-ui';
import Badge from './Badge.vue';

export interface ComboboxOption<TValue extends string | number> {
  value: TValue;
  label: string;
  disabled?: boolean;
  /** Cle de groupement optionnelle (ComboboxGroup + ComboboxLabel rendus). */
  group?: string;
}

export interface ComboboxProps<TValue extends string | number = string> {
  /**
   * Valeur(s) selectionnee(s). `T` si `multiple=false`, `T[]` si `multiple=true`.
   * `null` autorise (pas de selection initiale). Note implementation Q Phase 0
   * (DEF-10.19-1) : discriminated union `{multiple:true, modelValue:T[]}` non
   * nativement supportee par TS 5.x sur defineProps → fallback permissif
   * `T | T[] | null` accepte.
   */
  modelValue: TValue | TValue[] | null;
  /** Liste des options. Tri et filtrage assures cote composant. */
  options: Array<ComboboxOption<TValue>>;
  /** Label obligatoire (a11y aria-labelledby) — pas de combobox sans label WAI-ARIA. */
  label: string;
  /** Mode single (default) vs multi-select (badges × rendus). */
  multiple?: boolean;
  /** Placeholder input. Default 'Sélectionner...'. */
  placeholder?: string;
  /** Message empty state default. Override via slot #empty possible. */
  emptyLabel?: string;
  /** Active la recherche (filter case+diacritic insensible). Default true. */
  searchable?: boolean;
  /** Desactive l'ensemble du combobox. */
  disabled?: boolean;
  /** Attribut required sur l'input interne. */
  required?: boolean;
  /** v-model:open optionnel (par defaut controle par Reka UI). */
  open?: boolean;
}

type ComboboxPropsWithGeneric = ComboboxProps<T>;

const props = withDefaults(defineProps<ComboboxPropsWithGeneric>(), {
  multiple: false,
  placeholder: 'Sélectionner...',
  emptyLabel: 'Aucun résultat',
  searchable: true,
  disabled: false,
  required: false,
  open: undefined,
});

const emit = defineEmits<{
  (e: 'update:modelValue', value: T | T[] | null): void;
  (e: 'update:open', value: boolean): void;
}>();

defineSlots<{
  /** Override complet de l'empty state (fallback: emptyLabel + role="status"). */
  empty?: () => unknown;
}>();

const searchTerm = ref('');
const isComposing = ref(false);
const labelId = useId();

// AC3 — normalisation Unicode NFD + toLowerCase (case + diacritic insensitive).
// Pattern byte-identique documente §3.6 codemap. `[̀-ͯ]` = plage
// Unicode des diacritiques combinants (tildes, accents aigus/graves, cedilles).
function normalize(str: string): string {
  return str.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
}

const filteredOptions = computed<Array<ComboboxOption<T>>>(() => {
  if (!props.searchable || isComposing.value || !searchTerm.value) {
    return props.options;
  }
  const needle = normalize(searchTerm.value);
  return props.options.filter((opt) => normalize(opt.label).includes(needle));
});

const groupedOptions = computed(() => {
  const groups = new Map<string | undefined, Array<ComboboxOption<T>>>();
  for (const opt of filteredOptions.value) {
    const key = opt.group;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key)!.push(opt);
  }
  return Array.from(groups.entries()).map(([label, items]) => ({ label, items }));
});

const selectedValues = computed<T[]>(() => {
  if (props.modelValue === null || props.modelValue === undefined) return [];
  return Array.isArray(props.modelValue)
    ? (props.modelValue as T[])
    : [props.modelValue as T];
});

function labelFor(value: T): string {
  return props.options.find((o) => o.value === value)?.label ?? String(value);
}

function removeValue(value: T) {
  if (!props.multiple) return;
  const next = selectedValues.value.filter((v) => v !== value);
  emit('update:modelValue', next);
}

function handleCompositionStart() {
  isComposing.value = true;
}

function handleCompositionEnd(e: Event) {
  isComposing.value = false;
  const target = e.target as HTMLInputElement | null;
  if (target) {
    searchTerm.value = target.value;
  }
}

function handleRootUpdate(value: string | number | boolean | Array<string | number | boolean> | null | undefined) {
  emit('update:modelValue', value as T | T[] | null);
}

// Reka UI ComboboxRoot applique par defaut un filter interne sur le contenu
// texte de `ComboboxItem` qui se superpose a notre `filteredOptions` computed
// (case-sensitive + pas de NFD normalisation + pas d'IME guard). On passe
// `:ignore-filter="true"` sur le Root pour controler le filtrage
// exclusivement cote composant (AC3 + IME guard + piege #38 codemap).
</script>

<template>
  <div class="w-full">
    <label
      :id="labelId"
      class="block text-sm font-medium text-surface-text dark:text-surface-dark-text mb-1"
    >
      {{ label }}
      <span v-if="required" class="text-brand-red" aria-hidden="true">*</span>
    </label>
    <ComboboxRoot
      :model-value="modelValue ?? undefined"
      :multiple="multiple"
      :disabled="disabled"
      :open="open"
      :ignore-filter="true"
      @update:model-value="handleRootUpdate"
      @update:open="(v: boolean) => emit('update:open', v)"
    >
      <ComboboxAnchor
        class="flex flex-wrap items-center gap-1 min-h-11 px-2 py-1 border rounded-md bg-white dark:bg-dark-input border-gray-300 dark:border-dark-border focus-within:ring-2 focus-within:ring-brand-green dark:focus-within:ring-brand-green"
      >
        <template v-if="multiple && selectedValues.length > 0">
          <Badge
            v-for="val in selectedValues"
            :key="String(val)"
            variant="lifecycle"
            state="draft"
            size="sm"
          >
            <span class="inline-flex items-center gap-1">
              <span>{{ labelFor(val) }}</span>
              <button
                type="button"
                class="inline-flex items-center justify-center min-h-11 min-w-11 rounded hover:bg-gray-200 dark:hover:bg-dark-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-green"
                :aria-label="`Retirer ${labelFor(val)}`"
                @click.stop="removeValue(val)"
              >
                <svg aria-hidden="true" width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor">
                  <path d="M3 3 L9 9 M9 3 L3 9" stroke-width="1.5" stroke-linecap="round" />
                </svg>
              </button>
            </span>
          </Badge>
        </template>
        <ComboboxInput
          v-model="searchTerm"
          :placeholder="placeholder"
          :aria-labelledby="labelId"
          :required="required"
          class="flex-1 min-w-0 bg-transparent outline-none text-surface-text dark:text-surface-dark-text placeholder:text-surface-text/40 dark:placeholder:text-surface-dark-text/40 disabled:cursor-not-allowed disabled:opacity-50"
          @compositionstart="handleCompositionStart"
          @compositionend="handleCompositionEnd"
        />
        <ComboboxCancel
          v-if="searchable && searchTerm.length > 0"
          class="inline-flex items-center justify-center min-h-11 min-w-11 p-1 text-surface-text/60 dark:text-surface-dark-text/60 hover:text-surface-text dark:hover:text-surface-dark-text"
          :aria-label="'Effacer la recherche'"
        >
          <svg aria-hidden="true" width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor">
            <path d="M3 3 L11 11 M11 3 L3 11" stroke-width="1.5" stroke-linecap="round" />
          </svg>
        </ComboboxCancel>
        <ComboboxTrigger
          class="inline-flex items-center justify-center p-1 text-surface-text dark:text-surface-dark-text disabled:cursor-not-allowed"
        >
          <svg aria-hidden="true" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor">
            <path d="M4 6 L8 10 L12 6" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </ComboboxTrigger>
      </ComboboxAnchor>
      <ComboboxPortal>
        <ComboboxContent
          class="z-50 mt-1 max-h-[300px] overflow-hidden rounded-md border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card shadow-lg data-[state=open]:animate-in data-[state=closed]:animate-out motion-reduce:animate-none"
          position="popper"
        >
          <ComboboxViewport class="p-1">
            <ComboboxEmpty
              role="status"
              aria-live="polite"
              class="p-4 text-center text-sm text-surface-text/60 dark:text-surface-dark-text/60"
            >
              <slot name="empty">{{ emptyLabel }}</slot>
            </ComboboxEmpty>
            <template v-for="(group, idx) in groupedOptions" :key="group.label ?? `__flat-${idx}`">
              <template v-if="group.label">
                <ComboboxSeparator
                  v-if="idx > 0"
                  class="my-1 h-px bg-gray-200 dark:bg-dark-border"
                />
                <ComboboxGroup>
                  <ComboboxLabel
                    class="px-2 py-1 text-xs font-semibold uppercase text-surface-text/60 dark:text-surface-dark-text/60"
                  >
                    {{ group.label }}
                  </ComboboxLabel>
                  <ComboboxItem
                    v-for="opt in group.items"
                    :key="String(opt.value)"
                    :value="opt.value"
                    :disabled="opt.disabled"
                    class="flex items-center justify-between px-2 py-2 rounded cursor-pointer text-sm text-surface-text dark:text-surface-dark-text data-[highlighted]:bg-gray-100 dark:data-[highlighted]:bg-dark-hover data-[state=checked]:bg-brand-green/10 dark:data-[state=checked]:bg-brand-green/20 data-[disabled]:opacity-50 data-[disabled]:cursor-not-allowed focus-visible:outline-none"
                  >
                    <span>{{ opt.label }}</span>
                    <ComboboxItemIndicator>
                      <svg aria-hidden="true" width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor">
                        <path d="M3 7 L6 10 L11 4" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
                      </svg>
                    </ComboboxItemIndicator>
                  </ComboboxItem>
                </ComboboxGroup>
              </template>
              <template v-else>
                <ComboboxItem
                  v-for="opt in group.items"
                  :key="String(opt.value)"
                  :value="opt.value"
                  :disabled="opt.disabled"
                  class="flex items-center justify-between px-2 py-2 rounded cursor-pointer text-sm text-surface-text dark:text-surface-dark-text data-[highlighted]:bg-gray-100 dark:data-[highlighted]:bg-dark-hover data-[state=checked]:bg-brand-green/10 dark:data-[state=checked]:bg-brand-green/20 data-[disabled]:opacity-50 data-[disabled]:cursor-not-allowed focus-visible:outline-none"
                >
                  <span>{{ opt.label }}</span>
                  <ComboboxItemIndicator>
                    <svg aria-hidden="true" width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor">
                      <path d="M3 7 L6 10 L11 4" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
                    </svg>
                  </ComboboxItemIndicator>
                </ComboboxItem>
              </template>
            </template>
          </ComboboxViewport>
        </ComboboxContent>
      </ComboboxPortal>
    </ComboboxRoot>
  </div>
</template>
