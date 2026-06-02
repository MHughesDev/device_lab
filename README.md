# DeviceLab

> **Local-first device testing for humans and AI agents, with optional BYOC cloud capacity when local resources are not enough.**

DeviceLab is an open-source control plane for creating, operating, and auditing device test environments. It starts on the developer machine and can optionally extend into the user's own AWS account for larger, longer-running, or hardware-specific workloads.

The default posture is local-first: the control plane runs on `localhost`, the web UI is a local operator console, and MCP is the primary automation interface for coding agents. When a team needs more capacity or device coverage, DeviceLab can provision cloud resources in that team's AWS account without introducing a DeviceLab-hosted SaaS control plane.

## ✅ Core positioning

DeviceLab is designed around three operating principles:

1. **🏠 Local-first by default.** Run the control plane locally, keep the operator surface on `localhost`, and use local runtimes where they fit the workload.
2. **☁️ Optional cloud expansion.** Choose BYOC AWS provisioning for EC2, Mac Dedicated Host, Android emulator capacity, AWS Device Farm targets, S3 artifacts, and runtime agents when cloud execution is the right fit.
3. **🤖 Agent-native automation.** Expose device capabilities through MCP so AI agents can observe, act, record, and replay work without relying on screenshot-only loops.

## 🧭 Operating modes

| Mode | Best for | Resource location | Control plane |
|------|----------|-------------------|---------------|
| 🏠 Local | Fast setup, local development, short feedback loops, and host-available device families. | Developer machine | `localhost` |
| ☁️ BYOC cloud | Scale-out capacity, AWS-only device families, real Device Farm coverage, and longer-running sessions. | User-owned AWS account | `localhost` |
| 🔀 Hybrid | Local iteration with selective cloud sessions for coverage, performance, or device availability. | Local machine + user-owned AWS account | `localhost` |

DeviceLab does not require users to choose one permanent deployment model. A workspace can stay local for routine work and use cloud-backed devices only when the task requires them.

## 🧱 End-state architecture

When complete, the repository resolves into this shape:

```text
Local developer machine
├── Web UI            React 19 + Vite + TanStack browser workspace
├── Control API       FastAPI + SQLModel + Postgres device control plane
├── MCP Gateway       FastMCP tool surface for coding agents
├── Stream Gateway    aiortc WebRTC media + input data channel
└── Local runtime     optional local devices with resource accounting

Optional user-owned AWS account
├── EC2 Linux / Windows / macOS capacity
├── Android emulator capacity with nested virtualization
├── AWS Device Farm real iOS / Android devices
├── S3 artifact and evidence storage
└── Runtime agents bootstrapped through SSM + mTLS
```

The core services remain shared across local and cloud execution: lifecycle management, placement, cost guardrails, identity brokerage, observation/action routing, recipe execution, artifact capture, evidence replay, and the versioned adapter SPI. Device-family-specific behavior belongs in adapters, not in the control-plane core.

## 📌 Current status

DeviceLab is in structured buildout:

- The authoritative product contract is captured in the spec.
- The long-term roadmap tracks the phase sequence and end-state component map.
- The foundational stack is FastAPI + SQLModel + Postgres, React 19 + Vite + TanStack, Docker Compose, FastMCP, and aiortc.
- The remaining northbound work focuses on low-latency streaming, device manifests, the browser-tab workspace, and root/cloud infrastructure settings.

## 🔒 Architecture invariants

| Invariant | Meaning |
|-----------|---------|
| 🏠 Localhost-only control plane | The API is a local operator surface, not a public internet service. |
| ☁️ Optional BYOC boundary | Cloud resources, when used, are created in the user's AWS account. |
| 🤖 MCP first | Agents are first-class operators; the web UI is the human cockpit. |
| 🔐 SecretRef only | Plaintext secrets do not enter model context. |
| 🧾 Append-only audit | HMAC-SHA256 hash chain; history is tamper-evident evidence. |
| 🧩 Adapter SPI | Device families plug in through versioned contracts. |

## 🖥️ Supported device families

| Family | Local path | Cloud path |
|--------|------------|------------|
| Linux | Local runtime where available. | EC2 Linux lifecycle and SSM bootstrap. |
| Browser | Local browser sessions. | Cloud-backed browser sessions when needed. |
| Android | Local emulator/device paths where available. | Nested-virtualization emulator capacity and Device Farm. |
| Windows | Local VM/host paths where available. | EC2 Windows capacity. |
| macOS | Local Mac host paths where available. | Mac Dedicated Host capacity. |
| iOS Simulator | Local macOS simulator path. | macOS cloud host path where configured. |
| Real iOS | Not local in OSS core. | AWS Device Farm-backed real-device coverage. |

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

1. Read `README.md`, then `AGENTS.md`.
2. Run `make skills:list` and read any matching skill before planning.
3. Prefer canonical `make` targets over ad hoc shell.
4. Preserve the architecture invariants above.
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
