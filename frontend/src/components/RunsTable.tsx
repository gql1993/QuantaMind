import { Link } from 'react-router-dom'
import type { ReactNode } from 'react'

import type { RunRecord } from '../api/runs'

type RunsTableProps = {
  runs: RunRecord[]
  title: string
  admin?: boolean
  action?: ReactNode
}

export function RunsTable({ runs, title, admin = false, action }: RunsTableProps) {
  const basePath = admin ? '/admin/runs' : '/workspace/tasks'

  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <span className="card-kicker">{admin ? 'Admin' : 'Workspace'}</span>
          <h2>{title}</h2>
        </div>
        {action}
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
              <td>
                <Link to={`${basePath}/${run.run_id}`}>{run.run_id}</Link>
              </td>
              <td>{run.run_type}</td>
              <td>{run.stage}</td>
              <td>
                <span className={`badge ${run.state}`}>{run.state}</span>
              </td>
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
