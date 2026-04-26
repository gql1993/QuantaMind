import { useEffect, useState } from 'react'

import { fetchHealth, type HealthResponse } from '../api/health'
import { fetchSystemStatus, type SystemStatusResponse } from '../api/system'
import { MetricCard } from '../components/MetricCard'

export function AdminSystemPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [systemStatus, setSystemStatus] = useState<SystemStatusResponse['data']>({})
  const [error, setError] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState(false)

  async function loadSystemStatus() {
    setRefreshing(true)
    try {
      const [healthData, systemData] = await Promise.all([fetchHealth(), fetchSystemStatus()])
      setHealth(healthData)
      setSystemStatus(systemData.data)
      setError(null)
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Unknown API error')
    } finally {
      setRefreshing(false)
    }
  }

  useEffect(() => {
    let ignore = false

    Promise.all([fetchHealth(), fetchSystemStatus()])
      .then(([healthData, systemData]) => {
        if (ignore) {
          return
        }
        setHealth(healthData)
        setSystemStatus(systemData.data)
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

  const modules = Object.entries(systemStatus)
  const okCount = modules.filter(([, item]) => item.status === 'ok').length

  return (
    <>
      {error && <div className="error-banner">系统状态加载失败：{error}</div>}

      <section className="panel admin-hero">
        <div>
          <span className="card-kicker">Admin System</span>
          <h2>系统状态监控</h2>
          <p>用于后台查看分离式 API、前端工作台和运行时兼容层的可用状态。</p>
        </div>
        <button type="button" className="primary-action" disabled={refreshing} onClick={loadSystemStatus}>
          {refreshing ? '刷新中...' : '刷新状态'}
        </button>
      </section>

      <section className="metric-grid">
        <MetricCard label="服务状态" value={health?.data.status ?? 'unknown'} />
        <MetricCard label="模块数" value={modules.length} />
        <MetricCard label="OK 模块" value={okCount} />
        <MetricCard label="兼容/其他" value={Math.max(modules.length - okCount, 0)} />
      </section>

      <section className="system-grid">
        <article className="panel">
          <div className="panel-head">
            <div>
              <span className="card-kicker">Health</span>
              <h2>API 健康检查</h2>
            </div>
            <span className={health?.data.status === 'ok' ? 'status ok' : 'status'}>
              {health?.data.status ?? 'unknown'}
            </span>
          </div>
          <div className="detail-fields">
            <div>
              <span>服务</span>
              <strong>{health?.data.service ?? '-'}</strong>
            </div>
            <div>
              <span>最近响应</span>
              <strong>{health?.data.timestamp ?? '-'}</strong>
            </div>
          </div>
        </article>

        <article className="panel">
          <div className="panel-head">
            <div>
              <span className="card-kicker">Modules</span>
              <h2>模块状态</h2>
            </div>
          </div>
          <div className="module-list">
            {modules.map(([key, item]) => (
              <article className="module-card" key={key}>
                <div>
                  <span>{key}</span>
                  <h3>{item.label}</h3>
                </div>
                <span className={item.status === 'ok' ? 'badge completed' : 'badge'}>{item.status}</span>
              </article>
            ))}
          </div>
        </article>
      </section>
    </>
  )
}
