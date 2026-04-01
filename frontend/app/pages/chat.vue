<script setup lang="ts">
import { useChat } from '~/composables/useChat'
import { useUiStore } from '~/stores/ui'

definePageMeta({
  layout: 'default',
})

const uiStore = useUiStore()

const {
  currentConversation,
  messages,
  isStreaming,
  error,
  searchQuery,
  filteredConversations,
  documentProgress,
  reportSuggestion,
  activeToolCall,
  fetchConversations,
  createConversation,
  selectConversation,
  sendMessage,
  deleteConversation,
  renameConversation,
} = useChat()

const messagesContainer = ref<HTMLElement | null>(null)
const userScrolledUp = ref(false)

// Charger les conversations au montage
onMounted(async () => {
  await fetchConversations()
})

// Auto-scroll vers le bas quand un nouveau message arrive
watch(
  () => messages.value.length > 0 ? messages.value[messages.value.length - 1]?.content : '',
  () => {
    if (!userScrolledUp.value) {
      nextTick(() => scrollToBottom())
    }
  },
)

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTo({
      top: messagesContainer.value.scrollHeight,
      behavior: 'smooth',
    })
  }
}

function handleScroll() {
  if (!messagesContainer.value) return
  const { scrollTop, scrollHeight, clientHeight } = messagesContainer.value
  userScrolledUp.value = scrollHeight - scrollTop - clientHeight > 100
}

async function handleNewConversation() {
  const conv = await createConversation()
  await selectConversation(conv)
  uiStore.conversationDrawerOpen = false
}

async function handleSelect(conv: Parameters<typeof selectConversation>[0]) {
  await selectConversation(conv)
  uiStore.conversationDrawerOpen = false
}

async function handleSend(content: string) {
  if (!currentConversation.value) {
    const conv = await createConversation()
    await selectConversation(conv)
  }
  await sendMessage(content)
  await fetchConversations()
}

async function handleSendWithFile(content: string, file: File) {
  if (!currentConversation.value) {
    const conv = await createConversation()
    await selectConversation(conv)
  }
  await sendMessage(content, file)
  await fetchConversations()
}

async function handleDelete(conversationId: string) {
  await deleteConversation(conversationId)
}

async function handleRename(conversationId: string, title: string) {
  await renameConversation(conversationId, title)
}
</script>

<template>
  <div class="flex h-full -m-6 overflow-hidden">
    <!-- Panneau lateral desktop : liste des conversations -->
    <aside class="hidden md:flex w-72 flex-col border-r border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card">
      <ConversationList
        :conversations="filteredConversations"
        :current-id="currentConversation?.id"
        :search-query="searchQuery"
        @select="handleSelect"
        @create="handleNewConversation"
        @delete="handleDelete"
        @rename="handleRename"
        @update:search-query="searchQuery = $event"
      />
    </aside>

    <!-- Drawer mobile : overlay conversations -->
    <Transition
      enter-active-class="transition-opacity duration-200"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition-opacity duration-200"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="uiStore.conversationDrawerOpen"
        class="md:hidden fixed inset-0 z-40 bg-black/50"
        @click="uiStore.conversationDrawerOpen = false"
      />
    </Transition>
    <Transition
      enter-active-class="transition-transform duration-200"
      enter-from-class="-translate-x-full"
      enter-to-class="translate-x-0"
      leave-active-class="transition-transform duration-200"
      leave-from-class="translate-x-0"
      leave-to-class="-translate-x-full"
    >
      <aside
        v-if="uiStore.conversationDrawerOpen"
        class="md:hidden fixed inset-y-0 left-0 z-50 w-80 max-w-[85vw] bg-white dark:bg-dark-card shadow-xl"
      >
        <ConversationList
          :conversations="filteredConversations"
          :current-id="currentConversation?.id"
          :search-query="searchQuery"
          :is-drawer="true"
          @select="handleSelect"
          @create="handleNewConversation"
          @delete="handleDelete"
          @rename="handleRename"
          @update:search-query="searchQuery = $event"
          @close-drawer="uiStore.conversationDrawerOpen = false"
        />
      </aside>
    </Transition>

    <!-- Zone principale de chat -->
    <div class="flex-1 flex flex-col min-w-0">
      <!-- En-tete conversation -->
      <header class="flex items-center gap-3 px-4 py-3 border-b border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card">
        <!-- Bouton hamburger mobile -->
        <button
          class="md:hidden w-8 h-8 flex items-center justify-center rounded-lg text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-dark-hover"
          @click="uiStore.toggleConversationDrawer()"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 15a1 1 0 011-1h6a1 1 0 110 2H4a1 1 0 01-1-1z" clip-rule="evenodd" />
          </svg>
        </button>
        <h2 class="text-sm font-semibold text-surface-text dark:text-surface-dark-text truncate">
          {{ currentConversation?.title || 'Nouvelle conversation' }}
        </h2>
      </header>

      <!-- Messages -->
      <div
        ref="messagesContainer"
        class="flex-1 overflow-y-auto bg-surface-bg dark:bg-surface-dark-bg"
        @scroll="handleScroll"
      >
        <WelcomeMessage v-if="!currentConversation || messages.length === 0" />
        <div v-else class="py-4">
          <ChatMessage
            v-for="(msg, idx) in messages"
            :key="msg.id"
            :message="msg"
            :is-streaming="isStreaming && idx === messages.length - 1 && msg.role === 'assistant'"
            :document-progress="isStreaming && idx === messages.length - 1 && msg.role === 'assistant' ? documentProgress : null"
          />
        </div>
      </div>

      <!-- Indicateur tool call en cours -->
      <div v-if="activeToolCall" class="mx-4 mb-2">
        <ChatToolCallIndicator
          :tool-name="activeToolCall.name"
          :args="activeToolCall.args"
        />
      </div>

      <!-- Notification rapport disponible -->
      <div
        v-if="reportSuggestion"
        class="mx-4 mb-2 p-3 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-lg flex items-center gap-3"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 text-emerald-600 dark:text-emerald-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <span class="flex-1 text-sm text-emerald-800 dark:text-emerald-300">
          {{ reportSuggestion.message }}
        </span>
        <NuxtLink
          :to="`/esg/results?id=${reportSuggestion.assessmentId}`"
          class="px-3 py-1.5 text-xs font-medium bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors whitespace-nowrap"
          @click="reportSuggestion = null"
        >
          Generer le rapport
        </NuxtLink>
        <button
          class="text-emerald-400 hover:text-emerald-600 dark:hover:text-emerald-300"
          @click="reportSuggestion = null"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Erreur -->
      <div
        v-if="error"
        class="px-4 py-2 bg-red-50 dark:bg-red-900/20 text-brand-red text-sm"
      >
        {{ error }}
      </div>

      <!-- Zone de saisie -->
      <ChatInput
        :disabled="isStreaming"
        @send="handleSend"
        @send-with-file="handleSendWithFile"
      />
    </div>
  </div>
</template>
