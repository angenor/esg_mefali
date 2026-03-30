<script setup lang="ts">
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { useMessageParser } from '~/composables/useMessageParser'
import type { ParsedSegment } from '~/types/richblocks'

const props = defineProps<{
  content: string
  isStreaming?: boolean
}>()

const { parse } = useMessageParser()

const segments = computed<ParsedSegment[]>(() => parse(props.content))

function renderMarkdown(text: string): string {
  const raw = marked.parse(text, { async: false }) as string
  return DOMPurify.sanitize(raw)
}
</script>

<template>
  <div class="message-parser">
    <template v-for="(segment, index) in segments" :key="index">
      <!-- Texte markdown -->
      <div
        v-if="segment.type === 'text'"
        class="prose prose-sm dark:prose-invert max-w-none prose-p:my-1 prose-ul:my-1 prose-ol:my-1 prose-li:my-0.5 prose-headings:my-2 prose-a:text-brand-blue prose-code:text-brand-green prose-code:bg-gray-100 dark:prose-code:bg-dark-card prose-code:px-1 prose-code:rounded"
        v-html="renderMarkdown(segment.content)"
      />

      <!-- Bloc incomplet (streaming) -->
      <BlockPlaceholder
        v-else-if="!segment.isComplete"
      />

      <!-- Blocs visuels complets -->
      <ChartBlock
        v-else-if="segment.type === 'chart'"
        :raw-content="segment.content"
      />
      <MermaidBlock
        v-else-if="segment.type === 'mermaid'"
        :raw-content="segment.content"
      />
      <TableBlock
        v-else-if="segment.type === 'table'"
        :raw-content="segment.content"
      />
      <GaugeBlock
        v-else-if="segment.type === 'gauge'"
        :raw-content="segment.content"
      />
      <ProgressBlock
        v-else-if="segment.type === 'progress'"
        :raw-content="segment.content"
      />
      <TimelineBlock
        v-else-if="segment.type === 'timeline'"
        :raw-content="segment.content"
      />
    </template>
  </div>
</template>
