<script setup lang="ts">
import type { ProfileUpdateEvent } from '~/types/company'

defineProps<{
  updates: ProfileUpdateEvent[]
}>()
</script>

<template>
  <div
    v-if="updates.length > 0"
    class="flex items-start gap-2 px-3 py-2 my-1 rounded-lg bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 text-xs"
  >
    <!-- Icône -->
    <svg
      xmlns="http://www.w3.org/2000/svg"
      class="w-4 h-4 text-brand-green shrink-0 mt-0.5"
      viewBox="0 0 20 20"
      fill="currentColor"
    >
      <path
        fill-rule="evenodd"
        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
        clip-rule="evenodd"
      />
    </svg>

    <div class="text-emerald-800 dark:text-emerald-200">
      <span class="font-medium">Profil mis à jour :</span>
      <span
        v-for="(update, idx) in updates"
        :key="update.field"
      >
        {{ update.label }} = {{ update.value }}<span v-if="idx < updates.length - 1">, </span>
      </span>
    </div>
  </div>
</template>
