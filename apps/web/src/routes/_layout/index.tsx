import { createFileRoute } from "@tanstack/react-router"
import { useQuery } from "@tanstack/react-query"

export const Route = createFileRoute("/_layout/")({
  component: StatusDashboard,
  head: () => ({
    meta: [{ title: "DeviceLab — Status" }],
  }),
})

interface WorkspaceStatus {
  id: string
  name: string
  version: string
  bind_host: string
  dangerous_mode: boolean
  capabilities: {
    aws_connect: boolean
    device_lifecycle: boolean
    mcp_gateway: boolean
    streaming: boolean
    recipes: boolean
  }
  cloud_accounts: Array<{
    id: string
    provider: string
    account_id: string
    display_name: string
    status: string
  }>
}

interface HealthStatus {
  status: string
  db_ok: boolean
  version: string
  timestamp: string
}

function CapabilityBadge({
  label,
  enabled,
}: {
  label: string
  enabled: boolean
}) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium ${
        enabled
          ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
          : "bg-muted text-muted-foreground"
      }`}
    >
      <span
        className={`h-1.5 w-1.5 rounded-full ${enabled ? "bg-green-500" : "bg-gray-400"}`}
      />
      {label}
    </span>
  )
}

function StatusDashboard() {
  const { data: workspace, isLoading: wsLoading } = useQuery<WorkspaceStatus>({
    queryKey: ["workspace"],
    queryFn: async () => {
      const res = await fetch("/api/v1/workspace/")
      if (!res.ok) throw new Error("Failed to load workspace")
      return res.json()
    },
    refetchInterval: 30_000,
  })

  const { data: health } = useQuery<HealthStatus>({
    queryKey: ["health"],
    queryFn: async () => {
      const res = await fetch("/api/v1/health/")
      if (!res.ok) throw new Error("Failed to load health")
      return res.json()
    },
    refetchInterval: 10_000,
  })

  const dbOk = health?.db_ok ?? false
  const apiOk = health?.status === "ok"

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">
            {wsLoading ? "DeviceLab" : (workspace?.name ?? "DeviceLab")}
          </h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Local-first BYOC device platform
            {workspace && (
              <span className="ml-2 font-mono text-xs">v{workspace.version}</span>
            )}
          </p>
        </div>

        <div className="flex items-center gap-2 text-sm">
          <span
            className={`h-2.5 w-2.5 rounded-full ${apiOk && dbOk ? "bg-green-500 animate-pulse" : "bg-red-500"}`}
          />
          <span className="text-muted-foreground">
            {apiOk && dbOk ? "Healthy" : "Degraded"}
          </span>
        </div>
      </div>

      <div className="rounded-lg border p-4 space-y-3">
        <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
          Capabilities
        </h2>
        <div className="flex flex-wrap gap-2">
          <CapabilityBadge label="AWS Connect" enabled={workspace?.capabilities.aws_connect ?? false} />
          <CapabilityBadge label="Device Lifecycle" enabled={workspace?.capabilities.device_lifecycle ?? false} />
          <CapabilityBadge label="MCP Gateway" enabled={workspace?.capabilities.mcp_gateway ?? false} />
          <CapabilityBadge label="Streaming" enabled={workspace?.capabilities.streaming ?? false} />
          <CapabilityBadge label="Recipes" enabled={workspace?.capabilities.recipes ?? false} />
        </div>
      </div>

      {workspace && (
        <div className="rounded-lg border p-4 space-y-2 text-sm">
          <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
            Control plane
          </h2>
          <div className="grid grid-cols-2 gap-x-8 gap-y-1">
            <span className="text-muted-foreground">Bind host</span>
            <span className="font-mono">{workspace.bind_host}</span>
            <span className="text-muted-foreground">Dangerous mode</span>
            <span className={workspace.dangerous_mode ? "text-red-600 font-medium" : ""}>
              {workspace.dangerous_mode ? "ENABLED" : "off"}
            </span>
            <span className="text-muted-foreground">DB</span>
            <span className={dbOk ? "text-green-600" : "text-red-600"}>
              {dbOk ? "connected" : "unreachable"}
            </span>
          </div>
        </div>
      )}

      <div className="rounded-lg border p-4 space-y-3">
        <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
          Cloud accounts
        </h2>
        {!workspace || workspace.cloud_accounts.length === 0 ? (
          <div className="py-8 text-center space-y-2">
            <p className="text-muted-foreground text-sm">No cloud accounts connected</p>
            <p className="text-xs text-muted-foreground">
              Connect an AWS account to start provisioning devices — available in Phase 02
            </p>
            <button
              disabled
              className="mt-3 rounded-md border px-4 py-2 text-sm opacity-50 cursor-not-allowed"
            >
              Connect AWS account (coming soon)
            </button>
          </div>
        ) : (
          <div className="divide-y">
            {workspace.cloud_accounts.map((acct) => (
              <div key={acct.id} className="py-2 flex items-center justify-between">
                <div>
                  <p className="font-medium text-sm">{acct.display_name}</p>
                  <p className="text-xs text-muted-foreground font-mono">
                    {acct.provider} · {acct.account_id}
                  </p>
                </div>
                <span
                  className={`text-xs px-2 py-0.5 rounded-full ${
                    acct.status === "ok"
                      ? "bg-green-100 text-green-700"
                      : "bg-muted text-muted-foreground"
                  }`}
                >
                  {acct.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
