// Shared types for DeviceLab frontend — Phase 11

export type DeviceFamily = "linux" | "android" | "windows" | "macos" | "ios_sim"

export type DeviceState =
  | "requested"
  | "preflight_blocked"
  | "provisioning"
  | "bootstrapping_agent"
  | "ready"
  | "stopping"
  | "stopped"
  | "terminating"
  | "terminated"
  | "failed"

export interface Device {
  id: string
  family: DeviceFamily
  name: string | null
  display_mode: "headless" | "interactive"
  mcp_exposed: boolean
  state: DeviceState
  phase: string | null
  cost_estimate: number | null
  source_manifest_id: string | null
  created_at: string
  updated_at: string
}

export function deviceTitle(d: Pick<Device, "id" | "family" | "name">): string {
  return d.name ?? `${d.family} · ${d.id.slice(0, 8)}`
}

export interface DeviceManifest {
  id: string
  workspace_id: string
  name: string | null
  family: DeviceFamily
  location: string
  description: string | null
  source_device_id: string | null
  created_at: string
  updated_at: string
  title: string
}

export interface Template {
  id: string
  family: DeviceFamily
  location: string
  name: string
  spec: Record<string, unknown>
}

export interface HostResources {
  total_ram_mb: number
  committed_ram_mb: number
  available_ram_mb: number
  total_cpu_cores: number
  committed_cpu_cores: number
  device_count: number
  max_devices: number
}
