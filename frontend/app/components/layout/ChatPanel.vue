<script setup lang="ts">
import { useUiStore } from '~/stores/ui'

const uiStore = useUiStore()
const { fetchConversations, createConversation, selectConversation, sendMessage, deleteConversation, conversations, currentConversation, messages, isStreaming, error } = useChat()

const showConversationList = ref(true)

onMounted(async () => {
  try {
    await fetchConversations()
  } catch {
    // Silencieux — l'utilisateur verra la liste vide
  }
})

async function handleCreate() {
  try {
    const conv = await createConversation()
    await selectConversation(conv)
    showConversationList.value = false
  } catch {
    // Erreur geree par le composable
  }
}

async function handleSend(content: string) {
  await sendMessage(content)
}

function handleBack() {
  showConversationList.value = true
}

const messagesContainer = ref<HTMLElement | null>(null)

watch(messages, () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}, { deep: true })
</script>

<template>
  <aside
    v-if="uiStore.chatPanelOpen"
    class="w-80 lg:w-96 border-l border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card flex flex-col h-full"
  >
    <!-- Header du panneau -->
    <div class="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-dark-border bg-gray-50 dark:bg-surface-dark-bg">
      <div class="flex items-center gap-2">
        <button
          v-if="!showConversationList && currentConversation"
          class="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
          @click="handleBack"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clip-rule="evenodd" />
          </svg>
        </button>
        <h3 class="text-sm font-semibold text-surface-text dark:text-surface-dark-text">
          {{ showConversationList ? 'Conversations' : (currentConversation?.title || 'Chat IA') }}
        </h3>
      </div>
      <button
        class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
        @click="uiStore.toggleChatPanel"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
        </svg>
      </button>
    </div>

    <!-- Contenu -->
    <template v-if="showConversationList">
      <ConversationList
        :conversations="conversations"
        :current-id="currentConversation?.id"
        @select="(conv) => { selectConversation(conv); showConversationList = false }"
        @create="handleCreate"
        @delete="deleteConversation"
      />
    </template>
    <template v-else>
      <!-- Messages -->
      <div ref="messagesContainer" class="flex-1 overflow-y-auto">
        <div
          v-if="messages.length === 0"
          class="flex items-center justify-center h-full text-sm text-gray-400 p-4 text-center"
        >
          Commencez la conversation en envoyant un message.
        </div>
        <ChatMessage
          v-for="(msg, idx) in messages"
          :key="msg.id"
          :message="msg"
          :is-streaming="isStreaming && idx === messages.length - 1 && msg.role === 'assistant'"
        />
      </div>

      <!-- Erreur -->
      <div v-if="error" class="px-4 py-2 text-xs text-brand-red bg-red-50 dark:bg-red-900/20">
        {{ error }}
      </div>

      <!-- Input -->
      <ChatInput :disabled="isStreaming" @send="handleSend" />
    </template>
  </aside>
</template>
