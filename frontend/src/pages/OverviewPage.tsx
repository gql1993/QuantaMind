import { useEffect, useState } from 'react'

import { fetchAgents } from '../api/agents'
import { fetchHealth, type HealthResponse } from '../api/health'
import { fetchRuns, type RunRecord } from '../api/runs'
import { MetricCard } from '../components/MetricCard'

export function OverviewPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [healthError, setHealthError] = useState<string | null>(null)
  const [runs, setRuns] = useState<RunRecord[]>([])
  const [agentCount, setAgentCount] = useState(0)

  useEffect(() => {
    async function load() {
      try {
        const [healthData, runData, agentData] = await Promise.all([
          fetchHealth(),
          fetchRuns(),
          fetchAgents(),
        ])
        setHealth(healthData)
        setRuns(runData.data.items)
        setAgentCount(agentData.data.total)
        setHealthError(null)
      } catch (error) {
        setHealth(null)
        setHealthError(error instanceof Error ? error.message : 'Unknown API error')
      }
    }

    load()
  }, [])

  const runningRuns = runs.filter((run) => run.state === 'running')
  const completedRuns = runs.filter((run) => run.state === 'completed')

  return (
    <>
      <section className="hero">
        <div>
          <h2>统一前台工作台 + 后台管理台</h2>
          <p>
            当前前端已拆分为路由化页面，并接入 `runs / artifacts / agents / chat`
            API。后续可继续扩展角色首页、Run 详情、产物详情和后台治理页面。
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
        <MetricCard label="智能体" value={agentCount} />
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
  )
}
