<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { gsap } from 'gsap'
import { useUiStore } from '~/stores/ui'
import { useChat } from '~/composables/useChat'
import { useAuthStore } from '~/stores/auth'
import type { InteractiveQuestionAnswer } from '~/types/interactive-question'

// Constantes de dimension
const WIDGET_MIN_WIDTH = 300
const WIDGET_MIN_HEIGHT = 400
const WIDGET_DEFAULT_WIDTH = 400
const WIDGET_DEFAULT_HEIGHT = 600
const WIDGET_MARGIN = 100

const uiStore = useUiStore()
const runtimeConfig = useRuntimeConfig()
const {
  conversations,
  currentConversation,
  searchQuery,
  filteredConversations,
  fetchConversations,
  selectConversation,
  createConversation,
  deleteConversation,
  renameConversation,
  messages,
  isStreaming,
  streamingContent,
  error,
  documentProgress,
  activeToolCall,
  currentInteractiveQuestion,
  interactiveQuestionsByMessage,
  sendMessage,
  submitInteractiveAnswer,
  onInteractiveQuestionAbandoned,
} = useChat()

const widgetRef = ref<HTMLElement | null>(null)
const isVisible = ref(false)
const isCreatingConversation = ref(false)
const currentView = ref<'chat' | 'history'>('chat')
const messagesContainer = ref<HTMLElement | null>(null)
const userScrolledUp = ref(false)
const isResizing = ref(false)

// Detecter prefers-reduced-motion
const prefersReducedMotion = typeof window !== 'undefined'
  ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
  : false

// --- Resize logic (Task 2, 3, 4) ---

type ResizeDirection = 'left' | 'top' | 'top-left' | 'top-right'

// Dimensions dynamiques liees au store
const widgetWidth = computed(() => uiStore.chatWidgetWidth)
const widgetHeight = computed(() => uiStore.chatWidgetHeight)

// Style dynamique du widget
const widgetStyle = computed(() => ({
  width: `${widgetWidth.value}px`,
  height: `${widgetHeight.value}px`,
}))

let resizeState: {
  direction: ResizeDirection
  startX: number
  startY: number
  startWidth: number
  startHeight: number
  pointerId: number
} | null = null

function clampWidth(w: number): number {
  const maxW = typeof window !== 'undefined' ? window.innerWidth - WIDGET_MARGIN : 1200
  return Math.min(Math.max(w, WIDGET_MIN_WIDTH), maxW)
}

function clampHeight(h: number): number {
  const maxH = typeof window !== 'undefined' ? window.innerHeight - WIDGET_MARGIN : 800
  return Math.min(Math.max(h, WIDGET_MIN_HEIGHT), maxH)
}

function startResize(direction: ResizeDirection, event: PointerEvent) {
  event.preventDefault()
  const target = event.currentTarget as HTMLElement
  target.setPointerCapture(event.pointerId)

  isResizing.value = true
  resizeState = {
    direction,
    startX: event.clientX,
    startY: event.clientY,
    startWidth: widgetWidth.value,
    startHeight: widgetHeight.value,
    pointerId: event.pointerId,
  }

  document.addEventListener('pointermove', onPointerMove)
  document.addEventListener('pointerup', onPointerUp)
}

function onPointerMove(event: PointerEvent) {
  if (!resizeState) return

  const deltaX = resizeState.startX - event.clientX
  const deltaY = resizeState.startY - event.clientY

  let newWidth = resizeState.startWidth
  let newHeight = resizeState.startHeight

  const dir = resizeState.direction

  // Bord gauche ou coins gauche : augmenter la largeur quand on tire vers la gauche
  if (dir === 'left' || dir === 'top-left') {
    newWidth = resizeState.startWidth + deltaX
  }

  // Bord superieur ou coins superieur : augmenter la hauteur quand on tire vers le haut
  if (dir === 'top' || dir === 'top-left' || dir === 'top-right') {
    newHeight = resizeState.startHeight + deltaY
  }

  // Coin superieur-droit : largeur augmente vers la droite (inverse)
  if (dir === 'top-right') {
    newWidth = resizeState.startWidth - deltaX
  }

  uiStore.chatWidgetWidth = clampWidth(newWidth)
  uiStore.chatWidgetHeight = clampHeight(newHeight)
}

function onPointerUp(event: PointerEvent) {
  if (!resizeState) return

  const target = event.target as HTMLElement
  if (target.releasePointerCapture) {
    try { target.releasePointerCapture(resizeState.pointerId) } catch { /* ignore */ }
  }

  // Persister la taille dans localStorage
  uiStore.setChatWidgetSize(widgetWidth.value, widgetHeight.value)

  resizeState = null
  isResizing.value = false

  document.removeEventListener('pointermove', onPointerMove)
  document.removeEventListener('pointerup', onPointerUp)
}

function handleResizeDoubleClick() {
  uiStore.resetChatWidgetSize()
}

// --- Gestion du viewport (Task 3) ---

function clampToViewport() {
  if (typeof window === 'undefined') return
  const maxW = window.innerWidth - WIDGET_MARGIN
  const maxH = window.innerHeight - WIDGET_MARGIN
  if (widgetWidth.value > maxW || widgetHeight.value > maxH) {
    uiStore.chatWidgetWidth = clampWidth(widgetWidth.value)
    uiStore.chatWidgetHeight = clampHeight(widgetHeight.value)
  }
}

function onWindowResize() {
  clampToViewport()
}

onMounted(() => {
  uiStore.initWidgetSize()
  clampToViewport()
  window.addEventListener('resize', onWindowResize)
})

function animateOpen() {
  const el = widgetRef.value
  if (!el) return

  gsap.killTweensOf(el)
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

  gsap.killTweensOf(el)
  const duration = prefersReducedMotion ? 0 : 0.2

  if (duration === 0) {
    // P3: reduction de mouvement — pas d'animation, masquer immediatement
    isVisible.value = false
    return
  }

  gsap.to(el, {
    scale: 0.8,
    opacity: 0,
    y: 20,
    duration,
    ease: 'power2.in',
    onComplete: () => {
      isVisible.value = false
    },
  })
}

async function handleToggleHistory() {
  if (currentView.value === 'history') {
    currentView.value = 'chat'
  } else {
    try {
      if (conversations.value.length === 0) {
        await fetchConversations()
      }
    } catch {
      // Continuer vers la vue historique meme en cas d'erreur reseau
      // ConversationList gere l'etat vide
    }
    currentView.value = 'history'
  }
}

async function handleSelectConversation(conversation: Parameters<typeof selectConversation>[0]) {
  try {
    await selectConversation(conversation)
    currentView.value = 'chat'
    userScrolledUp.value = false // P5: reset auto-scroll
    await nextTick()
    scrollToBottom()
  } catch {
    // Rester sur la vue historique en cas d'echec
  }
}

async function handleCreateConversation() {
  try {
    const conv = await createConversation()
    await selectConversation(conv) // P4: selectionner la nouvelle conversation
    currentView.value = 'chat'
    userScrolledUp.value = false // P5: reset auto-scroll
  } catch {
    // Rester sur la vue historique en cas d'echec
  }
}

// --- Handlers chat (Task 3) ---

async function handleSend(content: string) {
  if (isCreatingConversation.value) return // P10: guard double send
  try {
    if (!currentConversation.value) {
      isCreatingConversation.value = true
      const conv = await createConversation()
      await selectConversation(conv)
      isCreatingConversation.value = false
    }
    await sendMessage(content)
    await fetchConversations()
  } catch (e) {
    isCreatingConversation.value = false
    // P2: surfacer l'erreur si useChat ne l'a pas fait
    if (!error.value) {
      error.value = e instanceof Error ? e.message : 'Une erreur est survenue'
    }
  }
}

async function handleSendWithFile(content: string, file: File) {
  if (isCreatingConversation.value) return // P10: guard double send
  try {
    if (!currentConversation.value) {
      isCreatingConversation.value = true
      const conv = await createConversation()
      await selectConversation(conv)
      isCreatingConversation.value = false
    }
    await sendMessage(content, file)
    await fetchConversations()
  } catch (e) {
    isCreatingConversation.value = false
    // P2: surfacer l'erreur si useChat ne l'a pas fait
    if (!error.value) {
      error.value = e instanceof Error ? e.message : 'Une erreur est survenue'
    }
  }
}

async function handleInteractiveSubmit(answer: InteractiveQuestionAnswer) {
  try {
    if (!currentInteractiveQuestion.value) return
    await submitInteractiveAnswer(currentInteractiveQuestion.value.id, answer)
    await fetchConversations()
  } catch {
    // Erreur geree par useChat
  }
}

async function handleAbandonAndSend(content: string) {
  try {
    if (!currentInteractiveQuestion.value) return
    const qid = currentInteractiveQuestion.value.id
    // P1: appel backend abandon (best effort) — identique a pages/chat.vue
    try {
      const authStore = useAuthStore()
      const headers: Record<string, string> = { 'Content-Type': 'application/json' }
      if (authStore.accessToken) {
        headers.Authorization = `Bearer ${authStore.accessToken}`
      }
      await fetch(
        `${runtimeConfig.public.apiBase}/chat/interactive-questions/${qid}/abandon`,
        { method: 'POST', headers, body: '{}' },
      )
    } catch {
      // Best effort : le backend marquera la question comme expired au prochain message
    }
    onInteractiveQuestionAbandoned(qid)
    await sendMessage(content)
    await fetchConversations()
  } catch {
    // Erreur geree par useChat
  }
}

function handleQuickAction(action: string) {
  handleSend(action)
}

// --- Auto-scroll (Task 4) ---

function scrollToBottom() {
  // P7: ne pas scroller si le widget est cache
  if (!messagesContainer.value || !isVisible.value) return
  messagesContainer.value.scrollTo({
    top: messagesContainer.value.scrollHeight,
    behavior: 'smooth',
  })
}

function handleScroll() {
  if (!messagesContainer.value) return
  const { scrollTop, scrollHeight, clientHeight } = messagesContainer.value
  userScrolledUp.value = scrollHeight - scrollTop - clientHeight > 100 // P9: seuil aligne avec pages/chat.vue
}

onBeforeUnmount(() => {
  if (widgetRef.value) gsap.killTweensOf(widgetRef.value)
  window.removeEventListener('resize', onWindowResize)
  document.removeEventListener('pointermove', onPointerMove)
  document.removeEventListener('pointerup', onPointerUp)
})

// P6: observer la longueur du tableau (pas le contenu) pour detecter les nouveaux messages
watch(
  () => messages.value.length,
  () => {
    if (!userScrolledUp.value) {
      nextTick(() => scrollToBottom())
    }
  },
)

// Auto-scroll pendant le streaming
watch(streamingContent, () => {
  if (!userScrolledUp.value) {
    nextTick(() => scrollToBottom())
  }
})

watch(
  () => uiStore.chatWidgetOpen,
  async (open) => {
    if (open) {
      userScrolledUp.value = false // P5: reset auto-scroll a l'ouverture
      await nextTick()
      animateOpen()
      await nextTick()
      scrollToBottom() // P7: scroll initial a l'ouverture
    } else {
      currentView.value = 'chat'
      searchQuery.value = ''
      animateClose()
    }
  },
)
</script>

<template>
  <div
    v-show="isVisible || uiStore.chatWidgetOpen"
    ref="widgetRef"
    id="copilot-widget"
    :aria-hidden="!isVisible"
    :style="widgetStyle"
    :class="[
      'fixed bottom-24 right-6 z-50 rounded-2xl flex flex-col widget-glass',
      isResizing ? 'select-none' : '',
      isResizing ? '' : 'overflow-hidden',
    ]"
  >
    <!-- Poignees de resize (Task 2.2) -->
    <!-- Bord gauche -->
    <div
      class="absolute left-0 top-2 bottom-2 w-1 cursor-ew-resize z-10"
      @pointerdown="startResize('left', $event)"
      @dblclick="handleResizeDoubleClick"
    />
    <!-- Bord superieur -->
    <div
      class="absolute top-0 left-2 right-2 h-1 cursor-ns-resize z-10"
      @pointerdown="startResize('top', $event)"
      @dblclick="handleResizeDoubleClick"
    />
    <!-- Coin superieur-gauche -->
    <div
      class="absolute top-0 left-0 w-3 h-3 cursor-nwse-resize z-10"
      @pointerdown="startResize('top-left', $event)"
      @dblclick="handleResizeDoubleClick"
    />
    <!-- Coin superieur-droit -->
    <div
      class="absolute top-0 right-0 w-3 h-3 cursor-nesw-resize z-10"
      @pointerdown="startResize('top-right', $event)"
      @dblclick="handleResizeDoubleClick"
    />

    <!-- Header -->
    <ChatWidgetHeader
      :title="currentView === 'history' ? 'Conversations' : (currentConversation?.title ?? 'Assistant IA')"
      :show-back-button="currentView === 'history'"
      @close="uiStore.closeChatWidget()"
      @toggle-history="handleToggleHistory"
      @back="currentView = 'chat'"
    />

    <!-- Vue historique -->
    <ConversationList
      v-if="currentView === 'history'"
      :conversations="filteredConversations"
      :current-id="currentConversation?.id"
      :search-query="searchQuery"
      :is-drawer="false"
      class="flex-1 overflow-hidden"
      @select="handleSelectConversation"
      @create="handleCreateConversation"
      @delete="deleteConversation"
      @rename="renameConversation"
      @update:search-query="searchQuery = $event"
    />

    <!-- Vue chat -->
    <div v-else class="flex flex-col flex-1 overflow-hidden">
      <!-- Zone messages scrollable -->
      <div
        ref="messagesContainer"
        :class="[
          'flex-1 overflow-x-auto p-4 space-y-4 bg-surface-bg dark:bg-surface-dark-bg',
          isResizing ? 'overflow-hidden' : 'overflow-y-auto',
        ]"
        @scroll="handleScroll"
      >
        <WelcomeMessage v-if="!messages.length" />
        <template v-else>
          <ChatMessage
            v-for="(msg, idx) in messages"
            :key="msg.id"
            :message="msg"
            :is-streaming="isStreaming && idx === messages.length - 1 && msg.role === 'assistant'"
            :document-progress="isStreaming && idx === messages.length - 1 && msg.role === 'assistant' ? documentProgress : null"
            :interactive-question="interactiveQuestionsByMessage[msg.id] || (idx === messages.length - 1 && msg.role === 'assistant' && currentInteractiveQuestion?.id ? currentInteractiveQuestion : null)"
          />
        </template>
      </div>

      <!-- Indicateur tool call en cours -->
      <div v-if="activeToolCall" class="mx-4 mb-2">
        <ToolCallIndicator
          :tool-name="activeToolCall.name"
          :args="activeToolCall.args"
        />
      </div>

      <!-- Banniere d'erreur -->
      <div
        v-if="error"
        class="px-4 py-2 text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20"
      >
        {{ error }}
      </div>

      <!-- Zone de saisie / Bottom sheet interactif -->
      <InteractiveQuestionInputBar
        v-if="currentInteractiveQuestion?.state === 'pending'"
        :question="currentInteractiveQuestion"
        :loading="isStreaming"
        @submit="handleInteractiveSubmit"
        @abandon-and-send="handleAbandonAndSend"
      />
      <ChatInput
        v-else
        :disabled="isStreaming"
        @send="handleSend"
        @send-with-file="handleSendWithFile"
      />
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
