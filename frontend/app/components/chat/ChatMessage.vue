<script setup lang="ts">
import type { Message } from '~/types'
import type { ProfileUpdateEvent } from '~/types/company'
import { useCompanyStore } from '~/stores/company'

const props = defineProps<{
  message: Message
  isStreaming?: boolean
}>()

const companyStore = useCompanyStore()
const isUser = computed(() => props.message.role === 'user')
const copied = ref(false)

// Notifications de profil associées à ce message
const profileUpdates = computed<ProfileUpdateEvent[]>(() => {
  if (isUser.value || props.isStreaming) return []
  return companyStore.recentUpdates
})

async function copyContent() {
  try {
    await navigator.clipboard.writeText(props.message.content)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    // Fallback silencieux
  }
}
</script>

<template>
  <div>
    <div
      class="flex gap-3 px-4 py-3"
      :class="isUser ? 'justify-end' : 'justify-start'"
    >
      <!-- Avatar assistant -->
      <div
        v-if="!isUser"
        class="shrink-0 w-8 h-8 rounded-full bg-brand-green flex items-center justify-center text-white text-sm font-bold mt-1"
      >
        IA
      </div>

      <!-- Bulle de message -->
      <div
        class="rounded-2xl px-4 py-2.5 text-sm leading-relaxed"
        :class="[
          isUser
            ? 'bg-brand-green text-white rounded-br-md max-w-[75%] whitespace-pre-wrap'
            : 'bg-gray-100 dark:bg-dark-hover text-surface-text dark:text-surface-dark-text rounded-bl-md max-w-[85%]',
        ]"
      >
        <!-- Messages utilisateur : texte brut -->
        <template v-if="isUser">
          {{ message.content }}
        </template>

        <!-- Messages assistant : rendu enrichi -->
        <template v-else>
          <MessageParser
            :content="message.content"
            :is-streaming="isStreaming"
          />
          <span
            v-if="isStreaming"
            class="inline-block w-1.5 h-4 bg-brand-green ml-0.5 animate-pulse"
          />
          <!-- Bouton copier -->
          <div v-if="!isStreaming && message.content" class="flex justify-end mt-2 pt-1 border-t border-gray-200/50 dark:border-dark-border/50">
            <button
              class="text-xs text-gray-400 hover:text-brand-green flex items-center gap-1 transition-colors"
              @click="copyContent"
            >
              <svg v-if="!copied" xmlns="http://www.w3.org/2000/svg" class="w-3 h-3" viewBox="0 0 20 20" fill="currentColor">
                <path d="M8 3a1 1 0 011-1h2a1 1 0 110 2H9a1 1 0 01-1-1z" />
                <path d="M6 3a2 2 0 00-2 2v11a2 2 0 002 2h8a2 2 0 002-2V5a2 2 0 00-2-2 3 3 0 01-3 3H9a3 3 0 01-3-3z" />
              </svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" class="w-3 h-3 text-brand-green" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
              </svg>
              {{ copied ? 'Copié !' : 'Copier' }}
            </button>
          </div>
        </template>
      </div>

      <!-- Avatar utilisateur -->
      <div
        v-if="isUser"
        class="shrink-0 w-8 h-8 rounded-full bg-brand-blue flex items-center justify-center text-white text-sm font-bold mt-1"
      >
        U
      </div>
    </div>

    <!-- Notification de mise à jour du profil -->
    <div v-if="!isUser && !isStreaming && profileUpdates.length > 0" class="px-4 pb-1">
      <ProfileNotification :updates="profileUpdates" />
    </div>
  </div>
</template>
