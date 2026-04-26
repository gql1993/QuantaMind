export {}

declare global {
  interface Window {
    electronAPI?: {
      gatewayUrl: string
    }
  }
}
