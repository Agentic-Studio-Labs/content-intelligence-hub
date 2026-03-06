const BASE_URL = 'http://localhost:8420'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(error.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

import type {
  ContentItem, PaginatedResponse, ContentStats, SearchResponse,
  GeneratedItem, RepurposeRequest, RepurposeResponse, DiscoverResponse, AppSettings,
} from './types'

export const api = {
  health: () => request<{ status: string }>('/health'),

  listContent: (params?: Record<string, string | number>) => {
    const query = params ? '?' + new URLSearchParams(
      Object.entries(params).map(([k, v]) => [k, String(v)])
    ).toString() : ''
    return request<PaginatedResponse<ContentItem>>(`/api/content${query}`)
  },
  getContent: (id: string) => request<ContentItem>(`/api/content/${id}`),
  getSimilar: (id: string) => request<ContentItem[]>(`/api/content/${id}/similar`),
  searchContent: (query: string, filters?: Record<string, string>) =>
    request<SearchResponse>('/api/content/search', {
      method: 'POST',
      body: JSON.stringify({ query, filters }),
    }),
  getContentStats: () => request<ContentStats>('/api/content/stats'),

  repurpose: (req: RepurposeRequest) =>
    request<RepurposeResponse>('/api/agents/repurpose', {
      method: 'POST',
      body: JSON.stringify(req),
    }),
  discover: (query: string) =>
    request<DiscoverResponse>('/api/agents/query', {
      method: 'POST',
      body: JSON.stringify({ query }),
    }),

  listGenerated: (params?: Record<string, string | number>) => {
    const query = params ? '?' + new URLSearchParams(
      Object.entries(params).map(([k, v]) => [k, String(v)])
    ).toString() : ''
    return request<PaginatedResponse<GeneratedItem>>(`/api/generated${query}`)
  },
  getGenerated: (id: string) => request<GeneratedItem>(`/api/generated/${id}`),

  ingest: (paths: string[]) =>
    request<{ ingested: number }>('/api/ingest', {
      method: 'POST',
      body: JSON.stringify({ paths }),
    }),

  getSettings: () => request<AppSettings>('/api/settings'),
  updateSettings: (updates: { anthropic_api_key?: string; watched_folders?: string[] }) =>
    request<{ status: string }>('/api/settings', {
      method: 'PUT',
      body: JSON.stringify(updates),
    }),
}
