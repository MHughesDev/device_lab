// Device workspace route — Phase 11 (11-01, 11-02)
// Browser-like tabbed layout: each open device is a tab.
// Tab close does NOT terminate the device — it only closes the view.

import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { useState, useEffect, useRef } from "react"
import { Plus, X, Pin, Monitor } from "lucide-react"
import { toast } from "sonner"
import { DeviceTabStore } from "@/stores/deviceTabs"
import type { DeviceTab } from "@/stores/deviceTabs"
import { useDeviceTabs } from "@/hooks/useDeviceTabs"
import { CreateChooser } from "@/components/devices/CreateChooser"
import { NewDeviceWizard } from "@/components/devices/NewDeviceWizard"
import { ManifestPicker } from "@/components/devices/ManifestPicker"
import { ScreenPane } from "@/components/devices/ScreenPane"
import { LogPanel } from "@/components/devices/LogPanel"
import { ResourceHud } from "@/components/devices/ResourceHud"
import { DeviceOptionsMenu } from "@/components/devices/DeviceOptionsMenu"
import { deviceTitle, type Device } from "@/lib/types"
import { ClipboardSync } from "@/lib/webrtc/clipboard"

export const Route = createFileRoute("/_layout/workspace")({
  component: WorkspacePage,
  head: () => ({ meta: [{ title: "DeviceLab — Workspace" }] }),
})

type CreateFlow = "none" | "chooser" | "new" | "existing"

// ── tab strip item ───────────────────────────────────────────────────────────

interface TabItemProps {
  tab: DeviceTab
  isActive: boolean
  onActivate(): void
  onClose(e: React.MouseEvent): void
  onRenameStart(): void
}

function TabItem({ tab, isActive, onActivate, onClose, onRenameStart }: TabItemProps) {
  return (
    <button
      onClick={onActivate}
      onDoubleClick={onRenameStart}
      className={`group flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-t border-b-2 transition-colors shrink-0 max-w-48 ${
        isActive
          ? "border-primary text-foreground bg-background"
          : "border-transparent text-muted-foreground hover:text-foreground hover:bg-muted"
      }`}
      title={tab.title}
    >
      {tab.pinned && <Pin className="h-3 w-3 shrink-0 text-muted-foreground" />}
      <span className="truncate text-xs">{tab.title}</span>
      <span
        className={`inline-flex h-4 w-4 items-center justify-center rounded text-muted-foreground hover:text-foreground hover:bg-muted transition-colors shrink-0 ${
          tab.pinned ? "invisible" : "opacity-0 group-hover:opacity-100"
        }`}
        onClick={onClose}
        role="button"
        aria-label={`Close ${tab.title}`}
      >
        <X className="h-3 w-3" />
      </span>
    </button>
  )
}

// ── rename overlay ────────────────────────────────────────────────────────────

function RenameInput({ tab, onDone }: { tab: DeviceTab; onDone(): void }) {
  const [val, setVal] = useState(tab.title)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => { inputRef.current?.select() }, [])

  async function commit() {
    const name = val.trim()
    if (!name || name === tab.title) { onDone(); return }
    try {
      const res = await fetch(`/api/v1/devices/${tab.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      })
      if (res.ok) {
        DeviceTabStore.updateTab(tab.id, { title: name })
      }
    } catch { /* ignore */ }
    onDone()
  }

  return (
    <input
      ref={inputRef}
      value={val}
      onChange={(e) => setVal(e.target.value)}
      onBlur={commit}
      onKeyDown={(e) => {
        if (e.key === "Enter") commit()
        if (e.key === "Escape") onDone()
      }}
      className="absolute inset-0 rounded bg-background border border-primary text-xs px-2 z-20 w-full"
    />
  )
}

// ── main workspace page ───────────────────────────────────────────────────────

function WorkspacePage() {
  const { tabs, activeId } = useDeviceTabs()
  const qc = useQueryClient()
  const navigate = useNavigate()

  const [createFlow, setCreateFlow] = useState<CreateFlow>("none")
  const [renamingId, setRenamingId] = useState<string | null>(null)
  const [clipboardEnabled, setClipboardEnabled] = useState(false)
  const [audioMuted, setAudioMuted] = useState(false)

  // Hydrate tabs from stored IDs on first mount
  const { data: devices } = useQuery<Device[]>({
    queryKey: ["devices"],
    queryFn: async () => {
      const res = await fetch("/api/v1/devices/")
      if (!res.ok) throw new Error("Failed to load devices")
      return res.json()
    },
    refetchInterval: 5_000,
  })

  useEffect(() => {
    if (!devices) return
    const liveTabs = devices
      .filter((d) => d.state !== "terminated" && d.state !== "failed")
      .map((d) => ({
        id: d.id,
        title: deviceTitle(d),
        family: d.family,
        state: d.state,
        displayMode: d.display_mode,
        mcpExposed: d.mcp_exposed,
        pinned: false,
      }))
    DeviceTabStore.hydrate(liveTabs)
  }, []) // intentionally run once — hydrate from localStorage

  // Keep tab state in sync with device updates
  useEffect(() => {
    if (!devices) return
    for (const d of devices) {
      if (DeviceTabStore.isOpen(d.id)) {
        DeviceTabStore.updateTab(d.id, {
          title: deviceTitle(d),
          state: d.state,
          displayMode: d.display_mode,
          mcpExposed: d.mcp_exposed,
        })
      }
    }
  }, [devices])

  const activeTab = tabs.find((t) => t.id === activeId)
  const activeDevice = devices?.find((d) => d.id === activeId)

  async function attach() {
    if (!activeId) return
    const res = await fetch(`/api/v1/devices/${activeId}/display/attach`, { method: "POST" })
    if (!res.ok) throw new Error(await res.text())
    DeviceTabStore.updateTab(activeId, { displayMode: "interactive" })
    qc.invalidateQueries({ queryKey: ["devices"] })
  }

  async function detach() {
    if (!activeId) return
    await fetch(`/api/v1/devices/${activeId}/display/detach`, { method: "POST" })
    DeviceTabStore.updateTab(activeId, { displayMode: "headless" })
    qc.invalidateQueries({ queryKey: ["devices"] })
  }

  async function filePull() {
    const path = window.prompt("Remote path to pull:", "/tmp/")
    if (!path || !activeId) return
    try {
      const res = await fetch(`/api/v1/devices/${activeId}/files/pull?path=${encodeURIComponent(path)}`)
      if (!res.ok) throw new Error(await res.text())
      const blob = await res.blob()
      const fname = path.split("/").pop() ?? "file"
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url; a.download = fname; a.click()
      URL.revokeObjectURL(url)
      toast.success(`Downloaded ${fname}`)
    } catch (e: unknown) {
      toast.error(String(e))
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* tab strip */}
      <div className="flex items-center border-b bg-muted/30 shrink-0 overflow-x-auto">
        {tabs.map((tab) => (
          <div key={tab.id} className="relative">
            {renamingId === tab.id && (
              <RenameInput tab={tab} onDone={() => setRenamingId(null)} />
            )}
            <TabItem
              tab={tab}
              isActive={tab.id === activeId}
              onActivate={() => DeviceTabStore.activateTab(tab.id)}
              onClose={(e) => {
                e.stopPropagation()
                if (!tab.pinned) DeviceTabStore.closeTab(tab.id)
              }}
              onRenameStart={() => setRenamingId(tab.id)}
            />
          </div>
        ))}

        <button
          onClick={() => setCreateFlow("chooser")}
          className="flex items-center justify-center h-8 w-8 rounded text-muted-foreground hover:text-foreground hover:bg-muted transition-colors shrink-0 ml-1"
          title="Open new device"
        >
          <Plus className="h-4 w-4" />
        </button>

        <div className="flex-1" />

        {/* options menu for active tab */}
        {activeTab && (
          <div className="px-2">
            <DeviceOptionsMenu
              tab={activeTab}
              device={activeDevice}
              onRename={() => setRenamingId(activeTab.id)}
              onAttach={attach}
              onDetach={detach}
              onFilePush={() => toast.info("Drag a file onto the screen to push it")}
              onFilePull={filePull}
              onClipboardToggle={() => setClipboardEnabled((v) => !v)}
              clipboardEnabled={clipboardEnabled}
              audioMuted={audioMuted}
              onAudioToggle={() => setAudioMuted((v) => !v)}
            />
          </div>
        )}
      </div>

      {/* empty state */}
      {tabs.length === 0 && (
        <div className="flex-1 flex flex-col items-center justify-center gap-4 text-center">
          <Monitor className="h-12 w-12 text-muted-foreground" />
          <div className="space-y-1">
            <p className="font-medium">No devices open</p>
            <p className="text-sm text-muted-foreground">
              Press <kbd className="rounded border px-1 font-mono text-xs">+</kbd> to create a
              device, or open one from the{" "}
              <button
                className="underline text-primary"
                onClick={() => navigate({ to: "/devices" })}
              >
                Devices list
              </button>
            </p>
          </div>
          <button
            onClick={() => setCreateFlow("chooser")}
            className="flex items-center gap-2 rounded-md bg-primary text-primary-foreground px-4 py-2 text-sm font-medium"
          >
            <Plus className="h-4 w-4" /> Open a device
          </button>
        </div>
      )}

      {/* active tab content */}
      {activeTab && activeDevice && (
        <div className="flex flex-col flex-1 min-h-0">
          {/* screen pane */}
          <div className="flex-1 min-h-0">
            <ScreenPane
              deviceId={activeTab.id}
              displayMode={activeTab.displayMode}
              deviceState={activeDevice.state}
              onAttach={attach}
              onDetach={detach}
            />
          </div>

          {/* log panel */}
          <div className="h-48 shrink-0">
            <LogPanel deviceId={activeTab.id} />
          </div>
        </div>
      )}

      {/* resource HUD — bottom */}
      <ResourceHud />

      {/* create dialogs */}
      <CreateChooser
        open={createFlow === "chooser"}
        onClose={() => setCreateFlow("none")}
        onNew={() => setCreateFlow("new")}
        onExisting={() => setCreateFlow("existing")}
      />
      <NewDeviceWizard
        open={createFlow === "new"}
        onClose={() => setCreateFlow("none")}
      />
      <ManifestPicker
        open={createFlow === "existing"}
        onClose={() => setCreateFlow("none")}
        onBack={() => setCreateFlow("chooser")}
      />
    </div>
  )
}
