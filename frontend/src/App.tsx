import { useEffect, useState } from 'react'
import { fetchAgents, type AgentProfile } from './api/agents'
import { fetchArtifacts, type ArtifactRecord } from './api/artifacts'
import { streamChatMessage } from './api/chat'
import { fetchHealth, type HealthResponse } from './api/health'
import { fetchRuns, type RunRecord } from './api/runs'
import { fetchSystemStatus, type SystemStatusResponse } from './api/system'
import './App.css'

type ViewKey = 'overview' | 'ai' | 'tasks' | 'artifacts' | 'agents' | 'admin-runs'

type ChatMessage = {
  role: 'user' | 'assistant' | 'system'
  content: string
  runId?: string
}

const navItems: Array<{ key: ViewKey; label: string }> = [
  { key: 'overview', label: '工作台总览' },
  { key: 'ai', label: 'AI 工作台' },
  { key: 'tasks', label: '我的任务' },
  { key: 'artifacts', label: '产物中心' },
  { key: 'agents', label: '智能体' },
  { key: 'admin-runs', label: '后台 Run 控制台' },
]

function App() {
  const [activeView, setActiveView] = useState<ViewKey>('overview')
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [healthError, setHealthError] = useState<string | null>(null)
  const [runs, setRuns] = useState<RunRecord[]>([])
  const [artifacts, setArtifacts] = useState<ArtifactRecord[]>([])
  const [agents, setAgents] = useState<AgentProfile[]>([])
  const [systemStatus, setSystemStatus] = useState<SystemStatusResponse['data']>({})
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      role: 'system',
      content: '欢迎使用量智大脑 AI 工作台。输入问题后，新前端会通过分离后的 /api/v1/chat 调用后端。',
    },
  ])
  const [chatInput, setChatInput] = useState('')
  const [chatLoading, setChatLoading] = useState(false)

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [healthData, runData, artifactData, agentData, systemData] = await Promise.all([
          fetchHealth(),
          fetchRuns(),
          fetchArtifacts(),
          fetchAgents(),
          fetchSystemStatus(),
        ])
        setHealth(healthData)
        setRuns(runData.data.items)
        setArtifacts(artifactData.data.items)
        setAgents(agentData.data.items)
        setSystemStatus(systemData.data)
        setHealthError(null)
      } catch (error: unknown) {
        setHealth(null)
        setHealthError(error instanceof Error ? error.message : 'Unknown API error')
      }
    }

    loadDashboard()
  }, [])

  async function handleSendChat() {
    const message = chatInput.trim()
    if (!message || chatLoading) {
      return
    }
    setChatInput('')
    setChatLoading(true)
    const assistantIndex = chatMessages.length + 1
    setChatMessages((items) => [
      ...items,
      { role: 'user', content: message },
      { role: 'assistant', content: '' },
    ])
    await streamChatMessage(message, {
      onEvent: async (event) => {
        if (event.type === 'run') {
          setChatMessages((items) =>
            items.map((item, index) => (index === assistantIndex ? { ...item, runId: event.run_id } : item)),
          )
          return
        }
        if (event.type === 'content') {
          setChatMessages((items) =>
            items.map((item, index) =>
              index === assistantIndex
                ? { ...item, content: `${item.content}${event.data}`, runId: event.run_id }
                : item,
            ),
          )
          return
        }
        if (event.type === 'done') {
          const runData = await fetchRuns()
          setRuns(runData.data.items)
          setChatLoading(false)
          return
        }
        if (event.type === 'error') {
          setChatMessages((items) =>
            items.map((item, index) =>
              index === assistantIndex ? { ...item, content: `调用失败：${event.data}` } : item,
            ),
          )
          setChatLoading(false)
        }
      },
      onError: (error) => {
        setChatMessages((items) =>
          items.map((item, index) =>
            index === assistantIndex ? { ...item, content: `调用失败：${error.message}` } : item,
          ),
        )
        setChatLoading(false)
      },
    })
    setChatLoading(false)
  }

  const runningRuns = runs.filter((run) => run.state === 'running')
  const completedRuns = runs.filter((run) => run.state === 'completed')

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">QuantaMind</div>
        <nav>
          {navItems.map((item) => (
            <button
              key={item.key}
              type="button"
              className={item.key === activeView ? 'active' : ''}
              onClick={() => setActiveView(item.key)}
            >
              {item.label}
            </button>
          ))}
        </nav>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <p className="eyebrow">Frontend / Backend Split</p>
            <h1>量智大脑分离式工作台</h1>
          </div>
          <div className={health?.data.status === 'ok' ? 'status ok' : 'status'}>
            {health?.data.status === 'ok' ? 'API 已连接' : 'API 未连接'}
          </div>
        </header>

        {activeView === 'overview' && (
          <>
            <section className="hero">
              <div>
                <h2>统一前台工作台 + 后台管理台</h2>
                <p>
                  当前页面是前后端分离改造的第二版骨架。前端已接入
                  `runs / artifacts / agents / admin system` API，可作为后续工作台和后台管理台的开发基线。
                </p>
              </div>
              <div className="api-card">
                <span>Backend Health</span>
                <strong>{health?.data.service ?? 'quantamind-api'}</strong>
                <small>{healthError ?? health?.data.timestamp ?? '等待后端响应'}</small>
              </div>
            </section>

            <section className="metric-grid">
              <MetricCard label="Run 总数" value={runs.length} />
              <MetricCard label="运行中" value={runningRuns.length} />
              <MetricCard label="已完成" value={completedRuns.length} />
              <MetricCard label="智能体" value={agents.length} />
            </section>

            <section className="grid">
              <article className="card">
                <span className="card-kicker">Workspace</span>
                <h3>角色化前台</h3>
                <p>面向芯片设计、测控、数据分析和项目经理，提供不同首页与默认入口。</p>
              </article>
              <article className="card">
                <span className="card-kicker">Runs</span>
                <h3>任务驱动</h3>
                <p>将长任务统一建模为 Run，前端展示阶段、工具调用、日志和产物。</p>
              </article>
              <article className="card">
                <span className="card-kicker">Admin</span>
                <h3>后台治理</h3>
                <p>后台管理台围绕运行、系统、数据、智能体、策略和审计展开。</p>
              </article>
            </section>
          </>
        )}

        {activeView === 'ai' && (
          <AiWorkbench
            messages={chatMessages}
            input={chatInput}
            loading={chatLoading}
            onInputChange={setChatInput}
            onSend={handleSendChat}
          />
        )}
        {activeView === 'tasks' && <RunsTable runs={runs} title="我的任务" />}
        {activeView === 'admin-runs' && <RunsTable runs={runs} title="后台 Run 控制台" admin />}
        {activeView === 'artifacts' && <ArtifactsPanel artifacts={artifacts} />}
        {activeView === 'agents' && <AgentsPanel agents={agents} systemStatus={systemStatus} />}
      </main>
    </div>
  )
}

function AiWorkbench({
  messages,
  input,
  loading,
  onInputChange,
  onSend,
}: {
  messages: ChatMessage[]
  input: string
  loading: boolean
  onInputChange: (value: string) => void
  onSend: () => void
}) {
  return (
    <section className="ai-layout">
      <div className="chat-panel">
        <div className="panel-head">
          <div>
            <span className="card-kicker">AI Workbench</span>
            <h2>AI 工作台</h2>
          </div>
          <span className={loading ? 'badge running' : 'badge completed'}>{loading ? '生成中' : '就绪'}</span>
        </div>
        <div className="message-list">
          {messages.map((message, index) => (
            <article className={`message ${message.role}`} key={`${message.role}-${index}`}>
              <span>{message.role}</span>
              <p>{message.content}</p>
              {message.runId && <small>关联 Run：{message.runId}</small>}
            </article>
          ))}
        </div>
        <div className="chat-composer">
          <textarea
            value={input}
            placeholder="例如：帮我分析 20 比特芯片设计风险，并生成下一步建议"
            onChange={(event) => onInputChange(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
                onSend()
              }
            }}
          />
          <button type="button" className="primary-action" disabled={loading} onClick={onSend}>
            {loading ? '发送中...' : '发送'}
          </button>
        </div>
      </div>
      <aside className="context-panel">
        <h3>执行说明</h3>
        <p>当前版本调用非流式 Chat API，并自动生成一个 `chat_run`。后续可升级为 SSE/WebSocket 流式输出。</p>
        <h3>快捷问题</h3>
        <ul>
          <li>检查当前系统状态</li>
          <li>帮我生成今日情报摘要</li>
          <li>分析芯片设计参数风险</li>
        </ul>
      </aside>
    </section>
  )
}

function MetricCard({ label, value }: { label: string; value: number }) {
  return (
    <article className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  )
}

function RunsTable({ runs, title, admin = false }: { runs: RunRecord[]; title: string; admin?: boolean }) {
  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <span className="card-kicker">{admin ? 'Admin' : 'Workspace'}</span>
          <h2>{title}</h2>
        </div>
        <button type="button" className="primary-action">新建 Run</button>
      </div>
      <table>
        <thead>
          <tr>
            <th>Run ID</th>
            <th>类型</th>
            <th>阶段</th>
            <th>状态</th>
            <th>负责人</th>
            <th>来源</th>
            <th>产物</th>
            <th>更新时间</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => (
            <tr key={run.run_id}>
              <td>{run.run_id}</td>
              <td>{run.run_type}</td>
              <td>{run.stage}</td>
              <td><span className={`badge ${run.state}`}>{run.state}</span></td>
              <td>{run.owner_agent ?? '-'}</td>
              <td>{String(run.metadata.source ?? run.origin ?? '-')}</td>
              <td>{run.artifacts.length}</td>
              <td>{run.updated_at}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}

function ArtifactsPanel({ artifacts }: { artifacts: ArtifactRecord[] }) {
  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <span className="card-kicker">Artifacts</span>
          <h2>产物中心</h2>
        </div>
      </div>
      <div className="artifact-list">
        {artifacts.map((artifact) => (
          <article className="artifact-card" key={artifact.artifact_id}>
            <span>{artifact.artifact_type}</span>
            <h3>{artifact.title}</h3>
            <p>{artifact.summary}</p>
            <small>来源 Run：{artifact.run_id}</small>
          </article>
        ))}
      </div>
    </section>
  )
}

function AgentsPanel({
  agents,
  systemStatus,
}: {
  agents: AgentProfile[]
  systemStatus: SystemStatusResponse['data']
}) {
  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <span className="card-kicker">Agents</span>
          <h2>智能体目录</h2>
        </div>
      </div>
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
            <h3>{agent.display_name}</h3>
            <p>{agent.role}</p>
            <small>{agent.capabilities.join(' / ')}</small>
          </article>
        ))}
      </div>
    </section>
  )
}

export default App
