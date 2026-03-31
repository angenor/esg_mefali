/**
 * Types TypeScript pour le module documents.
 */

export type DocumentStatus = 'uploaded' | 'processing' | 'analyzed' | 'error'

export type DocumentType =
  | 'statuts_juridiques'
  | 'rapport_activite'
  | 'facture'
  | 'contrat'
  | 'politique_interne'
  | 'bilan_financier'
  | 'autre'

export interface ESGRelevantInfo {
  environmental: string[]
  social: string[]
  governance: string[]
}

export interface DocumentAnalysis {
  summary: string | null
  key_findings: string[] | null
  structured_data: Record<string, unknown> | null
  esg_relevant_info: ESGRelevantInfo | null
  analyzed_at: string | null
}

export interface Document {
  id: string
  original_filename: string
  mime_type: string
  file_size: number
  status: DocumentStatus
  document_type: DocumentType | null
  has_analysis: boolean
  created_at: string
}

export interface DocumentDetail extends Omit<Document, 'has_analysis'> {
  analysis: DocumentAnalysis | null
}

export interface DocumentUploadResponse {
  documents: Document[]
}

export interface DocumentListResponse {
  documents: Document[]
  total: number
  page: number
  limit: number
}

export interface ReanalyzeResponse {
  id: string
  status: DocumentStatus
  message: string
}
