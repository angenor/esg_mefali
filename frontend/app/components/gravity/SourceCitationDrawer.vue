<!--
  SourceCitationDrawer — squelette UI FR71 (Story 10.14, logique metier Epic 13).
  Pattern side drawer consultatif (role="complementary") — PAS dialog modal.
  Escape ferme en bonus (UX attendue), pas de focus trap (consultation parallele).
-->
<script setup lang="ts">
import { computed, onMounted, onBeforeUnmount, watch } from 'vue';
import { ScrollAreaRoot, ScrollAreaViewport, ScrollAreaScrollbar, ScrollAreaThumb } from 'reka-ui';

type DrawerState = 'closed' | 'opening' | 'open' | 'loading' | 'error' | 'closing';
type SourceType = 'rule' | 'criterion' | 'fact' | 'template' | 'intermediary' | 'fund';

interface Props {
  state: DrawerState;
  sourceType?: SourceType;
  sourceUrl?: string;
  sourceAccessedAt?: string;
  sourceTitle?: string;
  sourceContent?: string;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  close: [];
  retry: [];
}>();

const isVisible = computed(() => props.state !== 'closed' && props.state !== 'closing');
const isLoading = computed(() => props.state === 'loading' || props.state === 'opening');
const hasError = computed(() => props.state === 'error');

function handleEscape(e: KeyboardEvent): void {
  if (e.key === 'Escape' && isVisible.value) {
    emit('close');
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleEscape);
});

onBeforeUnmount(() => {
  document.removeEventListener('keydown', handleEscape);
});

watch(isVisible, (visible) => {
  if (!visible) {
    // no-op : le parent gere l'etat, pas de focus trap a liberer
  }
});
</script>

<template>
  <!-- STUB: Drawer remplace par ui/Drawer Story 10.16 -->
  <Teleport v-if="isVisible" to="body">
    <aside
      role="complementary"
      aria-label="Sources documentaires"
      class="fixed right-0 top-0 z-40 h-full w-[420px] max-w-full bg-white dark:bg-dark-card p-6 shadow-xl border-l border-gray-200 dark:border-dark-border"
    >
      <div class="flex items-center justify-between">
        <h2
          id="source-drawer-title"
          class="text-base font-semibold text-surface-text dark:text-surface-dark-text"
        >
          Source · {{ sourceType ?? 'document' }}
        </h2>
        <button
          type="button"
          aria-label="Fermer le panneau des sources"
          class="rounded p-1 text-surface-text dark:text-surface-dark-text hover:bg-gray-100 dark:hover:bg-dark-hover focus:outline-2 focus:outline-brand-blue"
          @click="emit('close')"
        >
          ✕
        </button>
      </div>

      <div
        v-if="isLoading"
        role="status"
        aria-live="polite"
        class="mt-6 text-sm text-surface-text/70 dark:text-surface-dark-text/70"
      >
        Chargement de la source…
      </div>

      <div
        v-else-if="hasError"
        role="alert"
        class="mt-6 rounded border border-brand-red/30 bg-brand-red/10 p-3 text-sm text-brand-red"
      >
        Erreur de chargement.
        <button
          type="button"
          class="ml-2 underline"
          @click="emit('retry')"
        >
          Reessayer
        </button>
      </div>

      <ScrollAreaRoot
        v-else
        class="mt-6 h-[calc(100%-4rem)] overflow-hidden"
      >
        <ScrollAreaViewport class="h-full w-full pr-3">
          <dl class="space-y-3 text-sm text-surface-text dark:text-surface-dark-text">
            <div>
              <dt class="font-medium">Titre</dt>
              <dd>{{ sourceTitle ?? '—' }}</dd>
            </div>
            <div>
              <dt class="font-medium">URL</dt>
              <dd>
                <a
                  v-if="sourceUrl"
                  :href="sourceUrl"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="text-brand-blue underline focus:outline-2 focus:outline-brand-blue"
                >
                  {{ sourceUrl }}
                </a>
                <span v-else>—</span>
              </dd>
            </div>
            <div>
              <dt class="font-medium">Acces</dt>
              <dd>{{ sourceAccessedAt ?? '—' }}</dd>
            </div>
            <div v-if="sourceContent">
              <dt class="font-medium">Extrait</dt>
              <dd class="mt-1 whitespace-pre-wrap rounded bg-gray-50 dark:bg-dark-input p-2 text-xs">
                {{ sourceContent }}
              </dd>
            </div>
          </dl>
        </ScrollAreaViewport>
        <ScrollAreaScrollbar orientation="vertical" class="w-2 bg-gray-200 dark:bg-dark-border">
          <ScrollAreaThumb class="bg-gray-400 dark:bg-dark-hover rounded" />
        </ScrollAreaScrollbar>
      </ScrollAreaRoot>
    </aside>
  </Teleport>
</template>
