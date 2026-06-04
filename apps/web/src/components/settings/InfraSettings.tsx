// Infrastructure settings UI — Phase 12 (12-07)
// Six grouped sections: Cloud, Host, Streaming, MCP, Manifests, Security.
// Secret inputs are write-only (never echo stored secrets).

import { useState, useEffect } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import {
  Cloud, Server, Radio, Layers, Shield, Monitor,
  CheckCircle, XCircle, Loader2, RefreshCw
} from "lucide-react"
import { toast } from "sonner"
import { SettingRow } from "./SettingRow"
import { SecretInput } from "./SecretInput"

type AllSettings = Record<string, Record<string, unknown>>

async function fetchSettings(): Promise<AllSettings> {
  const res = await fetch("/api/v1/settings/")
  if (!res.ok) throw new Error("Failed to load settings")
  return res.json()
}

async function patchGroup(group: string, values: Record<string, unknown>): Promise<Record<string, unknown>> {
  const res = await fetch(`/api/v1/settings/${group}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ values }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? res.statusText)
  }
  return res.json()
}

// ── section wrapper ──────────────────────────────────────────────────────────

interface SectionProps {
  icon: React.ElementType
  title: string
  description: string
  children: React.ReactNode
  onSave(): void
  saving: boolean
  dirty: boolean
}

function Section({ icon: Icon, title, description, children, onSave, saving, dirty }: SectionProps) {
  return (
    <div className="rounded-lg border">
      <div className="flex items-start justify-between p-4 border-b">
        <div className="flex items-start gap-3">
          <Icon className="h-5 w-5 text-muted-foreground mt-0.5 shrink-0" />
          <div>
            <h3 className="font-medium text-sm">{title}</h3>
            <p className="text-xs text-muted-foreground mt-0.5">{description}</p>
          </div>
        </div>
        <button
          onClick={onSave}
          disabled={!dirty || saving}
          className="flex items-center gap-1.5 rounded-md bg-primary text-primary-foreground px-3 py-1.5 text-xs font-medium disabled:opacity-50 shrink-0 ml-4"
        >
          {saving && <Loader2 className="h-3 w-3 animate-spin" />}
          Save
        </button>
      </div>
      <div className="divide-y px-4">{children}</div>
    </div>
  )
}

// ── input helpers ─────────────────────────────────────────────────────────────

function TextInput({ value, onChange, placeholder }: { value: string; onChange(v: string): void; placeholder?: string }) {
  return (
    <input
      className="w-full rounded-md border bg-background px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
      value={value ?? ""}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
    />
  )
}

function NumberInput({ value, onChange, min, max }: { value: number | null; onChange(v: number | null): void; min?: number; max?: number }) {
  return (
    <input
      type="number"
      className="w-full rounded-md border bg-background px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
      value={value ?? ""}
      onChange={(e) => onChange(e.target.value === "" ? null : Number(e.target.value))}
      min={min}
      max={max}
    />
  )
}

function Toggle({ value, onChange, onLabel = "On", offLabel = "Off" }: { value: boolean; onChange(v: boolean): void; onLabel?: string; offLabel?: string }) {
  return (
    <button
      onClick={() => onChange(!value)}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${value ? "bg-primary" : "bg-muted-foreground/30"}`}
    >
      <span className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${value ? "translate-x-6" : "translate-x-1"}`} />
      <span className="sr-only">{value ? onLabel : offLabel}</span>
    </button>
  )
}

function SelectInput({ value, onChange, options }: { value: string; onChange(v: string): void; options: { value: string; label: string }[] }) {
  return (
    <select
      className="w-full rounded-md border bg-background px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
      value={value ?? ""}
      onChange={(e) => onChange(e.target.value)}
    >
      {options.map((o) => (
        <option key={o.value} value={o.value}>{o.label}</option>
      ))}
    </select>
  )
}

// ── main component ────────────────────────────────────────────────────────────

export function InfraSettings() {
  const qc = useQueryClient()
  const { data, isLoading } = useQuery({ queryKey: ["settings"], queryFn: fetchSettings })

  // Local draft state per group
  const [cloud, setCloud] = useState<Record<string, unknown>>({})
  const [host, setHost] = useState<Record<string, unknown>>({})
  const [streaming, setStreaming] = useState<Record<string, unknown>>({})
  const [mcp, setMcp] = useState<Record<string, unknown>>({})
  const [manifests, setManifests] = useState<Record<string, unknown>>({})
  const [security, setSecurity] = useState<Record<string, unknown>>({})
  const [dirty, setDirty] = useState<Record<string, boolean>>({})

  const [testConnStatus, setTestConnStatus] = useState<{ status: string; detail: string } | null>(null)
  const [testConnLoading, setTestConnLoading] = useState(false)

  useEffect(() => {
    if (!data) return
    setCloud(data.cloud ?? {})
    setHost(data.host ?? {})
    setStreaming(data.streaming ?? {})
    setMcp(data.mcp ?? {})
    setManifests(data.manifests ?? {})
    setSecurity(data.security ?? {})
  }, [data])

  function patch(group: string, setter: React.Dispatch<React.SetStateAction<Record<string, unknown>>>, key: string, value: unknown) {
    setter((prev) => ({ ...prev, [key]: value }))
    setDirty((prev) => ({ ...prev, [group]: true }))
  }

  const saveMutation = useMutation({
    mutationFn: ({ group, values }: { group: string; values: Record<string, unknown> }) =>
      patchGroup(group, values),
    onSuccess: (_, { group }) => {
      setDirty((prev) => ({ ...prev, [group]: false }))
      qc.invalidateQueries({ queryKey: ["settings"] })
      toast.success(`${group} settings saved`)
    },
    onError: (e: Error, { group }) => toast.error(`Failed to save ${group}: ${e.message}`),
  })

  async function save(group: string, values: Record<string, unknown>) {
    saveMutation.mutate({ group, values })
  }

  async function testConnection() {
    setTestConnLoading(true)
    setTestConnStatus(null)
    try {
      const res = await fetch("/api/v1/settings/cloud/test-connection", { method: "POST" })
      const data = await res.json()
      setTestConnStatus(data)
    } catch (e: unknown) {
      setTestConnStatus({ status: "error", detail: String(e) })
    } finally {
      setTestConnLoading(false)
    }
  }

  if (isLoading) {
    return <div className="text-sm text-muted-foreground py-8 text-center">Loading settings…</div>
  }

  const saving = saveMutation.isPending

  return (
    <div className="space-y-6">

      {/* ── Cloud infra ─────────────────────────────────────────────── */}
      <Section
        icon={Cloud}
        title="Cloud infrastructure (AWS)"
        description="BYOC: all resources provision in your own AWS account. Credentials stay in the OS keychain via SecretRef — never in the database."
        onSave={() => save("cloud", cloud)}
        saving={saving}
        dirty={!!dirty.cloud}
      >
        <SettingRow label="Credential source" description="How to authenticate with AWS">
          <SelectInput
            value={String(cloud.credential_source ?? "env")}
            onChange={(v) => patch("cloud", setCloud, "credential_source", v)}
            options={[
              { value: "env", label: "Environment variables (AWS_ACCESS_KEY_ID)" },
              { value: "profile", label: "~/.aws/credentials profile" },
              { value: "role", label: "IAM role ARN (assume-role)" },
            ]}
          />
        </SettingRow>

        {cloud.credential_source === "profile" && (
          <SettingRow label="AWS profile name" indent>
            <SecretInput
              value={cloud.credential_profile as string ?? null}
              onChange={(v) => patch("cloud", setCloud, "credential_profile", v)}
              placeholder="default"
            />
          </SettingRow>
        )}

        {cloud.credential_source === "role" && (
          <SettingRow label="Role ARN" indent>
            <SecretInput
              value={cloud.credential_role_arn as string ?? null}
              onChange={(v) => patch("cloud", setCloud, "credential_role_arn", v)}
              placeholder="arn:aws:iam::123456789012:role/DeviceLab"
            />
          </SettingRow>
        )}

        <SettingRow label="Default region">
          <TextInput
            value={String(cloud.default_region ?? "us-east-1")}
            onChange={(v) => patch("cloud", setCloud, "default_region", v)}
          />
        </SettingRow>

        <SettingRow label="Artifact S3 bucket" description="Logs, snapshots, and test artifacts">
          <TextInput
            value={String(cloud.artifact_bucket ?? "")}
            onChange={(v) => patch("cloud", setCloud, "artifact_bucket", v || null)}
            placeholder="my-devicelab-artifacts"
          />
        </SettingRow>

        <SettingRow label="STUN URL" description="Public STUN server for cloud WebRTC">
          <TextInput
            value={String(cloud.stun_url ?? "")}
            onChange={(v) => patch("cloud", setCloud, "stun_url", v || null)}
            placeholder="stun:stun.l.google.com:19302"
          />
        </SettingRow>

        <SettingRow label="TURN URL (coturn)" description="BYOC coturn in your VPC (ADR-0007)">
          <SecretInput
            value={cloud.turn_url as string ?? null}
            onChange={(v) => patch("cloud", setCloud, "turn_url", v || null)}
            placeholder="turn:coturn.mycompany.internal:3478"
          />
        </SettingRow>

        <SettingRow label="TURN username">
          <SecretInput
            value={cloud.turn_username as string ?? null}
            onChange={(v) => patch("cloud", setCloud, "turn_username", v || null)}
          />
        </SettingRow>

        <SettingRow label="TURN credential">
          <SecretInput
            value={cloud.turn_credential as string ?? null}
            onChange={(v) => patch("cloud", setCloud, "turn_credential", v || null)}
          />
        </SettingRow>

        <div className="py-3 flex items-center gap-3">
          <button
            onClick={testConnection}
            disabled={testConnLoading}
            className="flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-xs font-medium disabled:opacity-50"
          >
            {testConnLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : <RefreshCw className="h-3 w-3" />}
            Test AWS connection
          </button>
          {testConnStatus && (
            <span className={`flex items-center gap-1 text-xs ${testConnStatus.status === "ok" ? "text-green-600" : "text-red-600"}`}>
              {testConnStatus.status === "ok"
                ? <CheckCircle className="h-3.5 w-3.5" />
                : <XCircle className="h-3.5 w-3.5" />}
              {testConnStatus.detail}
            </span>
          )}
        </div>
      </Section>

      {/* ── Host budget ─────────────────────────────────────────────── */}
      <Section
        icon={Server}
        title="Local host budget"
        description="Resource limits for devices running on this machine. Lowering budget below current commitments will be refused."
        onSave={() => save("host", host)}
        saving={saving}
        dirty={!!dirty.host}
      >
        <SettingRow label="RAM budget (MB)" description="Max RAM for all devices combined. Blank = auto (all RAM minus headroom)">
          <NumberInput
            value={host.device_ram_budget_mb as number ?? null}
            onChange={(v) => patch("host", setHost, "device_ram_budget_mb", v)}
            min={512}
          />
        </SettingRow>

        <SettingRow label="CPU budget (cores)" description="Blank = all logical cores">
          <NumberInput
            value={host.device_cpu_budget_cores as number ?? null}
            onChange={(v) => patch("host", setHost, "device_cpu_budget_cores", v)}
            min={1}
          />
        </SettingRow>

        <SettingRow label="Host headroom %" description="Percentage of total RAM reserved for the host OS (0–50)">
          <NumberInput
            value={host.headroom_pct as number ?? 20}
            onChange={(v) => patch("host", setHost, "headroom_pct", v)}
            min={0}
            max={50}
          />
        </SettingRow>

        <SettingRow label="Max devices">
          <NumberInput
            value={host.max_devices as number ?? 10}
            onChange={(v) => patch("host", setHost, "max_devices", v)}
            min={1}
            max={50}
          />
        </SettingRow>

        <SettingRow label="Placement policy">
          <SelectInput
            value={String(host.placement_policy ?? "local_first")}
            onChange={(v) => patch("host", setHost, "placement_policy", v)}
            options={[
              { value: "local_first", label: "Local first" },
              { value: "cloud_first", label: "Cloud first" },
              { value: "local_only", label: "Local only" },
            ]}
          />
        </SettingRow>

        <SettingRow label="Storage path" description="Base image and disk image storage">
          <TextInput
            value={String(host.storage_path ?? "")}
            onChange={(v) => patch("host", setHost, "storage_path", v)}
          />
        </SettingRow>
      </Section>

      {/* ── Streaming ───────────────────────────────────────────────── */}
      <Section
        icon={Monitor}
        title="Streaming"
        description="Default codec, bitrate, and quality profile for new WebRTC sessions."
        onSave={() => save("streaming", streaming)}
        saving={saving}
        dirty={!!dirty.streaming}
      >
        <SettingRow label="Default codec">
          <SelectInput
            value={String(streaming.default_codec ?? "h264")}
            onChange={(v) => patch("streaming", setStreaming, "default_codec", v)}
            options={[{ value: "h264", label: "H.264 (default)" }]}
          />
        </SettingRow>

        <SettingRow label="Default quality profile">
          <SelectInput
            value={String(streaming.default_profile ?? "smooth")}
            onChange={(v) => patch("streaming", setStreaming, "default_profile", v)}
            options={[
              { value: "smooth", label: "Smooth (30 fps, 8 Mbps)" },
              { value: "sharp_text", label: "Sharp text (12 fps, 4 Mbps)" },
            ]}
          />
        </SettingRow>

        <SettingRow label="Local bitrate cap (kbps)">
          <NumberInput
            value={streaming.local_bitrate_kbps as number ?? 8000}
            onChange={(v) => patch("streaming", setStreaming, "local_bitrate_kbps", v)}
            min={1000}
          />
        </SettingRow>

        <SettingRow label="Cloud bitrate cap (kbps)">
          <NumberInput
            value={streaming.cloud_bitrate_kbps as number ?? 4000}
            onChange={(v) => patch("streaming", setStreaming, "cloud_bitrate_kbps", v)}
            min={500}
          />
        </SettingRow>

        <SettingRow label="Max concurrent streams">
          <NumberInput
            value={streaming.max_concurrent_streams as number ?? 8}
            onChange={(v) => patch("streaming", setStreaming, "max_concurrent_streams", v)}
            min={1}
            max={64}
          />
        </SettingRow>

        <SettingRow label="WebCodecs canvas (default)" description="Off by default — power-user low-latency path">
          <Toggle
            value={Boolean(streaming.webcodecs_canvas_default)}
            onChange={(v) => patch("streaming", setStreaming, "webcodecs_canvas_default", v)}
          />
        </SettingRow>
      </Section>

      {/* ── MCP ─────────────────────────────────────────────────────── */}
      <Section
        icon={Radio}
        title="MCP gateway"
        description="Agent-facing MCP settings. Bind host is loopback-only — the localhost-only invariant is enforced server-side."
        onSave={() => save("mcp", mcp)}
        saving={saving}
        dirty={!!dirty.mcp}
      >
        <SettingRow label="MCP gateway enabled">
          <Toggle
            value={Boolean(mcp.global_enabled ?? true)}
            onChange={(v) => patch("mcp", setMcp, "global_enabled", v)}
          />
        </SettingRow>

        <SettingRow label="Expose new devices by default" description="Sets the default for mcp_exposed on device creation">
          <Toggle
            value={Boolean(mcp.default_exposure ?? true)}
            onChange={(v) => patch("mcp", setMcp, "default_exposure", v)}
          />
        </SettingRow>

        <SettingRow label="Default role">
          <SelectInput
            value={String(mcp.default_role ?? "observe")}
            onChange={(v) => patch("mcp", setMcp, "default_role", v)}
            options={[
              { value: "observe", label: "Observe (read-only)" },
              { value: "test", label: "Test (observe + actions)" },
              { value: "operate", label: "Operate (test + lifecycle)" },
              { value: "admin", label: "Admin (full)" },
            ]}
          />
        </SettingRow>

        <SettingRow label="Session token TTL (minutes)">
          <NumberInput
            value={mcp.token_ttl_minutes as number ?? 60}
            onChange={(v) => patch("mcp", setMcp, "token_ttl_minutes", v)}
            min={5}
            max={1440}
          />
        </SettingRow>

        <SettingRow
          label="Bind host"
          description="Must be 127.0.0.1 or ::1 — non-loopback values are rejected"
        >
          <TextInput
            value={String(mcp.bind_host ?? "127.0.0.1")}
            onChange={(v) => patch("mcp", setMcp, "bind_host", v)}
          />
        </SettingRow>
      </Section>

      {/* ── Manifests ───────────────────────────────────────────────── */}
      <Section
        icon={Layers}
        title="Manifest registry"
        description="Storage, retention, and validation settings for device environment manifests."
        onSave={() => save("manifests", manifests)}
        saving={saving}
        dirty={!!dirty.manifests}
      >
        <SettingRow label="Export directory">
          <TextInput
            value={String(manifests.export_dir ?? "")}
            onChange={(v) => patch("manifests", setManifests, "export_dir", v)}
          />
        </SettingRow>

        <SettingRow label="Import directory">
          <TextInput
            value={String(manifests.import_dir ?? "")}
            onChange={(v) => patch("manifests", setManifests, "import_dir", v)}
          />
        </SettingRow>

        <SettingRow label="Max manifest count">
          <NumberInput
            value={manifests.max_count as number ?? 100}
            onChange={(v) => patch("manifests", setManifests, "max_count", v)}
            min={1}
          />
        </SettingRow>

        <SettingRow label="Retention (days)" description="Manifests older than this are eligible for pruning">
          <NumberInput
            value={manifests.retention_days as number ?? 90}
            onChange={(v) => patch("manifests", setManifests, "retention_days", v)}
            min={1}
          />
        </SettingRow>

        <SettingRow label="Import validation">
          <SelectInput
            value={String(manifests.validation_strictness ?? "standard")}
            onChange={(v) => patch("manifests", setManifests, "validation_strictness", v)}
            options={[
              { value: "permissive", label: "Permissive (warn only)" },
              { value: "standard", label: "Standard" },
              { value: "strict", label: "Strict (reject on any warning)" },
            ]}
          />
        </SettingRow>
      </Section>

      {/* ── Security / Audit ────────────────────────────────────────── */}
      <Section
        icon={Shield}
        title="Security & audit"
        description="Audit log, keyring backend, dangerous-mode policy, and log redaction."
        onSave={() => save("security", security)}
        saving={saving}
        dirty={!!dirty.security}
      >
        <SettingRow label="Dangerous mode" description="Enables destructive operations without confirmation. Leave off unless you know what you're doing.">
          <Toggle
            value={Boolean(security.dangerous_mode)}
            onChange={(v) => patch("security", setSecurity, "dangerous_mode", v)}
          />
        </SettingRow>

        <SettingRow label="Audit log path">
          <TextInput
            value={String(security.audit_log_path ?? "")}
            onChange={(v) => patch("security", setSecurity, "audit_log_path", v)}
          />
        </SettingRow>

        <SettingRow label="Keyring backend">
          <SelectInput
            value={String(security.keyring_backend ?? "auto")}
            onChange={(v) => patch("security", setSecurity, "keyring_backend", v)}
            options={[
              { value: "auto", label: "Auto (OS keychain)" },
              { value: "system", label: "System keychain only" },
              { value: "file", label: "Encrypted file fallback" },
            ]}
          />
        </SettingRow>

        <SettingRow
          label="Log redaction patterns"
          description="Regex patterns matched against log field names; matching values are redacted to ***REDACTED***"
        >
          <textarea
            className="w-full rounded-md border bg-background px-3 py-1.5 text-xs font-mono focus:outline-none focus:ring-2 focus:ring-ring h-24 resize-none"
            value={(security.log_redaction_patterns as string[] ?? []).join("\n")}
            onChange={(e) =>
              patch("security", setSecurity, "log_redaction_patterns",
                e.target.value.split("\n").map((s) => s.trim()).filter(Boolean))
            }
          />
        </SettingRow>
      </Section>
    </div>
  )
}
