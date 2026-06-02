// Screen pane — Phase 11 (11-07, 11-10)
// WebRTC video+audio+input when interactive; headless placeholder + Attach affordance otherwise.

import { useEffect, useRef, useState, useCallback } from "react"
import { Monitor, Plug, Unplug, Volume2, VolumeX, Wifi, WifiOff } from "lucide-react"
import { toast } from "sonner"
import { negotiateSession, type WebRTCSession } from "@/lib/webrtc/client"
import { createInputSender, getModifiers } from "@/lib/webrtc/input"
import { ClipboardSync } from "@/lib/webrtc/clipboard"
import { FileDrop } from "./FileDrop"

interface Props {
  deviceId: string
  displayMode: "headless" | "interactive"
  deviceState: string
  onAttach(): Promise<void>
  onDetach(): Promise<void>
}

type ConnState = "idle" | "connecting" | "connected" | "failed"

export function ScreenPane({ deviceId, displayMode, deviceState, onAttach, onDetach }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const audioRef = useRef<HTMLAudioElement>(null)
  const sessionRef = useRef<WebRTCSession | null>(null)
  const clipboardRef = useRef<ClipboardSync | null>(null)
  const [connState, setConnState] = useState<ConnState>("idle")
  const [muted, setMuted] = useState(false)
  const [attaching, setAttaching] = useState(false)
  const [latencyMs, setLatencyMs] = useState<number | null>(null)
  const pingInterval = useRef<ReturnType<typeof setInterval> | null>(null)

  const ready = deviceState === "ready"

  // Connect WebRTC when interactive+ready
  useEffect(() => {
    if (displayMode !== "interactive" || !ready) return

    let cancelled = false

    async function connect() {
      setConnState("connecting")
      try {
        const session = await negotiateSession(deviceId)
        if (cancelled) { session.close(); return }
        sessionRef.current = session
        clipboardRef.current = new ClipboardSync(session.clipboardChannel)

        if (videoRef.current && session.videoTrack) {
          const stream = new MediaStream([session.videoTrack])
          videoRef.current.srcObject = stream
          await videoRef.current.play().catch(() => {})
        }
        if (audioRef.current && session.audioTrack) {
          const stream = new MediaStream([session.audioTrack])
          audioRef.current.srcObject = stream
          await audioRef.current.play().catch(() => {})
        }

        session.peer.onconnectionstatechange = () => {
          if (session.peer.connectionState === "failed") setConnState("failed")
          if (session.peer.connectionState === "connected") setConnState("connected")
        }

        setConnState("connected")

        // Latency probe via ping/pong over input channel
        pingInterval.current = setInterval(() => {
          if (session.inputChannel.readyState === "open") {
            const t0 = performance.now()
            session.inputChannel.send(JSON.stringify({ kind: "ping", t: t0 }))
          }
        }, 2_000)
        session.inputChannel.onmessage = (e) => {
          try {
            const msg = JSON.parse(e.data as string)
            if (msg.kind === "pong") setLatencyMs(Math.round(performance.now() - msg.t))
          } catch {}
        }
      } catch (err) {
        if (!cancelled) {
          setConnState("failed")
          toast.error(`Stream failed: ${err instanceof Error ? err.message : String(err)}`)
        }
      }
    }

    connect()

    return () => {
      cancelled = true
      if (pingInterval.current) clearInterval(pingInterval.current)
      sessionRef.current?.close()
      sessionRef.current = null
      clipboardRef.current = null
    }
  }, [deviceId, displayMode, ready])

  // Mouse input
  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLVideoElement>) => {
    const session = sessionRef.current
    if (!session) return
    const rect = e.currentTarget.getBoundingClientRect()
    const x = (e.clientX - rect.left) / rect.width
    const y = (e.clientY - rect.top) / rect.height
    createInputSender(session.inputChannel).move(x, y)
  }, [])

  const handleMouseDown = useCallback((e: React.MouseEvent<HTMLVideoElement>) => {
    const session = sessionRef.current
    if (!session) return
    const rect = e.currentTarget.getBoundingClientRect()
    const x = (e.clientX - rect.left) / rect.width
    const y = (e.clientY - rect.top) / rect.height
    createInputSender(session.inputChannel).mousedown(x, y, e.button)
  }, [])

  const handleMouseUp = useCallback((e: React.MouseEvent<HTMLVideoElement>) => {
    const session = sessionRef.current
    if (!session) return
    const rect = e.currentTarget.getBoundingClientRect()
    const x = (e.clientX - rect.left) / rect.width
    const y = (e.clientY - rect.top) / rect.height
    createInputSender(session.inputChannel).mouseup(x, y, e.button)
  }, [])

  const handleWheel = useCallback((e: React.WheelEvent<HTMLVideoElement>) => {
    const session = sessionRef.current
    if (!session) return
    const rect = e.currentTarget.getBoundingClientRect()
    const x = (e.clientX - rect.left) / rect.width
    const y = (e.clientY - rect.top) / rect.height
    createInputSender(session.inputChannel).scroll(x, y, e.deltaX / 100, e.deltaY / 100)
  }, [])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    const session = sessionRef.current
    if (!session) return
    e.preventDefault()
    createInputSender(session.inputChannel).keydown(e.key, getModifiers(e.nativeEvent))
  }, [])

  const handleKeyUp = useCallback((e: React.KeyboardEvent) => {
    const session = sessionRef.current
    if (!session) return
    createInputSender(session.inputChannel).keyup(e.key, getModifiers(e.nativeEvent))
  }, [])

  async function handleAttach() {
    setAttaching(true)
    try {
      await onAttach()
    } catch (err) {
      toast.error(`Attach failed: ${err instanceof Error ? err.message : String(err)}`)
    } finally {
      setAttaching(false)
    }
  }

  async function handleDetach() {
    await onDetach()
  }

  // ── Headless placeholder
  if (displayMode === "headless") {
    return (
      <div className="flex flex-col items-center justify-center h-full bg-muted/30 gap-4">
        <Monitor className="h-12 w-12 text-muted-foreground" />
        <div className="text-center space-y-1">
          <p className="font-medium text-sm">Headless — fully agent-operable via MCP</p>
          <p className="text-xs text-muted-foreground max-w-xs">
            No display attached. Agents can observe and control this device through MCP.
            Click Attach to add a live view and keyboard/mouse input.
          </p>
        </div>
        <button
          onClick={handleAttach}
          disabled={attaching || !ready}
          className="flex items-center gap-2 rounded-md bg-primary text-primary-foreground px-4 py-2 text-sm font-medium disabled:opacity-50"
        >
          <Plug className="h-4 w-4" />
          {attaching ? "Attaching…" : "Attach interactive session"}
        </button>
        {!ready && (
          <p className="text-xs text-muted-foreground">
            Device must be in ready state to attach
          </p>
        )}
      </div>
    )
  }

  // ── Interactive: WebRTC view
  return (
    <FileDrop deviceId={deviceId}>
      <div className="relative h-full bg-black flex items-center justify-center">
        {/* connection overlay */}
        {connState === "connecting" && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/70 z-10">
            <div className="text-center space-y-2 text-white">
              <div className="animate-spin h-6 w-6 border-2 border-white border-t-transparent rounded-full mx-auto" />
              <p className="text-sm">Connecting stream…</p>
            </div>
          </div>
        )}

        {connState === "failed" && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/70 z-10">
            <div className="text-center space-y-2">
              <WifiOff className="h-8 w-8 text-red-400 mx-auto" />
              <p className="text-sm text-white">Stream failed</p>
              <button
                onClick={() => setConnState("idle")}
                className="text-xs text-white underline"
              >
                Retry
              </button>
            </div>
          </div>
        )}

        {/* video */}
        <video
          ref={videoRef}
          className="max-h-full max-w-full object-contain cursor-crosshair"
          autoPlay
          playsInline
          tabIndex={0}
          onMouseMove={handleMouseMove}
          onMouseDown={handleMouseDown}
          onMouseUp={handleMouseUp}
          onWheel={handleWheel}
          onKeyDown={handleKeyDown}
          onKeyUp={handleKeyUp}
          onContextMenu={(e) => e.preventDefault()}
        />

        {/* hidden audio */}
        <audio ref={audioRef} autoPlay playsInline hidden />

        {/* HUD */}
        <div className="absolute top-2 right-2 flex items-center gap-2 text-xs text-white/70">
          {latencyMs !== null && (
            <span className="bg-black/50 rounded px-1.5 py-0.5">{latencyMs} ms</span>
          )}
          {connState === "connected" ? (
            <Wifi className="h-3.5 w-3.5 text-green-400" />
          ) : (
            <WifiOff className="h-3.5 w-3.5 text-red-400" />
          )}
          <button
            onClick={() => {
              setMuted(!muted)
              if (audioRef.current) audioRef.current.muted = !muted
            }}
            className="bg-black/50 rounded p-1"
            title={muted ? "Unmute" : "Mute"}
          >
            {muted ? <VolumeX className="h-3.5 w-3.5" /> : <Volume2 className="h-3.5 w-3.5" />}
          </button>
          <button
            onClick={handleDetach}
            className="bg-black/50 rounded p-1"
            title="Detach interactive session"
          >
            <Unplug className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>
    </FileDrop>
  )
}
