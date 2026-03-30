// Types TypeScript partagés pour ESG Mefali

export interface User {
  id: string
  email: string
  full_name: string
  company_name: string
  created_at: string
  updated_at?: string
}

export interface Conversation {
  id: string
  title: string
  current_module: string
  created_at: string
  updated_at: string
}

export interface Message {
  id: string
  conversation_id?: string
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

export interface TokenResponse {
  access_token: string
  refresh_token?: string
  token_type: string
  expires_in: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  limit: number
}

export interface ApiError {
  detail: string
}
