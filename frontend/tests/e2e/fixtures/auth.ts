import type { Page } from '@playwright/test'
import type { TestUser } from './users'

/**
 * Authentifie un utilisateur sans passer par le formulaire /login.
 *
 * Strategie adoptee : injection directe des tokens dans localStorage via
 * `page.addInitScript` AVANT tout `page.goto`. Le middleware global `auth.global.ts`
 * charge les tokens depuis localStorage au premier render (store.loadFromStorage)
 * et considere alors l'utilisateur authentifie.
 *
 * Pourquoi pas un login UI reel ?
 * - Rapide (<100 ms) vs ~2 s pour un login UI avec redirections + fetchUser()
 * - Aucun JWT reel requis — tous les endpoints auth sont mockes (cf mock-backend.ts)
 * - Deterministe — aucune depedance aux animations du formulaire ni au rate-limiting
 *
 * Important : `installMockBackend` DOIT avoir ete appele avant `loginAs` pour que
 * la route `GET /api/auth/me` renvoie l'utilisateur — sans quoi le dashboard
 * affichera des erreurs 404.
 */
export async function loginAs(page: Page, user: TestUser): Promise<void> {
  await page.addInitScript(
    ({ accessToken, refreshToken }) => {
      // ExecuteInPageContext : s'execute avant tout script de l'app.
      // Reset complet du storage pour garantir l'isolation entre tests (workers=1).
      window.localStorage.clear()
      window.localStorage.setItem('access_token', accessToken)
      window.localStorage.setItem('refresh_token', refreshToken)
    },
    { accessToken: user.fakeAccessToken, refreshToken: user.fakeRefreshToken },
  )
}
