<script setup lang="ts">
import type { DocumentDetail } from '~/types/documents'

const props = defineProps<{
  document: DocumentDetail
}>()

const emit = defineEmits<{
  close: []
  reanalyze: [id: string]
}>()

const activeSection = ref<'summary' | 'findings' | 'esg' | 'raw'>('summary')

const typeLabels: Record<string, string> = {
  statuts_juridiques: 'Statuts juridiques',
  rapport_activite: 'Rapport d\'activite',
  facture: 'Facture',
  contrat: 'Contrat',
  politique_interne: 'Politique interne',
  bilan_financier: 'Bilan financier',
  autre: 'Autre',
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} o`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} Ko`
  return `${(bytes / (1024 * 1024)).toFixed(1)} Mo`
}

const sections = [
  { key: 'summary' as const, label: 'Resume' },
  { key: 'findings' as const, label: 'Points cles' },
  { key: 'esg' as const, label: 'ESG' },
  { key: 'raw' as const, label: 'Texte brut' },
]

const esgPillars = computed(() => {
  const esg = props.document.analysis?.esg_relevant_info
  if (!esg) return []
  return [
    { key: 'environmental', label: 'Environnement', color: 'text-emerald-600 dark:text-emerald-400', items: esg.environmental || [] },
    { key: 'social', label: 'Social', color: 'text-blue-600 dark:text-blue-400', items: esg.social || [] },
    { key: 'governance', label: 'Gouvernance', color: 'text-purple-600 dark:text-purple-400', items: esg.governance || [] },
  ]
})
</script>

<template>
  <div class="bg-white dark:bg-dark-card rounded-xl border border-gray-200 dark:border-dark-border overflow-hidden">
    <!-- Header -->
    <div class="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-dark-border">
      <div class="min-w-0">
        <h3 class="text-sm font-semibold text-surface-text dark:text-surface-dark-text truncate">
          {{ document.original_filename }}
        </h3>
        <p class="text-xs text-gray-500 dark:text-gray-400">
          {{ formatFileSize(document.file_size) }}
          <span v-if="document.document_type"> — {{ typeLabels[document.document_type] || document.document_type }}</span>
        </p>
      </div>
      <div class="flex items-center gap-2 shrink-0">
        <button
          v-if="document.status === 'error'"
          class="text-xs px-2.5 py-1 bg-brand-green text-white rounded-lg hover:bg-emerald-600 transition-colors"
          @click="emit('reanalyze', document.id)"
        >
          Relancer
        </button>
        <button
          class="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          @click="emit('close')"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Onglets -->
    <div v-if="document.analysis" class="flex border-b border-gray-200 dark:border-dark-border">
      <button
        v-for="section in sections"
        :key="section.key"
        class="flex-1 px-3 py-2 text-xs font-medium transition-colors"
        :class="activeSection === section.key
          ? 'text-brand-green border-b-2 border-brand-green'
          : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'"
        @click="activeSection = section.key"
      >
        {{ section.label }}
      </button>
    </div>

    <!-- Contenu -->
    <div class="p-4 max-h-96 overflow-y-auto">
      <!-- Pas d'analyse -->
      <div v-if="!document.analysis" class="text-center py-6 text-gray-500 dark:text-gray-400">
        <div v-if="document.status === 'processing'" class="flex flex-col items-center gap-2">
          <div class="w-6 h-6 border-2 border-brand-green border-t-transparent rounded-full animate-spin" />
          <p class="text-sm">Analyse en cours...</p>
        </div>
        <div v-else-if="document.status === 'error'">
          <p class="text-sm text-red-500">Erreur lors de l'analyse</p>
          <button
            class="mt-2 text-xs text-brand-green hover:underline"
            @click="emit('reanalyze', document.id)"
          >
            Relancer l'analyse
          </button>
        </div>
        <p v-else class="text-sm">Analyse non disponible</p>
      </div>

      <!-- Resume -->
      <div v-else-if="activeSection === 'summary'" class="prose prose-sm dark:prose-invert max-w-none">
        <p class="text-sm text-surface-text dark:text-surface-dark-text leading-relaxed whitespace-pre-wrap">
          {{ document.analysis.summary }}
        </p>
        <!-- Donnees structurees -->
        <div v-if="document.analysis.structured_data && Object.keys(document.analysis.structured_data).length > 0" class="mt-4">
          <h4 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-2">Donnees cles</h4>
          <div class="grid grid-cols-2 gap-2">
            <div
              v-for="(value, key) in document.analysis.structured_data"
              :key="String(key)"
              class="bg-gray-50 dark:bg-dark-hover rounded-lg p-2"
            >
              <p class="text-xs text-gray-500 dark:text-gray-400">{{ String(key).replace(/_/g, ' ') }}</p>
              <p class="text-sm font-medium text-surface-text dark:text-surface-dark-text">{{ value }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Points cles -->
      <div v-else-if="activeSection === 'findings'">
        <ul v-if="document.analysis.key_findings?.length" class="space-y-2">
          <li
            v-for="(finding, idx) in document.analysis.key_findings"
            :key="idx"
            class="flex gap-2 text-sm text-surface-text dark:text-surface-dark-text"
          >
            <span class="shrink-0 w-5 h-5 rounded-full bg-brand-green/10 text-brand-green flex items-center justify-center text-xs font-bold">
              {{ idx + 1 }}
            </span>
            <span>{{ finding }}</span>
          </li>
        </ul>
        <p v-else class="text-sm text-gray-500 dark:text-gray-400">Aucun point cle extrait</p>
      </div>

      <!-- ESG -->
      <div v-else-if="activeSection === 'esg'">
        <div v-if="esgPillars.some(p => p.items.length > 0)" class="space-y-4">
          <div v-for="pillar in esgPillars" :key="pillar.key">
            <h4 class="text-xs font-semibold uppercase mb-1.5" :class="pillar.color">
              {{ pillar.label }}
            </h4>
            <ul v-if="pillar.items.length > 0" class="space-y-1">
              <li
                v-for="(item, idx) in pillar.items"
                :key="idx"
                class="text-sm text-surface-text dark:text-surface-dark-text flex gap-2"
              >
                <span class="shrink-0">•</span>
                <span>{{ item }}</span>
              </li>
            </ul>
            <p v-else class="text-xs text-gray-400 dark:text-gray-500 italic">Aucune information</p>
          </div>
        </div>
        <p v-else class="text-sm text-gray-500 dark:text-gray-400">Aucune information ESG extraite</p>
      </div>

      <!-- Texte brut -->
      <div v-else-if="activeSection === 'raw'">
        <p class="text-xs text-gray-500 dark:text-gray-400 mb-2">Texte extrait du document</p>
        <pre class="text-xs text-surface-text dark:text-surface-dark-text whitespace-pre-wrap bg-gray-50 dark:bg-dark-hover rounded-lg p-3 max-h-72 overflow-y-auto">{{ document.analysis.summary ? '(Texte brut non disponible dans cette vue)' : '' }}</pre>
      </div>
    </div>
  </div>
</template>
