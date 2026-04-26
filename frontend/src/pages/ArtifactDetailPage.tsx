import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import {
  archiveArtifact,
  exportArtifact,
  fetchArtifact,
  previewArtifact,
  shareArtifact,
  type ArtifactActionResult,
  type ArtifactPreview,
  type ArtifactRecord,
} from '../api/artifacts'

export function ArtifactDetailPage() {
  const { artifactId } = useParams<{ artifactId: string }>()
  const [artifact, setArtifact] = useState<ArtifactRecord | null>(null)
  const [preview, setPreview] = useState<ArtifactPreview | null>(null)
  const [actionResult, setActionResult] = useState<ArtifactActionResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [loadingAction, setLoadingAction] = useState<string | null>(null)

  useEffect(() => {
    if (!artifactId) {
      return
    }
    const currentArtifactId = artifactId

    async function load() {
      try {
        const data = await fetchArtifact(currentArtifactId)
        setArtifact(data.data)
        setError(null)
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : 'Unknown API error')
      }
    }

    load()
  }, [artifactId])

  async function runAction(action: 'preview' | 'export' | 'share' | 'archive') {
    if (!artifactId) {
      return
    }
    setLoadingAction(action)
    setActionError(null)
    try {
      if (action === 'preview') {
        const data = await previewArtifact(artifactId)
        setPreview(data.data)
        setActionResult(null)
        return
      }
      const data =
        action === 'export'
          ? await exportArtifact(artifactId)
          : action === 'share'
            ? await shareArtifact(artifactId)
            : await archiveArtifact(artifactId)
      setActionResult(data.data)
    } catch (loadError) {
      setActionError(loadError instanceof Error ? loadError.message : 'Unknown API error')
    } finally {
      setLoadingAction(null)
    }
  }

  if (error) {
    return (
      <section className="panel">
        <Link to="/workspace/artifacts" className="back-link">
          返回产物中心
        </Link>
        <div className="error-banner">产物详情加载失败：{error}</div>
      </section>
    )
  }

  if (!artifact) {
    return (
      <section className="panel">
        <Link to="/workspace/artifacts" className="back-link">
          返回产物中心
        </Link>
        <p>正在加载产物详情...</p>
      </section>
    )
  }

  return (
    <section className="detail-grid">
      <article className="panel detail-main">
        <Link to="/workspace/artifacts" className="back-link">
          返回产物中心
        </Link>
        <div className="panel-head">
          <div>
            <span className="card-kicker">Artifact Detail</span>
            <h2>{artifact.title}</h2>
          </div>
          <div className="detail-actions">
            <span className="badge">{artifact.artifact_type}</span>
            <button type="button" className="secondary-action" onClick={() => runAction('preview')}>
              {loadingAction === 'preview' ? '预览中...' : '预览'}
            </button>
            <button type="button" className="secondary-action" onClick={() => runAction('export')}>
              {loadingAction === 'export' ? '导出中...' : '导出'}
            </button>
            <button type="button" className="secondary-action" onClick={() => runAction('share')}>
              {loadingAction === 'share' ? '分享中...' : '分享'}
            </button>
            <button type="button" className="primary-action" onClick={() => runAction('archive')}>
              {loadingAction === 'archive' ? '归档中...' : '归档'}
            </button>
          </div>
        </div>
        {actionError && <div className="error-banner">产物操作失败：{actionError}</div>}
        {actionResult && (
          <div className="info-banner">
            操作完成：{actionResult.action} / {actionResult.status}
            {actionResult.download_url ? ` / ${actionResult.download_url}` : ''}
            {actionResult.share_url ? ` / ${actionResult.share_url}` : ''}
          </div>
        )}

        <div className="detail-fields">
          <div>
            <span>产物 ID</span>
            <strong>{artifact.artifact_id}</strong>
          </div>
          <div>
            <span>来源 Run</span>
            <strong>
              <Link to={`/workspace/tasks/${artifact.run_id}`}>{artifact.run_id}</Link>
            </strong>
          </div>
          <div>
            <span>产物类型</span>
            <strong>{artifact.artifact_type}</strong>
          </div>
          <div>
            <span>创建时间</span>
            <strong>{artifact.created_at}</strong>
          </div>
        </div>

        <div className="status-message">
          <span>摘要</span>
          <p>{artifact.summary || '暂无摘要'}</p>
        </div>
        {preview && (
          <div className="status-message">
            <span>预览内容</span>
            <pre className="inline-json-viewer">{JSON.stringify(preview.content, null, 2)}</pre>
          </div>
        )}
      </article>

      <aside className="panel detail-side">
        <div className="panel-head">
          <div>
            <span className="card-kicker">Payload</span>
            <h2>结构化内容</h2>
          </div>
        </div>
        <pre className="json-viewer">{JSON.stringify(artifact.payload, null, 2)}</pre>
      </aside>
    </section>
  )
}
