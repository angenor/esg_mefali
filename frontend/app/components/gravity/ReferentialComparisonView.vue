<!--
  ReferentialComparisonView — squelette UI FR26 (Story 10.14, logique metier Epic 14).
-->
<script setup lang="ts">
import { computed } from 'vue';
import { TabsRoot, TabsList, TabsTrigger, TabsContent } from 'reka-ui';

type ComparisonState = 'loading' | 'loaded' | 'partial' | 'error';
type Variant = 'compact' | 'fullpage';
type Verdict = 'pass' | 'fail' | 'reported' | 'na';

interface CriterionRow {
  readonly id: string;
  readonly label: string;
  readonly verdicts: Readonly<Record<string, Verdict>>;
}

interface Props {
  state: ComparisonState;
  activeReferentials: readonly string[];
  variant?: Variant;
  rows?: readonly CriterionRow[];
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'fullpage',
  rows: () => [],
});
const emit = defineEmits<{
  retry: [];
}>();

const isLoading = computed(() => props.state === 'loading');
const hasError = computed(() => props.state === 'error');
const isPartial = computed(() => props.state === 'partial');
const containerClass = computed(() =>
  props.variant === 'compact' ? 'p-3 text-xs' : 'p-6 text-sm'
);
const verdictClass = (v: Verdict): string => {
  if (v === 'pass') return 'bg-verdict-pass-soft text-verdict-pass';
  if (v === 'fail') return 'bg-verdict-fail-soft text-verdict-fail';
  if (v === 'reported') return 'bg-verdict-reported-soft text-verdict-reported';
  return 'bg-verdict-na-soft text-verdict-na';
};
</script>

<template>
  <section
    :class="containerClass"
    class="rounded border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card text-surface-text dark:text-surface-dark-text"
    aria-labelledby="refcmp-title"
  >
    <h2 id="refcmp-title" class="text-base font-semibold">
      Comparaison multi-referentiels
    </h2>

    <div
      v-if="isLoading"
      role="status"
      aria-live="polite"
      class="mt-4"
    >
      Chargement des verdicts…
    </div>

    <div
      v-else-if="hasError"
      role="alert"
      class="mt-4 text-brand-red"
    >
      Erreur de chargement.
      <button type="button" class="ml-2 underline" @click="emit('retry')">
        Reessayer
      </button>
    </div>

    <TabsRoot v-else :default-value="activeReferentials[0] ?? ''" class="mt-4">
      <TabsList
        role="tablist"
        class="flex gap-2 border-b border-gray-200 dark:border-dark-border"
      >
        <TabsTrigger
          v-for="ref in activeReferentials"
          :key="ref"
          :value="ref"
          class="px-3 py-2 text-sm data-[state=active]:border-b-2 data-[state=active]:border-brand-green"
        >
          {{ ref }}
        </TabsTrigger>
      </TabsList>
      <TabsContent
        v-for="ref in activeReferentials"
        :key="ref"
        :value="ref"
        class="pt-4"
      >
        <div
          v-if="isPartial"
          role="status"
          class="mb-3 rounded bg-brand-orange/10 p-2 text-xs text-brand-orange"
        >
          Donnees partielles (timeout 1 referentiel).
        </div>
        <table role="table" class="w-full border-collapse">
          <caption class="sr-only">
            Verdicts pour referentiel {{ ref }}
          </caption>
          <thead>
            <tr>
              <th scope="col" class="border-b border-gray-200 dark:border-dark-border p-2 text-left">
                Critere
              </th>
              <th scope="col" class="border-b border-gray-200 dark:border-dark-border p-2 text-left">
                Verdict
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in rows" :key="row.id">
              <th scope="row" class="border-b border-gray-100 dark:border-dark-border/60 p-2 text-left font-normal">
                {{ row.label }}
              </th>
              <td class="border-b border-gray-100 dark:border-dark-border/60 p-2">
                <span
                  :class="verdictClass(row.verdicts[ref] ?? 'na')"
                  class="rounded px-2 py-0.5 text-xs font-medium"
                >
                  {{ row.verdicts[ref] ?? 'na' }}
                </span>
              </td>
            </tr>
            <tr v-if="rows.length === 0">
              <td colspan="2" class="p-4 text-center text-surface-text/60 dark:text-surface-dark-text/60">
                Aucun critere.
              </td>
            </tr>
          </tbody>
        </table>
      </TabsContent>
    </TabsRoot>
  </section>
</template>
