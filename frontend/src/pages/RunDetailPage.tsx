import { Link, useNavigate, useParams } from 'react-router-dom'
import { useEffect, useState } from 'react'

import { cancelRun, fetchRun, fetchRunEvents, retryRun, type RunEvent, type RunRecord } from '../api/runs'
import { useCurrentPermissions } from '../hooks/useCurrentPermissions'

type RunDetailPageProps = {
  admin?: boolean
}

export function RunDetailPage({ admin = false }: RunDetailPageProps) {
  const { runId } = useParams<{ runId: string }>()
  const navigate = useNavigate()
  const [run, setRun] = useState<RunRecord | null>(null)
  const [events, setEvents] = useState<RunEvent[]>([])
  const [error, setError] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState<'cancel' | 'retry' | null>(null)
  const { permissions, hasPermission } = useCurrentPermissions()

  async function loadRunDetails(currentRunId: string) {
    try {
      const [runData, eventData] = await Promise.all([fetchRun(currentRunId), fetchRunEvents(currentRunId)])
      setRun(runData.data)
      setEvents(eventData.data.items)
      setError(null)
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Unknown API error')
    }
  }

  useEffect(() => {
    if (!runId) {
      return
    }
    const currentRunId = runId
    let ignore = false

    Promise.all([fetchRun(currentRunId), fetchRunEvents(currentRunId)])
      .then(([runData, eventData]) => {
        if (ignore) {
          return
        }
        setRun(runData.data)
        setEvents(eventData.data.items)
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
  }, [runId])

  const backPath = admin ? '/admin/runs' : '/workspace/tasks'
  const isReadOnlyV1 = run?.run_id.startsWith('v1-') ?? false
  const canCancelRun = hasPermission('run:cancel')
  const canRetryRun = hasPermission('run:retry')

  async function handleCancel() {
    if (!runId) {
      return
    }
    setActionLoading('cancel')
    setActionError(null)
    try {
      await cancelRun(runId)
      await loadRunDetails(runId)
    } catch (cancelError) {
      setActionError(cancelError instanceof Error ? cancelError.message : 'Unknown API error')
    } finally {
      setActionLoading(null)
    }
  }

  async function handleRetry() {
    if (!runId) {
      return
    }
    setActionLoading('retry')
    setActionError(null)
    try {
      const retryData = await retryRun(runId)
      navigate(`${backPath}/${retryData.data.run_id}`)
    } catch (retryError) {
      setActionError(retryError instanceof Error ? retryError.message : 'Unknown API error')
    } finally {
      setActionLoading(null)
    }
  }

  if (error) {
    return (
      <section className="panel">
        <Link to={backPath} className="back-link">
          返回 Run 列表
        </Link>
        <div className="error-banner">Run 详情加载失败：{error}</div>
      </section>
    )
  }

  if (!run) {
    return (
      <section className="panel">
        <Link to={backPath} className="back-link">
          返回 Run 列表
        </Link>
        <p>正在加载 Run 详情...</p>
      </section>
    )
  }

  return (
    <section className="detail-grid">
      <article className="panel detail-main">
        <Link to={backPath} className="back-link">
          返回 Run 列表
        </Link>
        <div className="panel-head">
          <div>
            <span className="card-kicker">{admin ? 'Admin Run Detail' : 'Run Detail'}</span>
            <h2>{run.run_id}</h2>
          </div>
          <div className="detail-actions">
            <span className={`badge ${run.state}`}>{run.state}</span>
            <button
              type="button"
              className="secondary-action"
              disabled={!canCancelRun || isReadOnlyV1 || actionLoading !== null || run.state === 'cancelled'}
              onClick={handleCancel}
            >
              {actionLoading === 'cancel' ? '取消中...' : '取消 Run'}
            </button>
            <button
              type="button"
              className="primary-action"
              disabled={!canRetryRun || isReadOnlyV1 || actionLoading !== null}
              onClick={handleRetry}
            >
              {actionLoading === 'retry' ? '重试中...' : '重试'}
            </button>
          </div>
        </div>
        {isReadOnlyV1 && <div className="info-banner">V1 兼容 Run 当前为只读，暂不支持取消或重试。</div>}
        {permissions && (!canCancelRun || !canRetryRun) && (
          <div className="info-banner">当前角色缺少取消或重试权限，相关操作已禁用。</div>
        )}
        {actionError && <div className="error-banner">Run 操作失败：{actionError}</div>}

        <div className="detail-fields">
          <div>
            <span>类型</span>
            <strong>{run.run_type}</strong>
          </div>
          <div>
            <span>阶段</span>
            <strong>{run.stage}</strong>
          </div>
          <div>
            <span>负责人</span>
            <strong>{run.owner_agent ?? '-'}</strong>
          </div>
          <div>
            <span>来源</span>
            <strong>{String(run.metadata.source ?? run.origin ?? '-')}</strong>
          </div>
          <div>
            <span>创建时间</span>
            <strong>{run.created_at}</strong>
          </div>
          <div>
            <span>更新时间</span>
            <strong>{run.updated_at}</strong>
          </div>
        </div>

        <div className="status-message">
          <span>当前状态说明</span>
          <p>{run.status_message || '暂无状态说明'}</p>
        </div>

        <div className="artifact-list compact">
          {run.artifacts.length > 0 ? (
            run.artifacts.map((artifactId) => (
              <article className="artifact-card" key={artifactId}>
                <span>Artifact</span>
                <h3>
                  <Link to={`/workspace/artifacts/${artifactId}`}>{artifactId}</Link>
                </h3>
              </article>
            ))
          ) : (
            <p>暂无关联产物。</p>
          )}
        </div>
      </article>

      <aside className="panel detail-side">
        <div className="panel-head">
          <div>
            <span className="card-kicker">Timeline</span>
            <h2>事件时间线</h2>
          </div>
        </div>
        <div className="timeline">
          {events.length > 0 ? (
            events.map((event) => (
              <article className="timeline-item" key={event.event_id}>
                <span>{event.created_at}</span>
                <h3>{event.event_type}</h3>
                <pre>{JSON.stringify(event.payload, null, 2)}</pre>
              </article>
            ))
          ) : (
            <p>暂无事件记录。</p>
          )}
        </div>
      </aside>
    </section>
  )
}
