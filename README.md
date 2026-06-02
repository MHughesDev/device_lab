# DeviceLab

> **Local-first device testing for human operators and AI agents, with optional BYOC cloud capacity for workloads that require additional scale, duration, or device coverage.**

DeviceLab creates and manages test devices that run locally on the developer machine or, when cloud optionally selected over local AWS VMs are provisioned. Each device is streamed into the web application as a dedicated workspace tab with its own display, input controls, logs, and session actions. The same device capabilities are exposed as scoped MCP contracts, allowing AI coding agents such as Claude Code or Cursor to inspect device state, execute interactions, and test applications through emulated or cloud-backed device environments.

The control plane runs on `localhost`. The web UI provides human session management and operational visibility, while MCP provides the automation interface for agents. Cloud execution is optional and uses BYOC resources in the user's AWS account; DeviceLab does not introduce a hosted SaaS control plane.

## 🖥️ Supported device families

| Family | Local path | Optional cloud path |
|--------|------------|---------------------|
| Linux | Host-local runtime when supported by the machine and adapter. | EC2 Linux lifecycle with SSM bootstrap. |
| Browser | Host-local browser sessions. | Cloud-backed browser sessions for isolation, duration, or scale. |
| Android | Host-local emulator or attached-device paths where supported. | Nested-virtualization emulator capacity and AWS Device Farm. |
| Windows | Host-local VM or attached-host paths where supported. | EC2 Windows capacity. |
| macOS | Host-local macOS paths where supported. | Mac Dedicated Host capacity. |
| iOS Simulator | Local macOS simulator path. | macOS cloud host path where configured. |
| Real iOS | No local real-device path in the OSS core. | AWS Device Farm-backed real-device coverage. |

## ✅ Core positioning

DeviceLab is organized around three operating principles:

1. **🏠 Local-first by default.** Run the API and web UI locally, keep management traffic on `localhost`, and use local runtimes when host resources and device-family support are sufficient.
2. **☁️ Optional cloud expansion.** Enable BYOC AWS provisioning for EC2, Mac Dedicated Host, Android emulator capacity, AWS Device Farm targets, S3 artifacts, and runtime agents when a workload requires cloud resources.
3. **🤖 Agent-native automation.** Expose scoped device capabilities through MCP so AI agents can inspect structured observations, execute typed actions, record sessions, and replay evidence without relying on screenshot-only loops.

## 🧭 Operating modes

| Mode | Best for | Resource location | Control plane |
|------|----------|-------------------|---------------|
| 🏠 Local | Local development, short feedback loops, and device families supported by the host machine. | Developer machine | `localhost` |
| ☁️ BYOC cloud | Additional capacity, AWS-only device families, real Device Farm coverage, and longer-running sessions. | User-owned AWS account | `localhost` |
| 🔀 Hybrid | Local iteration with selected cloud sessions for coverage, performance, duration, or device availability. | Local machine + user-owned AWS account | `localhost` |

DeviceLab does not require a permanent choice between local and cloud execution. A workspace can run routine sessions locally and start cloud-backed sessions only for tasks that require cloud capacity or cloud-only device access.

## 🧱 Runtime surfaces

```text
Local developer machine
├── Web UI            React 19 + Vite + TanStack session management UI
│   └── Device tabs   streamed display, input controls, logs, and session actions
├── Control API       FastAPI + SQLModel + Postgres device control plane
├── MCP Gateway       FastMCP capability and action contracts for agents
├── Stream Gateway    aiortc WebRTC media + input data channel
└── Local runtime     local device execution with resource accounting

Optional user-owned AWS account
├── EC2 Linux / Windows / macOS capacity
├── Android emulator capacity with nested virtualization
├── AWS Device Farm real iOS / Android devices
├── S3 artifact and evidence storage
└── Runtime agents bootstrapped through SSM + mTLS
```

The same control-plane services coordinate local and cloud execution: lifecycle management, placement, cost guardrails, identity brokerage, observation/action routing, recipe execution, artifact capture, evidence replay, and the versioned adapter SPI. Device-family-specific behavior is isolated in adapters rather than embedded in core services.

## 🔒 Architecture invariants

| Invariant | Meaning |
|-----------|---------|
| 🏠 Localhost-only control plane | The API is bound to local operation and is not designed as a public internet service. |
| ☁️ Optional BYOC boundary | Cloud resources are optional and, when enabled, are created in the user's AWS account. |
| 🤖 MCP first | MCP is the primary automation interface for agents; the web UI provides human session management, inspection, and operational controls. |
| 🔐 SecretRef only | Secrets are referenced through SecretRef indirection and are not exposed as plaintext to model context. |
| 🧾 Append-only audit | Audit entries use an HMAC-SHA256 hash chain to make historical records tamper-evident. |
| 🧩 Adapter SPI | Device families integrate through versioned adapter contracts. |

## 🧰 Locked dependency spine

| Concern | Package / source |
|---------|------------------|
| MCP server | `mcp` via FastMCP |
| WebRTC streaming | `aiortc` |
| Browser adapter | `browser-use` |
| Android control | `uiautomator2` + `adb` |
| AWS cost | `boto3` + `awspricing` |
| Device FSM | `pytransitions` |
| Recipes | `pypyr` |
| Secrets | `keyring` |
| Network proxy | `mitmproxy` |
| Audit log | Small in-repo HMAC-SHA256 implementation |

## 🤖 Quick orientation for agents

1. Read `README.md`, then `AGENTS.md`, before modifying code or policy.
2. Run `make skills:list` and read every matching skill before planning changes.
3. Prefer canonical `make` targets over ad hoc shell.
4. Preserve the architecture invariants listed above.
5. If security, data integrity, or policy semantics are unclear, stop instead of guessing.

## 🛠️ Canonical commands

```bash
make help          # list the command surface
make dev           # run the local development stack entrypoint
make lint          # Ruff lint
make fmt           # Ruff format
make typecheck     # mypy strict checks
make test          # backend tests with coverage
make skills:list   # enumerate procedural playbooks
```

## 🔗 Links

- [Authoritative spec](spec/spec.md)
- [Long-term implementation plan](docs/roadmap/long-term-plan.md)
- [End-state capabilities](docs/product/end-state-capabilities.md)
- [Architecture docs](docs/architecture/README.md)
- [API docs](docs/api/README.md)
- [Security docs](docs/security/README.md)
- [OSS dependency decisions](docs/research/notes/oss-repo-candidates.md)
- [Skills index](skills/README.md)
- [Agent instructions](AGENTS.md)
