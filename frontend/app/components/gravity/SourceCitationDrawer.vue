<!--
  SourceCitationDrawer — squelette UI FR71 (Story 10.14, logique metier Epic 13).
-->
<script setup lang="ts">
import { computed } from 'vue';
import {
  DialogRoot,
  DialogPortal,
  DialogContent,
  DialogOverlay,
  DialogTitle,
  DialogClose,
} from 'reka-ui';

type DrawerState = 'closed' | 'opening' | 'open' | 'loading' | 'error' | 'closing';
type SourceType = 'rule' | 'criterion' | 'fact' | 'template' | 'intermediary' | 'fund';

interface Props {
  state: DrawerState;
  sourceType?: SourceType;
  sourceUrl?: string;
  sourceAccessedAt?: string;
  sourceTitle?: string;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  close: [];
  retry: [];
}>();

const isOpen = computed(() => props.state !== 'closed' && props.state !== 'closing');
const isLoading = computed(() => props.state === 'loading' || props.state === 'opening');
const hasError = computed(() => props.state === 'error');
</script>

<template>
  <!-- STUB: Drawer remplace par ui/Drawer Story 10.16 -->
  <DialogRoot
    :open="isOpen"
    @update:open="(v: boolean) => !v && emit('close')"
  >
    <DialogPortal>
      <DialogOverlay class="fixed inset-0 bg-black/40 dark:bg-black/70" />
      <DialogContent
        role="dialog"
        aria-modal="true"
        aria-labelledby="source-drawer-title"
        class="fixed right-0 top-0 h-full w-[420px] max-w-full bg-white dark:bg-dark-card p-6 shadow-xl focus:outline-none border-l border-gray-200 dark:border-dark-border"
      >
        <div class="flex items-center justify-between">
          <DialogTitle
            id="source-drawer-title"
            class="text-base font-semibold text-surface-text dark:text-surface-dark-text"
          >
            Source · {{ sourceType ?? 'document' }}
          </DialogTitle>
          <DialogClose
            aria-label="Fermer le panneau des sources"
            class="rounded p-1 text-surface-text dark:text-surface-dark-text hover:bg-gray-100 dark:hover:bg-dark-hover"
          >
            ✕
          </DialogClose>
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

        <dl
          v-else
          class="mt-6 space-y-3 text-sm text-surface-text dark:text-surface-dark-text"
        >
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
        </dl>
      </DialogContent>
    </DialogPortal>
  </DialogRoot>
</template>
