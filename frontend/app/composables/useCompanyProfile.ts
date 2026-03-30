import { ref } from 'vue'
import type { CompanyProfile, CompletionResponse } from '~/types/company'
import { useAuthStore } from '~/stores/auth'
import { useCompanyStore } from '~/stores/company'

export function useCompanyProfile() {
  const config = useRuntimeConfig()
  const authStore = useAuthStore()
  const companyStore = useCompanyStore()
  const apiBase = config.public.apiBase

  const loading = ref(false)
  const error = ref('')

  function getHeaders(): Record<string, string> {
    return {
      'Content-Type': 'application/json',
      ...(authStore.accessToken
        ? { Authorization: `Bearer ${authStore.accessToken}` }
        : {}),
    }
  }

  async function fetchProfile(): Promise<CompanyProfile | null> {
    loading.value = true
    error.value = ''
    try {
      const response = await fetch(`${apiBase}/company/profile`, {
        headers: getHeaders(),
      })
      if (!response.ok) {
        throw new Error('Erreur lors du chargement du profil')
      }
      const data: CompanyProfile = await response.json()
      companyStore.setProfile(data)
      return data
    } catch (e) {
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
      const response = await fetch(`${apiBase}/company/profile`, {
        method: 'PATCH',
        headers: getHeaders(),
        body: JSON.stringify(updates),
      })
      if (!response.ok) {
        if (response.status === 422) {
          error.value = 'Données invalides. Veuillez vérifier les champs.'
          return null
        }
        throw new Error('Erreur lors de la mise à jour du profil')
      }
      const data: CompanyProfile = await response.json()
      companyStore.setProfile(data)
      // Rafraîchir la complétion après mise à jour
      await fetchCompletion()
      return data
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Erreur inconnue'
      return null
    } finally {
      loading.value = false
    }
  }

  async function fetchCompletion(): Promise<CompletionResponse | null> {
    try {
      const response = await fetch(`${apiBase}/company/profile/completion`, {
        headers: getHeaders(),
      })
      if (!response.ok) return null
      const data: CompletionResponse = await response.json()
      companyStore.setCompletion(data)
      return data
    } catch {
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
