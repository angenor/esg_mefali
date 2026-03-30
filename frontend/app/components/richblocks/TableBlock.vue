<script setup lang="ts">
import type { TableBlockData } from '~/types/richblocks'

const props = defineProps<{
  rawContent: string
}>()

const parseError = ref('')
const tableData = ref<TableBlockData | null>(null)
const sortColumn = ref<number | null>(null)
const sortAsc = ref(true)

try {
  const parsed = JSON.parse(props.rawContent) as TableBlockData
  if (!parsed.headers || !parsed.rows) {
    parseError.value = 'Données de tableau incomplètes (headers et rows requis)'
  } else {
    tableData.value = parsed
  }
} catch {
  parseError.value = 'JSON invalide pour le tableau'
}

const sortedRows = computed(() => {
  if (!tableData.value) return []
  const rows = [...tableData.value.rows]
  if (sortColumn.value !== null && tableData.value.sortable) {
    const col = sortColumn.value
    rows.sort((a, b) => {
      const valA = a[col]
      const valB = b[col]
      if (typeof valA === 'number' && typeof valB === 'number') {
        return sortAsc.value ? valA - valB : valB - valA
      }
      const strA = String(valA)
      const strB = String(valB)
      return sortAsc.value ? strA.localeCompare(strB) : strB.localeCompare(strA)
    })
  }
  return rows
})

function toggleSort(index: number) {
  if (!tableData.value?.sortable) return
  if (sortColumn.value === index) {
    sortAsc.value = !sortAsc.value
  } else {
    sortColumn.value = index
    sortAsc.value = true
  }
}
</script>

<template>
  <div v-if="parseError">
    <BlockError :raw-content="rawContent" :error-message="parseError" />
  </div>
  <div v-else-if="tableData" class="my-3 overflow-x-auto rounded-lg border border-gray-200 dark:border-dark-border">
    <table class="w-full text-sm">
      <thead>
        <tr class="bg-gray-50 dark:bg-dark-card">
          <th
            v-for="(header, idx) in tableData.headers"
            :key="idx"
            class="px-4 py-2.5 text-left font-medium text-surface-text dark:text-surface-dark-text border-b border-gray-200 dark:border-dark-border"
            :class="[
              tableData.sortable ? 'cursor-pointer hover:bg-gray-100 dark:hover:bg-dark-hover select-none' : '',
              tableData.highlightColumn === idx ? 'bg-brand-green/10 dark:bg-brand-green/20' : '',
            ]"
            @click="toggleSort(idx)"
          >
            <span class="flex items-center gap-1">
              {{ header }}
              <span v-if="tableData.sortable && sortColumn === idx" class="text-brand-green">
                {{ sortAsc ? '▲' : '▼' }}
              </span>
            </span>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(row, rowIdx) in sortedRows"
          :key="rowIdx"
          class="border-b border-gray-100 dark:border-dark-border last:border-0 hover:bg-gray-50 dark:hover:bg-dark-hover transition-colors"
        >
          <td
            v-for="(cell, cellIdx) in row"
            :key="cellIdx"
            class="px-4 py-2 text-surface-text dark:text-surface-dark-text"
            :class="tableData.highlightColumn === cellIdx ? 'bg-brand-green/10 dark:bg-brand-green/20 font-medium' : ''"
          >
            {{ cell }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
