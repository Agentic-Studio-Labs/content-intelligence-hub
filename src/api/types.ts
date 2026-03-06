export interface ContentItem {
  id: string
  title: string
  body: string
  summary: string
  content_type: string
  persona: string
  funnel_stage: string
  channel: string
  topics: string
  performance_score: number
  url: string
  created_at: string
  source_path: string
  score?: number
}

export interface GeneratedItem {
  id: string
  source_content_id: string
  source_title: string
  format: string
  tone: string
  body: string
  quality_score: number | null
  prompts: string
  created_at: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  limit: number
  offset: number
  has_more: boolean
}

export interface ContentStats {
  total: number
  avg_performance: number
  by_content_type: Record<string, number>
  by_persona: Record<string, number>
  by_funnel_stage: Record<string, number>
  by_channel: Record<string, number>
}

export interface SearchResponse {
  items: ContentItem[]
  query: string
}

export interface RepurposeRequest {
  content_id: string
  formats: string[]
  tone: string
  custom_instructions?: Record<string, string>
  save?: boolean
}

export interface RepurposeResponse {
  success: boolean
  generated_content: Record<string, string>
  quality_scores: Record<string, number>
  analysis: Record<string, string>
  errors: string[]
  saved_ids?: Record<string, string>
}

export interface DiscoverResponse {
  query: string
  answer: string
  results: ContentItem[]
  filters_applied: Record<string, string>
  search_terms: string
}

export interface AppSettings {
  anthropic_api_key_set: boolean
  watched_folders: string[]
  llm_model: string
  embedding_model: string
}
