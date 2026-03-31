// Types TypeScript pour le module ESG

export type ESGPillar = 'environment' | 'social' | 'governance'
export type ESGStatus = 'draft' | 'in_progress' | 'completed'
export type ImpactLevel = 'high' | 'medium' | 'low'
export type BenchmarkPosition = 'above_average' | 'average' | 'below_average'

export interface CriteriaScoreDetail {
  score: number
  justification: string
  sources: string[]
}

export interface PillarWeights {
  [criterionCode: string]: number
}

export interface PillarDetail {
  raw_score: number
  weighted_score: number
  weights_applied: PillarWeights
}

export interface AssessmentData {
  criteria_scores: Record<string, CriteriaScoreDetail>
  pillar_details: Record<ESGPillar, PillarDetail>
}

export interface ESGRecommendation {
  priority: number
  criteria_code: string
  pillar: ESGPillar
  title: string
  description: string
  impact: ImpactLevel
  effort: ImpactLevel
  timeline: string
}

export interface ESGStrength {
  criteria_code: string
  pillar: ESGPillar
  title: string
  description: string
  score: number
}

export interface ESGGap {
  criteria_code: string
  pillar: ESGPillar
  title: string
  score: number
}

export interface SectorBenchmark {
  sector: string
  averages: {
    environment: number
    social: number
    governance: number
    overall: number
  }
  position: BenchmarkPosition
  percentile: number
}

export interface ESGAssessment {
  id: string
  user_id: string
  conversation_id: string | null
  version: number
  status: ESGStatus
  sector: string
  overall_score: number | null
  environment_score: number | null
  social_score: number | null
  governance_score: number | null
  assessment_data: AssessmentData | null
  recommendations: ESGRecommendation[] | null
  strengths: ESGStrength[] | null
  gaps: ESGGap[] | null
  sector_benchmark: SectorBenchmark | null
  current_pillar: ESGPillar | null
  evaluated_criteria: string[]
  created_at: string
  updated_at: string
}

export interface ESGAssessmentSummary {
  id: string
  version: number
  status: ESGStatus
  sector: string
  overall_score: number | null
  environment_score: number | null
  social_score: number | null
  governance_score: number | null
  created_at: string
}

export interface ESGAssessmentList {
  data: ESGAssessmentSummary[]
  total: number
  page: number
  limit: number
}

export interface CriteriaScoreResponse {
  code: string
  label: string
  score: number
  max: number
  weight: number
}

export interface PillarScoreResponse {
  score: number
  criteria: CriteriaScoreResponse[]
}

export interface ScoreResponse {
  assessment_id: string
  status: ESGStatus
  overall_score: number
  color: string
  pillars: Record<ESGPillar, PillarScoreResponse>
  strengths_count: number
  gaps_count: number
  recommendations_count: number
}

export interface BenchmarkResponse {
  sector: string
  sector_label: string
  sample_size: string
  averages: {
    environment: number
    social: number
    governance: number
    overall: number
  }
  top_criteria: string[]
  weak_criteria: string[]
}

export interface EvaluateResponse {
  assessment_id: string
  status: ESGStatus
  current_pillar: ESGPillar | null
  evaluated_criteria: string[]
  progress_percent: number
  total_criteria: number
}
