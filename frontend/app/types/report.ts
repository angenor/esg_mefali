// Types TypeScript pour le module rapports ESG PDF

export type ReportType = 'esg_compliance'
export type ReportStatus = 'generating' | 'completed' | 'failed'

export interface ReportGenerateResponse {
  id: string
  assessment_id: string
  report_type: ReportType
  status: ReportStatus
  created_at: string
}

export interface ReportStatusResponse {
  id: string
  status: ReportStatus
  generated_at: string | null
}

export interface ReportResponse {
  id: string
  assessment_id: string
  report_type: ReportType
  status: ReportStatus
  file_size: number | null
  generated_at: string | null
  created_at: string
}

export interface ReportListResponse {
  items: ReportResponse[]
  total: number
  page: number
  limit: number
}
