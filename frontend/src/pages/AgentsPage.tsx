import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { fetchAgents, type AgentProfile } from '../api/agents'
import { fetchSystemStatus, type SystemStatusResponse } from '../api/system'

export function AgentsPage() {
  const [agents, setAgents] = useState<AgentProfile[]>([])
  const [systemStatus, setSystemStatus] = useState<SystemStatusResponse['data']>({})
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function load() {
      try {
        const [agentData, systemData] = await Promise.all([fetchAgents(), fetchSystemStatus()])
        setAgents(agentData.data.items)
        setSystemStatus(systemData.data)
        setError(null)
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : 'Unknown API error')
      }
    }

    load()
  }, [])

  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <span className="card-kicker">Agents</span>
          <h2>智能体目录</h2>
        </div>
      </div>
      {error && <div className="error-banner">智能体数据加载失败：{error}</div>}
      <div className="system-strip">
        {Object.entries(systemStatus).map(([key, item]) => (
          <div key={key}>
            <strong>{item.label}</strong>
            <span>{item.status}</span>
          </div>
        ))}
      </div>
      <div className="agent-grid">
        {agents.map((agent) => (
          <article className="agent-card" key={agent.agent_id}>
            <span>{agent.agent_id}</span>
            <h3>
              <Link to={`/workspace/agents/${agent.agent_id}`}>{agent.display_name}</Link>
            </h3>
            <p>{agent.role}</p>
            <small>{agent.capabilities.join(' / ')}</small>
          </article>
        ))}
      </div>
    </section>
  )
}
