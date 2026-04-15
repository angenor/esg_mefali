import { expect, test, type Page } from '@playwright/test'
import { loginAs } from './fixtures/auth'
import { installMockBackend } from './fixtures/mock-backend'
import {
  MOUSSA,
  MOUSSA_COMPANY,
  MOUSSA_FINANCING_MATCHES,
  MOUSSA_FUNDS,
} from './fixtures/users'

/**
 * Parcours Moussa — guidage refuse, chat contextuel sur /financing.
 *
 * Scenario (PRD epic 8, story 8.2) :
 *   1. Moussa atterrit directement sur /financing (logged in via localStorage).
 *   2. Il ouvre le widget flottant et pose une question sur les fonds.
 *   3. L'assistant repond de maniere CONTEXTUELLE (cite les fonds + la page)
 *      puis propose un guidage via widget QCU de consentement.
 *   4. Moussa refuse → les boutons sont disabled, aucun Driver.js ne demarre,
 *      un message d'accuse reception s'affiche.
 *   5. Le widget reste ouvert, en superposition glassmorphism sur la page
 *      /financing qui reste visible derriere.
 *
 * Observation visuelle ralentie :
 *   PLAYWRIGHT_SLOWMO=800 PLAYWRIGHT_FULL_MOTION=1 \
 *     npm run test:e2e -- --headed 8-2-parcours-moussa
 */

/**
 * Helper local — enchaine les etapes communes jusqu'a l'affichage du widget
 * de consentement (AC3). Factorise pour eviter la duplication entre les
 * tests AC4 (refus) et AC5 (glassmorphism) sans creer un 4e test.
 */
async function setupUntilConsent(page: Page): Promise<void> {
  // Etat initial : le widget est cache par v-show (chatWidgetOpen=false).
  // Note dev : le AC3 step 2 du story mentionnait aria-hidden="true", mais le
  // comportement reel repose sur v-show → toBeHidden() (pattern story 8.1).
  await expect(page.getByTestId('floating-chat-button')).toBeVisible()
  await expect(page.locator('#copilot-widget')).toBeHidden()
  await expect(
    page.locator('[data-guide-target="financing-fund-list"]'),
  ).toBeVisible()

  // Ouverture du widget
  await page.getByTestId('floating-chat-button').click()
  await expect(page.locator('#copilot-widget')).toBeVisible()

  // Question contextuelle
  await page.getByTestId('chat-textarea').fill(
    'Quels fonds sont compatibles avec mon profil cooperative cacao ?',
  )
  await page.getByTestId('chat-send-button').click()

  // Reponse contextuelle (regex tolerante — cf. story 8.2 AC3 step 8)
  await expect(page.locator('#copilot-widget')).toContainText(
    /fonds|financement|catalogue/i,
    { timeout: 10_000 },
  )
  await expect(page.getByTestId('interactive-choice-yes')).toBeVisible({
    timeout: 10_000,
  })
  await expect(page.getByTestId('interactive-choice-no')).toBeVisible()
}

test.describe('Parcours Moussa — guidage refuse, chat contextuel sur /financing', () => {
  test.beforeEach(async ({ page }) => {
    // 1. Mock backend (routes /api/**). Reuse story 8.1 + extensions 8.2.
    await installMockBackend(page, {
      user: MOUSSA,
      companyProfile: MOUSSA_COMPANY,
      financingData: {
        matches: MOUSSA_FINANCING_MATCHES,
        funds: MOUSSA_FUNDS,
      },
      chatScenario: 'propose_guided_tour_after_financing_question',
    })

    // 2. Auth programmatique (tokens en localStorage avant tout goto).
    await loginAs(page, MOUSSA)

    // 3. Atterrissage direct sur /financing (Moussa connait l'app, il zappe
    //    le dashboard). On attend le bouton flottant pour garantir que la
    //    page est hydratee avant les interactions.
    await page.goto('/financing')
    await page.getByTestId('floating-chat-button').waitFor({ state: 'visible' })
  })

  /**
   * AC3 — Moussa arrive sur /financing, ouvre le widget et recoit une reponse
   * contextuelle adaptee a la page (mention financement + noms de fonds).
   */
  test('Moussa recoit une reponse contextuelle sur /financing et voit le widget de consentement', async ({
    page,
  }) => {
    // Etat initial : bouton flottant visible, widget cache (v-show), page chargee
    await expect(page.getByTestId('floating-chat-button')).toBeVisible()
    await expect(page.locator('#copilot-widget')).toBeHidden()
    await expect(
      page.locator('[data-guide-target="financing-fund-list"]'),
    ).toBeVisible()

    // Ouverture du widget
    await page.getByTestId('floating-chat-button').click()
    await expect(page.locator('#copilot-widget')).toBeVisible()

    // Envoi de la question contextuelle
    await page.getByTestId('chat-textarea').fill(
      'Quels fonds sont compatibles avec mon profil cooperative cacao ?',
    )
    await page.getByTestId('chat-send-button').click()

    // Reponse contextuelle (regex tolerante — cf. story 8.2 AC3 step 8)
    await expect(page.locator('#copilot-widget')).toContainText(
      /fonds|financement|catalogue/i,
      { timeout: 10_000 },
    )
    await expect(page.locator('#copilot-widget')).toContainText(
      /4\s*fonds|GCF|BOAD|SUNREF/i,
    )

    // Widget interactif de consentement affiche
    await expect(page.getByTestId('interactive-choice-yes')).toBeVisible({
      timeout: 10_000,
    })
    await expect(page.getByTestId('interactive-choice-no')).toBeVisible()

    // Aucune erreur affichee (role=alert doit etre absent)
    await expect(page.locator('[role="alert"]')).toHaveCount(0)
  })

  /**
   * AC4 — Moussa refuse le guidage. Les boutons se desactivent, aucun
   * Driver.js ne demarre, le chat reste fonctionnel, un accuse reception
   * s'affiche dans l'historique.
   */
  test('Moussa refuse, aucun Driver.js ne demarre, le chat reste fonctionnel', async ({
    page,
  }) => {
    await setupUntilConsent(page)

    const choiceYes = page.getByTestId('interactive-choice-yes')
    const choiceNo = page.getByTestId('interactive-choice-no')

    // Clic sur « Non merci »
    await choiceNo.click()

    // Les deux boutons sont desactives immediatement (pattern 8.1 patch review)
    await expect(choiceYes).toBeDisabled({ timeout: 5_000 })
    await expect(choiceNo).toBeDisabled()

    // Courte attente deterministe — on cherche a DETECTER un declenchement
    // errone de Driver.js (toHaveCount(0) retourne tot si deja 0). Seule
    // exception autorisee a la regle anti-waitForTimeout (cf. AC4 step 3).
    await page.waitForTimeout(500)

    // Aucun popover Driver.js
    await expect(page.locator('.driver-popover')).toHaveCount(0)
    await expect(
      page.locator('.driver-overlay, .driver-highlight, .driver-active-element'),
    ).toHaveCount(0)

    // Le widget reste visible et non retracte
    await expect(page.locator('#copilot-widget')).toBeVisible()
    await expect(page.locator('#copilot-widget')).toHaveAttribute(
      'aria-hidden',
      'false',
    )

    // Le bouton flottant n'est PAS en mode disabled
    await expect(page.getByTestId('floating-chat-button')).not.toHaveClass(
      /cursor-not-allowed|opacity-60/,
    )

    // Le chat est fonctionnel : input enabled + bouton send enabled
    await expect(page.getByTestId('chat-textarea')).toBeEnabled()
    await page.getByTestId('chat-textarea').fill(
      'Montre-moi juste le fond GCF Agriculture',
    )
    await expect(page.getByTestId('chat-send-button')).toBeEnabled()

    // Accuse reception du refus dans l'historique
    await expect(page.locator('#copilot-widget')).toContainText(
      /(disposition|pas de souci|d'accord|compris)/i,
    )
  })

  /**
   * AC5 — Glassmorphism : le widget est en superposition, la page /financing
   * reste visible derriere, les donnees financieres sont floutees (ou fallback
   * opaque sur navigateur sans backdrop-filter).
   */
  test('Glassmorphism — widget en superposition, page /financing visible derriere, donnees floutees', async ({
    page,
  }) => {
    await setupUntilConsent(page)

    const widget = page.locator('#copilot-widget')

    // 5.1 — CSS computed : classe .widget-glass appliquee
    await expect(widget).toHaveClass(/widget-glass/)

    // backdrop-filter actif avec blur >= 20px, OU fallback opaque
    const filter = await widget.evaluate((el) => {
      const cs = getComputedStyle(el)
      return cs.backdropFilter || (cs as unknown as { webkitBackdropFilter: string }).webkitBackdropFilter || ''
    })

    if (filter.includes('blur(')) {
      const match = filter.match(/blur\((\d+(?:\.\d+)?)px\)/)
      expect(match).not.toBeNull()
      const blurPx = Number(match?.[1] ?? 0)
      // On exige >= 20px pour que les donnees financieres derriere soient
      // illisibles a l'oeil humain (config projet = 24px, cf. FloatingChatWidget.vue:644).
      expect(blurPx).toBeGreaterThanOrEqual(20)
    } else {
      // Pas de backdrop-filter → fallback opaque doit etre actif
      const bg = await widget.evaluate((el) => getComputedStyle(el).backgroundColor)
      // Rejeter toute transparence (rgba(_, _, _, <1)) — on veut un fond plein
      expect(bg).not.toMatch(/rgba\([^)]*,\s*0?\.\d+\)$/)
      expect(bg).not.toBe('rgba(0, 0, 0, 0)')
      expect(bg).not.toBe('transparent')
    }

    // 5.2 — Contenu /financing visible derriere le widget
    await expect(
      page.locator('[data-guide-target="financing-fund-list"]'),
    ).toBeAttached()
    await expect(
      page.locator('[data-guide-target="financing-fund-list"]'),
    ).toContainText(/GCF|BOAD|SUNREF|FNDE/)

    // 5.3 — Empilement z-index : widget superieur a la page
    const widgetZ = await widget.evaluate((el) => {
      const raw = getComputedStyle(el).zIndex
      return Number.parseInt(raw, 10) || 0
    })
    expect(widgetZ).toBeGreaterThanOrEqual(50)

    const fundListZ = await page
      .locator('[data-guide-target="financing-fund-list"]')
      .evaluate((el) => {
        const raw = getComputedStyle(el).zIndex
        return Number.parseInt(raw, 10) || 0
      })
    // Le listing doit rester en z-index naturel (0 ou auto → NaN → 0).
    expect(fundListZ).toBeLessThan(widgetZ)
  })
})
