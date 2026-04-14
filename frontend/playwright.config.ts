import { defineConfig, devices } from '@playwright/test'

/**
 * Configuration Playwright pour les tests E2E de l'epic 8.
 * Story 8.1 — premiere instanciation de l'infrastructure E2E.
 *
 * Choix de design :
 * - workers=1 + fullyParallel=false : serialise les tests pour stabiliser les scenarios
 *   SSE et les overlays Driver.js qui manipulent le DOM global.
 * - reducedMotion: 'reduce' applique au niveau `use` (global) pour supprimer la variabilite
 *   des animations GSAP (retraction widget, entry popover, etc.) sans que chaque spec
 *   n'ait a l'activer dans un beforeEach.
 * - webServer : lance Nuxt en dev ; le backend est integralement mocke via page.route()
 *   dans fixtures/mock-backend.ts (aucune dependance Postgres/Redis/OpenRouter).
 */
// Port dedie pour les tests E2E afin d'eviter les conflits avec un dev server
// Nuxt tournant deja en local (le port 3000 peut etre occupe par un autre projet).
const E2E_PORT = Number(process.env.PLAYWRIGHT_PORT ?? 4321)
const E2E_BASE_URL = process.env.PLAYWRIGHT_BASE_URL ?? `http://localhost:${E2E_PORT}`

export default defineConfig({
  testDir: './tests/e2e',
  testMatch: /.*\.spec\.ts$/,
  // `PLAYWRIGHT_SLOWMO` rallonge chaque action → on augmente le timeout global
  // si slowMo est actif pour eviter les faux echecs.
  timeout: Number(process.env.PLAYWRIGHT_SLOWMO ?? 0) > 0 ? 120_000 : 30_000,
  expect: { timeout: Number(process.env.PLAYWRIGHT_SLOWMO ?? 0) > 0 ? 15_000 : 5_000 },
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: process.env.CI ? 'github' : [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: E2E_BASE_URL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    viewport: { width: 1280, height: 800 },
    // `PLAYWRIGHT_FULL_MOTION=1` desactive reducedMotion pour observer les
    // animations GSAP en dev/debug. Par defaut reduit (determinisme).
    reducedMotion: process.env.PLAYWRIGHT_FULL_MOTION === '1' ? undefined : 'reduce',
    // `PLAYWRIGHT_SLOWMO=<ms>` ralentit chaque action Playwright pour
    // observation visuelle. 0 = vitesse normale.
    launchOptions: {
      slowMo: Number(process.env.PLAYWRIGHT_SLOWMO ?? 0),
    },
  },
  projects: [
    {
      name: 'chromium-desktop',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: `npm run dev -- --port ${E2E_PORT}`,
    url: E2E_BASE_URL,
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
    stdout: 'pipe',
    stderr: 'pipe',
  },
})
