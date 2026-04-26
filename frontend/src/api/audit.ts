import { getJson } from './client'

export type ApprovalRecord = {
  approval_id: string
  title: string
  requester: string
  approval_type: string
  status: 'pending' | 'approved' | 'rejected'
  risk_level: 'low' | 'medium' | 'high'
  created_at: string
}

export type AuditEventRecord = {
  event_id: string
  actor: string
  action: string
  target: string
  result: string
  created_at: string
}

export type AuditSummary = {
  approval_count: number
  pending_count: number
  audit_event_count: number
  high_risk_count: number
}

export type ApprovalListResponse = {
  success: boolean
  data: {
    items: ApprovalRecord[]
    total: number
  }
  error: null
}

export type AuditEventListResponse = {
  success: boolean
  data: {
    items: AuditEventRecord[]
    total: number
  }
  error: null
}

export type AuditSummaryResponse = {
  success: boolean
  data: AuditSummary
  error: null
}

export function fetchApprovals() {
  return getJson<ApprovalListResponse>('/api/v1/admin/audit/approvals')
}

export function fetchAuditEvents() {
  return getJson<AuditEventListResponse>('/api/v1/admin/audit/events')
}

export function fetchAuditSummary() {
  return getJson<AuditSummaryResponse>('/api/v1/admin/audit/summary')
}
