import { getJson } from './client'

export type AgentProfile = {
  agent_id: string
  display_name: string
  role: string
  capabilities: string[]
  default_context_layers: string[]
  default_tool_classes: string[]
  output_artifact_types: string[]
  aliases: string[]
  metadata: Record<string, unknown>
}

export type AgentListResponse = {
  success: boolean
  data: {
    items: AgentProfile[]
    total: number
  }
  error: null
}

export function fetchAgents() {
  return getJson<AgentListResponse>('/api/v1/agents')
}

export type AgentResponse = {
  success: boolean
  data: AgentProfile
  error: null
}

export function fetchAgent(agentId: string) {
  return getJson<AgentResponse>(`/api/v1/agents/${agentId}`)
}
