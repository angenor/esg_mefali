// Simuler import.meta.client / import.meta.server de Nuxt
// pour que les guards dans les stores fonctionnent en environnement de test
;(import.meta as Record<string, unknown>).client = true
;(import.meta as Record<string, unknown>).server = false
