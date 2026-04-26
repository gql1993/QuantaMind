import { getJson, postJson } from './client'

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

export type CreateRunPayload = {
  run_type: string
  origin?: string
  owner_agent?: string
  status_message?: string
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

export type RunResponse = {
  success: boolean
  data: RunRecord
  error: null
}

export function fetchRun(runId: string) {
  return getJson<RunResponse>(`/api/v1/runs/${runId}`)
}

export function fetchRunEvents(runId: string) {
  return getJson<RunEventsResponse>(`/api/v1/runs/${runId}/events`)
}

export function createRun(payload: CreateRunPayload) {
  return postJson<RunResponse>('/api/v1/runs', payload)
}

export function cancelRun(runId: string) {
  return postJson<RunResponse>(`/api/v1/runs/${runId}/cancel`, {})
}

export function retryRun(runId: string) {
  return postJson<RunResponse>(`/api/v1/runs/${runId}/retry`, {})
}
