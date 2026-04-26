import { useEffect, useState } from 'react'

import {
  fetchDataQuality,
  fetchDatasetCatalog,
  type DataQualityResponse,
  type DatasetRecord,
} from '../api/data'
import { MetricCard } from '../components/MetricCard'

export function DataCenterPage() {
  const [datasets, setDatasets] = useState<DatasetRecord[]>([])
  const [quality, setQuality] = useState<DataQualityResponse['data'] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let ignore = false

    Promise.all([fetchDatasetCatalog(), fetchDataQuality()])
      .then(([catalogData, qualityData]) => {
        if (ignore) {
          return
        }
        setDatasets(catalogData.data.items)
        setQuality(qualityData.data)
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
      {error && <div className="error-banner">数据中心加载失败：{error}</div>}

      <section className="role-hero">
        <div>
          <span className="card-kicker">Data Center</span>
          <h2>数据中心</h2>
          <p>统一管理设计、测控、制造等跨域数据资产，为后续数据接入、质量治理和分析看板提供入口。</p>
        </div>
      </section>

      <section className="metric-grid">
        <MetricCard label="数据集" value={datasets.length} />
        <MetricCard label="平均质量分" value={quality?.average_score ?? '-'} />
        <MetricCard label="健康数据集" value={quality?.healthy_count ?? '-'} />
        <MetricCard label="需关注" value={quality?.warning_count ?? '-'} />
      </section>

      <section className="system-grid">
        <article className="panel">
          <div className="panel-head">
            <div>
              <span className="card-kicker">Catalog</span>
              <h2>数据目录</h2>
            </div>
          </div>
          <div className="dataset-list">
            {datasets.map((dataset) => (
              <article className="dataset-card" key={dataset.dataset_id}>
                <div>
                  <span>{dataset.domain}</span>
                  <h3>{dataset.name}</h3>
                  <p>{dataset.owner}</p>
                </div>
                <div className="dataset-meta">
                  <strong>{dataset.record_count.toLocaleString()} 条</strong>
                  <span className={dataset.status === 'healthy' ? 'badge completed' : 'badge running'}>
                    {dataset.status}
                  </span>
                </div>
                <small>最近同步：{dataset.last_sync_at}</small>
              </article>
            ))}
          </div>
        </article>

        <article className="panel">
          <div className="panel-head">
            <div>
              <span className="card-kicker">Quality</span>
              <h2>数据质量规则</h2>
            </div>
          </div>
          <div className="module-list">
            {quality?.rules.map((rule) => (
              <article className="module-card" key={rule.rule_id}>
                <div>
                  <span>{rule.rule_id}</span>
                  <h3>{rule.label}</h3>
                </div>
                <span className={rule.status === 'ok' ? 'badge completed' : 'badge running'}>{rule.status}</span>
              </article>
            ))}
          </div>
        </article>
      </section>
    </>
  )
}
