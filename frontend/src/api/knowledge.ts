import { getJson } from './client'

export type KnowledgeItem = {
  item_id: string
  title: string
  source: string
  tags: string[]
  summary: string
  updated_at: string
}

export type MemoryItem = {
  memory_id: string
  scope: string
  content: string
  confidence: number
  last_used_at: string
}

export type KnowledgeListResponse = {
  success: boolean
  data: {
    items: KnowledgeItem[]
    total: number
  }
  error: null
}

export type MemoryListResponse = {
  success: boolean
  data: {
    items: MemoryItem[]
    total: number
  }
  error: null
}

export function fetchKnowledgeItems() {
  return getJson<KnowledgeListResponse>('/api/v1/knowledge/items')
}

export function fetchMemories() {
  return getJson<MemoryListResponse>('/api/v1/knowledge/memories')
}
