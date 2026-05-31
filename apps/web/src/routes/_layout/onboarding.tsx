import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"

export const Route = createFileRoute("/_layout/onboarding")({
  component: OnboardingWizard,
  head: () => ({ meta: [{ title: "DeviceLab — First-run setup" }] }),
})

type Step = "connect" | "preflight" | "bootstrap" | "device" | "done"

interface CloudAccountForm {
  display_name: string
  region: string
  credential_source: "env" | "profile" | "role"
  credential_profile: string
  credential_role_arn: string
}

interface PreflightCheck {
  name: string
  status: "pass" | "warn" | "fail"
  severity: string
  message: string
  remediation: string
}

interface PreflightReport {
  status: "pass" | "warn" | "fail"
  checks: PreflightCheck[]
}

interface BootstrapResource {
  resource_type: string
  resource_id: string
  action: string
  estimated_cost: string
}

interface BootstrapPlan {
  account_id: string
  region: string
  resources: BootstrapResource[]
  total_estimated_cost: string
}

const STEPS: { id: Step; label: string }[] = [
  { id: "connect", label: "Connect account" },
  { id: "preflight", label: "Preflight" },
  { id: "bootstrap", label: "Bootstrap" },
  { id: "device", label: "First device" },
  { id: "done", label: "Done" },
]

function StepIndicator({ current }: { current: Step }) {
  const currentIdx = STEPS.findIndex((s) => s.id === current)
  return (
    <div className="flex items-center gap-0">
      {STEPS.map((step, i) => (
        <div key={step.id} className="flex items-center">
          <div className={`flex items-center gap-1.5 text-xs px-3 py-1 rounded-full font-medium ${
            i === currentIdx ? "bg-primary text-primary-foreground" :
            i < currentIdx ? "text-green-600" : "text-muted-foreground"
          }`}>
            {i < currentIdx && <span>✓</span>}
            {step.label}
          </div>
          {i < STEPS.length - 1 && <div className="w-6 h-px bg-border mx-1" />}
        </div>
      ))}
    </div>
  )
}

function StatusIcon({ status }: { status: "pass" | "warn" | "fail" }) {
  if (status === "pass") return <span className="text-green-600 font-bold">✓</span>
  if (status === "warn") return <span className="text-yellow-500 font-bold">⚠</span>
  return <span className="text-red-500 font-bold">✗</span>
}

function OnboardingWizard() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [step, setStep] = useState<Step>("connect")
  const [accountId, setAccountId] = useState<string | null>(null)
  const [preflight, setPreflight] = useState<PreflightReport | null>(null)
  const [bootstrapPlan, setBootstrapPlan] = useState<BootstrapPlan | null>(null)
  const [deviceId, setDeviceId] = useState<string | null>(null)
  const [form, setForm] = useState<CloudAccountForm>({
    display_name: "My AWS Account",
    region: "us-east-1",
    credential_source: "env",
    credential_profile: "",
    credential_role_arn: "",
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function post(path: string, body?: unknown) {
    const res = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined,
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }))
      throw new Error(err.detail ?? res.statusText)
    }
    return res.json()
  }

  async function get(path: string) {
    const res = await fetch(path)
    if (!res.ok) throw new Error(res.statusText)
    return res.json()
  }

  // Step 1: Connect account
  async function handleConnect() {
    setLoading(true)
    setError(null)
    try {
      const body: Record<string, unknown> = {
        provider: "aws",
        display_name: form.display_name,
        region: form.region,
        credential_source: form.credential_source,
      }
      if (form.credential_source === "profile") body.credential_profile = form.credential_profile
      if (form.credential_source === "role") body.credential_role_arn = form.credential_role_arn
      const acct = await post("/api/v1/cloud-accounts/", body)
      setAccountId(acct.id)
      setStep("preflight")
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  // Step 2: Preflight
  async function handlePreflight() {
    setLoading(true)
    setError(null)
    try {
      const report: PreflightReport = await post(`/api/v1/cloud-accounts/${accountId}/preflight`)
      setPreflight(report)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  // Step 3: Bootstrap plan + execute
  async function handleBootstrapPlan() {
    setLoading(true)
    setError(null)
    try {
      const plan: BootstrapPlan = await get(`/api/v1/cloud-accounts/${accountId}/bootstrap/plan`)
      setBootstrapPlan(plan)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleBootstrapExecute() {
    setLoading(true)
    setError(null)
    try {
      await post(`/api/v1/cloud-accounts/${accountId}/bootstrap/execute`)
      setStep("device")
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  // Step 4: First device
  async function handleProvisionDevice() {
    setLoading(true)
    setError(null)
    try {
      const templates: any[] = await get("/api/v1/templates/")
      const linux = templates.find((t) => t.family === "linux")
      if (!linux) throw new Error("Linux template not found")
      const device = await post("/api/v1/devices/", {
        template_id: linux.id,
        cloud_account_id: accountId,
        region: form.region,
      })
      setDeviceId(device.id)
      setStep("done")
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const mcpConfig = `{
  "mcpServers": {
    "devicelab": {
      "url": "http://127.0.0.1:8000/mcp",
      "transport": "streamable-http"
    }
  }
}`

  return (
    <div className="p-6 max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">First-run setup</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Connect your AWS account, run preflight, and provision your first device.
        </p>
      </div>

      <StepIndicator current={step} />

      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 dark:bg-red-950 p-3 text-sm text-red-700 dark:text-red-300">
          {error}
        </div>
      )}

      {/* Step 1: Connect */}
      {step === "connect" && (
        <div className="rounded-lg border p-6 space-y-4">
          <h2 className="font-medium">Connect AWS account</h2>
          <div className="space-y-3">
            <div>
              <label className="text-sm font-medium">Display name</label>
              <input
                className="mt-1 w-full rounded-md border px-3 py-2 text-sm bg-background"
                value={form.display_name}
                onChange={(e) => setForm({ ...form, display_name: e.target.value })}
              />
            </div>
            <div>
              <label className="text-sm font-medium">Region</label>
              <select
                className="mt-1 w-full rounded-md border px-3 py-2 text-sm bg-background"
                value={form.region}
                onChange={(e) => setForm({ ...form, region: e.target.value })}
              >
                {["us-east-1","us-east-2","us-west-1","us-west-2","eu-west-1","eu-west-2","eu-central-1","ap-southeast-1","ap-northeast-1"].map((r) => (
                  <option key={r} value={r}>{r}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-sm font-medium">Credential source</label>
              <select
                className="mt-1 w-full rounded-md border px-3 py-2 text-sm bg-background"
                value={form.credential_source}
                onChange={(e) => setForm({ ...form, credential_source: e.target.value as any })}
              >
                <option value="env">Environment variables (AWS_ACCESS_KEY_ID)</option>
                <option value="profile">~/.aws/credentials profile</option>
                <option value="role">IAM role ARN (assume-role)</option>
              </select>
            </div>
            {form.credential_source === "profile" && (
              <div>
                <label className="text-sm font-medium">Profile name</label>
                <input
                  className="mt-1 w-full rounded-md border px-3 py-2 text-sm bg-background"
                  placeholder="default"
                  value={form.credential_profile}
                  onChange={(e) => setForm({ ...form, credential_profile: e.target.value })}
                />
              </div>
            )}
            {form.credential_source === "role" && (
              <div>
                <label className="text-sm font-medium">Role ARN</label>
                <input
                  className="mt-1 w-full rounded-md border px-3 py-2 text-sm bg-background font-mono text-xs"
                  placeholder="arn:aws:iam::123456789012:role/DeviceLab"
                  value={form.credential_role_arn}
                  onChange={(e) => setForm({ ...form, credential_role_arn: e.target.value })}
                />
              </div>
            )}
          </div>
          <button
            className="rounded-md bg-primary text-primary-foreground px-4 py-2 text-sm font-medium disabled:opacity-50"
            onClick={handleConnect}
            disabled={loading}
          >
            {loading ? "Saving…" : "Save & continue →"}
          </button>
        </div>
      )}

      {/* Step 2: Preflight */}
      {step === "preflight" && (
        <div className="rounded-lg border p-6 space-y-4">
          <h2 className="font-medium">AWS preflight checks</h2>
          {!preflight ? (
            <button
              className="rounded-md bg-primary text-primary-foreground px-4 py-2 text-sm font-medium disabled:opacity-50"
              onClick={handlePreflight}
              disabled={loading}
            >
              {loading ? "Running checks…" : "Run preflight →"}
            </button>
          ) : (
            <div className="space-y-3">
              <div className={`text-sm font-medium ${
                preflight.status === "pass" ? "text-green-600" :
                preflight.status === "warn" ? "text-yellow-600" : "text-red-600"
              }`}>
                Overall: {preflight.status.toUpperCase()}
              </div>
              {preflight.checks.map((c) => (
                <div key={c.name} className="flex gap-3 text-sm">
                  <StatusIcon status={c.status} />
                  <div>
                    <p className="font-medium">{c.name}</p>
                    <p className="text-muted-foreground">{c.message}</p>
                    {c.remediation && c.status !== "pass" && (
                      <p className="text-xs text-yellow-700 dark:text-yellow-400 mt-0.5">→ {c.remediation}</p>
                    )}
                  </div>
                </div>
              ))}
              {(preflight.status === "pass" || preflight.status === "warn") && (
                <button
                  className="rounded-md bg-primary text-primary-foreground px-4 py-2 text-sm font-medium mt-2"
                  onClick={() => { handleBootstrapPlan(); setStep("bootstrap") }}
                >
                  Continue to bootstrap →
                </button>
              )}
              {preflight.status === "fail" && (
                <button
                  className="rounded-md border px-4 py-2 text-sm font-medium"
                  onClick={() => { setPreflight(null); handlePreflight() }}
                >
                  Re-run preflight
                </button>
              )}
            </div>
          )}
        </div>
      )}

      {/* Step 3: Bootstrap */}
      {step === "bootstrap" && (
        <div className="rounded-lg border p-6 space-y-4">
          <h2 className="font-medium">Bootstrap AWS resources</h2>
          {loading && !bootstrapPlan && <p className="text-sm text-muted-foreground">Loading plan…</p>}
          {bootstrapPlan && (
            <div className="space-y-3">
              <p className="text-sm text-muted-foreground">
                The following resources will be created in your AWS account ({bootstrapPlan.account_id} / {bootstrapPlan.region}):
              </p>
              <div className="divide-y rounded-md border">
                {bootstrapPlan.resources.map((r) => (
                  <div key={r.resource_id} className="flex items-center justify-between px-3 py-2 text-sm">
                    <div>
                      <span className="font-mono text-xs text-muted-foreground">{r.resource_type}</span>
                      <span className="ml-2 font-medium">{r.resource_id}</span>
                    </div>
                    <span className="text-xs text-muted-foreground">{r.estimated_cost}</span>
                  </div>
                ))}
              </div>
              <p className="text-xs text-muted-foreground">
                Estimated cost: <strong>{bootstrapPlan.total_estimated_cost}</strong>
              </p>
              <button
                className="rounded-md bg-primary text-primary-foreground px-4 py-2 text-sm font-medium disabled:opacity-50"
                onClick={handleBootstrapExecute}
                disabled={loading}
              >
                {loading ? "Bootstrapping…" : "Confirm & bootstrap →"}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Step 4: First device */}
      {step === "device" && (
        <div className="rounded-lg border p-6 space-y-4">
          <h2 className="font-medium">Provision your first device</h2>
          <p className="text-sm text-muted-foreground">
            This will launch a Linux (Ubuntu 24.04) EC2 t3.medium instance in {form.region} and bootstrap the DeviceLab runtime agent via SSM.
          </p>
          <button
            className="rounded-md bg-primary text-primary-foreground px-4 py-2 text-sm font-medium disabled:opacity-50"
            onClick={handleProvisionDevice}
            disabled={loading}
          >
            {loading ? "Provisioning…" : "Provision Linux device →"}
          </button>
        </div>
      )}

      {/* Step 5: Done */}
      {step === "done" && (
        <div className="rounded-lg border p-6 space-y-4">
          <h2 className="font-medium text-green-600">🎉 DeviceLab is ready</h2>
          <p className="text-sm text-muted-foreground">
            Your device is provisioning. Add the MCP config to your agent to connect.
          </p>
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1">MCP config snippet</p>
            <pre className="rounded-md border bg-muted p-3 text-xs font-mono overflow-x-auto">{mcpConfig}</pre>
          </div>
          <button
            className="rounded-md bg-primary text-primary-foreground px-4 py-2 text-sm font-medium"
            onClick={() => navigate({ to: "/" })}
          >
            Go to status →
          </button>
        </div>
      )}
    </div>
  )
}
