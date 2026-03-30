<script setup lang="ts">
import { useToast } from '~/composables/useToast'

const { toasts, dismiss } = useToast()

const typeStyles: Record<string, string> = {
  success: 'bg-emerald-50 border-brand-green text-emerald-800',
  error: 'bg-red-50 border-brand-red text-red-800',
  info: 'bg-blue-50 border-brand-blue text-blue-800',
}

const typeIcons: Record<string, string> = {
  success: '✓',
  error: '✕',
  info: 'ℹ',
}
</script>

<template>
  <Teleport to="body">
    <div class="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
      <TransitionGroup name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          class="flex items-start gap-2 px-4 py-3 rounded-lg border shadow-lg text-sm"
          :class="typeStyles[toast.type]"
        >
          <span class="flex-shrink-0 font-bold">
            {{ typeIcons[toast.type] }}
          </span>
          <span class="flex-1">{{ toast.message }}</span>
          <button
            class="flex-shrink-0 opacity-60 hover:opacity-100 transition-opacity"
            @click="dismiss(toast.id)"
          >
            ✕
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.toast-enter-active {
  transition: all 0.3s ease-out;
}
.toast-leave-active {
  transition: all 0.2s ease-in;
}
.toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}
.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}
</style>
