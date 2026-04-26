import { getJson } from './client'

export type DatasetRecord = {
  dataset_id: string
  name: string
  domain: string
  owner: string
  record_count: number
  quality_score: number
  last_sync_at: string
  status: 'healthy' | 'warning' | 'failed'
}

export type DataQualityRule = {
  rule_id: string
  label: string
  status: 'ok' | 'warning' | 'failed'
}

export type DatasetCatalogResponse = {
  success: boolean
  data: {
    items: DatasetRecord[]
    total: number
  }
  error: null
}

export type DataQualityResponse = {
  success: boolean
  data: {
    average_score: number
    healthy_count: number
    warning_count: number
    rules: DataQualityRule[]
  }
  error: null
}

export function fetchDatasetCatalog() {
  return getJson<DatasetCatalogResponse>('/api/v1/data/catalog')
}

export function fetchDataQuality() {
  return getJson<DataQualityResponse>('/api/v1/data/quality')
}
