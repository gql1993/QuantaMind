import { getJson, postJson } from './client'

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

export type ArtifactResponse = {
  success: boolean
  data: ArtifactRecord
  error: null
}

export function fetchArtifact(artifactId: string) {
  return getJson<ArtifactResponse>(`/api/v1/artifacts/${artifactId}`)
}

export type ArtifactPreview = {
  artifact_id: string
  title: string
  preview_type: string
  content: Record<string, unknown>
}

export type ArtifactActionResult = {
  artifact_id: string
  action: 'export' | 'share' | 'archive'
  status: string
  download_url?: string
  share_url?: string
}

export type ArtifactPreviewResponse = {
  success: boolean
  data: ArtifactPreview
  error: null
}

export type ArtifactActionResponse = {
  success: boolean
  data: ArtifactActionResult
  error: null
}

export function previewArtifact(artifactId: string) {
  return getJson<ArtifactPreviewResponse>(`/api/v1/artifacts/${artifactId}/preview`)
}

export function exportArtifact(artifactId: string) {
  return postJson<ArtifactActionResponse>(`/api/v1/artifacts/${artifactId}/export`, {})
}

export function shareArtifact(artifactId: string) {
  return postJson<ArtifactActionResponse>(`/api/v1/artifacts/${artifactId}/share`, {})
}

export function archiveArtifact(artifactId: string) {
  return postJson<ArtifactActionResponse>(`/api/v1/artifacts/${artifactId}/archive`, {})
}
