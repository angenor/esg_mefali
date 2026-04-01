// Types TypeScript pour le module Dashboard

export interface EsgSummary {
  score: number
  grade: string
  trend: string | null
  last_assessment_date: string | null
  pillar_scores: Record<string, number>
}

export interface CarbonSummary {
  total_tco2e: number
  year: number
  variation_percent: number | null
  top_category: string | null
  categories: Record<string, number>
}

export interface CreditSummary {
  score: number
  grade: string
  last_calculated: string | null
}

export interface FinancingSummary {
  recommended_funds_count: number
  active_applications_count: number
  application_statuses: Record<string, number>
  next_intermediary_action: {
    title: string
    due_date: string
    intermediary_name: string
  } | null
  has_intermediary_paths: boolean
}

export interface NextAction {
  id: string
  title: string
  category: string
  due_date: string | null
  status: string
  intermediary_name: string | null
  intermediary_address: string | null
}

export interface ActivityEvent {
  type: string
  title: string
  description: string | null
  timestamp: string
  related_entity_type: string | null
  related_entity_id: string | null
}

export interface BadgeSummary {
  badge_type: string
  unlocked_at: string
}

export interface DashboardSummary {
  esg: EsgSummary | null
  carbon: CarbonSummary | null
  credit: CreditSummary | null
  financing: FinancingSummary
  next_actions: NextAction[]
  recent_activity: ActivityEvent[]
  badges: BadgeSummary[]
}
