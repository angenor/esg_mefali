<script setup lang="ts">
// FR33/NFR17 — Indicateur visuel de reconnexion affiche sous le header du widget
// quand la connexion SSE/reseau est perdue. Purement presentationnel (aucune logique metier).
defineProps<{ isConnected: boolean }>()
</script>

<template>
  <div
    v-if="!isConnected"
    role="status"
    aria-live="polite"
    class="flex items-center gap-2 px-4 py-2 text-xs bg-amber-50 dark:bg-amber-900/20 text-amber-800 dark:text-amber-300 border-b border-amber-200 dark:border-amber-800/50"
  >
    <svg
      xmlns="http://www.w3.org/2000/svg"
      class="w-3.5 h-3.5 animate-pulse shrink-0"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
      aria-hidden="true"
    >
      <path d="M1 1l22 22" />
      <path d="M16.72 11.06A10.94 10.94 0 0119 12.55" />
      <path d="M5 12.55a10.94 10.94 0 015.17-2.39" />
      <path d="M10.71 5.05A16 16 0 0122.58 9" />
      <path d="M1.42 9a15.91 15.91 0 014.7-2.88" />
      <path d="M8.53 16.11a6 6 0 016.95 0" />
      <path d="M12 20h.01" />
    </svg>
    <span>Reconnexion...</span>
  </div>
</template>
