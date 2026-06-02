// Resource / ledger HUD — Phase 11 (11-14)
// Shows per-host RAM/CPU committed vs total and a host budget bar.

import { useQuery } from "@tanstack/react-query"
import type { HostResources } from "@/lib/types"

function Bar({ value, max, color = "bg-primary" }: { value: number; max: number; color?: string }) {
  const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0
  const warn = pct > 80
  return (
    <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
      <div
        className={`h-full rounded-full transition-all ${warn ? "bg-yellow-500" : color}`}
        style={{ width: `${pct}%` }}
      />
    </div>
  )
}

function mb(n: number): string {
  return n >= 1024 ? `${(n / 1024).toFixed(1)} GB` : `${n} MB`
}

export function ResourceHud() {
  const { data } = useQuery<HostResources>({
    queryKey: ["host-resources"],
    queryFn: async () => {
      const res = await fetch("/api/v1/host/resources")
      if (!res.ok) throw new Error("Failed to load resources")
      return res.json()
    },
    refetchInterval: 10_000,
  })

  if (!data) return null

  const ramPct = data.total_ram_mb > 0
    ? Math.round((data.committed_ram_mb / data.total_ram_mb) * 100)
    : 0

  return (
    <div className="px-3 py-2 border-t text-xs space-y-2">
      <div className="flex items-center justify-between text-muted-foreground">
        <span>Host budget</span>
        <span>
          {data.device_count}/{data.max_devices} devices
        </span>
      </div>
      <div className="space-y-1.5">
        <div className="flex justify-between">
          <span className="text-muted-foreground">RAM</span>
          <span>
            {mb(data.committed_ram_mb)} / {mb(data.total_ram_mb)} ({ramPct}%)
          </span>
        </div>
        <Bar value={data.committed_ram_mb} max={data.total_ram_mb} />

        <div className="flex justify-between">
          <span className="text-muted-foreground">CPU</span>
          <span>
            {data.committed_cpu_cores} / {data.total_cpu_cores} cores
          </span>
        </div>
        <Bar value={data.committed_cpu_cores} max={data.total_cpu_cores} />
      </div>
    </div>
  )
}
