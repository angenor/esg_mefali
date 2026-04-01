<script setup lang="ts">
import type { ActionItem, ReminderType } from '~/types/actionPlan'

interface Props {
  show: boolean
  actionItem?: ActionItem | null
}

const props = withDefaults(defineProps<Props>(), {
  actionItem: null,
})

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'submit', data: { action_item_id: string | null; type: ReminderType; message: string; scheduled_at: string }): void
}>()

const reminderType = ref<ReminderType>('action_due')
const message = ref('')
const scheduledDate = ref('')
const scheduledTime = ref('09:00')

const typeOptions: Array<{ value: ReminderType; label: string }> = [
  { value: 'action_due', label: 'Échéance d\'action' },
  { value: 'assessment_renewal', label: 'Renouvellement évaluation' },
  { value: 'fund_deadline', label: 'Date limite fonds' },
  { value: 'intermediary_followup', label: 'Relance intermédiaire' },
  { value: 'custom', label: 'Personnalisé' },
]

// Pré-remplir si une action est liée
watch(
  () => props.actionItem,
  (item) => {
    if (item) {
      message.value = `Rappel : ${item.title}`
      if (item.category === 'intermediary_contact') {
        reminderType.value = 'intermediary_followup'
      }
      if (item.due_date) {
        scheduledDate.value = item.due_date
      }
    }
  },
  { immediate: true }
)

function onSubmit() {
  if (!scheduledDate.value || !message.value) return

  const scheduled_at = new Date(`${scheduledDate.value}T${scheduledTime.value}:00`).toISOString()
  emit('submit', {
    action_item_id: props.actionItem?.id ?? null,
    type: reminderType.value,
    message: message.value,
    scheduled_at,
  })
}

// Date minimale : demain
const minDate = computed(() => {
  const tomorrow = new Date()
  tomorrow.setDate(tomorrow.getDate() + 1)
  return tomorrow.toISOString().split('T')[0]
})
</script>

<template>
  <Teleport to="body">
    <div
      v-if="show"
      class="fixed inset-0 z-50 flex items-center justify-center p-4"
      @click.self="emit('close')"
    >
      <div class="absolute inset-0 bg-black/50" />

      <div class="relative bg-white dark:bg-dark-card rounded-xl shadow-xl border border-gray-200 dark:border-dark-border max-w-md w-full">
        <div class="flex items-center justify-between p-5 border-b border-gray-200 dark:border-dark-border">
          <h3 class="text-lg font-semibold text-surface-text dark:text-surface-dark-text">
            Créer un rappel
          </h3>
          <button
            class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            @click="emit('close')"
          >
            ✕
          </button>
        </div>

        <form class="p-5 space-y-4" @submit.prevent="onSubmit">
          <!-- Type -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Type</label>
            <select
              v-model="reminderType"
              class="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-input text-surface-text dark:text-surface-dark-text text-sm"
            >
              <option v-for="opt in typeOptions" :key="opt.value" :value="opt.value">
                {{ opt.label }}
              </option>
            </select>
          </div>

          <!-- Message -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Message</label>
            <textarea
              v-model="message"
              rows="2"
              maxlength="500"
              required
              class="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-input text-surface-text dark:text-surface-dark-text text-sm resize-none"
              placeholder="Rappel : ..."
            />
          </div>

          <!-- Date et heure -->
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Date</label>
              <input
                v-model="scheduledDate"
                type="date"
                :min="minDate"
                required
                class="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-input text-surface-text dark:text-surface-dark-text text-sm"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Heure</label>
              <input
                v-model="scheduledTime"
                type="time"
                required
                class="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-input text-surface-text dark:text-surface-dark-text text-sm"
              />
            </div>
          </div>

          <!-- Boutons -->
          <div class="flex justify-end gap-2 pt-2">
            <button
              type="button"
              class="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-dark-hover rounded-lg"
              @click="emit('close')"
            >
              Annuler
            </button>
            <button
              type="submit"
              class="px-4 py-2 text-sm font-medium bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
            >
              Créer le rappel
            </button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>
</template>
