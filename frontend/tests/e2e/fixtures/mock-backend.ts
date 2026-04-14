import type { Page, Route } from '@playwright/test'
import type { CompanyProfile } from '../../../app/types/company'
import type { DashboardSummary } from '../../../app/types/dashboard'
import type { CarbonAssessment, CarbonSummary } from '../../../app/types/carbon'
import { FATOU, FATOU_COMPANY, FATOU_DASHBOARD_SUMMARY } from './users'
import type { CarbonSummaryFixture, TestUser } from './users'
import {
  createSSEResponse,
  FIXTURE_FROZEN_DATE,
  sseAssistantMessageWithConsent,
  sseGuidedTourAcceptanceResponse,
} from './sse-stream'

/**
 * Scenarios chat supportes par le mock backend.
 * A etendre dans les stories 8.2-8.6 (refuse, direct, expire, mobile, etc.).
 */
export type ChatScenario =
  | 'propose_guided_tour_after_carbon'
  | 'idle'

export interface MockBackendOptions {
  user?: TestUser
  companyProfile?: CompanyProfile
  carbonData?: CarbonSummaryFixture
  dashboardSummary?: DashboardSummary
  chatScenario?: ChatScenario
  /**
   * Routes supplementaires (override ou ajout) — appliquees APRES les routes
   * par defaut. Permet aux stories 8.2-8.6 d'etendre sans reecrire.
   */
  extraRoutes?: Array<{
    url: string | RegExp
    handler: (route: Route) => Promise<void> | void
  }>
}

const CONVERSATION_ID = 'conv-fatou-001'
const ASSESSMENT_ID = 'assessment-fatou-carbon-2025'
const INTERACTIVE_QUESTION_ID = 'iq-tour-consent-001'

/**
 * Helper : construit une reponse JSON via route.fulfill.
 */
function jsonResponse(route: Route, body: unknown, status = 200): Promise<void> {
  return route.fulfill({
    status,
    contentType: 'application/json',
    body: JSON.stringify(body),
  })
}

/**
 * Helper : construit une reponse SSE (text/event-stream) via route.fulfill.
 */
function sseResponse(route: Route, events: Parameters<typeof createSSEResponse>[0]): Promise<void> {
  const { body, headers } = createSSEResponse(events)
  return route.fulfill({
    status: 200,
    headers,
    body,
  })
}

/**
 * Installe tous les intercepteurs page.route() necessaires pour simuler
 * le backend. DOIT etre appele AVANT page.goto() sinon les requetes
 * initiales passent.
 *
 * Usage minimal (story 8.1) :
 *   await installMockBackend(page, {
 *     user: FATOU,
 *     companyProfile: FATOU_COMPANY,
 *     carbonData: FATOU_CARBON_SUMMARY,
 *     chatScenario: 'propose_guided_tour_after_carbon',
 *   })
 */
export async function installMockBackend(
  page: Page,
  options: MockBackendOptions = {},
): Promise<void> {
  const user = options.user ?? FATOU
  const companyProfile = options.companyProfile ?? FATOU_COMPANY
  const dashboardSummary = options.dashboardSummary ?? FATOU_DASHBOARD_SUMMARY
  const carbonData = options.carbonData ?? {
    total_tco2: 47.2,
    top_category: 'transport',
    top_category_pct: 62,
    sector: 'agroalimentaire',
  }
  const chatScenario: ChatScenario = options.chatScenario ?? 'idle'

  // ── CATCH-ALL /api/** (INSCRIT EN PREMIER → EVALUE EN DERNIER) ──────
  // Playwright evalue les page.route() handlers dans l'ordre inverse de leur
  // inscription : le dernier inscrit est evalue en premier. La catch-all est
  // donc inscrite EN PREMIER pour qu'elle soit evaluee en dernier, apres que
  // toutes les routes specifiques aient eu leur chance. Les `extraRoutes`
  // (inscrites en dernier plus bas) prennent priorite sur tout le reste.
  //
  // Politique : un appel a une route non mockee est une erreur de test — on
  // fulfill avec 500 pour faire echouer explicitement la spec plutot que de
  // laisser le frontend interpreter un 404 silencieux comme une UI valide.
  await page.route(/.*\/api\/.*/, async (route) => {
    const url = route.request().url()
    const message = `[mock-backend] Route non mockee: ${route.request().method()} ${url}`
    // Log visible cote Playwright (apparaitra dans la trace en cas d'echec).
    // eslint-disable-next-line no-console
    console.error(message)
    await route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ detail: message }),
    })
  })

  // ── AUTH ─────────────────────────────────────────────────────────────

  await page.route(/.*\/api\/auth\/login$/, async (route) => {
    const method = route.request().method()
    if (method !== 'POST') return route.continue()
    await jsonResponse(route, {
      access_token: user.fakeAccessToken,
      refresh_token: user.fakeRefreshToken,
      token_type: 'bearer',
      expires_in: 3600,
    })
  })

  await page.route(/.*\/api\/auth\/me$/, async (route) => {
    await jsonResponse(route, {
      id: user.id,
      email: user.email,
      full_name: user.full_name,
      company_name: user.company_name,
      created_at: user.created_at,
      updated_at: user.updated_at,
    })
  })

  await page.route(/.*\/api\/auth\/refresh$/, async (route) => {
    await jsonResponse(route, {
      access_token: `${user.fakeAccessToken}-refreshed`,
      refresh_token: user.fakeRefreshToken,
      token_type: 'bearer',
      expires_in: 3600,
    })
  })

  await page.route(/.*\/api\/auth\/detect-country$/, async (route) => {
    await jsonResponse(route, {
      detected_country: companyProfile.country,
      supported_countries: ['SN', 'CI', 'ML', 'BF', 'NE'],
    })
  })

  // ── COMPANY PROFILE ──────────────────────────────────────────────────

  await page.route(/.*\/api\/company\/profile$/, async (route) => {
    await jsonResponse(route, companyProfile)
  })

  await page.route(/.*\/api\/company\/profile\/completion$/, async (route) => {
    await jsonResponse(route, {
      identity_completion: 85,
      esg_completion: 60,
      overall_completion: 72,
      identity_fields: {
        filled: ['company_name', 'sector', 'employee_count', 'country'],
        missing: ['annual_revenue_xof'],
      },
      esg_fields: {
        filled: ['has_waste_management', 'has_gender_policy', 'has_training_program'],
        missing: ['has_energy_policy', 'has_financial_transparency'],
      },
    })
  })

  // ── DASHBOARD ────────────────────────────────────────────────────────

  await page.route(/.*\/api\/dashboard\/summary$/, async (route) => {
    await jsonResponse(route, dashboardSummary)
  })

  // ── CARBON ───────────────────────────────────────────────────────────
  // Liste des bilans (filtree par status dans la query)
  await page.route(/.*\/api\/carbon\/assessments(\?.*)?$/, async (route) => {
    await jsonResponse(route, {
      items: [
        {
          id: ASSESSMENT_ID,
          year: 2025,
          status: 'completed',
          total_emissions_tco2e: carbonData.total_tco2,
          completed_categories: ['transport', 'energy', 'waste', 'industrial'],
          created_at: '2026-03-01T10:00:00Z',
          updated_at: '2026-04-01T14:00:00Z',
        },
      ],
      total: 1,
      page: 1,
      limit: 50,
    })
  })

  // Detail d'un bilan
  await page.route(/.*\/api\/carbon\/assessments\/[^/]+$/, async (route) => {
    const assessment: CarbonAssessment = {
      id: ASSESSMENT_ID,
      user_id: user.id,
      conversation_id: CONVERSATION_ID,
      year: 2025,
      status: 'completed',
      sector: carbonData.sector,
      total_emissions_tco2e: carbonData.total_tco2,
      completed_categories: ['transport', 'energy', 'waste', 'industrial'],
      reduction_plan: {
        quick_wins: [
          {
            action: 'Optimiser les trajets logistiques (regroupement)',
            reduction_tco2e: 4.5,
            savings_fcfa: 1_200_000,
            timeline: '3 mois',
          },
        ],
        long_term: [
          {
            action: 'Passer au biodiesel pour le transport',
            reduction_tco2e: 12.0,
            savings_fcfa: 3_500_000,
            timeline: '18 mois',
          },
        ],
      },
      entries: [],
      created_at: '2026-03-01T10:00:00Z',
      updated_at: '2026-04-01T14:00:00Z',
    }
    await jsonResponse(route, assessment)
  })

  // Summary d'un bilan (utilise pour donut + benchmark cote page)
  await page.route(/.*\/api\/carbon\/assessments\/[^/]+\/summary$/, async (route) => {
    const summary: CarbonSummary = {
      assessment_id: ASSESSMENT_ID,
      year: 2025,
      status: 'completed',
      total_emissions_tco2e: carbonData.total_tco2,
      by_category: {
        transport: {
          emissions_tco2e: (carbonData.total_tco2 * carbonData.top_category_pct) / 100,
          percentage: carbonData.top_category_pct,
          entries_count: 4,
        },
        energy: {
          emissions_tco2e: carbonData.total_tco2 * 0.22,
          percentage: 22,
          entries_count: 3,
        },
        waste: {
          emissions_tco2e: carbonData.total_tco2 * 0.11,
          percentage: 11,
          entries_count: 2,
        },
        industrial: {
          emissions_tco2e: carbonData.total_tco2 * 0.05,
          percentage: 5,
          entries_count: 1,
        },
        agriculture: {
          emissions_tco2e: 0,
          percentage: 0,
          entries_count: 0,
        },
      },
      equivalences: [
        { label: 'vols Paris-Dakar', value: 12 },
        { label: 'arbres a planter/an', value: 470 },
      ],
      reduction_plan: {
        quick_wins: [
          {
            action: 'Optimiser les trajets logistiques (regroupement)',
            reduction_tco2e: 4.5,
            savings_fcfa: 1_200_000,
            timeline: '3 mois',
          },
        ],
        long_term: [
          {
            action: 'Passer au biodiesel pour le transport',
            reduction_tco2e: 12.0,
            savings_fcfa: 3_500_000,
            timeline: '18 mois',
          },
        ],
      },
      sector_benchmark: {
        sector: carbonData.sector,
        sector_average_tco2e: 42.0,
        position: 'above_average',
        percentile: 65,
      },
    }
    await jsonResponse(route, summary)
  })

  // Benchmark secteur
  await page.route(/.*\/api\/carbon\/benchmarks\/[^/]+$/, async (route) => {
    await jsonResponse(route, {
      sector: carbonData.sector,
      average_emissions_tco2e: 42.0,
      median_emissions_tco2e: 38.5,
      by_category: {
        transport: 18.2,
        energy: 10.5,
        waste: 4.3,
        industrial: 9.0,
      },
      sample_size: '50+ PME ouest-africaines',
      source: 'Base de donnees ADEME + UEMOA',
    })
  })

  // ── CHAT ─────────────────────────────────────────────────────────────
  // Liste des conversations
  await page.route(/.*\/api\/chat\/conversations(\?.*)?$/, async (route) => {
    const method = route.request().method()
    if (method === 'GET') {
      await jsonResponse(route, {
        items: [
          {
            id: CONVERSATION_ID,
            title: 'Conversation Fatou',
            current_module: 'chat',
            created_at: '2026-04-14T09:00:00Z',
            updated_at: '2026-04-14T10:00:00Z',
          },
        ],
        total: 1,
        page: 1,
        limit: 20,
      })
      return
    }
    if (method === 'POST') {
      await jsonResponse(route, {
        id: CONVERSATION_ID,
        title: 'Conversation Fatou',
        current_module: 'chat',
        created_at: FIXTURE_FROZEN_DATE,
        updated_at: FIXTURE_FROZEN_DATE,
      })
      return
    }
    await route.continue()
  })

  // Messages d'une conversation (GET liste + POST envoi)
  await page.route(
    /.*\/api\/chat\/conversations\/[^/]+\/messages(\?.*)?$/,
    async (route) => {
      const method = route.request().method()
      if (method === 'GET') {
        await jsonResponse(route, {
          items: [],
          total: 0,
          page: 1,
          limit: 50,
        })
        return
      }
      if (method === 'POST') {
        await handleChatPost(route, chatScenario, carbonData)
        return
      }
      await route.continue()
    },
  )

  // Questions interactives d'une conversation (hydratation)
  // Envelope aligne sur le reste des endpoints list (items/total/page/limit).
  await page.route(
    /.*\/api\/chat\/conversations\/[^/]+\/interactive-questions.*/,
    async (route) => {
      await jsonResponse(route, { items: [], total: 0, page: 1, limit: 50 })
    },
  )

  // Abandon d'une question interactive
  await page.route(
    /.*\/api\/chat\/interactive-questions\/[^/]+\/abandon$/,
    async (route) => {
      await jsonResponse(route, { ok: true })
    },
  )

  // PATCH/DELETE conversations (rename / delete)
  await page.route(/.*\/api\/chat\/conversations\/[^/]+$/, async (route) => {
    const method = route.request().method()
    if (method === 'PATCH') {
      await jsonResponse(route, {
        id: CONVERSATION_ID,
        title: 'Conversation Fatou',
        current_module: 'chat',
        created_at: '2026-04-14T09:00:00Z',
        updated_at: FIXTURE_FROZEN_DATE,
      })
      return
    }
    if (method === 'DELETE') {
      await route.fulfill({ status: 204 })
      return
    }
    await route.continue()
  })

  // ── ROUTES SUPPLEMENTAIRES (extraRoutes) ────────────────────────────
  // Inscrites en DERNIER → evaluees en PREMIER par Playwright (LIFO).
  for (const extra of options.extraRoutes ?? []) {
    await page.route(extra.url, extra.handler)
  }
}

/**
 * Parse le body d'une requete POST `messages` pour en extraire les champs
 * relatifs a la reponse a une question interactive. Le frontend (useChat.ts:637-654)
 * envoie en `multipart/form-data` :
 *   - `interactive_question_id` : string
 *   - `interactive_question_values` : JSON array stringifie (ex. `["yes"]`)
 *   - `interactive_question_justification` : string optionnel
 *
 * Retourne `questionId = null` quand la question n'est pas presente (envoi
 * initial d'un message).
 */
function parseInteractiveAnswer(
  postData: string,
  contentType: string | null,
): { questionId: string | null; values: string[] } {
  if (!postData.includes('interactive_question_id')) {
    return { questionId: null, values: [] }
  }

  let questionId: string | null = null
  let valuesRaw: string | null = null

  if (contentType?.startsWith('multipart/form-data')) {
    // Parsing par regex sur les sections Content-Disposition.
    const questionMatch = postData.match(
      /name="interactive_question_id"[\s\S]*?\r?\n\r?\n([\s\S]*?)\r?\n--/,
    )
    const valuesMatch = postData.match(
      /name="interactive_question_values"[\s\S]*?\r?\n\r?\n([\s\S]*?)\r?\n--/,
    )
    questionId = questionMatch?.[1]?.trim() ?? null
    valuesRaw = valuesMatch?.[1]?.trim() ?? null
  } else {
    // urlencoded : URLSearchParams parse les cle=valeur.
    try {
      const params = new URLSearchParams(postData)
      questionId = params.get('interactive_question_id')
      valuesRaw = params.get('interactive_question_values')
    } catch {
      // ignore — fallback retourne listes vides
    }
  }

  let values: string[] = []
  if (valuesRaw) {
    try {
      const parsed = JSON.parse(valuesRaw)
      if (Array.isArray(parsed)) {
        values = parsed.filter((v): v is string => typeof v === 'string')
      }
    } catch {
      // valeur brute non-JSON : traiter comme un seul choix.
      values = [valuesRaw]
    }
  }

  return { questionId, values }
}

/**
 * Gestionnaire du POST /api/chat/conversations/{id}/messages.
 *
 * - Si FormData contient `interactive_question_id` → c'est une reponse au widget
 *   de consentement (AC3) → renvoie le marker guided_tour.
 * - Sinon, envoi initial d'un message → scenario-dependent (propose tour, idle, ...).
 */
async function handleChatPost(
  route: Route,
  scenario: ChatScenario,
  carbonData: CarbonSummaryFixture,
): Promise<void> {
  const postData = route.request().postData() ?? ''
  const contentType = route.request().headers()['content-type'] ?? null
  const { questionId, values } = parseInteractiveAnswer(postData, contentType)
  const isInteractiveAnswer = questionId !== null

  if (scenario === 'propose_guided_tour_after_carbon') {
    if (isInteractiveAnswer) {
      // QCU : un seul choix attendu dans le tableau.
      if (values.includes('yes')) {
        await sseResponse(
          route,
          sseGuidedTourAcceptanceResponse({
            tourId: 'show_carbon_results',
            context: {
              total_tco2: carbonData.total_tco2,
              top_category: carbonData.top_category,
              top_category_pct: carbonData.top_category_pct,
              sector: carbonData.sector,
            },
            messageId: `msg-tour-trigger-${Date.now()}`,
          }),
        )
        return
      }
      // Refus (values = ['no'] ou autre)
      await sseResponse(route, [
        { type: 'token', content: 'Pas de probleme, revenez quand vous voulez.' },
        { type: 'done', message_id: `msg-refuse-${Date.now()}` },
      ])
      return
    }
    // Envoi initial — propose le consentement
    await sseResponse(
      route,
      sseAssistantMessageWithConsent({
        questionId: INTERACTIVE_QUESTION_ID,
        conversationId: CONVERSATION_ID,
        messageId: `msg-propose-${Date.now()}`,
      }),
    )
    return
  }

  // Scenario 'idle' (fallback)
  await sseResponse(route, [
    { type: 'token', content: 'Bonjour, comment puis-je vous aider ?' },
    { type: 'done', message_id: `msg-idle-${Date.now()}` },
  ])
}
