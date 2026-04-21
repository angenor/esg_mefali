<!--
  SectionReviewCheckpoint — squelette UI FR41 (Story 10.14, logique metier Epic 12).
-->
<script setup lang="ts">
import { computed, ref, watch } from 'vue';

type CheckpointState = 'locked' | 'in-progress' | 'all-reviewed' | 'exporting' | 'exported';

interface Section {
  readonly id: string;
  readonly title: string;
}

interface Props {
  state: CheckpointState;
  amountUsd: number;
  sections: readonly Section[];
  reviewed?: readonly string[];
}

const props = withDefaults(defineProps<Props>(), {
  reviewed: () => [],
});
const emit = defineEmits<{
  toggle: [sectionId: string];
  export: [];
}>();

const localReviewed = ref<Set<string>>(new Set(props.reviewed));

watch(
  () => props.reviewed,
  (next) => {
    localReviewed.value = new Set(next);
  }
);

const isLocked = computed(() => props.state === 'locked');
const isExporting = computed(() => props.state === 'exporting');
const isExported = computed(() => props.state === 'exported');
const allReviewed = computed(
  () =>
    props.sections.length > 0 &&
    props.sections.every((s) => localReviewed.value.has(s.id))
);
const canExport = computed(() => allReviewed.value && !isLocked.value && !isExporting.value);

function onToggle(sectionId: string): void {
  if (localReviewed.value.has(sectionId)) {
    localReviewed.value.delete(sectionId);
  } else {
    localReviewed.value.add(sectionId);
  }
  // nouvelle ref pour reactivite (immutabilite — rule common/coding-style)
  localReviewed.value = new Set(localReviewed.value);
  emit('toggle', sectionId);
}
</script>

<template>
  <section
    class="rounded border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card p-6 text-surface-text dark:text-surface-dark-text"
    aria-labelledby="review-title"
  >
    <div class="flex items-center justify-between">
      <h2 id="review-title" class="text-base font-semibold">
        Checkpoint revue sections
      </h2>
      <span
        v-if="amountUsd > 50_000"
        role="status"
        class="rounded bg-brand-orange/10 px-2 py-0.5 text-xs text-brand-orange"
      >
        Revue sequentielle obligatoire (&gt; 50 000 USD)
      </span>
    </div>

    <fieldset
      :disabled="isLocked"
      class="mt-4 space-y-2"
      :aria-describedby="isLocked ? 'review-locked-hint' : undefined"
    >
      <legend class="sr-only">Sections a relire avant export</legend>
      <p
        v-if="isLocked"
        id="review-locked-hint"
        class="text-xs text-surface-text/70 dark:text-surface-dark-text/70"
      >
        Sections verrouillees — relachez les pre-requis Epic 12.
      </p>
      <label
        v-for="section in sections"
        :key="section.id"
        class="flex items-center gap-2 rounded p-2 hover:bg-gray-50 dark:hover:bg-dark-hover"
      >
        <input
          type="checkbox"
          :checked="localReviewed.has(section.id)"
          :aria-label="`Marquer ${section.title} comme relue`"
          class="h-4 w-4 rounded border-gray-300 dark:border-dark-border text-brand-green focus:ring-2 focus:ring-brand-green"
          @change="onToggle(section.id)"
        />
        <span class="text-sm">{{ section.title }}</span>
      </label>
    </fieldset>

    <div class="mt-6 flex justify-end">
      <button
        type="button"
        class="rounded bg-brand-green px-3 py-2 text-sm text-white disabled:opacity-50"
        :disabled="!canExport"
        :aria-busy="isExporting"
        @click="emit('export')"
      >
        {{ isExporting ? 'Export…' : isExported ? 'Exporte' : 'Exporter' }}
      </button>
    </div>
  </section>
</template>
