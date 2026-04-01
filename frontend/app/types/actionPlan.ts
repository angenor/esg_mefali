// Types TypeScript pour le module Plan d'Action

export type ActionItemCategory = 'environment' | 'social' | 'governance' | 'financing' | 'carbon' | 'intermediary_contact'
export type ActionItemStatus = 'todo' | 'in_progress' | 'on_hold' | 'completed' | 'cancelled'
export type ActionItemPriority = 'high' | 'medium' | 'low'
export type ReminderType = 'action_due' | 'assessment_renewal' | 'fund_deadline' | 'intermediary_followup' | 'custom'
export type BadgeType = 'first_carbon' | 'esg_above_50' | 'first_application' | 'first_intermediary_contact' | 'full_journey'
export type PlanStatus = 'active' | 'archived'

export interface ActionItem {
  id: string
  plan_id: string
  title: string
  description: string | null
  category: ActionItemCategory
  priority: ActionItemPriority
  status: ActionItemStatus
  due_date: string | null
  estimated_cost_xof: number | null
  estimated_benefit: string | null
  completion_percentage: number
  related_fund_id: string | null
  related_intermediary_id: string | null
  intermediary_name: string | null
  intermediary_address: string | null
  intermediary_phone: string | null
  intermediary_email: string | null
  sort_order: number
  created_at: string
  updated_at: string
}

export interface ActionPlan {
  id: string
  user_id: string
  title: string
  timeframe: number
  status: PlanStatus
  total_actions: number
  completed_actions: number
  items: ActionItem[]
  created_at: string
  updated_at: string
}

export interface ProgressByCategory {
  total: number
  completed: number
  percentage: number
}

export interface ActionItemsListResponse {
  items: ActionItem[]
  total: number
  page: number
  limit: number
  progress: {
    global_percentage: number
    by_category: Record<ActionItemCategory, ProgressByCategory>
  }
}

export interface Reminder {
  id: string
  user_id: string
  action_item_id: string | null
  type: ReminderType
  message: string
  scheduled_at: string
  sent: boolean
  created_at: string
  action_item: ActionItem | null
}

export interface Badge {
  id: string
  user_id: string
  badge_type: BadgeType
  unlocked_at: string
}
