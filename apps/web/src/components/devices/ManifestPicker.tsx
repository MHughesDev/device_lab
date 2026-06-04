// Manifest picker — Phase 11 (11-05)
// Lists named manifests; selecting one creates a device from that manifest.

import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { ChevronLeft, Layers } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { DeviceTabStore } from "@/stores/deviceTabs"
import { deviceTitle, type Device, type DeviceManifest } from "@/lib/types"

interface Props {
  open: boolean
  onClose(): void
  onBack(): void
}

export function ManifestPicker({ open, onClose, onBack }: Props) {
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const { data: manifests, isLoading } = useQuery<DeviceManifest[]>({
    queryKey: ["manifests"],
    queryFn: async () => {
      const res = await fetch("/api/v1/manifests/")
      if (!res.ok) throw new Error("Failed to load manifests")
      return res.json()
    },
    enabled: open,
  })

  function handleClose() {
    setSelectedId(null)
    setError(null)
    onClose()
  }

  async function handleCreate() {
    if (!selectedId) return
    setCreating(true)
    setError(null)
    try {
      const res = await fetch("/api/v1/devices/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ manifest_id: selectedId }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(err.detail ?? res.statusText)
      }
      const device: Device = await res.json()
      DeviceTabStore.openTab({
        id: device.id,
        title: deviceTitle(device),
        family: device.family,
        state: device.state,
        displayMode: device.display_mode,
        mcpExposed: device.mcp_exposed,
        pinned: false,
      })
      handleClose()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setCreating(false)
    }
  }

  const selected = manifests?.find((m) => m.id === selectedId)

  return (
    <Dialog open={open} onOpenChange={(v) => !v && handleClose()}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Choose a saved environment</DialogTitle>
        </DialogHeader>

        <div className="space-y-3">
          {isLoading && (
            <div className="py-8 text-center text-sm text-muted-foreground">
              Loading manifests…
            </div>
          )}

          {!isLoading && (!manifests || manifests.length === 0) && (
            <div className="py-8 text-center space-y-1">
              <Layers className="h-8 w-8 mx-auto text-muted-foreground" />
              <p className="text-sm text-muted-foreground">No saved environments yet</p>
              <p className="text-xs text-muted-foreground">
                Capture a manifest from a running device to save its environment.
              </p>
            </div>
          )}

          {manifests && manifests.length > 0 && (
            <div className="space-y-2 max-h-72 overflow-y-auto">
              {manifests.map((m) => (
                <button
                  key={m.id}
                  onClick={() => setSelectedId(m.id)}
                  className={`w-full rounded-lg border-2 p-3 text-left transition-colors ${
                    selectedId === m.id
                      ? "border-primary bg-primary/5"
                      : "border-border hover:border-muted-foreground"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <p className="font-medium text-sm truncate">{m.title}</p>
                      {m.description && (
                        <p className="text-xs text-muted-foreground mt-0.5 truncate">
                          {m.description}
                        </p>
                      )}
                    </div>
                    <div className="shrink-0 text-right">
                      <span className="text-xs bg-muted px-1.5 py-0.5 rounded capitalize">
                        {m.family}
                      </span>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {new Date(m.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}

          {error && (
            <div className="rounded-md border border-red-200 bg-red-50 dark:bg-red-950 p-3 text-xs text-red-700 dark:text-red-300">
              {error}
            </div>
          )}

          <div className="flex justify-between pt-1">
            <button
              onClick={onBack}
              className="flex items-center gap-1 rounded-md border px-4 py-2 text-sm"
            >
              <ChevronLeft className="h-4 w-4" /> Back
            </button>
            <button
              onClick={handleCreate}
              disabled={!selectedId || creating}
              className="rounded-md bg-primary text-primary-foreground px-4 py-2 text-sm font-medium disabled:opacity-50"
            >
              {creating ? "Creating…" : `Create from "${selected?.title ?? "…"}"`}
            </button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
