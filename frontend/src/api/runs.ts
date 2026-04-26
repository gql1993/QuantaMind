import { getJson } from './client'

export type RunRecord = {
  run_id: string
  run_type: string
  origin: string
  parent_run_id?: string | null
  state: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled'
  stage: string
  status_message: string
  owner_agent?: string | null
  artifacts: string[]
  events: string[]
  metadata: Record<string, unknown>
  created_at: string
  updated_at: string
  completed_at?: string | null
}

export type RunEvent = {
  event_id: string
  run_id: string
  event_type: string
  payload: Record<string, unknown>
  created_at: string
}

export type RunListResponse = {
  success: boolean
  data: {
    items: RunRecord[]
    total: number
  }
  error: null
}

export type RunEventsResponse = {
  success: boolean
  data: {
    items: RunEvent[]
    total: number
  }
  error: null
}

export function fetchRuns() {
  return getJson<RunListResponse>('/api/v1/runs')
}

export function fetchRunEvents(runId: string) {
  return getJson<RunEventsResponse>(`/api/v1/runs/${runId}/events`)
}
