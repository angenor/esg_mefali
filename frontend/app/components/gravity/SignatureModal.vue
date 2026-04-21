<!--
  SignatureModal — squelette UI FR40 (Story 10.14, logique metier Epic 11).
  Respect prefers-reduced-motion natif via Reka UI (aucune animation custom GSAP).
-->
<script setup lang="ts">
import { computed } from 'vue';
import {
  DialogRoot,
  DialogPortal,
  DialogContent,
  DialogOverlay,
  DialogTitle,
  DialogDescription,
} from 'reka-ui';

type SignatureState = 'initial' | 'ready' | 'signing' | 'signed' | 'error';

interface Props {
  state: SignatureState;
  fundApplicationId?: string;
  destinataireBailleur?: string;
  snapshotPreview?: string;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  cancel: [];
  sign: [fundApplicationId: string];
  saveDraft: [];
}>();

const isOpen = computed(() => props.state !== 'signed');
const canSign = computed(() => props.state === 'ready');
const isSigning = computed(() => props.state === 'signing');
const hasError = computed(() => props.state === 'error');

function handleSign(): void {
  if (canSign.value && props.fundApplicationId) {
    emit('sign', props.fundApplicationId);
  }
}
</script>

<template>
  <!-- STUB: Dialog/Button remplaces par ui/Dialog + ui/Button Stories 10.15 -->
  <DialogRoot :open="isOpen" @update:open="(v: boolean) => !v && emit('cancel')">
    <DialogPortal>
      <DialogOverlay class="fixed inset-0 bg-black/50 dark:bg-black/70" />
      <DialogContent
        role="dialog"
        aria-modal="true"
        aria-labelledby="signature-modal-title"
        aria-describedby="signature-modal-disclaimer"
        class="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[480px] max-w-[90vw] rounded-lg bg-white dark:bg-dark-card p-6 shadow-xl focus:outline-none"
      >
        <DialogTitle
          id="signature-modal-title"
          class="text-lg font-semibold text-surface-text dark:text-surface-dark-text"
        >
          Signature electronique · {{ destinataireBailleur ?? 'Bailleur' }}
        </DialogTitle>
        <DialogDescription
          id="signature-modal-disclaimer"
          class="mt-3 rounded border border-brand-orange/30 bg-brand-orange/10 p-3 text-sm text-surface-text dark:text-surface-dark-text"
        >
          Disclaimer IA — verifiez le snapshot ci-dessous avant de signer.
        </DialogDescription>
        <pre
          class="mt-3 overflow-auto rounded bg-gray-100 dark:bg-dark-input p-2 text-xs text-surface-text dark:text-surface-dark-text"
        >{{ snapshotPreview ?? '— aucun snapshot —' }}</pre>
        <div
          v-if="hasError"
          role="alert"
          class="mt-3 text-sm text-brand-red"
        >
          Erreur durant la signature — reessayez.
        </div>
        <div class="mt-6 flex justify-end gap-2">
          <button
            type="button"
            class="rounded border border-gray-300 dark:border-dark-border px-3 py-2 text-sm text-surface-text dark:text-surface-dark-text hover:bg-gray-50 dark:hover:bg-dark-hover"
            @click="emit('saveDraft')"
          >
            Enregistrer brouillon
          </button>
          <button
            type="button"
            class="rounded bg-brand-purple px-3 py-2 text-sm text-white disabled:opacity-50"
            :disabled="!canSign || isSigning"
            :aria-busy="isSigning"
            @click="handleSign"
          >
            {{ isSigning ? 'Signature…' : 'Signer et figer' }}
          </button>
        </div>
      </DialogContent>
    </DialogPortal>
  </DialogRoot>
</template>
