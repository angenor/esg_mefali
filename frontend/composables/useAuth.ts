import type { TokenResponse, User, ApiError } from '~/types'
import { useAuthStore } from '~/stores/auth'

export function useAuth() {
  const config = useRuntimeConfig()
  const authStore = useAuthStore()
  const router = useRouter()

  const apiBase = config.public.apiBase

  async function apiFetch<T>(url: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...((options.headers as Record<string, string>) || {}),
    }
    if (authStore.accessToken) {
      headers['Authorization'] = `Bearer ${authStore.accessToken}`
    }

    const response = await fetch(`${apiBase}${url}`, {
      ...options,
      headers,
    })

    if (!response.ok) {
      const error: ApiError = await response.json().catch(() => ({ detail: 'Erreur inconnue' }))
      throw new Error(error.detail || `Erreur ${response.status}`)
    }

    return response.json() as Promise<T>
  }

  async function register(data: {
    email: string
    password: string
    full_name: string
    company_name: string
  }): Promise<User> {
    return apiFetch<User>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async function login(email: string, password: string): Promise<void> {
    const tokens = await apiFetch<TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
    authStore.setTokens(tokens)
    await fetchUser()
  }

  async function fetchUser(): Promise<void> {
    const user = await apiFetch<User>('/auth/me')
    authStore.setUser(user)
  }

  async function refresh(): Promise<boolean> {
    if (!authStore.refreshToken) return false

    try {
      const tokens = await apiFetch<TokenResponse>('/auth/refresh', {
        method: 'POST',
        body: JSON.stringify({ refresh_token: authStore.refreshToken }),
      })
      authStore.setTokens(tokens)
      return true
    } catch {
      authStore.clearAuth()
      return false
    }
  }

  function logout(): void {
    authStore.clearAuth()
    router.push('/login')
  }

  return {
    register,
    login,
    fetchUser,
    refresh,
    logout,
    isAuthenticated: authStore.isAuthenticated,
  }
}
