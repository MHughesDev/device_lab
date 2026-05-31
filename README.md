# DeviceLab

Open-source, local-first, BYOC (Bring Your Own Cloud) device testing platform. Provision and operate Linux, Android, Windows, macOS, iOS Simulator, real iOS, and browser environments in your own AWS account — accessible to both humans (web UI) and AI agents (MCP).

The control plane runs on your laptop. All cloud resources live in your AWS account. No SaaS, no vendor lock-in.

## Status

Pre-code. Spec, research, and roadmap are finalized. The template scaffold (FastAPI + React + Docker Compose) will be cloned in next, followed by Phase 1 MVP work.

## Navigation

| Path | Contents |
|------|----------|
| `spec/spec.md` | Authoritative product spec (v5.0) |
| `docs/product/end-state-capabilities.md` | Full feature enumeration |
| `docs/roadmap/long-term-plan.md` | 6-phase roadmap |
| `docs/research/notes/oss-repo-candidates.md` | OSS dependency decisions (locked) |
| `docs/architecture/` | System design docs |
| `docs/api/` | REST API design + error codes |
| `docs/adr/` | Architecture decision records |
| `docs/security/` | Threat model, secrets, accepted risks |

## Quick orientation

- **BYOC hard boundary**: DeviceLab never hosts your devices. All EC2, Device Farm, and Mac Dedicated Host resources are created in your own AWS account via `boto3`.
- **MCP first**: AI agents interact through a per-device filtered MCP tool manifest. The web UI is secondary.
- **Local control plane**: The server runs on `localhost`. No inbound ports, no cloud control plane.
- **Observation tiers**: AX tree (Tier 1) → OCR (Tier 2) → Screenshot (Tier 3) → VLM (Tier 4, gated).

## Key dependencies (locked)

| Concern | Package |
|---------|---------|
| WebRTC streaming | `aiortc` |
| MCP server | `mcp` (FastMCP) |
| Browser adapter | `browser-use` |
| Android control | `uiautomator2` + `adb` |
| AWS cost | `boto3` + `awspricing` |
| Recipe DSL | `pypyr` |
| Secrets | `keyring` |
| Network proxy | `mitmproxy` |
| Audit log | ~100-line HMAC-SHA256 scratch impl |

See `docs/research/notes/oss-repo-candidates.md` for full rationale and rejects.
