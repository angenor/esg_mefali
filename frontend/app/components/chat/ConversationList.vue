<script setup lang="ts">
import type { Conversation } from '~/types'

defineProps<{
  conversations: Conversation[]
  currentId?: string
  searchQuery?: string
  isDrawer?: boolean
}>()

const emit = defineEmits<{
  select: [conversation: Conversation]
  create: []
  delete: [conversationId: string]
  rename: [conversationId: string, title: string]
  'update:searchQuery': [value: string]
  closeDrawer: []
}>()

const editingId = ref<string | null>(null)
const editingTitle = ref('')
const deletingId = ref<string | null>(null)

function startRename(conv: Conversation) {
  editingId.value = conv.id
  editingTitle.value = conv.title
}

function confirmRename() {
  if (editingId.value && editingTitle.value.trim()) {
    emit('rename', editingId.value, editingTitle.value.trim())
  }
  editingId.value = null
  editingTitle.value = ''
}

function cancelRename() {
  editingId.value = null
  editingTitle.value = ''
}

function handleRenameKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter') {
    event.preventDefault()
    confirmRename()
  } else if (event.key === 'Escape') {
    cancelRename()
  }
}

function confirmDelete(conversationId: string) {
  deletingId.value = conversationId
}

function executeDelete() {
  if (deletingId.value) {
    emit('delete', deletingId.value)
    deletingId.value = null
  }
}
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- En-tete drawer mobile -->
    <div v-if="isDrawer" class="flex items-center justify-between p-3 border-b border-gray-200 dark:border-dark-border">
      <span class="text-sm font-semibold text-surface-text dark:text-surface-dark-text">Conversations</span>
      <button
        class="w-8 h-8 flex items-center justify-center rounded-full text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-dark-hover"
        @click="emit('closeDrawer')"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
        </svg>
      </button>
    </div>

    <!-- Recherche -->
    <div class="p-3 border-b border-gray-200 dark:border-dark-border space-y-2">
      <input
        :value="searchQuery"
        type="text"
        placeholder="Rechercher..."
        class="w-full text-sm rounded-lg border border-gray-300 dark:border-dark-border dark:bg-dark-input dark:text-surface-dark-text px-3 py-1.5 focus:ring-2 focus:ring-brand-green focus:border-transparent outline-none"
        @input="emit('update:searchQuery', ($event.target as HTMLInputElement).value)"
      >
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
      <div
        v-for="conv in conversations"
        :key="conv.id"
        class="w-full text-left px-4 py-3 border-b border-gray-100 dark:border-dark-border hover:bg-gray-50 dark:hover:bg-dark-hover transition-colors group cursor-pointer"
        :class="conv.id === currentId ? 'bg-emerald-50 dark:bg-emerald-900/20 border-l-2 border-l-brand-green' : ''"
        @click="editingId !== conv.id && emit('select', conv)"
      >
        <!-- Mode edition du titre -->
        <div v-if="editingId === conv.id" class="flex items-center gap-1" @click.stop>
          <input
            v-model="editingTitle"
            type="text"
            class="flex-1 text-sm rounded border border-brand-green dark:bg-dark-input dark:text-surface-dark-text px-2 py-0.5 focus:ring-1 focus:ring-brand-green outline-none"
            @keydown="handleRenameKeydown"
          >
          <button class="text-brand-green p-1" @click="confirmRename">
            <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" /></svg>
          </button>
          <button class="text-gray-400 p-1" @click="cancelRename">
            <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" /></svg>
          </button>
        </div>

        <!-- Mode normal -->
        <template v-else>
          <div class="flex items-center justify-between">
            <span class="text-sm font-medium text-surface-text dark:text-surface-dark-text truncate">
              {{ conv.title }}
            </span>
            <div class="flex items-center opacity-0 group-hover:opacity-100 transition-all">
              <!-- Renommer -->
              <button
                class="text-gray-400 hover:text-brand-blue p-1"
                @click.stop="startRename(conv)"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor"><path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" /></svg>
              </button>
              <!-- Supprimer -->
              <button
                class="text-gray-400 hover:text-brand-red p-1"
                @click.stop="confirmDelete(conv.id)"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" /></svg>
              </button>
            </div>
          </div>
          <span class="text-xs text-gray-400">
            {{ new Date(conv.updated_at).toLocaleDateString('fr-FR') }}
          </span>

          <!-- Confirmation de suppression -->
          <div
            v-if="deletingId === conv.id"
            class="mt-2 p-2 bg-red-50 dark:bg-red-900/20 rounded-lg text-xs"
            @click.stop
          >
            <p class="text-brand-red mb-2">Supprimer cette conversation ?</p>
            <div class="flex gap-2">
              <button
                class="px-2 py-1 bg-brand-red text-white rounded text-xs hover:bg-red-600"
                @click="executeDelete"
              >
                Supprimer
              </button>
              <button
                class="px-2 py-1 bg-gray-200 dark:bg-dark-hover text-surface-text dark:text-surface-dark-text rounded text-xs"
                @click="deletingId = null"
              >
                Annuler
              </button>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>
