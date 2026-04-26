import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { fetchAgent, type AgentProfile } from '../api/agents'

export function AgentDetailPage() {
  const { agentId } = useParams<{ agentId: string }>()
  const [agent, setAgent] = useState<AgentProfile | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!agentId) {
      return
    }
    const currentAgentId = agentId

    async function load() {
      try {
        const data = await fetchAgent(currentAgentId)
        setAgent(data.data)
        setError(null)
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : 'Unknown API error')
      }
    }

    load()
  }, [agentId])

  if (error) {
    return (
      <section className="panel">
        <Link to="/workspace/agents" className="back-link">
          返回智能体目录
        </Link>
        <div className="error-banner">智能体详情加载失败：{error}</div>
      </section>
    )
  }

  if (!agent) {
    return (
      <section className="panel">
        <Link to="/workspace/agents" className="back-link">
          返回智能体目录
        </Link>
        <p>正在加载智能体详情...</p>
      </section>
    )
  }

  return (
    <section className="detail-grid">
      <article className="panel detail-main">
        <Link to="/workspace/agents" className="back-link">
          返回智能体目录
        </Link>
        <div className="panel-head">
          <div>
            <span className="card-kicker">Agent Detail</span>
            <h2>{agent.display_name}</h2>
          </div>
          <span className="badge">{agent.agent_id}</span>
        </div>

        <div className="status-message">
          <span>角色定位</span>
          <p>{agent.role}</p>
        </div>

        <div className="detail-section">
          <h3>能力</h3>
          <div className="tag-list">
            {agent.capabilities.map((item) => (
              <span key={item}>{item}</span>
            ))}
          </div>
        </div>

        <div className="detail-section">
          <h3>默认上下文层</h3>
          <div className="tag-list">
            {agent.default_context_layers.map((item) => (
              <span key={item}>{item}</span>
            ))}
          </div>
        </div>

        <div className="detail-section">
          <h3>默认工具类型</h3>
          <div className="tag-list">
            {agent.default_tool_classes.map((item) => (
              <span key={item}>{item}</span>
            ))}
          </div>
        </div>

        <div className="detail-section">
          <h3>输出产物类型</h3>
          <div className="tag-list">
            {agent.output_artifact_types.map((item) => (
              <span key={item}>{item}</span>
            ))}
          </div>
        </div>
      </article>

      <aside className="panel detail-side">
        <div className="panel-head">
          <div>
            <span className="card-kicker">Metadata</span>
            <h2>智能体配置</h2>
          </div>
        </div>
        <div className="detail-section">
          <h3>别名</h3>
          <div className="tag-list">
            {agent.aliases.length > 0 ? agent.aliases.map((item) => <span key={item}>{item}</span>) : <span>无</span>}
          </div>
        </div>
        <pre className="json-viewer">{JSON.stringify(agent.metadata, null, 2)}</pre>
      </aside>
    </section>
  )
}
