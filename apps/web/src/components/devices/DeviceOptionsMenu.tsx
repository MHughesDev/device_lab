// Per-device options menu — Phase 11 (11-12, 11-13)
// Full action set items a–q from the phase spec.

import { useState } from "react"
import { useQueryClient } from "@tanstack/react-query"
import {
  MoreHorizontal,
  Radio,
  Plug,
  Unplug,
  Pencil,
  BookmarkPlus,
  RotateCcw,
  Square,
  Trash2,
  Video,
  Monitor,
  FileText,
  Upload,
  Download,
  Clipboard,
  Volume2,
  Cpu,
  Network,
  Copy,
  Pin,
  PinOff,
} from "lucide-react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { toast } from "sonner"
import { DeviceTabStore } from "@/stores/deviceTabs"
import type { DeviceTab } from "@/stores/deviceTabs"
import type { Device } from "@/lib/types"

interface Props {
  tab: DeviceTab
  device: Device | undefined
  onRename(): void
  onAttach(): void
  onDetach(): void
  onFilePush(): void
  onFilePull(): void
  onClipboardToggle(): void
  clipboardEnabled: boolean
  audioMuted: boolean
  onAudioToggle(): void
}

export function DeviceOptionsMenu({
  tab,
  device,
  onRename,
  onAttach,
  onDetach,
  onFilePush,
  onFilePull,
  onClipboardToggle,
  clipboardEnabled,
  audioMuted,
  onAudioToggle,
}: Props) {
  const [terminateConfirm, setTerminateConfirm] = useState(false)
  const qc = useQueryClient()

  const deviceId = tab.id
  const interactive = tab.displayMode === "interactive"
  const ready = device?.state === "ready"
  const stopped = device?.state === "stopped"

  async function post(path: string, body?: unknown) {
    const res = await fetch(path, {
      method: "POST",
      headers: body ? { "Content-Type": "application/json" } : {},
      body: body ? JSON.stringify(body) : undefined,
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }))
      throw new Error(err.detail ?? res.statusText)
    }
    return res.json()
  }

  async function patch(path: string, body: unknown) {
    const res = await fetch(path, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }))
      throw new Error(err.detail ?? res.statusText)
    }
    return res.json()
  }

  async function toggleMcp() {
    try {
      await patch(`/api/v1/devices/${deviceId}`, { mcp_exposed: !tab.mcpExposed })
      DeviceTabStore.updateTab(deviceId, { mcpExposed: !tab.mcpExposed })
      qc.invalidateQueries({ queryKey: ["devices"] })
      toast.success(tab.mcpExposed ? "MCP disabled" : "MCP enabled")
    } catch (e: unknown) {
      toast.error(String(e))
    }
  }

  async function copyMcpUrl() {
    const url = `http://127.0.0.1:8000/mcp/devices/${deviceId}`
    await navigator.clipboard.writeText(url)
    toast.success("MCP connection string copied")
  }

  async function lifecycle(action: "stop" | "start" | "terminate") {
    try {
      await post(`/api/v1/devices/${deviceId}/lifecycle/${action}`)
      qc.invalidateQueries({ queryKey: ["devices"] })
      toast.success(`${action} initiated`)
    } catch (e: unknown) {
      toast.error(String(e))
    }
  }

  async function captureManifest() {
    const tid = toast.loading("Capturing environment manifest…")
    try {
      const manifest = await post(`/api/v1/devices/${deviceId}/manifest/capture`)
      qc.invalidateQueries({ queryKey: ["manifests"] })
      toast.success(`Manifest saved: "${manifest.name ?? manifest.id}"`, { id: tid })
    } catch (e: unknown) {
      toast.error(String(e), { id: tid })
    }
  }

  async function duplicateDevice() {
    if (!device?.source_manifest_id) {
      toast.error("No source manifest — capture a manifest first")
      return
    }
    const tid = toast.loading("Duplicating device…")
    try {
      await post("/api/v1/devices/", { manifest_id: device.source_manifest_id })
      qc.invalidateQueries({ queryKey: ["devices"] })
      toast.success("Duplicate device provisioning", { id: tid })
    } catch (e: unknown) {
      toast.error(String(e), { id: tid })
    }
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          className="rounded p-1 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
          title="Device options"
        >
          <MoreHorizontal className="h-4 w-4" />
        </button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel className="text-xs text-muted-foreground font-normal">
          {tab.title}
        </DropdownMenuLabel>
        <DropdownMenuSeparator />

        {/* a: MCP */}
        <DropdownMenuItem onClick={toggleMcp}>
          <Radio className="mr-2 h-4 w-4" />
          {tab.mcpExposed ? "Disable MCP server" : "Enable MCP server"}
        </DropdownMenuItem>
        {tab.mcpExposed && (
          <DropdownMenuItem onClick={copyMcpUrl}>
            <Copy className="mr-2 h-4 w-4" />
            Copy MCP connection string
          </DropdownMenuItem>
        )}

        <DropdownMenuSeparator />

        {/* b: Attach/Detach */}
        {interactive ? (
          <DropdownMenuItem onClick={onDetach}>
            <Unplug className="mr-2 h-4 w-4" />
            Detach interactive session
          </DropdownMenuItem>
        ) : (
          <DropdownMenuItem onClick={onAttach} disabled={!ready}>
            <Plug className="mr-2 h-4 w-4" />
            Attach interactive session
          </DropdownMenuItem>
        )}

        {/* c: Rename */}
        <DropdownMenuItem onClick={onRename}>
          <Pencil className="mr-2 h-4 w-4" />
          Rename
        </DropdownMenuItem>

        {/* d: Capture manifest */}
        <DropdownMenuItem onClick={captureManifest} disabled={!ready}>
          <BookmarkPlus className="mr-2 h-4 w-4" />
          Capture environment manifest…
        </DropdownMenuItem>

        <DropdownMenuSeparator />

        {/* e: Restart */}
        <DropdownMenuItem onClick={() => lifecycle("stop")} disabled={!ready}>
          <RotateCcw className="mr-2 h-4 w-4" />
          Restart device
        </DropdownMenuItem>

        {/* f: Stop / Terminate */}
        {ready && (
          <DropdownMenuItem onClick={() => lifecycle("stop")}>
            <Square className="mr-2 h-4 w-4" />
            Stop device
          </DropdownMenuItem>
        )}
        {stopped && (
          <DropdownMenuItem onClick={() => lifecycle("start")}>
            <Plug className="mr-2 h-4 w-4" />
            Start device
          </DropdownMenuItem>
        )}

        {!terminateConfirm ? (
          <DropdownMenuItem
            onClick={() => setTerminateConfirm(true)}
            className="text-red-600 dark:text-red-400"
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Terminate device…
          </DropdownMenuItem>
        ) : (
          <DropdownMenuItem
            onClick={() => { lifecycle("terminate"); setTerminateConfirm(false) }}
            className="text-red-600 dark:text-red-400 font-semibold"
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Confirm terminate
          </DropdownMenuItem>
        )}

        <DropdownMenuSeparator />

        {/* g: Recording (h: quality deferred) */}
        <DropdownMenuItem disabled>
          <Video className="mr-2 h-4 w-4" />
          Start screen recording
        </DropdownMenuItem>

        {/* h: Display quality — deferred (Phase 09) */}
        <DropdownMenuItem disabled title="Available once Phase 09 streaming ships">
          <Monitor className="mr-2 h-4 w-4" />
          Display & quality…
          <span className="ml-auto text-xs text-muted-foreground">soon</span>
        </DropdownMenuItem>

        {/* i: Logs */}
        <DropdownMenuItem asChild>
          <a href={`/api/v1/devices/${deviceId}/logs/stream`} target="_blank" rel="noreferrer">
            <FileText className="mr-2 h-4 w-4" />
            View full logs
          </a>
        </DropdownMenuItem>

        <DropdownMenuSeparator />

        {/* j/k: File push/pull */}
        <DropdownMenuItem onClick={onFilePush} disabled={!interactive}>
          <Upload className="mr-2 h-4 w-4" />
          Push file…
        </DropdownMenuItem>
        <DropdownMenuItem onClick={onFilePull} disabled={!interactive}>
          <Download className="mr-2 h-4 w-4" />
          Pull file…
        </DropdownMenuItem>

        {/* l: Clipboard sync */}
        <DropdownMenuItem onClick={onClipboardToggle} disabled={!interactive}>
          <Clipboard className="mr-2 h-4 w-4" />
          {clipboardEnabled ? "Disable clipboard sync" : "Enable clipboard sync"}
        </DropdownMenuItem>

        {/* m: Audio */}
        <DropdownMenuItem onClick={onAudioToggle} disabled={!interactive}>
          <Volume2 className="mr-2 h-4 w-4" />
          {audioMuted ? "Unmute device audio" : "Mute device audio"}
        </DropdownMenuItem>

        <DropdownMenuSeparator />

        {/* n: Resource usage — shown in HUD */}
        <DropdownMenuItem disabled>
          <Cpu className="mr-2 h-4 w-4" />
          Resource usage
          <span className="ml-auto text-xs text-muted-foreground">in HUD</span>
        </DropdownMenuItem>

        {/* o: Network proxy — deferred */}
        <DropdownMenuItem disabled title="Network proxy coming in a future phase">
          <Network className="mr-2 h-4 w-4" />
          Network proxy (mitmproxy)
          <span className="ml-auto text-xs text-muted-foreground">deferred</span>
        </DropdownMenuItem>

        {/* p: Duplicate */}
        <DropdownMenuItem onClick={duplicateDevice}>
          <Copy className="mr-2 h-4 w-4" />
          Duplicate device
        </DropdownMenuItem>

        {/* q: Pin/unpin tab */}
        <DropdownMenuItem onClick={() => DeviceTabStore.pinTab(deviceId, !tab.pinned)}>
          {tab.pinned ? (
            <>
              <PinOff className="mr-2 h-4 w-4" />
              Unpin tab
            </>
          ) : (
            <>
              <Pin className="mr-2 h-4 w-4" />
              Pin tab
            </>
          )}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
