// Types pour la feature 018 — Interactive chat widgets

export type InteractiveQuestionType =
  | 'qcu'
  | 'qcm'
  | 'qcu_justification'
  | 'qcm_justification'

export type InteractiveQuestionState =
  | 'pending'
  | 'answered'
  | 'abandoned'
  | 'expired'

export interface InteractiveOption {
  id: string
  label: string
  emoji?: string
  description?: string
}

export interface InteractiveQuestionEvent {
  type: 'interactive_question'
  id: string
  conversation_id: string
  question_type: InteractiveQuestionType
  prompt: string
  options: InteractiveOption[]
  min_selections: number
  max_selections: number
  requires_justification: boolean
  justification_prompt: string | null
  module: string
  created_at: string
}

export interface InteractiveQuestionResolvedEvent {
  type: 'interactive_question_resolved'
  id: string
  state: InteractiveQuestionState
  response_values: string[] | null
  response_justification: string | null
  answered_at: string
}

export interface InteractiveQuestion extends Omit<InteractiveQuestionEvent, 'type'> {
  state: InteractiveQuestionState
  response_values: string[] | null
  response_justification: string | null
  answered_at: string | null
}

export interface InteractiveQuestionAnswer {
  values: string[]
  justification?: string
}
