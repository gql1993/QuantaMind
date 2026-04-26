import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { fetchArtifacts, type ArtifactRecord } from '../api/artifacts'

export function ArtifactsPage() {
  const [artifacts, setArtifacts] = useState<ArtifactRecord[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchArtifacts()
        setArtifacts(data.data.items)
        setError(null)
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : 'Unknown API error')
      }
    }

    load()
  }, [])

  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <span className="card-kicker">Artifacts</span>
          <h2>产物中心</h2>
        </div>
      </div>
      {error && <div className="error-banner">产物数据加载失败：{error}</div>}
      <div className="artifact-list">
        {artifacts.map((artifact) => (
          <article className="artifact-card" key={artifact.artifact_id}>
            <span>{artifact.artifact_type}</span>
            <h3>
              <Link to={`/workspace/artifacts/${artifact.artifact_id}`}>{artifact.title}</Link>
            </h3>
            <p>{artifact.summary}</p>
            <small>来源 Run：{artifact.run_id}</small>
          </article>
        ))}
      </div>
    </section>
  )
}
