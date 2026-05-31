import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"

export const Route = createFileRoute("/_layout/devices")({
  component: DevicesPage,
  head: () => ({ meta: [{ title: "DeviceLab — Devices" }] }),
})

interface Device {
  id: string
  family: string
  state: string
  phase: string | null
  cost_estimate: number | null
  created_at: string
  updated_at: string
}

const STATE_COLORS: Record<string, string> = {
  requested: "bg-blue-100 text-blue-700",
  preflight_blocked: "bg-yellow-100 text-yellow-700",
  provisioning: "bg-blue-100 text-blue-700 animate-pulse",
  bootstrapping_agent: "bg-purple-100 text-purple-700 animate-pulse",
  ready: "bg-green-100 text-green-700",
  stopping: "bg-orange-100 text-orange-700",
  stopped: "bg-gray-100 text-gray-700",
  terminating: "bg-red-100 text-red-700 animate-pulse",
  terminated: "bg-gray-100 text-gray-400",
  failed: "bg-red-100 text-red-700",
}

function StateBadge({ state }: { state: string }) {
  const color = STATE_COLORS[state] ?? "bg-muted text-muted-foreground"
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${color}`}>
      {state.replace(/_/g, " ")}
    </span>
  )
}

function DevicesPage() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  const { data: devices, isLoading } = useQuery<Device[]>({
    queryKey: ["devices"],
    queryFn: async () => {
      const res = await fetch("/api/v1/devices/")
      if (!res.ok) throw new Error("Failed to load devices")
      return res.json()
    },
    refetchInterval: 5_000,
  })

  async function lifecycle(deviceId: string, action: "stop" | "start" | "terminate") {
    setActionLoading(`${deviceId}-${action}`)
    try {
      await fetch(`/api/v1/devices/${deviceId}/lifecycle/${action}`, { method: "POST" })
      qc.invalidateQueries({ queryKey: ["devices"] })
    } finally {
      setActionLoading(null)
    }
  }

  const activeDevices = devices?.filter((d) => d.state !== "terminated") ?? []

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Devices</h1>
        <button
          className="rounded-md bg-primary text-primary-foreground px-4 py-2 text-sm font-medium"
          onClick={() => navigate({ to: "/onboarding" })}
        >
          + New device
        </button>
      </div>

      {isLoading && <p className="text-sm text-muted-foreground">Loading…</p>}

      {!isLoading && activeDevices.length === 0 && (
        <div className="rounded-lg border p-12 text-center space-y-2">
          <p className="text-muted-foreground text-sm">No devices yet</p>
          <p className="text-xs text-muted-foreground">
            Complete the first-run setup to provision your first device
          </p>
          <button
            className="mt-3 rounded-md bg-primary text-primary-foreground px-4 py-2 text-sm font-medium"
            onClick={() => navigate({ to: "/onboarding" })}
          >
            Run setup wizard →
          </button>
        </div>
      )}

      {activeDevices.map((device) => (
        <div key={device.id} className="rounded-lg border p-4">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="font-medium text-sm font-mono">{device.id.slice(0, 8)}…</span>
                <StateBadge state={device.state} />
                <span className="text-xs text-muted-foreground capitalize">{device.family}</span>
              </div>
              {device.cost_estimate !== null && (
                <p className="text-xs text-muted-foreground">
                  Est. ${device.cost_estimate.toFixed(2)}/month
                </p>
              )}
              <p className="text-xs text-muted-foreground">
                Created {new Date(device.created_at).toLocaleDateString()}
              </p>
            </div>

            <div className="flex gap-2">
              {device.state === "ready" && (
                <button
                  className="rounded border px-3 py-1.5 text-xs font-medium disabled:opacity-50"
                  onClick={() => lifecycle(device.id, "stop")}
                  disabled={!!actionLoading}
                >
                  Stop
                </button>
              )}
              {device.state === "stopped" && (
                <button
                  className="rounded border px-3 py-1.5 text-xs font-medium disabled:opacity-50"
                  onClick={() => lifecycle(device.id, "start")}
                  disabled={!!actionLoading}
                >
                  Start
                </button>
              )}
              {["ready", "stopped", "provisioning", "bootstrapping_agent", "preflight_blocked"].includes(device.state) && (
                <button
                  className="rounded border border-red-200 text-red-600 px-3 py-1.5 text-xs font-medium disabled:opacity-50"
                  onClick={() => lifecycle(device.id, "terminate")}
                  disabled={!!actionLoading}
                >
                  Terminate
                </button>
              )}
            </div>
          </div>
        </div>
      ))}

      {devices && devices.filter((d) => d.state === "terminated").length > 0 && (
        <details className="text-sm">
          <summary className="cursor-pointer text-muted-foreground">
            {devices.filter((d) => d.state === "terminated").length} terminated device(s)
          </summary>
          <div className="mt-2 space-y-2">
            {devices.filter((d) => d.state === "terminated").map((device) => (
              <div key={device.id} className="rounded border p-3 flex items-center gap-3 opacity-60">
                <span className="font-mono text-xs">{device.id.slice(0, 8)}…</span>
                <StateBadge state={device.state} />
                <span className="text-xs text-muted-foreground capitalize">{device.family}</span>
              </div>
            ))}
          </div>
        </details>
      )}
    </div>
  )
}
