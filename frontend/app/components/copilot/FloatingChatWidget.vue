<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { gsap } from 'gsap'
import { useUiStore } from '~/stores/ui'

const uiStore = useUiStore()
const widgetRef = ref<HTMLElement | null>(null)
const isAnimating = ref(false)
const isVisible = ref(false)

// Detecter prefers-reduced-motion
const prefersReducedMotion = typeof window !== 'undefined'
  ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
  : false

function animateOpen() {
  const el = widgetRef.value
  if (!el) return

  const duration = prefersReducedMotion ? 0 : 0.25

  isVisible.value = true
  gsap.fromTo(
    el,
    { scale: 0.8, opacity: 0, y: 20 },
    { scale: 1, opacity: 1, y: 0, duration, ease: 'power2.out' },
  )
}

function animateClose() {
  const el = widgetRef.value
  if (!el) return

  const duration = prefersReducedMotion ? 0 : 0.2

  isAnimating.value = true
  gsap.to(el, {
    scale: 0.8,
    opacity: 0,
    y: 20,
    duration,
    ease: 'power2.in',
    onComplete: () => {
      isVisible.value = false
      isAnimating.value = false
    },
  })
}

watch(
  () => uiStore.chatWidgetOpen,
  async (open) => {
    if (open) {
      await nextTick()
      animateOpen()
    } else {
      animateClose()
    }
  },
)
</script>

<template>
  <div
    v-show="isVisible || uiStore.chatWidgetOpen"
    ref="widgetRef"
    class="fixed bottom-24 right-6 z-50 w-[400px] h-[600px] rounded-2xl overflow-hidden flex flex-col widget-glass"
  >
    <!-- Header temporaire (sera remplace par ChatWidgetHeader.vue en Story 1.4) -->
    <div class="flex items-center justify-between px-4 py-3 border-b border-gray-200/50 dark:border-dark-border/50">
      <h2 class="text-sm font-semibold text-surface-text dark:text-surface-dark-text">
        Assistant IA
      </h2>
      <button
        type="button"
        class="p-1 rounded-md text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-dark-hover focus:outline-none focus:ring-2 focus:ring-brand-green"
        aria-label="Fermer l'assistant IA"
        @click="uiStore.closeChatWidget()"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    <!-- Body placeholder (sera remplace par l'integration chat en Story 1.5) -->
    <div class="flex-1 flex items-center justify-center p-4">
      <p class="text-sm text-gray-400 dark:text-gray-500 italic">
        Chat arrive en Story 1.5
      </p>
    </div>
  </div>
</template>

<style scoped>
.widget-glass {
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  background-color: rgb(255 255 255 / 0.8);
  border: 1px solid rgb(229 231 235 / 0.5);
  box-shadow: 0 25px 50px -12px rgb(0 0 0 / 0.25);
}

:where(.dark) .widget-glass {
  background-color: rgb(31 41 55 / 0.8);
  border-color: rgb(55 65 81 / 0.5);
}

/* Fallback opaque pour navigateurs sans backdrop-filter */
@supports not (backdrop-filter: blur(1px)) {
  .widget-glass {
    background-color: rgb(255 255 255);
    border-color: rgb(229 231 235);
  }

  :where(.dark) .widget-glass {
    background-color: rgb(31 41 55);
    border-color: rgb(55 65 81);
  }
}
</style>
