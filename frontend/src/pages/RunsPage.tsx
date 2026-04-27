import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'

import { createRun, fetchRuns, type CreateRunPayload, type RunRecord } from '../api/runs'
import { RunsTable } from '../components/RunsTable'
import { useCurrentPermissions } from '../hooks/useCurrentPermissions'

type RunsPageProps = {
  admin?: boolean
}

export function RunsPage({ admin = false }: RunsPageProps) {
  const [runs, setRuns] = useState<RunRecord[]>([])
  const [error, setError] = useState<string | null>(null)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [creating, setCreating] = useState(false)
  const { permissions, hasPermission } = useCurrentPermissions()
  const canCreateRun = hasPermission('run:create')
  const [form, setForm] = useState<CreateRunPayload>({
    run_type: 'chat_run',
    origin: admin ? 'admin_console' : 'workspace',
    owner_agent: '',
    status_message: 'Created from separated frontend.',
  })

  async function loadRuns() {
    try {
      const data = await fetchRuns()
      setRuns(data.data.items)
      setError(null)
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Unknown API error')
    }
  }

  useEffect(() => {
    let ignore = false

    fetchRuns()
      .then((data) => {
        if (ignore) {
          return
        }
        setRuns(data.data.items)
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

  async function handleCreateRun(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setCreating(true)
    try {
      await createRun({
        ...form,
        owner_agent: form.owner_agent?.trim() || undefined,
        status_message: form.status_message?.trim() || 'Created from separated frontend.',
      })
      setShowCreateForm(false)
      await loadRuns()
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : 'Unknown API error')
    } finally {
      setCreating(false)
    }
  }

  return (
    <>
      {error && <div className="error-banner">Run 数据加载失败：{error}</div>}
      {permissions && !canCreateRun && <div className="info-banner">当前角色仅可查看 Run，暂无新建权限。</div>}
      <RunsTable
        runs={runs}
        title={admin ? '后台 Run 控制台' : '我的任务'}
        admin={admin}
        action={
          <button
            type="button"
            className="primary-action"
            disabled={!canCreateRun}
            onClick={() => setShowCreateForm((value) => !value)}
          >
            {showCreateForm ? '收起' : '新建 Run'}
          </button>
        }
      />
      {showCreateForm && canCreateRun && (
        <section className="panel form-panel">
          <div className="panel-head">
            <div>
              <span className="card-kicker">Create Run</span>
              <h2>新建任务</h2>
            </div>
          </div>
          <form className="run-form" onSubmit={handleCreateRun}>
            <label>
              <span>Run 类型</span>
              <select
                value={form.run_type}
                onChange={(event) => setForm((value) => ({ ...value, run_type: event.target.value }))}
              >
                <option value="chat_run">chat_run</option>
                <option value="digest_run">digest_run</option>
                <option value="pipeline_run">pipeline_run</option>
                <option value="import_run">import_run</option>
                <option value="simulation_run">simulation_run</option>
                <option value="calibration_run">calibration_run</option>
                <option value="data_sync_run">data_sync_run</option>
                <option value="system_run">system_run</option>
                <option value="repair_run">repair_run</option>
              </select>
            </label>
            <label>
              <span>来源</span>
              <input
                value={form.origin}
                onChange={(event) => setForm((value) => ({ ...value, origin: event.target.value }))}
              />
            </label>
            <label>
              <span>负责人 Agent</span>
              <input
                value={form.owner_agent}
                placeholder="例如 design_specialist"
                onChange={(event) => setForm((value) => ({ ...value, owner_agent: event.target.value }))}
              />
            </label>
            <label>
              <span>状态说明</span>
              <textarea
                value={form.status_message}
                onChange={(event) => setForm((value) => ({ ...value, status_message: event.target.value }))}
              />
            </label>
            <button type="submit" className="primary-action" disabled={creating}>
              {creating ? '创建中...' : '创建 Run'}
            </button>
          </form>
        </section>
      )}
    </>
  )
}
