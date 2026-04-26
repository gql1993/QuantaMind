import { useEffect, useState } from 'react'

import {
  fetchAgentGovernance,
  fetchAgentGovernanceSummary,
  type AgentGovernanceRecord,
  type AgentGovernanceSummary,
} from '../api/adminAgents'
import { MetricCard } from '../components/MetricCard'

export function AdminAgentsPage() {
  const [agents, setAgents] = useState<AgentGovernanceRecord[]>([])
  const [summary, setSummary] = useState<AgentGovernanceSummary | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let ignore = false

    Promise.all([fetchAgentGovernance(), fetchAgentGovernanceSummary()])
      .then(([agentData, summaryData]) => {
        if (ignore) {
          return
        }
        setAgents(agentData.data.items)
        setSummary(summaryData.data)
        setError(null)
      })
      .catch((loadError: unknown) => {
        if (ignore) {
          return
        }
        setError(loadError instanceof Error ? loadError.message : 'Unknown API error')
      })

    return () => {
      ignore = true
    }
  }, [])

  return (
    <>
      {error && <div className="error-banner">后台智能体治理加载失败：{error}</div>}

      <section className="admin-hero panel">
        <div>
          <span className="card-kicker">Admin Agents</span>
          <h2>后台智能体治理</h2>
          <p>用于集中查看智能体启停状态、风险级别、工具权限策略和最近审计时间。</p>
        </div>
      </section>

      <section className="metric-grid">
        <MetricCard label="启用智能体" value={summary?.enabled_count ?? '-'} />
        <MetricCard label="停用智能体" value={summary?.disabled_count ?? '-'} />
        <MetricCard label="高风险" value={summary?.high_risk_count ?? '-'} />
        <MetricCard label="工具策略" value={summary?.policy_count ?? '-'} />
      </section>

      <section className="panel">
        <div className="panel-head">
          <div>
            <span className="card-kicker">Governance</span>
            <h2>智能体治理清单</h2>
          </div>
        </div>
        <div className="governance-list">
          {agents.map((agent) => (
            <article className="governance-card" key={agent.agent_id}>
              <div>
                <span>{agent.agent_id}</span>
                <h3>{agent.display_name}</h3>
                <p>
                  版本 {agent.version} · 策略 {agent.tool_policy} · 最近审计 {agent.last_audit_at}
                </p>
              </div>
              <div className="governance-status">
                <span className={agent.status === 'enabled' ? 'badge completed' : 'badge'}>{agent.status}</span>
                <span className={agent.risk_level === 'high' ? 'badge failed' : 'badge running'}>
                  {agent.risk_level}
                </span>
              </div>
              <div className="tag-list">
                {agent.allowed_tools.map((tool) => (
                  <span key={tool}>{tool}</span>
                ))}
              </div>
            </article>
          ))}
        </div>
      </section>
    </>
  )
}
