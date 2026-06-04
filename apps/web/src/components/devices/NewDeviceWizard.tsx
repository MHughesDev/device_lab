// New-device wizard — Phase 11 (11-04)
// Collects OS/location/display-mode/MCP-exposure/name, POSTs to /devices/, opens tab.

import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { ChevronLeft, ChevronRight, Check } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { DeviceTabStore } from "@/stores/deviceTabs"
import { deviceTitle, type Device, type Template } from "@/lib/types"

interface Props {
  open: boolean
  onClose(): void
}

type Step = "os" | "display" | "mcp" | "name" | "creating"

const FAMILY_LABELS: Record<string, string> = {
  linux: "Linux (Ubuntu)",
  android: "Android",
  windows: "Windows",
  macos: "macOS",
  ios_sim: "iOS Simulator",
}

const LOCATION_LABELS: Record<string, string> = {
  local: "Local (this machine)",
  cloud: "Cloud (AWS)",
}

export function NewDeviceWizard({ open, onClose }: Props) {
  const [step, setStep] = useState<Step>("os")
  const [family, setFamily] = useState("linux")
  const [location, setLocation] = useState("local")
  const [displayMode, setDisplayMode] = useState<"headless" | "interactive">("headless")
  const [mcpExposed, setMcpExposed] = useState(true)
  const [name, setName] = useState("")
  const [error, setError] = useState<string | null>(null)

  const { data: templates } = useQuery<Template[]>({
    queryKey: ["templates"],
    queryFn: async () => {
      const res = await fetch("/api/v1/templates/")
      if (!res.ok) throw new Error("Failed to load templates")
      return res.json()
    },
    enabled: open,
  })

  const availableFamilies = templates
    ? [...new Set(templates.map((t) => t.family))]
    : ["linux"]

  function reset() {
    setStep("os")
    setFamily("linux")
    setLocation("local")
    setDisplayMode("headless")
    setMcpExposed(true)
    setName("")
    setError(null)
  }

  function handleClose() {
    reset()
    onClose()
  }

  async function handleCreate() {
    setStep("creating")
    setError(null)
    try {
      const tmpl = templates?.find((t) => t.family === family && t.location === location)
        ?? templates?.find((t) => t.family === family)
      if (!tmpl) throw new Error(`No template found for ${family} / ${location}`)

      const body: Record<string, unknown> = {
        template_id: tmpl.id,
        location,
        display_mode: displayMode,
        mcp_exposed: mcpExposed,
      }
      if (name.trim()) body.name = name.trim()

      const res = await fetch("/api/v1/devices/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
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
      setStep("name")
    }
  }

  const canGoNext =
    step === "os" ||
    step === "display" ||
    step === "mcp" ||
    step === "name"

  return (
    <Dialog open={open} onOpenChange={(v) => !v && handleClose()}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>New device</DialogTitle>
        </DialogHeader>

        {step === "creating" && (
          <div className="py-8 text-center space-y-2">
            <div className="animate-spin h-6 w-6 border-2 border-primary border-t-transparent rounded-full mx-auto" />
            <p className="text-sm text-muted-foreground">Creating device…</p>
          </div>
        )}

        {step === "os" && (
          <div className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Operating system</label>
              <div className="grid grid-cols-2 gap-2">
                {availableFamilies.map((f) => (
                  <button
                    key={f}
                    onClick={() => setFamily(f)}
                    className={`rounded-lg border-2 p-3 text-sm text-left transition-colors ${
                      family === f
                        ? "border-primary bg-primary/5"
                        : "border-border hover:border-muted-foreground"
                    }`}
                  >
                    {FAMILY_LABELS[f] ?? f}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Location</label>
              <div className="grid grid-cols-2 gap-2">
                {["local", "cloud"].map((loc) => (
                  <button
                    key={loc}
                    onClick={() => setLocation(loc)}
                    className={`rounded-lg border-2 p-3 text-sm text-left transition-colors ${
                      location === loc
                        ? "border-primary bg-primary/5"
                        : "border-border hover:border-muted-foreground"
                    }`}
                  >
                    {LOCATION_LABELS[loc]}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex justify-end">
              <button
                onClick={() => setStep("display")}
                className="flex items-center gap-1 rounded-md bg-primary text-primary-foreground px-4 py-2 text-sm font-medium"
              >
                Next <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}

        {step === "display" && (
          <div className="space-y-4">
            <div className="space-y-3">
              <label className="text-sm font-medium">Display mode</label>

              <button
                onClick={() => setDisplayMode("headless")}
                className={`w-full rounded-lg border-2 p-4 text-left transition-colors ${
                  displayMode === "headless"
                    ? "border-primary bg-primary/5"
                    : "border-border hover:border-muted-foreground"
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className={`mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full border-2 ${displayMode === "headless" ? "border-primary" : "border-border"}`}>
                    {displayMode === "headless" && <div className="h-2 w-2 rounded-full bg-primary" />}
                  </div>
                  <div>
                    <p className="font-medium text-sm">Headless (agent-only)</p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      No display, minimal resources. MCP still fully operational — agents can
                      observe and control via the API. Use Attach to add a live view at any time.
                    </p>
                  </div>
                </div>
              </button>

              <button
                onClick={() => setDisplayMode("interactive")}
                className={`w-full rounded-lg border-2 p-4 text-left transition-colors ${
                  displayMode === "interactive"
                    ? "border-primary bg-primary/5"
                    : "border-border hover:border-muted-foreground"
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className={`mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full border-2 ${displayMode === "interactive" ? "border-primary" : "border-border"}`}>
                    {displayMode === "interactive" && <div className="h-2 w-2 rounded-full bg-primary" />}
                  </div>
                  <div>
                    <p className="font-medium text-sm">Interactive (live view)</p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      Full display, video stream, keyboard and mouse input. More resource usage.
                      Suitable for manual testing and visual inspection.
                    </p>
                  </div>
                </div>
              </button>
            </div>

            <div className="flex justify-between">
              <button
                onClick={() => setStep("os")}
                className="flex items-center gap-1 rounded-md border px-4 py-2 text-sm"
              >
                <ChevronLeft className="h-4 w-4" /> Back
              </button>
              <button
                onClick={() => setStep("mcp")}
                className="flex items-center gap-1 rounded-md bg-primary text-primary-foreground px-4 py-2 text-sm font-medium"
              >
                Next <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}

        {step === "mcp" && (
          <div className="space-y-4">
            <div className="space-y-3">
              <label className="text-sm font-medium">MCP exposure</label>
              <p className="text-xs text-muted-foreground">
                Should this device be accessible to AI agents via the MCP gateway?
              </p>

              {[
                { val: true, label: "Exposed via MCP", desc: "Agents can observe and control this device through the MCP tool manifest." },
                { val: false, label: "Private (no MCP)", desc: "Device is not visible to agents. Human-only via the workspace UI." },
              ].map(({ val, label, desc }) => (
                <button
                  key={String(val)}
                  onClick={() => setMcpExposed(val)}
                  className={`w-full rounded-lg border-2 p-4 text-left transition-colors ${
                    mcpExposed === val
                      ? "border-primary bg-primary/5"
                      : "border-border hover:border-muted-foreground"
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className={`mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full border-2 ${mcpExposed === val ? "border-primary" : "border-border"}`}>
                      {mcpExposed === val && <div className="h-2 w-2 rounded-full bg-primary" />}
                    </div>
                    <div>
                      <p className="font-medium text-sm">{label}</p>
                      <p className="text-xs text-muted-foreground mt-0.5">{desc}</p>
                    </div>
                  </div>
                </button>
              ))}
            </div>

            <div className="flex justify-between">
              <button
                onClick={() => setStep("display")}
                className="flex items-center gap-1 rounded-md border px-4 py-2 text-sm"
              >
                <ChevronLeft className="h-4 w-4" /> Back
              </button>
              <button
                onClick={() => setStep("name")}
                className="flex items-center gap-1 rounded-md bg-primary text-primary-foreground px-4 py-2 text-sm font-medium"
              >
                Next <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}

        {step === "name" && (
          <div className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Name (optional)</label>
              <input
                className="w-full rounded-md border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                placeholder={`${FAMILY_LABELS[family] ?? family} · auto-id`}
                value={name}
                onChange={(e) => setName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleCreate()}
                autoFocus
              />
              <p className="text-xs text-muted-foreground">
                Leave blank to use the auto-generated ID as the tab title.
              </p>
            </div>

            {error && (
              <div className="rounded-md border border-red-200 bg-red-50 dark:bg-red-950 p-3 text-xs text-red-700 dark:text-red-300">
                {error}
              </div>
            )}

            <div className="rounded-md border bg-muted/50 p-3 text-xs space-y-1 text-muted-foreground">
              <p><strong className="text-foreground">OS:</strong> {FAMILY_LABELS[family] ?? family}</p>
              <p><strong className="text-foreground">Location:</strong> {LOCATION_LABELS[location]}</p>
              <p><strong className="text-foreground">Display:</strong> {displayMode}</p>
              <p><strong className="text-foreground">MCP:</strong> {mcpExposed ? "exposed" : "private"}</p>
            </div>

            <div className="flex justify-between">
              <button
                onClick={() => setStep("mcp")}
                className="flex items-center gap-1 rounded-md border px-4 py-2 text-sm"
              >
                <ChevronLeft className="h-4 w-4" /> Back
              </button>
              <button
                onClick={handleCreate}
                className="flex items-center gap-1 rounded-md bg-primary text-primary-foreground px-4 py-2 text-sm font-medium"
              >
                <Check className="h-4 w-4" /> Create device
              </button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
