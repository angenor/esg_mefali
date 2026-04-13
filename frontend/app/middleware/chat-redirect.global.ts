// Redirige /chat vers / et ouvre le widget flottant
export default defineNuxtRouteMiddleware((to) => {
  if (to.path === '/chat' || to.path === '/chat/') {
    return navigateTo({ path: '/', query: { openChat: '1' } }, { replace: true })
  }
})
