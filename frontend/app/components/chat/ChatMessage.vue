<script setup lang="ts">
import type { Message } from '~/types'

const props = defineProps<{
  message: Message
  isStreaming?: boolean
}>()

const isUser = computed(() => props.message.role === 'user')
</script>

<template>
  <div
    class="flex gap-3 px-4 py-3"
    :class="isUser ? 'justify-end' : 'justify-start'"
  >
    <!-- Avatar assistant -->
    <div
      v-if="!isUser"
      class="flex-shrink-0 w-8 h-8 rounded-full bg-brand-green flex items-center justify-center text-white text-sm font-bold"
    >
      IA
    </div>

    <!-- Bulle de message -->
    <div
      class="max-w-[75%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap"
      :class="
        isUser
          ? 'bg-brand-green text-white rounded-br-md'
          : 'bg-gray-100 text-surface-text rounded-bl-md'
      "
    >
      {{ message.content }}
      <span
        v-if="isStreaming && !isUser"
        class="inline-block w-1.5 h-4 bg-brand-green ml-0.5 animate-pulse"
      />
    </div>

    <!-- Avatar utilisateur -->
    <div
      v-if="isUser"
      class="flex-shrink-0 w-8 h-8 rounded-full bg-brand-blue flex items-center justify-center text-white text-sm font-bold"
    >
      U
    </div>
  </div>
</template>
