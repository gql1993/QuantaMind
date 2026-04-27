const API_BASE = import.meta.env.VITE_API_BASE_URL ?? window.electronAPI?.gatewayUrl ?? ''
const TOKEN_STORAGE_KEY = 'quantamind.demoAccessToken'
const TOKEN_CHANGED_EVENT = 'quantamind:access-token-changed'

export async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: authHeaders(),
  })
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status} ${response.statusText}`)
  }
  return response.json() as Promise<T>
}

export async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
    body: JSON.stringify(body),
  })
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status} ${response.statusText}`)
  }
  return response.json() as Promise<T>
}

export function setAccessToken(token: string) {
  window.localStorage.setItem(TOKEN_STORAGE_KEY, token)
  window.dispatchEvent(new Event(TOKEN_CHANGED_EVENT))
}

export function getAccessToken() {
  return window.localStorage.getItem(TOKEN_STORAGE_KEY)
}

export function onAccessTokenChanged(listener: () => void) {
  window.addEventListener(TOKEN_CHANGED_EVENT, listener)
  return () => window.removeEventListener(TOKEN_CHANGED_EVENT, listener)
}

function authHeaders(): Record<string, string> {
  const token = getAccessToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}
