import { useEffect, useState } from 'react'

import { fetchKnowledgeItems, fetchMemories, type KnowledgeItem, type MemoryItem } from '../api/knowledge'
import { MetricCard } from '../components/MetricCard'

export function KnowledgeMemoryPage() {
  const [items, setItems] = useState<KnowledgeItem[]>([])
  const [memories, setMemories] = useState<MemoryItem[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let ignore = false

    Promise.all([fetchKnowledgeItems(), fetchMemories()])
      .then(([knowledgeData, memoryData]) => {
        if (ignore) {
          return
        }
        setItems(knowledgeData.data.items)
        setMemories(memoryData.data.items)
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

  const tagCount = new Set(items.flatMap((item) => item.tags)).size

  return (
    <>
      {error && <div className="error-banner">知识库/记忆中心加载失败：{error}</div>}

      <section className="role-hero">
        <div>
          <span className="card-kicker">Knowledge & Memory</span>
          <h2>知识库 / 记忆中心</h2>
          <p>沉淀组织知识、角色偏好和 AI 工作台上下文，为后续检索增强和长期记忆提供入口。</p>
        </div>
      </section>

      <section className="metric-grid">
        <MetricCard label="知识条目" value={items.length} />
        <MetricCard label="记忆条目" value={memories.length} />
        <MetricCard label="标签数" value={tagCount} />
        <MetricCard label="平均置信度" value={averageConfidence(memories)} />
      </section>

      <section className="system-grid">
        <article className="panel">
          <div className="panel-head">
            <div>
              <span className="card-kicker">Knowledge</span>
              <h2>知识条目</h2>
            </div>
          </div>
          <div className="knowledge-list">
            {items.map((item) => (
              <article className="knowledge-card" key={item.item_id}>
                <span>{item.source}</span>
                <h3>{item.title}</h3>
                <p>{item.summary}</p>
                <div className="tag-list">
                  {item.tags.map((tag) => (
                    <span key={tag}>{tag}</span>
                  ))}
                </div>
                <small>更新时间：{item.updated_at}</small>
              </article>
            ))}
          </div>
        </article>

        <article className="panel">
          <div className="panel-head">
            <div>
              <span className="card-kicker">Memory</span>
              <h2>长期记忆</h2>
            </div>
          </div>
          <div className="module-list">
            {memories.map((memory) => (
              <article className="module-card" key={memory.memory_id}>
                <div>
                  <span>{memory.scope}</span>
                  <h3>{memory.content}</h3>
                  <small>最近使用：{memory.last_used_at}</small>
                </div>
                <span className="badge completed">{Math.round(memory.confidence * 100)}%</span>
              </article>
            ))}
          </div>
        </article>
      </section>
    </>
  )
}

function averageConfidence(memories: MemoryItem[]) {
  if (memories.length === 0) {
    return '-'
  }
  const average = memories.reduce((total, item) => total + item.confidence, 0) / memories.length
  return `${Math.round(average * 100)}%`
}
