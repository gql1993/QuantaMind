import { getJson } from './client'

export type HealthResponse = {
  success: boolean
  data: {
    service: string
    status: string
    timestamp: string
  }
  error: null | {
    code?: string
    message?: string
  }
}

export function fetchHealth() {
  return getJson<HealthResponse>('/api/v1/health')
}
