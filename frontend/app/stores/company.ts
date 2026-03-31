import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { CompanyProfile, CompletionResponse, ProfileUpdateEvent } from '~/types/company'

export const useCompanyStore = defineStore('company', () => {
  const profile = ref<CompanyProfile | null>(null)
  const completion = ref<CompletionResponse | null>(null)
  const recentUpdates = ref<ProfileUpdateEvent[]>([])

  const overallCompletion = computed(() => completion.value?.overall_completion ?? 0)

  function setProfile(data: CompanyProfile) {
    profile.value = data
  }

  function setCompletion(data: CompletionResponse) {
    completion.value = data
  }

  function addProfileUpdate(update: ProfileUpdateEvent) {
    recentUpdates.value = [...recentUpdates.value, update]
  }

  function clearRecentUpdates() {
    recentUpdates.value = []
  }

  function updateProfileField(field: string, value: unknown) {
    if (profile.value) {
      profile.value = { ...profile.value, [field]: value }
    }
  }

  function reset() {
    profile.value = null
    completion.value = null
    recentUpdates.value = []
  }

  return {
    profile,
    completion,
    recentUpdates,
    overallCompletion,
    setProfile,
    setCompletion,
    addProfileUpdate,
    clearRecentUpdates,
    updateProfileField,
    reset,
  }
})
