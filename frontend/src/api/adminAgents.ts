import { getJson } from './client'

export type AgentGovernanceRecord = {
  agent_id: string
  display_name: string
  status: 'enabled' | 'disabled'
  version: string
  risk_level: 'low' | 'medium' | 'high'
  tool_policy: string
  allowed_tools: string[]
  last_audit_at: string
}

export type AgentGovernanceSummary = {
  enabled_count: number
  disabled_count: number
  high_risk_count: number
  policy_count: number
}

export type AgentGovernanceListResponse = {
  success: boolean
  data: {
    items: AgentGovernanceRecord[]
    total: number
  }
  error: null
}

export type AgentGovernanceSummaryResponse = {
  success: boolean
  data: AgentGovernanceSummary
  error: null
}

export function fetchAgentGovernance() {
  return getJson<AgentGovernanceListResponse>('/api/v1/admin/agents')
}

export function fetchAgentGovernanceSummary() {
  return getJson<AgentGovernanceSummaryResponse>('/api/v1/admin/agents/summary')
}
