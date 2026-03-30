import { useAuthStore } from '~/stores/auth'

export default defineNuxtRouteMiddleware((to) => {
  // Pages publiques accessibles sans authentification
  const publicPages = ['/login', '/register']
  const isPublicPage = publicPages.includes(to.path)

  const authStore = useAuthStore()

  // Charger les tokens depuis localStorage au premier chargement
  if (import.meta.client && !authStore.accessToken) {
    authStore.loadFromStorage()
  }

  if (!isPublicPage && !authStore.isAuthenticated) {
    return navigateTo('/login')
  }

  // Rediriger les utilisateurs connectés qui tentent d'accéder au login/register
  if (isPublicPage && authStore.isAuthenticated) {
    return navigateTo('/')
  }
})
