import { getJson } from './client'

export type SystemStatusResponse = {
  success: boolean
  data: Record<string, { status: string; label: string }>
  error: null
}

export function fetchSystemStatus() {
  return getJson<SystemStatusResponse>('/api/v1/admin/system/status')
}
