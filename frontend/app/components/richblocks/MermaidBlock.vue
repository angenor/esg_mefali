<script setup lang="ts">
import mermaid from 'mermaid'

const props = defineProps<{
  rawContent: string
}>()

const svgOutput = ref('')
const parseError = ref('')
const showFullscreen = ref(false)
const containerId = `mermaid-${Math.random().toString(36).slice(2, 9)}`

onMounted(async () => {
  mermaid.initialize({
    startOnLoad: false,
    theme: 'base',
    themeVariables: {
      primaryColor: '#10B981',
      primaryTextColor: '#111827',
      primaryBorderColor: '#059669',
      lineColor: '#3B82F6',
      secondaryColor: '#8B5CF6',
      tertiaryColor: '#F59E0B',
      fontFamily: 'system-ui, sans-serif',
    },
    securityLevel: 'strict',
  })

  try {
    // Valider la syntaxe
    await mermaid.parse(props.rawContent)
    const { svg } = await mermaid.render(containerId, props.rawContent)
    svgOutput.value = svg
  } catch {
    parseError.value = 'Syntaxe Mermaid invalide'
  }
})
</script>

<template>
  <div v-if="parseError">
    <BlockError :raw-content="rawContent" :error-message="parseError" />
  </div>
  <div v-else-if="svgOutput" class="my-3">
    <div class="rounded-lg border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card p-4 overflow-x-auto">
      <div class="flex justify-center" v-html="svgOutput" />
      <!-- Actions -->
      <div class="flex justify-end gap-2 mt-3 pt-3 border-t border-gray-100 dark:border-dark-border">
        <button
          class="text-xs text-gray-500 dark:text-gray-400 hover:text-brand-blue dark:hover:text-brand-blue flex items-center gap-1 transition-colors"
          @click="showFullscreen = true"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
            <path d="M3 4a1 1 0 011-1h4a1 1 0 010 2H6.414l2.293 2.293a1 1 0 11-1.414 1.414L5 6.414V8a1 1 0 01-2 0V4zm9 1a1 1 0 010-2h4a1 1 0 011 1v4a1 1 0 01-2 0V6.414l-2.293 2.293a1 1 0 11-1.414-1.414L13.586 5H12zm-9 7a1 1 0 012 0v1.586l2.293-2.293a1 1 0 111.414 1.414L6.414 15H8a1 1 0 010 2H4a1 1 0 01-1-1v-4zm13-1a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 010-2h1.586l-2.293-2.293a1 1 0 111.414-1.414L15 13.586V12a1 1 0 011-1z" />
          </svg>
          Agrandir
        </button>
      </div>
    </div>

    <!-- Modale plein écran -->
    <FullscreenModal :visible="showFullscreen" @close="showFullscreen = false">
      <div class="flex justify-center items-center min-h-[50vh]" v-html="svgOutput" />
    </FullscreenModal>
  </div>
  <div v-else>
    <BlockPlaceholder label="Génération du diagramme..." />
  </div>
</template>
