import { useAuthStore } from '~/stores/auth'

export default defineNuxtRouteMiddleware((to) => {
  const publicPages = ['/login', '/register']
  const isPublicPage = publicPages.includes(to.path)

  const authStore = useAuthStore()

  if (!isPublicPage && !authStore.isAuthenticated) {
    return navigateTo('/login')
  }

  if (isPublicPage && authStore.isAuthenticated) {
    return navigateTo('/')
  }
})
