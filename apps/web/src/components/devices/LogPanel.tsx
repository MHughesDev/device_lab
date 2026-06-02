// Backend-process log panel — Phase 11 (11-06)
// SSE feed with level/source filters, autoscroll, and download.

import { useEffect, useRef, useState, useCallback } from "react"
import { Download, Search, ChevronDown } from "lucide-react"
import { subscribeDeviceLogs, type LogEvent } from "@/lib/deviceLogs"

const LEVEL_COLORS: Record<string, string> = {
  debug: "text-muted-foreground",
  info: "text-foreground",
  warn: "text-yellow-600 dark:text-yellow-400",
  error: "text-red-600 dark:text-red-400",
}

const ALL_SOURCES = [
  "lifecycle", "provisioner", "transport", "stream",
  "mcp", "recording", "manifest", "ledger",
]

interface Props {
  deviceId: string
}

export function LogPanel({ deviceId }: Props) {
  const [events, setEvents] = useState<LogEvent[]>([])
  const [levelFilter, setLevelFilter] = useState<Set<string>>(new Set(["debug", "info", "warn", "error"]))
  const [sourceFilter, setSourceFilter] = useState<Set<string>>(new Set(ALL_SOURCES))
  const [search, setSearch] = useState("")
  const [autoScroll, setAutoScroll] = useState(true)
  const bottomRef = useRef<HTMLDivElement>(null)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const MAX = 2_000
    const unsub = subscribeDeviceLogs(deviceId, (ev) => {
      setEvents((prev) => {
        const next = [...prev, ev]
        return next.length > MAX ? next.slice(next.length - MAX) : next
      })
    })
    return unsub
  }, [deviceId])

  useEffect(() => {
    if (autoScroll) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" })
    }
  }, [events, autoScroll])

  const handleScroll = useCallback(() => {
    const el = scrollRef.current
    if (!el) return
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 40
    setAutoScroll(atBottom)
  }, [])

  function toggleLevel(l: string) {
    setLevelFilter((prev) => {
      const s = new Set(prev)
      s.has(l) ? s.delete(l) : s.add(l)
      return s
    })
  }

  function toggleSource(src: string) {
    setSourceFilter((prev) => {
      const s = new Set(prev)
      s.has(src) ? s.delete(src) : s.add(src)
      return s
    })
  }

  function downloadLogs() {
    const text = events.map((e) => `${e.ts} [${e.level}] [${e.source}] ${e.msg}`).join("\n")
    const blob = new Blob([text], { type: "text/plain" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `device-${deviceId.slice(0, 8)}-logs.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  const filtered = events.filter(
    (e) =>
      levelFilter.has(e.level) &&
      sourceFilter.has(e.source) &&
      (!search || e.msg.toLowerCase().includes(search.toLowerCase())),
  )

  return (
    <div className="flex flex-col h-full border-t bg-background">
      {/* toolbar */}
      <div className="flex items-center gap-2 px-3 py-1.5 border-b text-xs shrink-0 flex-wrap">
        <div className="flex items-center gap-1">
          {(["debug", "info", "warn", "error"] as const).map((l) => (
            <button
              key={l}
              onClick={() => toggleLevel(l)}
              className={`px-1.5 py-0.5 rounded capitalize transition-opacity ${
                levelFilter.has(l) ? "opacity-100" : "opacity-30"
              } ${LEVEL_COLORS[l]}`}
            >
              {l}
            </button>
          ))}
        </div>

        <div className="w-px h-4 bg-border" />

        <div className="flex items-center gap-1 flex-wrap">
          {ALL_SOURCES.map((src) => (
            <button
              key={src}
              onClick={() => toggleSource(src)}
              className={`px-1.5 py-0.5 rounded bg-muted transition-opacity ${
                sourceFilter.has(src) ? "opacity-100" : "opacity-30"
              }`}
            >
              {src}
            </button>
          ))}
        </div>

        <div className="flex-1" />

        <div className="flex items-center gap-1 rounded border px-2 py-0.5">
          <Search className="h-3 w-3 text-muted-foreground" />
          <input
            className="bg-transparent outline-none w-28 placeholder:text-muted-foreground"
            placeholder="Filter…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <button onClick={downloadLogs} title="Download logs">
          <Download className="h-3.5 w-3.5 text-muted-foreground hover:text-foreground" />
        </button>
      </div>

      {/* log output */}
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto font-mono text-xs p-3 space-y-0.5"
      >
        {filtered.length === 0 && (
          <p className="text-muted-foreground italic">No log events yet…</p>
        )}
        {filtered.map((e, i) => (
          <div key={i} className="flex gap-2 leading-5">
            <span className="text-muted-foreground shrink-0">
              {new Date(e.ts).toISOString().slice(11, 23)}
            </span>
            <span className={`shrink-0 w-12 ${LEVEL_COLORS[e.level]}`}>[{e.level}]</span>
            <span className="shrink-0 text-muted-foreground w-24 truncate">[{e.source}]</span>
            <span className="break-all">{e.msg}</span>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* autoscroll indicator */}
      {!autoScroll && (
        <button
          onClick={() => {
            setAutoScroll(true)
            bottomRef.current?.scrollIntoView({ behavior: "smooth" })
          }}
          className="absolute bottom-12 right-4 flex items-center gap-1 rounded-full bg-primary text-primary-foreground text-xs px-2 py-1 shadow"
        >
          <ChevronDown className="h-3 w-3" /> Latest
        </button>
      )}
    </div>
  )
}
