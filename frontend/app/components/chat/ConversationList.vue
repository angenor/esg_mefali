<script setup lang="ts">
import type { Conversation } from '~/types'

defineProps<{
  conversations: Conversation[]
  currentId?: string
}>()

const emit = defineEmits<{
  select: [conversation: Conversation]
  create: []
  delete: [conversationId: string]
}>()
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Bouton nouvelle conversation -->
    <div class="p-3 border-b border-gray-200 dark:border-dark-border">
      <button
        class="w-full py-2 px-3 text-sm font-medium text-brand-green border border-brand-green rounded-lg hover:bg-emerald-50 dark:hover:bg-emerald-900/20 transition-colors"
        @click="emit('create')"
      >
        + Nouvelle conversation
      </button>
    </div>

    <!-- Liste des conversations -->
    <div class="flex-1 overflow-y-auto">
      <div
        v-if="conversations.length === 0"
        class="p-4 text-center text-sm text-gray-400"
      >
        Aucune conversation
      </div>
      <button
        v-for="conv in conversations"
        :key="conv.id"
        class="w-full text-left px-4 py-3 border-b border-gray-100 dark:border-dark-border hover:bg-gray-50 dark:hover:bg-dark-hover transition-colors group"
        :class="conv.id === currentId ? 'bg-emerald-50 dark:bg-emerald-900/20 border-l-2 border-l-brand-green' : ''"
        @click="emit('select', conv)"
      >
        <div class="flex items-center justify-between">
          <span class="text-sm font-medium text-surface-text dark:text-surface-dark-text truncate">
            {{ conv.title }}
          </span>
          <button
            class="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-brand-red transition-all p-1"
            @click.stop="emit('delete', conv.id)"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
            </svg>
          </button>
        </div>
        <span class="text-xs text-gray-400">
          {{ new Date(conv.updated_at).toLocaleDateString('fr-FR') }}
        </span>
      </button>
    </div>
  </div>
</template>
