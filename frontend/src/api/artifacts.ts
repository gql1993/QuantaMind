import { getJson } from './client'

export type ArtifactRecord = {
  artifact_id: string
  run_id: string
  artifact_type: string
  title: string
  summary: string
  payload: Record<string, unknown>
  created_at: string
}

export type ArtifactListResponse = {
  success: boolean
  data: {
    items: ArtifactRecord[]
    total: number
  }
  error: null
}

export function fetchArtifacts() {
  return getJson<ArtifactListResponse>('/api/v1/artifacts')
}
