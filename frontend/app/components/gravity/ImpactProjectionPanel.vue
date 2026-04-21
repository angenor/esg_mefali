<!--
  ImpactProjectionPanel — squelette UI Q11+Q14 (Story 10.14, logique metier Epic 15).
-->
<script setup lang="ts">
import { computed } from 'vue';
import { ScrollAreaRoot, ScrollAreaViewport, ScrollAreaScrollbar, ScrollAreaThumb } from 'reka-ui';

type ProjectionState = 'computing' | 'computed-safe' | 'computed-blocked' | 'published';

interface Props {
  state: ProjectionState;
  thresholdPercent?: number;
  impactPercent?: number;
  migrationId?: string;
  impactedEntities?: number;
}

const props = withDefaults(defineProps<Props>(), {
  thresholdPercent: 20,
});
const emit = defineEmits<{
  publish: [migrationId: string];
  cancel: [];
}>();

const isComputing = computed(() => props.state === 'computing');
const isSafe = computed(() => props.state === 'computed-safe');
const isBlocked = computed(() => props.state === 'computed-blocked');
const isPublished = computed(() => props.state === 'published');

function handlePublish(): void {
  if (isSafe.value && props.migrationId) {
    emit('publish', props.migrationId);
  }
}
</script>

<template>
  <section
    class="rounded border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card p-6 text-surface-text dark:text-surface-dark-text"
    aria-labelledby="impact-title"
  >
    <h2 id="impact-title" class="text-base font-semibold">
      Projection d'impact · Migration referentiel
    </h2>

    <div
      v-if="isComputing"
      role="status"
      aria-live="polite"
      class="mt-4 text-sm"
    >
      Calcul de la projection…
    </div>

    <ScrollAreaRoot
      v-else
      class="mt-4 h-40 rounded bg-gray-50 dark:bg-dark-input"
    >
      <ScrollAreaViewport class="h-full w-full p-3">
        <dl class="space-y-2 text-sm">
          <div class="flex justify-between">
            <dt>Seuil bloquant</dt>
            <dd>{{ thresholdPercent }} %</dd>
          </div>
          <div class="flex justify-between">
            <dt>Impact mesure</dt>
            <dd>
              <span
                :class="isBlocked ? 'text-verdict-fail' : 'text-verdict-pass'"
                class="font-semibold"
              >
                {{ impactPercent ?? '—' }} %
              </span>
            </dd>
          </div>
          <div class="flex justify-between">
            <dt>Entites impactees</dt>
            <dd>{{ impactedEntities ?? '—' }}</dd>
          </div>
        </dl>
      </ScrollAreaViewport>
      <ScrollAreaScrollbar orientation="vertical" class="w-2 bg-gray-200 dark:bg-dark-border">
        <ScrollAreaThumb class="bg-gray-400 dark:bg-dark-hover rounded" />
      </ScrollAreaScrollbar>
    </ScrollAreaRoot>

    <div
      v-if="isBlocked"
      role="alert"
      class="mt-4 rounded border border-brand-red/30 bg-brand-red/10 p-3 text-sm text-brand-red"
    >
      Projection bloquante — impact &gt; {{ thresholdPercent }} %. Publication escaladee admin N2.
    </div>

    <div
      v-else-if="isPublished"
      role="status"
      class="mt-4 rounded border border-brand-green/30 bg-brand-green/10 p-3 text-sm text-verdict-pass"
    >
      Migration publiee.
    </div>

    <div class="mt-6 flex justify-end gap-2">
      <button
        type="button"
        class="rounded border border-gray-300 dark:border-dark-border px-3 py-2 text-sm hover:bg-gray-50 dark:hover:bg-dark-hover"
        @click="emit('cancel')"
      >
        Annuler
      </button>
      <button
        type="button"
        class="rounded bg-brand-purple px-3 py-2 text-sm text-white disabled:opacity-50"
        :disabled="!isSafe"
        @click="handlePublish"
      >
        Publier la migration
      </button>
    </div>
  </section>
</template>
