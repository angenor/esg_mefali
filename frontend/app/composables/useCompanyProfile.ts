import { ref } from 'vue'
import type { CompanyProfile, CompletionResponse } from '~/types/company'
import { useAuth, SessionExpiredError, ApiFetchError } from '~/composables/useAuth'
import { useCompanyStore } from '~/stores/company'

export function useCompanyProfile() {
  const { apiFetch, handleAuthFailure } = useAuth()
  const companyStore = useCompanyStore()

  const loading = ref(false)
  const error = ref('')

  async function fetchProfile(): Promise<CompanyProfile | null> {
    loading.value = true
    error.value = ''
    try {
      const data = await apiFetch<CompanyProfile>('/company/profile')
      companyStore.setProfile(data)
      return data
    } catch (e) {
      if (e instanceof SessionExpiredError) {
        await handleAuthFailure()
        return null
      }
      error.value = e instanceof Error ? e.message : 'Erreur inconnue'
      return null
    } finally {
      loading.value = false
    }
  }

  async function updateProfile(updates: Partial<CompanyProfile>): Promise<CompanyProfile | null> {
    loading.value = true
    error.value = ''
    try {
      const data = await apiFetch<CompanyProfile>('/company/profile', {
        method: 'PATCH',
        body: JSON.stringify(updates),
      })
      companyStore.setProfile(data)
      await fetchCompletion()
      return data
    } catch (e) {
      if (e instanceof SessionExpiredError) {
        await handleAuthFailure()
        return null
      }
      if (e instanceof ApiFetchError && e.status === 422) {
        error.value = 'Données invalides. Veuillez vérifier les champs.'
        return null
      }
      error.value = e instanceof Error ? e.message : 'Erreur inconnue'
      return null
    } finally {
      loading.value = false
    }
  }

  async function fetchCompletion(): Promise<CompletionResponse | null> {
    try {
      const data = await apiFetch<CompletionResponse>('/company/profile/completion')
      companyStore.setCompletion(data)
      return data
    } catch (e) {
      if (e instanceof SessionExpiredError) {
        await handleAuthFailure()
      }
      return null
    }
  }

  return {
    loading,
    error,
    fetchProfile,
    updateProfile,
    fetchCompletion,
  }
}
