// Types TypeScript pour le module Financement Vert

export type FundType = 'international' | 'regional' | 'national' | 'carbon_market' | 'local_bank_green_line'
export type FundStatus = 'active' | 'closed' | 'upcoming'
export type AccessType = 'direct' | 'intermediary_required' | 'mixed'
export type IntermediaryType = 'accredited_entity' | 'partner_bank' | 'implementation_agency' | 'project_developer' | 'national_agency'
export type OrganizationType = 'bank' | 'development_bank' | 'un_agency' | 'ngo' | 'government_agency' | 'consulting_firm' | 'carbon_developer'
export type MatchStatus = 'suggested' | 'interested' | 'contacting_intermediary' | 'applying' | 'submitted' | 'accepted' | 'rejected'

// --- Fonds ---

export interface FundSummary {
  id: string
  name: string
  organization: string
  fund_type: FundType
  status: FundStatus
  access_type: AccessType
  intermediary_type: IntermediaryType | null
  min_amount_xof: number | null
  max_amount_xof: number | null
  sectors_eligible: string[]
  typical_timeline_months: number | null
}

export interface FundIntermediary {
  id: string
  name: string
  intermediary_type: IntermediaryType
  organization_type: OrganizationType
  city: string
  role: string | null
  is_primary: boolean
  services_offered: Record<string, unknown>
  typical_fees: string | null
}

export interface Fund {
  id: string
  name: string
  organization: string
  fund_type: FundType
  description: string
  website_url: string | null
  contact_info: Record<string, unknown> | null
  eligibility_criteria: Record<string, unknown>
  sectors_eligible: string[]
  min_amount_xof: number | null
  max_amount_xof: number | null
  application_deadline: string | null
  required_documents: string[]
  esg_requirements: Record<string, unknown>
  status: FundStatus
  access_type: AccessType
  intermediary_type: IntermediaryType | null
  application_process: Array<{ step: number; title: string; description: string }>
  typical_timeline_months: number | null
  success_tips: string | null
  intermediaries: FundIntermediary[]
  created_at: string
  updated_at: string
}

export interface FundListResponse {
  items: FundSummary[]
  total: number
  page: number
  limit: number
}

// --- Intermediaires ---

export interface IntermediarySummary {
  id: string
  name: string
  intermediary_type: IntermediaryType
  organization_type: OrganizationType
  country: string
  city: string
  is_active: boolean
  services_offered: Record<string, unknown>
}

export interface FundCovered {
  id: string
  name: string
  role: string | null
  is_primary: boolean
}

export interface Intermediary {
  id: string
  name: string
  intermediary_type: IntermediaryType
  organization_type: OrganizationType
  description: string | null
  country: string
  city: string
  website_url: string | null
  contact_email: string | null
  contact_phone: string | null
  physical_address: string | null
  accreditations: string[]
  services_offered: Record<string, unknown>
  typical_fees: string | null
  eligibility_for_sme: Record<string, unknown>
  is_active: boolean
  funds_covered: FundCovered[]
  created_at: string
  updated_at: string
}

export interface IntermediaryListResponse {
  items: IntermediarySummary[]
  total: number
  page: number
  limit: number
}

// --- Matching ---

export interface MatchFundSummary {
  id: string
  name: string
  organization: string
  fund_type: FundType
  access_type: AccessType
  intermediary_type: IntermediaryType | null
  min_amount_xof: number | null
  max_amount_xof: number | null
}

export interface RecommendedIntermediary {
  id: string
  name: string
  city: string
}

export interface AccessPathwayStep {
  step: number
  phase: string
  title: string
  description: string
  duration_weeks: number | null
}

export interface AccessPathway {
  steps: AccessPathwayStep[]
  total_duration_months: number | null
}

export interface FundMatchSummary {
  id: string
  fund: MatchFundSummary
  compatibility_score: number
  matching_criteria: Record<string, number>
  missing_criteria: Record<string, string[]>
  recommended_intermediaries: RecommendedIntermediary[]
  estimated_timeline_months: number | null
  status: MatchStatus
}

export interface FundMatch {
  id: string
  fund: MatchFundSummary
  compatibility_score: number
  matching_criteria: Record<string, number>
  missing_criteria: Record<string, string[]>
  recommended_intermediaries: RecommendedIntermediary[]
  access_pathway: AccessPathway | null
  estimated_timeline_months: number | null
  status: MatchStatus
  contacted_intermediary_id: string | null
  created_at: string
}

export interface MatchListResponse {
  items: FundMatchSummary[]
  total: number
}
