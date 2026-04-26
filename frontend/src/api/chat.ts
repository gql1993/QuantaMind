import { postJson } from './client'

export type ChatResponse = {
  success: boolean
  data: {
    content: string
    run_id: string
    pipeline_id?: string | null
  }
  error: null
}

export type ChatStreamEvent =
  | { type: 'run'; run_id: string; session_id?: string | null }
  | { type: 'content'; data: string; run_id: string; session_id?: string | null }
  | {
      type: 'done'
      content: string
      run_id: string
      session_id?: string | null
      pipeline_id?: string | null
    }
  | { type: 'error'; data: string; run_id?: string; session_id?: string | null }

export function sendChatMessage(message: string, sessionId?: string | null) {
  return postJson<ChatResponse>('/api/v1/chat', {
    message,
    session_id: sessionId ?? undefined,
  })
}

export async function streamChatMessage(
  message: string,
  handlers: {
    onEvent: (event: ChatStreamEvent) => void | Promise<void>
    onError?: (error: Error) => void
  },
  sessionId?: string | null,
) {
  try {
    const response = await fetch('/api/v1/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        session_id: sessionId ?? undefined,
      }),
    })
    if (!response.ok) {
      throw new Error(`Request failed: ${response.status} ${response.statusText}`)
    }
    if (!response.body) {
      throw new Error('ReadableStream is not available in this browser.')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''

    while (true) {
      const { value, done } = await reader.read()
      if (done) {
        break
      }
      buffer += decoder.decode(value, { stream: true })
      const frames = buffer.split('\n\n')
      buffer = frames.pop() ?? ''
      for (const frame of frames) {
        const line = frame
          .split('\n')
          .find((item) => item.startsWith('data: '))
        if (!line) {
          continue
        }
        const raw = line.slice('data: '.length)
        await handlers.onEvent(JSON.parse(raw) as ChatStreamEvent)
      }
    }
  } catch (error) {
    handlers.onError?.(error instanceof Error ? error : new Error('Unknown stream error'))
  }
}
