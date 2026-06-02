# DeviceLab

> **A localhost mission control for cloud devices — built for agents, safe for humans, and paid for only in your own AWS account.**

DeviceLab is an open-source, local-first, BYOC (Bring Your Own Cloud) device testing platform. It turns your laptop into the control tower and your AWS account into the launchpad for Linux, Android, Windows, macOS, iOS Simulator, real-device, and browser environments.

No hosted control plane. No reseller markup. No "please paste the secret into chat" energy. Just a local API, a web cockpit, an MCP gateway, and a fleet of disposable devices that can be driven by humans or AI agents.

## The vibe

Imagine a tiny NASA console for test devices:

- **Launch** a Linux VM, Android emulator, browser session, Windows host, macOS runner, iOS Simulator, or real Device Farm target.
- **Observe** through the cheapest useful signal first: accessibility tree, then OCR, then screenshots, then gated VLMs.
- **Act** with semantic commands, batched steps, screen-version checks, and device-family capability maps.
- **Record** recipes, artifacts, timelines, logs, screenshots, and replayable evidence.
- **Stop spending money** with cost estimates, caps, lifecycle cleanup, and audit trails that make expensive paths explain themselves.

## North star

DeviceLab's finished form is a local control plane with three promises:

1. **Agent-native first.** MCP is the primary interface, not a bolt-on. Agents discover scoped tools, observe structured state, execute low-round-trip actions, and leave evidence behind.
2. **Your cloud, your devices.** EC2, Mac Dedicated Host, Android emulators, AWS Device Farm, S3 artifacts, and runtime agents live in the user's AWS account — DeviceLab does not host them.
3. **Safety with receipts.** Secrets stay behind `SecretRef` indirection in the OS keychain, dangerous actions are gated and audited, costs are visible, and the audit log is append-only.

## Where the repo is headed

When complete, the repository resolves into this shape:

```text
Local developer machine
├── Web UI            React 19 + Vite + TanStack browser workspace
├── Control API       FastAPI + SQLModel + Postgres device brain
├── MCP Gateway       FastMCP tool surface for coding agents
├── Stream Gateway    aiortc WebRTC media + input data channel
└── Local runtime     optional local devices with resource accounting

User-owned AWS account
├── EC2 Linux / Windows / macOS capacity
├── Android emulator capacity with nested virtualization
├── AWS Device Farm real iOS / Android devices
├── S3 artifact and evidence storage
└── Runtime agents bootstrapped through SSM + mTLS
```

The core stays boring in the best way: lifecycle services, cost guardrails, identity broker, observation/action hub, recipe runner, artifact store, evidence replay, and a versioned adapter SPI. Device-family quirks belong in adapters, not the control-plane bloodstream.

## Current status

DeviceLab is past the "blank napkin" stage and into a structured buildout:

- The authoritative product contract is captured in the spec.
- The long-term roadmap tracks the full phase sequence and end-state component map.
- The foundational stack is FastAPI + SQLModel + Postgres, React 19 + Vite + TanStack, Docker Compose, FastMCP, and aiortc.
- The remaining northbound work is centered on low-latency streaming, manifests, the browser-tab workspace, and root/cloud infrastructure settings.

## Architecture invariants

These are not decorative. They are load-bearing:

| Invariant | Meaning |
|-----------|---------|
| Localhost-only control plane | The API is a local operator surface, not an internet service. |
| BYOC hard boundary | All cloud resources are created in the user's account. |
| MCP first | Agents are first-class operators; web UI is the human cockpit. |
| SecretRef only | Plaintext secrets do not enter model context. |
| Append-only audit | HMAC-SHA256 hash chain; history is evidence, not clay. |
| Adapter SPI | Device families plug in through versioned contracts. |

## What DeviceLab operates

| Family | Why it matters |
|--------|----------------|
| Linux | The first vertical slice: provisioning, SSM bootstrap, lifecycle, streaming, cleanup. |
| Browser | Proves semantic automation beyond VM management. |
| Android | Emulator and real-device paths for mobile workflows. |
| Windows | Desktop automation and compatibility coverage. |
| macOS | Dedicated Host capacity and Apple-platform workflows. |
| iOS Simulator | Fast Apple mobile loops where simulator fidelity is enough. |
| Real iOS | Device Farm-backed coverage when physical devices matter. |

## Locked dependency spine

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

## Quick orientation for agents

1. Read `README.md`, then `AGENTS.md`.
2. Run `make skills:list` and read any matching skill before planning.
3. Prefer canonical `make` targets over ad hoc shell.
4. Preserve the architecture invariants above.
5. If security, data integrity, or policy semantics are unclear, stop instead of guessing.

## Canonical commands

```bash
make help          # list the command surface
make dev           # run the local development stack entrypoint
make lint          # Ruff lint
make fmt           # Ruff format
make typecheck     # mypy strict checks
make test          # backend tests with coverage
make skills:list   # enumerate procedural playbooks
```

## Bottom links

- [Authoritative spec](spec/spec.md)
- [Long-term implementation plan](docs/roadmap/long-term-plan.md)
- [End-state capabilities](docs/product/end-state-capabilities.md)
- [Architecture docs](docs/architecture/README.md)
- [API docs](docs/api/README.md)
- [Security docs](docs/security/README.md)
- [OSS dependency decisions](docs/research/notes/oss-repo-candidates.md)
- [Skills index](skills/README.md)
- [Agent instructions](AGENTS.md)
