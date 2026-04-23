<script setup lang="ts">
import EsgIcon from './EsgIcon.vue';

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

function handleBackdropClick(event: MouseEvent) {
  if (event.target === event.currentTarget) {
    emit('close')
  }
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    emit('close')
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition-opacity duration-200"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition-opacity duration-200"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="visible"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
        @click="handleBackdropClick"
      >
        <div class="relative w-full max-w-5xl max-h-[90vh] bg-white dark:bg-dark-card rounded-2xl shadow-2xl overflow-auto p-6">
          <!-- Bouton fermer -->
          <button
            class="absolute top-3 right-3 w-8 h-8 flex items-center justify-center rounded-full text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-dark-hover transition-colors"
            @click="emit('close')"
          >
            <EsgIcon name="x" class="w-5 h-5" decorative />
          </button>

          <slot />
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
