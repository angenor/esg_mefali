<!--
  SgesBetaBanner — squelette UI FR44 (Story 10.14, logique metier Epic 15.5).
-->
<script setup lang="ts">
import { computed } from 'vue';

type BetaReviewStatus =
  | 'beta-pending-review'
  | 'beta-review-requested'
  | 'beta-review-validated'
  | 'beta-review-rejected'
  | 'post-beta-ga';

interface Props {
  reviewStatus: BetaReviewStatus;
  sgesId?: string;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  requestReview: [sgesId: string];
}>();

const showBanner = computed(() => props.reviewStatus !== 'post-beta-ga');
const isRejected = computed(() => props.reviewStatus === 'beta-review-rejected');
const isValidated = computed(() => props.reviewStatus === 'beta-review-validated');
const isPending = computed(() => props.reviewStatus === 'beta-pending-review');
const isRequested = computed(() => props.reviewStatus === 'beta-review-requested');

const bannerClass = computed<string>(() => {
  if (isRejected.value) return 'bg-brand-red/10 border-brand-red/30 text-brand-red';
  if (isValidated.value) return 'bg-brand-green/10 border-brand-green/30 text-verdict-pass';
  if (isRequested.value) return 'bg-brand-blue/10 border-brand-blue/30 text-brand-blue';
  return 'bg-brand-orange/10 border-brand-orange/30 text-brand-orange';
});

const bannerLabel = computed<string>(() => {
  if (isRejected.value) return 'SGES BETA — Revue refusee, corrigez avant nouvelle soumission.';
  if (isValidated.value) return 'SGES BETA — Revue validee, passage GA imminent.';
  if (isRequested.value) return 'SGES BETA — Revue admin N2 demandee, en attente.';
  return 'SGES BETA — Revue admin N2 requise avant activation (bypass interdit).';
});

function handleRequest(): void {
  if (isPending.value && props.sgesId) {
    emit('requestReview', props.sgesId);
  }
}
</script>

<template>
  <div
    v-if="showBanner"
    role="status"
    aria-live="polite"
    :class="bannerClass"
    class="flex items-center justify-between gap-4 border-b px-4 py-3 text-sm"
  >
    <div class="flex items-center gap-2">
      <span
        aria-hidden="true"
        class="inline-block h-2 w-2 rounded-full bg-current"
      />
      <span>{{ bannerLabel }}</span>
    </div>
    <button
      v-if="isPending"
      type="button"
      class="rounded border border-current px-3 py-1 text-xs font-medium hover:bg-white/50 dark:hover:bg-black/30"
      @click="handleRequest"
    >
      Demander la revue
    </button>
  </div>
</template>
