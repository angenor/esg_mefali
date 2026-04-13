<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps<{
  title: string
  description: string
  countdown?: number
  currentStep: number
  totalSteps: number
}>()

const emit = defineEmits<{
  close: []
  next: []
  countdownExpired: []
}>()

// Flag pour empecher le double-clic sur Suivant (review #2)
const nextClicked = ref(false)

function handleNext() {
  if (nextClicked.value) return
  nextClicked.value = true
  emit('next')
}

// Countdown reactif integre (remplace l'ancien injectCountdownBadge DOM)
const countdownRemaining = ref(props.countdown)
let countdownIntervalId: ReturnType<typeof setInterval> | null = null

if (props.countdown !== undefined) {
  // Guard countdown <= 0 : emettre immediatement (review #3)
  if (props.countdown <= 0) {
    countdownRemaining.value = 0
    queueMicrotask(() => emit('countdownExpired'))
  } else {
    countdownIntervalId = setInterval(() => {
      if (countdownRemaining.value !== undefined && countdownRemaining.value > 0) {
        countdownRemaining.value--
        if (countdownRemaining.value <= 0) {
          if (countdownIntervalId !== null) {
            clearInterval(countdownIntervalId)
            countdownIntervalId = null
          }
          emit('countdownExpired')
        }
      }
    }, 1000)
  }
}

// Focus trap : boucle Tab entre le bouton fermer et le bouton suivant (NFR13, review #5)
const dialogRef = ref<HTMLElement | null>(null)

function handleKeydown(e: KeyboardEvent) {
  if (e.key !== 'Tab' || !dialogRef.value) return

  const focusable = dialogRef.value.querySelectorAll<HTMLElement>(
    'button:not([disabled]), [tabindex]:not([tabindex="-1"])',
  )
  if (focusable.length === 0) return

  const first = focusable[0]!
  const last = focusable[focusable.length - 1]!

  if (e.shiftKey && document.activeElement === first) {
    e.preventDefault()
    last.focus()
  } else if (!e.shiftKey && document.activeElement === last) {
    e.preventDefault()
    first.focus()
  }
}

onMounted(() => {
  // Focus initial sur le premier bouton focusable
  const firstBtn = dialogRef.value?.querySelector<HTMLElement>('button')
  firstBtn?.focus()
})

onBeforeUnmount(() => {
  if (countdownIntervalId !== null) {
    clearInterval(countdownIntervalId)
    countdownIntervalId = null
  }
})
</script>

<template>
  <div
    ref="dialogRef"
    role="dialog"
    :aria-label="title"
    aria-modal="true"
    class="relative rounded-xl shadow-xl border bg-white dark:bg-dark-card text-surface-text dark:text-surface-dark-text border-gray-200 dark:border-dark-border p-4 min-w-[260px] max-w-[360px]"
    @keydown="handleKeydown"
  >
    <!-- Bouton fermer (X) en haut a droite -->
    <button
      data-testid="popover-close-btn"
      class="absolute top-2 right-2 p-1 rounded-md text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-dark-hover transition-colors"
      aria-label="Fermer le guidage"
      @click="emit('close')"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
        <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
      </svg>
    </button>

    <!-- Indicateur de progression -->
    <div class="text-xs text-gray-400 dark:text-gray-500 mb-1 pr-6">
      Étape {{ currentStep }}/{{ totalSteps }}
    </div>

    <!-- Titre -->
    <h3 class="text-sm font-semibold mb-1 pr-6">
      {{ title }}
    </h3>

    <!-- Description -->
    <p class="text-sm text-gray-600 dark:text-gray-400 leading-relaxed mb-3">
      {{ description }}
    </p>

    <!-- Badge countdown -->
    <div
      v-if="countdownRemaining !== undefined"
      data-testid="countdown-badge"
      class="inline-flex items-center gap-1 rounded-full px-2.5 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 text-sm font-semibold tabular-nums mb-3"
    >
      {{ countdownRemaining }}s
    </div>

    <!-- Bouton Suivant -->
    <div class="flex justify-end">
      <button
        data-testid="popover-next-btn"
        class="px-3 py-1.5 rounded-md text-sm font-medium text-white bg-brand-green hover:opacity-90 transition-opacity"
        :disabled="nextClicked"
        @click="handleNext"
      >
        Suivant
      </button>
    </div>
  </div>
</template>
