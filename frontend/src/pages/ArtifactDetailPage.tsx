import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { fetchArtifact, type ArtifactRecord } from '../api/artifacts'

export function ArtifactDetailPage() {
  const { artifactId } = useParams<{ artifactId: string }>()
  const [artifact, setArtifact] = useState<ArtifactRecord | null>(null)
  const [error, setError] = useState<string | null>(null)

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
          <span className="badge">{artifact.artifact_type}</span>
        </div>

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
