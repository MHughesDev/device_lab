// SSE-based device log stream client — Phase 11 (11-06)

export interface LogEvent {
  ts: string
  level: "debug" | "info" | "warn" | "error"
  source: string
  msg: string
  fields?: Record<string, unknown>
}

export type LogHandler = (event: LogEvent) => void

export function subscribeDeviceLogs(deviceId: string, handler: LogHandler): () => void {
  const url = `/api/v1/devices/${deviceId}/logs/stream`
  let es: EventSource | null = null
  let closed = false
  let retryTimeout: ReturnType<typeof setTimeout> | null = null

  function connect() {
    if (closed) return
    es = new EventSource(url)
    es.onmessage = (e) => {
      try {
        handler(JSON.parse(e.data) as LogEvent)
      } catch {
        // malformed event — ignore
      }
    }
    es.onerror = () => {
      es?.close()
      es = null
      if (!closed) {
        retryTimeout = setTimeout(connect, 3_000)
      }
    }
  }

  connect()

  return () => {
    closed = true
    if (retryTimeout) clearTimeout(retryTimeout)
    es?.close()
  }
}
