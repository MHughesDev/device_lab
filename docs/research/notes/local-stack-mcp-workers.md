---
doc_id: "23.5"
title: "Research notes — local stack, MCP, workers"
section: "Research"
summary: "Skim notes on packaging, MCP frameworks, task queues, SQLite/Litestream for DeviceLab."
updated: "2026-05-17"
---

# Notes — Local packaging, MCP gateway, workers, persistence

## Packaging shell (localhost vs Tauri)

- **Decision guidance:** Ship **Docker Compose + localhost browser** as default OSS install (matches “software factory” stack); optional **Tauri** wrapper later for OS keychain ergonomics and single-binary UX without forcing Electron weight [research round 2 Q1].
- **Rationale:** DeviceLab operators are developers; browser-to-localhost is simplest cross-platform; Tauri adds signing/release complexity.

## MCP implementation stack

- Implement MCP toward AI clients using **spec transports** (stdio + Streamable HTTP with SSE where needed) [S021].
- Internal complexity (dynamic tool manifests per device, streaming observations) suggests **official MCP Python SDK first** [S023], with **FastMCP** evaluated if proxy/composition/auth saves code [S024].

## Background workers

- **Default:** In-process **asyncio supervisor** for tunnel lifecycle + provisioning orchestration to avoid Redis dependency for single-user mode.
- **Scale-out profile:** Pluggable **Taskiq or Dramatiq** over Redis when multi-device parallelism exceeds single-process limits [Q3 findings].
- **ARQ:** Consider only if “at-least-once + pessimistic queue” semantics are explicitly desired.

## Device lifecycle FSM

- Use **`transitions`** with YAML-exportable machine definitions for the collapsed state model (canonical states + orthogonal flags) [S041].

## SQLite / Litestream

- **SQLite WAL** for local control-plane DB.
- **Litestream** optional feature for users who run DeviceLab on a semi-persistent VM and want S3 backup — not required for pure localhost [S040].

## Telemetry / updates

- **Telemetry:** Off by default; optional opt-in diagnostics compatible with OSS norms.
- **Updates:** Container image tags + release notes; defer auto-update until Tauri/native shell exists.

## Python version

- Align with repo policy (**3.12+**); revisit 3.13 when CI matrix proves stable.
