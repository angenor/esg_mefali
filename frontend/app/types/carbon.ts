// Types TypeScript pour le module Calculateur d'Empreinte Carbone

export type CarbonStatus = 'in_progress' | 'completed'
export type EmissionCategory = 'energy' | 'transport' | 'waste' | 'industrial' | 'agriculture'
export type BenchmarkPosition = 'well_below_average' | 'below_average' | 'average' | 'above_average' | 'well_above_average' | 'unknown'

export interface CarbonEmissionEntry {
  id: string
  category: EmissionCategory
  subcategory: string
  quantity: number
  unit: string
  emission_factor: number
  emissions_tco2e: number
  source_description: string | null
  created_at: string
}

export interface ReductionAction {
  action: string
  reduction_tco2e: number
  savings_fcfa: number
  timeline: string
}

export interface ReductionPlan {
  quick_wins: ReductionAction[]
  long_term: ReductionAction[]
}

export interface CarbonAssessment {
  id: string
  user_id: string
  conversation_id: string | null
  year: number
  status: CarbonStatus
  sector: string | null
  total_emissions_tco2e: number | null
  completed_categories: EmissionCategory[]
  reduction_plan: ReductionPlan | null
  entries: CarbonEmissionEntry[]
  created_at: string
  updated_at: string
}

export interface CarbonAssessmentSummary {
  id: string
  year: number
  status: CarbonStatus
  total_emissions_tco2e: number | null
  completed_categories: EmissionCategory[]
  created_at: string
  updated_at: string
}

export interface CarbonAssessmentList {
  items: CarbonAssessmentSummary[]
  total: number
  page: number
  limit: number
}

export interface CategoryBreakdown {
  emissions_tco2e: number
  percentage: number
  entries_count: number
}

export interface Equivalence {
  label: string
  value: number
}

export interface SectorBenchmark {
  sector: string
  sector_average_tco2e: number | null
  position: BenchmarkPosition
  percentile: number | null
}

export interface CarbonSummary {
  assessment_id: string
  year: number
  status: CarbonStatus
  total_emissions_tco2e: number
  by_category: Record<EmissionCategory, CategoryBreakdown>
  equivalences: Equivalence[]
  reduction_plan: ReductionPlan | null
  sector_benchmark: SectorBenchmark | null
}

export interface AddEntriesRequest {
  entries: Omit<CarbonEmissionEntry, 'id' | 'created_at'>[]
  mark_category_complete?: EmissionCategory
}

export interface AddEntriesResponse {
  entries_added: number
  total_emissions_tco2e: number
  completed_categories: EmissionCategory[]
}

export interface BenchmarkResponse {
  sector: string
  average_emissions_tco2e: number
  median_emissions_tco2e: number
  by_category: Record<string, number>
  sample_size: string
  source: string
  fallback_sector?: string
}
