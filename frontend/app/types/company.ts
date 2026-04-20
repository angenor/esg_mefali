// Types TypeScript pour le profilage d'entreprise

export type SectorEnum =
  | 'agriculture'
  | 'energie'
  | 'recyclage'
  | 'transport'
  | 'construction'
  | 'textile'
  | 'agroalimentaire'
  | 'services'
  | 'commerce'
  | 'artisanat'
  | 'autre'

export interface CompanyProfile {
  id: string
  user_id: string
  company_name: string | null
  sector: SectorEnum | null
  sub_sector: string | null
  employee_count: number | null
  annual_revenue_xof: number | null
  city: string | null
  country: string | null
  year_founded: number | null
  has_waste_management: boolean | null
  has_energy_policy: boolean | null
  has_gender_policy: boolean | null
  has_training_program: boolean | null
  has_financial_transparency: boolean | null
  governance_structure: string | null
  environmental_practices: string | null
  social_practices: string | null
  notes: string | null
  // Story 9.5 : champs edites manuellement, proteges contre l'ecrasement LLM.
  manually_edited_fields: string[]
  created_at: string
  updated_at: string
}

export interface CompletionResponse {
  identity_completion: number
  esg_completion: number
  overall_completion: number
  identity_fields: {
    filled: string[]
    missing: string[]
  }
  esg_fields: {
    filled: string[]
    missing: string[]
  }
}

export interface ProfileUpdateEvent {
  field: string
  value: string | number | boolean
  label: string
}
