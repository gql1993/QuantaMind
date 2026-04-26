import { useEffect, useState } from 'react'

import {
  fetchApprovals,
  fetchAuditEvents,
  fetchAuditSummary,
  type ApprovalRecord,
  type AuditEventRecord,
  type AuditSummary,
} from '../api/audit'
import { MetricCard } from '../components/MetricCard'

export function AdminAuditPage() {
  const [approvals, setApprovals] = useState<ApprovalRecord[]>([])
  const [events, setEvents] = useState<AuditEventRecord[]>([])
  const [summary, setSummary] = useState<AuditSummary | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let ignore = false

    Promise.all([fetchApprovals(), fetchAuditEvents(), fetchAuditSummary()])
      .then(([approvalData, eventData, summaryData]) => {
        if (ignore) {
          return
        }
        setApprovals(approvalData.data.items)
        setEvents(eventData.data.items)
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
      {error && <div className="error-banner">审批/审计加载失败：{error}</div>}

      <section className="admin-hero panel">
        <div>
          <span className="card-kicker">Approval & Audit</span>
          <h2>审批 / 审计</h2>
          <p>集中查看高风险操作审批、权限读取、Run 操作和智能体策略审计记录。</p>
        </div>
      </section>

      <section className="metric-grid">
        <MetricCard label="审批总数" value={summary?.approval_count ?? '-'} />
        <MetricCard label="待审批" value={summary?.pending_count ?? '-'} />
        <MetricCard label="审计事件" value={summary?.audit_event_count ?? '-'} />
        <MetricCard label="高风险" value={summary?.high_risk_count ?? '-'} />
      </section>

      <section className="system-grid">
        <article className="panel">
          <div className="panel-head">
            <div>
              <span className="card-kicker">Approvals</span>
              <h2>审批事项</h2>
            </div>
          </div>
          <div className="module-list">
            {approvals.map((approval) => (
              <article className="module-card" key={approval.approval_id}>
                <div>
                  <span>{approval.approval_type}</span>
                  <h3>{approval.title}</h3>
                  <small>
                    申请人：{approval.requester} · 创建时间：{approval.created_at}
                  </small>
                </div>
                <div className="governance-status">
                  <span className={approval.status === 'approved' ? 'badge completed' : 'badge running'}>
                    {approval.status}
                  </span>
                  <span className={approval.risk_level === 'high' ? 'badge failed' : 'badge'}>
                    {approval.risk_level}
                  </span>
                </div>
              </article>
            ))}
          </div>
        </article>

        <article className="panel">
          <div className="panel-head">
            <div>
              <span className="card-kicker">Audit Log</span>
              <h2>审计事件</h2>
            </div>
          </div>
          <div className="timeline">
            {events.map((event) => (
              <article className="timeline-item" key={event.event_id}>
                <span>{event.created_at}</span>
                <h3>{event.action}</h3>
                <p>
                  {event.actor} · {event.target} · {event.result}
                </p>
              </article>
            ))}
          </div>
        </article>
      </section>
    </>
  )
}
