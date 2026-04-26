import { useState } from 'react'

import { streamChatMessage } from '../api/chat'

type ChatMessage = {
  role: 'user' | 'assistant' | 'system'
  content: string
  runId?: string
}

export function AiWorkbenchPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'system',
      content: '欢迎使用量智大脑 AI 工作台。输入问题后，前端会通过 /api/v1/chat/stream 接收流式回复。',
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSend() {
    const message = input.trim()
    if (!message || loading) {
      return
    }
    setInput('')
    setLoading(true)
    const assistantIndex = messages.length + 1
    setMessages((items) => [...items, { role: 'user', content: message }, { role: 'assistant', content: '' }])

    await streamChatMessage(message, {
      onEvent: (event) => {
        if (event.type === 'run') {
          setMessages((items) =>
            items.map((item, index) => (index === assistantIndex ? { ...item, runId: event.run_id } : item)),
          )
          return
        }
        if (event.type === 'content') {
          setMessages((items) =>
            items.map((item, index) =>
              index === assistantIndex
                ? { ...item, content: `${item.content}${event.data}`, runId: event.run_id }
                : item,
            ),
          )
          return
        }
        if (event.type === 'done') {
          setLoading(false)
          return
        }
        if (event.type === 'error') {
          setMessages((items) =>
            items.map((item, index) =>
              index === assistantIndex ? { ...item, content: `调用失败：${event.data}` } : item,
            ),
          )
          setLoading(false)
        }
      },
      onError: (error) => {
        setMessages((items) =>
          items.map((item, index) =>
            index === assistantIndex ? { ...item, content: `调用失败：${error.message}` } : item,
          ),
        )
        setLoading(false)
      },
    })
    setLoading(false)
  }

  return (
    <section className="ai-layout">
      <div className="chat-panel">
        <div className="panel-head">
          <div>
            <span className="card-kicker">AI Workbench</span>
            <h2>AI 工作台</h2>
          </div>
          <span className={loading ? 'badge running' : 'badge completed'}>{loading ? '生成中' : '就绪'}</span>
        </div>
        <div className="message-list">
          {messages.map((message, index) => (
            <article className={`message ${message.role}`} key={`${message.role}-${index}`}>
              <span>{message.role}</span>
              <p>{message.content}</p>
              {message.runId && <small>关联 Run：{message.runId}</small>}
            </article>
          ))}
        </div>
        <div className="chat-composer">
          <textarea
            value={input}
            placeholder="例如：帮我分析 20 比特芯片设计风险，并生成下一步建议"
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
                handleSend()
              }
            }}
          />
          <button type="button" className="primary-action" disabled={loading} onClick={handleSend}>
            {loading ? '发送中...' : '发送'}
          </button>
        </div>
      </div>
      <aside className="context-panel">
        <h3>执行说明</h3>
        <p>当前页面使用 POST SSE 流式接口，并自动生成一个 `chat_run`，可以在任务中心继续查看。</p>
        <h3>快捷问题</h3>
        <ul>
          <li>检查当前系统状态</li>
          <li>帮我生成今日情报摘要</li>
          <li>分析芯片设计参数风险</li>
        </ul>
      </aside>
    </section>
  )
}
