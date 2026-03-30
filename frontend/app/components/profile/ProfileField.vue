<script setup lang="ts">
const props = defineProps<{
  label: string
  field: string
  value: string | number | boolean | null
  type?: 'text' | 'number' | 'boolean' | 'select'
  options?: { value: string; label: string }[]
  placeholder?: string
}>()

const emit = defineEmits<{
  update: [field: string, value: string | number | boolean | null]
}>()

const isEditing = ref(false)
const editValue = ref<string>('')

const isFilled = computed(() => {
  if (props.value === null || props.value === undefined) return false
  if (typeof props.value === 'string' && !props.value.trim()) return false
  return true
})

const displayValue = computed(() => {
  if (!isFilled.value) return 'Non renseigné'
  if (typeof props.value === 'boolean') return props.value ? 'Oui' : 'Non'
  return String(props.value)
})

function startEdit() {
  if (props.type === 'boolean') {
    // Basculer directement pour les booléens
    const newValue = props.value === null ? true : !props.value
    emit('update', props.field, newValue)
    return
  }
  editValue.value = props.value !== null ? String(props.value) : ''
  isEditing.value = true
}

function confirmEdit() {
  isEditing.value = false
  const trimmed = editValue.value.trim()
  if (!trimmed) {
    emit('update', props.field, null)
    return
  }
  if (props.type === 'number') {
    const num = parseInt(trimmed, 10)
    emit('update', props.field, isNaN(num) ? null : num)
  } else {
    emit('update', props.field, trimmed)
  }
}

function cancelEdit() {
  isEditing.value = false
}
</script>

<template>
  <div
    class="flex items-center justify-between py-3 px-4 rounded-lg border transition-colors"
    :class="isFilled
      ? 'border-emerald-200 dark:border-emerald-800 bg-emerald-50/50 dark:bg-emerald-900/10'
      : 'border-gray-200 dark:border-dark-border bg-white dark:bg-dark-card'"
  >
    <div class="flex-1 min-w-0">
      <div class="flex items-center gap-2">
        <!-- Indicateur rempli/manquant -->
        <span
          class="w-2 h-2 rounded-full flex-shrink-0"
          :class="isFilled ? 'bg-emerald-500' : 'bg-gray-300 dark:bg-gray-600'"
        />
        <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
          {{ label }}
        </span>
      </div>

      <!-- Mode édition -->
      <div v-if="isEditing" class="mt-2 flex items-center gap-2">
        <select
          v-if="type === 'select' && options"
          v-model="editValue"
          class="flex-1 text-sm rounded-md border border-gray-300 dark:border-dark-border bg-white dark:bg-dark-input dark:text-surface-dark-text px-3 py-1.5 focus:ring-2 focus:ring-brand-green focus:border-transparent"
          @keyup.enter="confirmEdit"
        >
          <option value="">-- Choisir --</option>
          <option v-for="opt in options" :key="opt.value" :value="opt.value">
            {{ opt.label }}
          </option>
        </select>
        <input
          v-else
          v-model="editValue"
          :type="type === 'number' ? 'number' : 'text'"
          :placeholder="placeholder || label"
          class="flex-1 text-sm rounded-md border border-gray-300 dark:border-dark-border bg-white dark:bg-dark-input dark:text-surface-dark-text px-3 py-1.5 focus:ring-2 focus:ring-brand-green focus:border-transparent"
          @keyup.enter="confirmEdit"
          @keyup.escape="cancelEdit"
        />
        <button
          class="p-1.5 text-emerald-600 hover:bg-emerald-50 dark:hover:bg-emerald-900/20 rounded-md"
          @click="confirmEdit"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
          </svg>
        </button>
        <button
          class="p-1.5 text-gray-400 hover:bg-gray-100 dark:hover:bg-dark-hover rounded-md"
          @click="cancelEdit"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
          </svg>
        </button>
      </div>

      <!-- Mode affichage -->
      <p
        v-else
        class="mt-0.5 text-sm pl-4"
        :class="isFilled
          ? 'text-gray-900 dark:text-surface-dark-text'
          : 'text-gray-400 dark:text-gray-500 italic'"
      >
        {{ displayValue }}
      </p>
    </div>

    <!-- Bouton éditer -->
    <button
      v-if="!isEditing"
      class="ml-3 p-1.5 text-gray-400 hover:text-brand-green hover:bg-gray-50 dark:hover:bg-dark-hover rounded-md transition-colors flex-shrink-0"
      :title="'Modifier ' + label"
      @click="startEdit"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
        <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
      </svg>
    </button>
  </div>
</template>
