import type { User } from '../../../app/types'
import type { CompanyProfile } from '../../../app/types/company'
import type { DashboardSummary } from '../../../app/types/dashboard'

/**
 * Fixtures de donnees de test — story 8.1 (parcours Fatou).
 *
 * Ces structures matchent les interfaces reelles consommees par les composables
 * (useAuth, useCompanyProfile, useDashboard, useCarbon). Toute modification des
 * types TypeScript doit etre repercutee ici sous peine de casser les tests E2E.
 */

export interface TestUser extends User {
  fakeAccessToken: string
  fakeRefreshToken: string
}

/** Resume carbone simplifie consomme par l'interpolation useGuidedTour. */
export interface CarbonSummaryFixture {
  total_tco2: number
  top_category: string
  top_category_pct: number
  sector: string
}

// ── Fatou Diallo — PME Agro Dakar ──────────────────────────────────────
export const FATOU: TestUser = {
  id: 'user-fatou-001',
  email: 'fatou.diallo@pme-agro.sn',
  full_name: 'Fatou Diallo',
  company_name: 'PME Agro Dakar',
  created_at: '2026-01-15T09:30:00Z',
  updated_at: '2026-04-14T10:00:00Z',
  fakeAccessToken: 'fake-access-token-fatou-001',
  fakeRefreshToken: 'fake-refresh-token-fatou-001',
}

export const FATOU_COMPANY: CompanyProfile = {
  id: 'company-fatou-001',
  user_id: FATOU.id,
  company_name: 'PME Agro Dakar',
  sector: 'agroalimentaire',
  sub_sector: 'transformation cereales',
  employee_count: 15,
  annual_revenue_xof: 85_000_000,
  city: 'Dakar',
  country: 'SN',
  year_founded: 2019,
  has_waste_management: true,
  has_energy_policy: false,
  has_gender_policy: true,
  has_training_program: true,
  has_financial_transparency: true,
  governance_structure: 'Direction collegiale (3 personnes)',
  environmental_practices: 'Tri dechets + panneau solaire partiel',
  social_practices: 'Parite hommes/femmes ; formation continue',
  notes: null,
  created_at: '2026-01-15T09:35:00Z',
  updated_at: '2026-04-10T14:22:00Z',
}

/**
 * Donnees resumees du bilan carbone Fatou — utilisees pour interpoler les
 * popovers du parcours `show_carbon_results` (donut, benchmark, plan).
 */
export const FATOU_CARBON_SUMMARY: CarbonSummaryFixture = {
  total_tco2: 47.2,
  top_category: 'transport',
  top_category_pct: 62,
  sector: 'agroalimentaire',
}

/** Reponse minimale de /api/dashboard/summary pour Fatou. */
export const FATOU_DASHBOARD_SUMMARY: DashboardSummary = {
  esg: {
    score: 58,
    grade: 'C',
    trend: 'stable',
    last_assessment_date: '2026-03-20T10:00:00Z',
    pillar_scores: { environment: 55, social: 62, governance: 57 },
  },
  carbon: {
    total_tco2e: 47.2,
    year: 2025,
    variation_percent: null,
    top_category: 'transport',
    categories: { transport: 29.3, energie: 10.4, dechets: 5.1, industriel: 2.4 },
  },
  credit: null,
  financing: {
    recommended_funds_count: 3,
    active_applications_count: 0,
    application_statuses: {},
    next_intermediary_action: null,
    has_intermediary_paths: false,
  },
  next_actions: [],
  recent_activity: [],
  badges: [],
}
