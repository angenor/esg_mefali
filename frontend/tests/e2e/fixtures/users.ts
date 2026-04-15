import type { User } from '../../../app/types'
import type { CompanyProfile } from '../../../app/types/company'
import type { DashboardSummary } from '../../../app/types/dashboard'
import type {
  FundSummary,
  MatchListResponse,
  FundListResponse,
} from '../../../app/types/financing'

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

/**
 * Type alias local (facilite l'import cote mock-backend et specs).
 * Les reponses API `/financing/matches` et `/financing/funds` sont typees par
 * `MatchListResponse` et `FundListResponse` — on re-exporte pour lisibilite.
 */
export type FundMatchListFixture = MatchListResponse
export type FundListFixture = FundListResponse

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

// ── Moussa Ba — Cooperative Cacao Cote d'Ivoire (story 8.2) ────────────
//
// Profil « utilisateur experimente » qui navigue directement sur /financing,
// pose une question contextuelle et REFUSE la proposition de guidage.
// Secteur volontairement different de Fatou (agriculture/cacao vs agroalimentaire)
// pour garantir qu'aucun cache cross-parcours ne masque un bug metier.

export const MOUSSA: TestUser = {
  id: 'user-moussa-001',
  email: 'moussa.ba@coop-cacao.ci',
  full_name: 'Moussa Ba',
  company_name: 'Cooperative Cacao Cote d\'Ivoire',
  created_at: '2025-11-02T08:15:00Z',
  updated_at: '2026-04-10T16:40:00Z',
  fakeAccessToken: 'fake-access-token-moussa-001',
  fakeRefreshToken: 'fake-refresh-token-moussa-001',
}

export const MOUSSA_COMPANY: CompanyProfile = {
  id: 'company-moussa-001',
  user_id: MOUSSA.id,
  company_name: 'Cooperative Cacao Cote d\'Ivoire',
  sector: 'agriculture',
  sub_sector: 'cacao — cooperative',
  employee_count: 48,
  annual_revenue_xof: 350_000_000,
  city: 'Abidjan',
  country: 'CI',
  year_founded: 2017,
  has_waste_management: true,
  has_energy_policy: true,
  has_gender_policy: true,
  has_training_program: true,
  has_financial_transparency: true,
  governance_structure: 'Cooperative — AG annuelle + bureau elu',
  environmental_practices: 'Agroforesterie, compostage, bannissement pesticides interdits',
  social_practices: 'Prime a la productivite, alphabetisation, mutuelle sante',
  notes: null,
  created_at: '2025-11-02T08:20:00Z',
  updated_at: '2026-04-10T16:40:00Z',
}

/**
 * Matches financement pour Moussa — 4 fonds compatibles avec un score degressif.
 * Les noms courts (GCF, BOAD, SUNREF, FNDE) sont reutilises dans les assertions
 * AC3 et AC5 — NE PAS renommer sans mettre a jour les regex de la spec.
 */
export const MOUSSA_FINANCING_MATCHES: FundMatchListFixture = {
  total: 4,
  items: [
    {
      id: 'match-moussa-001',
      fund: {
        id: 'fund-gcf-agri',
        name: 'GCF Agriculture Resilient',
        organization: 'Green Climate Fund',
        fund_type: 'international',
        access_type: 'intermediary_required',
        intermediary_type: 'accredited_entity',
        min_amount_xof: 32_000_000,
        max_amount_xof: 320_000_000,
      },
      compatibility_score: 87,
      matching_criteria: { sector: 1, country: 1, esg: 0.8, size: 0.9 },
      missing_criteria: {},
      recommended_intermediaries: [
        { id: 'inter-boad-001', name: 'BOAD', city: 'Lome' },
      ],
      estimated_timeline_months: 9,
      status: 'suggested',
    },
    {
      id: 'match-moussa-002',
      fund: {
        id: 'fund-boad-pme',
        name: 'BOAD Ligne PME Verte',
        organization: 'Banque Ouest Africaine de Developpement',
        fund_type: 'regional',
        access_type: 'direct',
        intermediary_type: null,
        min_amount_xof: 13_000_000,
        max_amount_xof: 130_000_000,
      },
      compatibility_score: 78,
      matching_criteria: { sector: 1, country: 1, esg: 0.7, size: 0.85 },
      missing_criteria: {},
      recommended_intermediaries: [],
      estimated_timeline_months: 4,
      status: 'suggested',
    },
    {
      id: 'match-moussa-003',
      fund: {
        id: 'fund-sunref',
        name: 'SUNREF Cacao Durable',
        organization: 'Agence Francaise de Developpement',
        fund_type: 'international',
        access_type: 'intermediary_required',
        intermediary_type: 'partner_bank',
        min_amount_xof: 20_000_000,
        max_amount_xof: 200_000_000,
      },
      compatibility_score: 71,
      matching_criteria: { sector: 1, country: 1, esg: 0.6, size: 0.75 },
      missing_criteria: {},
      recommended_intermediaries: [
        { id: 'inter-nsia-001', name: 'NSIA Banque', city: 'Abidjan' },
      ],
      estimated_timeline_months: 6,
      status: 'suggested',
    },
    {
      id: 'match-moussa-004',
      fund: {
        id: 'fund-fnde',
        name: 'FNDE Cote d\'Ivoire',
        organization: 'Fonds National de Developpement Economique',
        fund_type: 'national',
        access_type: 'direct',
        intermediary_type: null,
        min_amount_xof: 6_500_000,
        max_amount_xof: 65_000_000,
      },
      compatibility_score: 64,
      matching_criteria: { sector: 0.7, country: 1, esg: 0.5, size: 0.6 },
      missing_criteria: { documents: ['audit_financier'] },
      recommended_intermediaries: [],
      estimated_timeline_months: 3,
      status: 'suggested',
    },
  ],
}

/**
 * Catalogue de fonds (onglet "Tous les fonds" de /financing).
 * Reprend les 4 fonds des matches + 2 fonds non-match pour enrichir le catalogue
 * et tester qu'aucun filtre ne casse le rendu.
 */
export const MOUSSA_FUNDS: FundListFixture = {
  total: 6,
  page: 1,
  limit: 50,
  items: [
    {
      id: 'fund-gcf-agri',
      name: 'GCF Agriculture Resilient',
      organization: 'Green Climate Fund',
      fund_type: 'international',
      status: 'active',
      access_type: 'intermediary_required',
      intermediary_type: 'accredited_entity',
      min_amount_xof: 32_000_000,
      max_amount_xof: 320_000_000,
      sectors_eligible: ['agriculture', 'forestry'],
      typical_timeline_months: 9,
    },
    {
      id: 'fund-boad-pme',
      name: 'BOAD Ligne PME Verte',
      organization: 'Banque Ouest Africaine de Developpement',
      fund_type: 'regional',
      status: 'active',
      access_type: 'direct',
      intermediary_type: null,
      min_amount_xof: 13_000_000,
      max_amount_xof: 130_000_000,
      sectors_eligible: ['agriculture', 'energie', 'industrie'],
      typical_timeline_months: 4,
    },
    {
      id: 'fund-sunref',
      name: 'SUNREF Cacao Durable',
      organization: 'Agence Francaise de Developpement',
      fund_type: 'international',
      status: 'active',
      access_type: 'intermediary_required',
      intermediary_type: 'partner_bank',
      min_amount_xof: 20_000_000,
      max_amount_xof: 200_000_000,
      sectors_eligible: ['agriculture'],
      typical_timeline_months: 6,
    },
    {
      id: 'fund-fnde',
      name: 'FNDE Cote d\'Ivoire',
      organization: 'Fonds National de Developpement Economique',
      fund_type: 'national',
      status: 'active',
      access_type: 'direct',
      intermediary_type: null,
      min_amount_xof: 6_500_000,
      max_amount_xof: 65_000_000,
      sectors_eligible: ['agriculture', 'artisanat'],
      typical_timeline_months: 3,
    },
    {
      id: 'fund-fem',
      name: 'FEM Petites Subventions',
      organization: 'Fonds pour l\'Environnement Mondial',
      fund_type: 'international',
      status: 'active',
      access_type: 'mixed',
      intermediary_type: 'implementation_agency',
      min_amount_xof: 3_000_000,
      max_amount_xof: 30_000_000,
      sectors_eligible: ['biodiversite', 'energie'],
      typical_timeline_months: 8,
    },
    {
      id: 'fund-bad',
      name: 'BAD Green Bank Initiative',
      organization: 'Banque Africaine de Developpement',
      fund_type: 'regional',
      status: 'active',
      access_type: 'intermediary_required',
      intermediary_type: 'partner_bank',
      min_amount_xof: 50_000_000,
      max_amount_xof: 500_000_000,
      sectors_eligible: ['energie', 'transport'],
      typical_timeline_months: 12,
    },
  ] as FundSummary[],
}
