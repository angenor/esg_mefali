import { test, expect } from '@playwright/test'
import { loginAs } from './fixtures/auth'
import { installMockBackend } from './fixtures/mock-backend'
import { FATOU, FATOU_COMPANY, FATOU_CARBON_SUMMARY } from './fixtures/users'

/**
 * Parcours Fatou — guidage propose et accepte (multi-pages).
 *
 * Scenario (PRD epic 8) :
 *   1. Fatou atterrit sur /dashboard (logged in via localStorage).
 *   2. Elle ouvre le widget flottant et envoie un message.
 *   3. L'assistant propose un guidage via widget QCU de consentement.
 *   4. Elle accepte → widget se retracte (scale=0.3) + bouton devient disabled.
 *   5. Le popover Driver.js pointe le lien sidebar carbone avec decompteur 8s.
 *   6. Elle clique le lien AVANT expiration → navigation /carbon/results.
 *   7. Le parcours reprend automatiquement sur les 3 popovers (donut, benchmark, plan).
 *   8. A la completion, widget redevient actif et le bouton flottant est re-enable.
 */
test.describe('Parcours Fatou — guidage propose et accepte (multi-pages)', () => {
  test.beforeEach(async ({ page }) => {
    // 1. Mock backend (routes /api/**). reduced-motion est configure au niveau
    //    `use.reducedMotion` dans playwright.config.ts — pas besoin d'emulateMedia ici.
    await installMockBackend(page, {
      user: FATOU,
      companyProfile: FATOU_COMPANY,
      carbonData: FATOU_CARBON_SUMMARY,
      chatScenario: 'propose_guided_tour_after_carbon',
    })

    // 2. Auth programmatique : tokens dans localStorage avant tout goto
    await loginAs(page, FATOU)

    // 3. Arrivee sur le dashboard (scene d'ouverture PRD) — on attend le
    //    selecteur du bouton flottant plutot que `networkidle` (flaky + masque
    //    les vraies regressions de streaming SSE).
    await page.goto('/dashboard')
    await page.getByTestId('floating-chat-button').waitFor({ state: 'visible' })
  })

  test('Fatou accepte le guidage propose apres un message, navigue vers /carbon/results et parcourt les popovers jusqu\'a la fin', async ({ page }) => {
    // ── AC1 : etat initial sur /dashboard ─────────────────────────────
    await expect(page.getByTestId('floating-chat-button')).toBeVisible()
    await expect(page.locator('#copilot-widget')).toBeHidden()
    await expect(page.locator('.driver-active')).toHaveCount(0)

    // ── AC2 : ouverture du widget + envoi message + consentement QCU ──
    await page.getByTestId('floating-chat-button').click()
    await expect(page.locator('#copilot-widget')).toBeVisible()

    await page.getByTestId('chat-textarea').fill(
      'Montre-moi mes resultats carbone s\'il te plait',
    )
    await page.getByTestId('chat-send-button').click()

    // La proposition de consentement arrive via SSE
    await expect(
      page.getByText(/Voulez-vous voir vos resultats carbone/i),
    ).toBeVisible({ timeout: 10_000 })

    // Les deux boutons de choix sont rendus par SingleChoiceWidget
    const choiceYes = page.getByTestId('interactive-choice-yes')
    const choiceNo = page.getByTestId('interactive-choice-no')
    await expect(choiceYes).toBeVisible()
    await expect(choiceNo).toBeVisible()

    // ── AC3 : acceptation + retraction + popover entry-step ──────────
    await choiceYes.click()

    // Apres submission, les deux boutons de choix doivent etre desactives
    // (pas de double-submit possible → garde-fou contre une regression qui
    // re-enablerait le widget resolu).
    await expect(choiceYes).toBeDisabled({ timeout: 5_000 })
    await expect(choiceNo).toBeDisabled()

    // Le bouton flottant passe en disabled (uiStore.guidedTourActive = true)
    await expect(page.getByTestId('floating-chat-button')).toHaveClass(
      /cursor-not-allowed/,
      { timeout: 5_000 },
    )
    // Le widget est retracte visuellement (scale=0.3 + aria-hidden='true')
    // — garantit que la retraction a bien joue et que les lecteurs d'ecran
    // n'interagissent plus avec son contenu pendant le tour.
    await expect(page.locator('#copilot-widget')).toHaveAttribute(
      'aria-hidden',
      'true',
      { timeout: 5_000 },
    )

    // Le popover Driver.js apparait sur le lien sidebar carbone
    // (waitForElement peut retarder selon loadDriver — timeout large)
    await expect(page.locator('.driver-popover')).toHaveCount(1, { timeout: 10_000 })
    await expect(
      page.getByRole('heading', { name: /R.sultats.*Empreinte Carbone/i }),
    ).toBeVisible()
    // Decompteur visible (valeur entre 1 et 8)
    await expect(page.getByTestId('countdown-badge')).toBeVisible()
    await expect(page.getByTestId('countdown-badge')).toContainText(/[1-8]s/)

    // ── AC4 : clic sidebar + navigation + reprise du parcours ────────
    // `force: true` contourne l'overlay Driver.js qui peut intercepter les
    // clics selon le timing d'arrivee du popover.
    await page
      .locator('[data-guide-target="sidebar-carbon-link"]')
      .click({ force: true })
    await page.waitForURL('**/carbon/results', { timeout: 10_000 })

    // Attendre que la page ait charge et que Driver.js pointe le donut
    await expect(
      page.locator('[data-guide-target="carbon-donut-chart"]'),
    ).toBeVisible({ timeout: 15_000 })

    // Le popover Driver.js interpole les donnees carbone
    const donutPopover = page.locator('.driver-popover').first()
    await expect(donutPopover).toContainText(/47[.,]2\s*tCO2e/i, {
      timeout: 10_000,
    })
    await expect(donutPopover).toContainText(/transport/i)
    // `62\s*%` — assertion stricte sur le pourcentage (evite un match sur un
    // numero de version, un percentile affichte ailleurs, etc.).
    await expect(donutPopover).toContainText(/62\s*%/)

    // ── AC5 : progression sur les 3 popovers ────────────────────────
    // Step 1 (donut) → Step 2 (benchmark)
    await page.getByTestId('popover-next-btn').click()
    await expect(
      page.locator('[data-guide-target="carbon-benchmark"]'),
    ).toBeVisible({ timeout: 10_000 })
    const benchmarkPopover = page.locator('.driver-popover').first()
    await expect(benchmarkPopover).toContainText(/Comparaison sectorielle/i)
    await expect(benchmarkPopover).toContainText(/agroalimentaire/i)

    // Step 2 (benchmark) → Step 3 (reduction plan)
    await page.getByTestId('popover-next-btn').click()
    await expect(
      page.locator('[data-guide-target="carbon-reduction-plan"]'),
    ).toBeVisible({ timeout: 10_000 })
    await expect(page.locator('.driver-popover').first()).toContainText(
      /Plan de r.duction/i,
    )

    // Step 3 (reduction plan) → completion
    await page.getByTestId('popover-next-btn').click()

    // Tous les popovers ont disparu
    await expect(page.locator('.driver-popover')).toHaveCount(0, {
      timeout: 10_000,
    })

    // Le bouton flottant n'est plus disabled
    await expect(page.getByTestId('floating-chat-button')).toBeVisible()
    await expect(page.getByTestId('floating-chat-button')).not.toHaveClass(
      /cursor-not-allowed/,
      { timeout: 5_000 },
    )

    // ── AC6 : chat fonctionnel apres completion ──────────────────────
    // Le widget etait minimized pendant le tour (pas ferme) — apres completion
    // le watcher chatWidgetMinimized=false lance expandWidget() qui restaure scale=1.
    // Il est donc deja visible, pas besoin de recliquer le bouton flottant.
    await expect(page.locator('#copilot-widget')).toBeVisible()
    // L'historique de la conversation est preserve (message de consentement precedent)
    await expect(page.locator('#copilot-widget')).toContainText(
      /Voulez-vous voir vos resultats carbone/i,
    )
    // L'input texte est disponible pour saisir un nouveau message
    await expect(page.getByTestId('chat-textarea')).toBeEnabled()
  })
})
