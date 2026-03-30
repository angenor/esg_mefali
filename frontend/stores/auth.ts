import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, TokenResponse } from '~/types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const accessToken = ref<string | null>(null)
  const refreshToken = ref<string | null>(null)

  const isAuthenticated = computed(() => !!accessToken.value)

  function setTokens(tokens: TokenResponse) {
    accessToken.value = tokens.access_token
    if (tokens.refresh_token) {
      refreshToken.value = tokens.refresh_token
    }
    // Persister dans localStorage
    if (import.meta.client) {
      localStorage.setItem('access_token', tokens.access_token)
      if (tokens.refresh_token) {
        localStorage.setItem('refresh_token', tokens.refresh_token)
      }
    }
  }

  function setUser(userData: User) {
    user.value = userData
  }

  function clearAuth() {
    user.value = null
    accessToken.value = null
    refreshToken.value = null
    if (import.meta.client) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    }
  }

  function loadFromStorage() {
    if (import.meta.client) {
      accessToken.value = localStorage.getItem('access_token')
      refreshToken.value = localStorage.getItem('refresh_token')
    }
  }

  return {
    user,
    accessToken,
    refreshToken,
    isAuthenticated,
    setTokens,
    setUser,
    clearAuth,
    loadFromStorage,
  }
})
