---
doc_id: "24.8"
title: "Phase 07 — Local hosting"
section: "Roadmap"
status: "planned"
completion: "0%"
updated: "2026-06-01"
---

# Phase 07 — Local Hosting

**Progress: 0%** `░░░░░░░░░░` — planned

## Objective

Let DeviceLab host device families **directly on the local host machine** with no AWS account, while keeping the MCP gateway, manifest filtering, permissions, and observation/action envelopes unchanged. Deliver the three seams from ADR-0003 — a **Channel** transport abstraction, a **LocalScheduler** with admission control and a reaper, and a **placement layer** (`location` attribute) — and prove them end-to-end on the Linux-via-Docker path first. Android-via-AVD and Windows-via-VM follow on the same seams. macOS / iOS Sim local are gated to Apple hardware.

This phase implements ADR-0003. Read it first: `docs/adr/0003-local-hosting-architecture.md`.

---

## OSS pulled in this phase

| Package / source | What we take | Where it lands |
|-----------------|-------------|----------------|
| `docker` (Python SDK, add to pyproject) | Container lifecycle + `exec` for local Linux devices | `transport/docker_exec.py`, `adapters/linux/local_provision.py` |
| `asyncssh` (add to pyproject) | SSH channel for local Windows/macOS VMs | `transport/ssh.py` |
| `psutil` (add to pyproject) | Host capacity probing (RAM/CPU/disk) + process-level reaping | `services/local/host_probe.py`, `services/local/scheduler.py` |
| `adb` (CLI, already used by Android adapter) | Direct ADB to local AVD (no SSM tunnel) | `transport/adb.py` |
| QEMU / libvirt (system dependency, documented not vendored) | Local Windows/macOS VM provisioning | `adapters/windows/local_provision.py` |
| `mitmproxy` (already in) | Per-family local proxy + CA injection (gated on OQ-012) | `services/local/proxy.py` |

Add to `apps/api/pyproject.toml`: `"docker>=7.0.0"`, `"asyncssh>=2.14.0"`, `"psutil>=5.9.0"`.

---

## Task batches and dependencies

```
Batch A (Channel SPI — everything depends on this)
  07-01  Channel ABC + ChannelFactory + location attribute on Device
  07-02  Extract existing SSM logic into SSMChannel (no behavior change)

Batch B (local scheduler — depends on A)
  07-03  Host capability probe (OS, arch, docker, virt, apple-hardware)
  07-04  LocalScheduler: capacity model + admission control + FSM gate
  07-05  Reaper: GC orphaned local resources by DeviceLab label convention

Batch C (placement — depends on A, B)
  07-06  Placement policy resolution (prefer_local/local_only/cloud_only)
  07-07  Host-capability family/template filtering in manifest layer

Batch D (Linux local — the proof; depends on A, B, C)
  07-08  DockerExecChannel
  07-09  Linux adapter local_provision (container create/start/stop/terminate)
  07-10  Conformance: run existing adapter conformance suite against local Linux

Batch E (Android local — depends on A, B, C, D)
  07-11  ADBChannel (direct) + AVD local_provision

Batch F (Windows local — depends on A, B, C, D; cloud remains primary)
  07-12  SSHChannel + QEMU/VirtualBox local_provision

Batch G (Apple-gated — depends on A, B, C, D)
  07-13  macOS + iOS Sim local provisioners, hard-refused on non-Apple hosts

Batch H (cross-cutting; depends on D)
  07-14  Startup reconciliation: DB state vs hypervisor reality
  07-15  Local networking + per-family proxy/CA injection (gated on OQ-012)
  07-16  `devicelab doctor` — local diagnostics (docker up? virt? disk? ports?)

Batch I (docs — last)
  07-17  Local hosting operator guide + per-family host prerequisites
```

---

## Task 07-01: Channel ABC + ChannelFactory + location attribute

**Files:** `apps/api/app/transport/__init__.py` (new), `apps/api/app/transport/channel.py` (new), `apps/api/app/models.py` (edit)

```python
# transport/channel.py
class Channel(ABC):
    @abstractmethod
    async def exec(self, command: str, timeout_ms: int = 30000) -> ExecResult: ...
    @abstractmethod
    async def push_file(self, local_path: str, remote_path: str) -> None: ...
    @abstractmethod
    async def pull_file(self, remote_path: str, local_path: str) -> None: ...
    @abstractmethod
    async def heartbeat(self) -> bool: ...
    async def close(self) -> None: ...

@dataclass
class ExecResult:
    stdout: str
    stderr: str
    exit_code: int

class ChannelFactory:
    """Resolve (family, location, provider_ids) -> concrete Channel."""
    @staticmethod
    def get(device: object) -> Channel: ...
```

**Wiring:** add `location: str = Field(default="cloud")` to the `Device` model (Alembic migration). `ChannelFactory.get` dispatches on `(device.family, device.location)`.

**Tests:** `test_channel_factory_resolves_ssm_for_cloud`, `test_channel_factory_resolves_docker_for_local_linux`, `test_device_defaults_to_cloud_location`.

**Do not:** implement DockerExecChannel here (07-08). Do not touch MCP tool code — transport is below the adapter.

---

## Task 07-02: Extract SSM logic into SSMChannel

**Files:** `apps/api/app/transport/ssm.py` (new); edit adapters that call `boto3.client("ssm")` inline.

Move the repeated `send_command` → poll `get_command_invocation` pattern out of `linux/interaction.py`, `macos/`, `windows/`, `ios_sim/` and behind `SSMChannel.exec()`. **Pure refactor — no behavior change.** Existing cloud devices must pass the conformance suite unchanged.

**Tests:** `test_ssm_channel_exec_polls_until_success`, `test_ssm_channel_exec_surfaces_failed_status`. Existing adapter tests must stay green.

**Do not:** change polling counts/timeouts; preserve current behavior exactly.

---

## Task 07-03: Host capability probe

**Files:** `apps/api/app/services/local/host_probe.py` (new)

```python
@dataclass
class HostCapabilities:
    os: Literal["linux", "macos", "windows"]
    arch: Literal["x86_64", "arm64"]
    docker_available: bool
    virtualization_available: bool   # KVM / WHPX / Hypervisor.framework
    is_apple_hardware: bool
    total_ram_mb: int
    total_vcpu: int
    free_disk_mb: int

def probe_host() -> HostCapabilities: ...
```

**Tests:** `test_probe_detects_os_and_arch`, `test_probe_reports_apple_hardware_false_on_linux`. Mock `psutil`/`platform` for determinism.

**Do not:** make network calls; probing is local-only and fast.

---

## Task 07-04: LocalScheduler — capacity + admission control

**Files:** `apps/api/app/services/local/scheduler.py` (new); edit `services/device_fsm.py`.

Maintain committed-vs-total resource accounting from `HostCapabilities`. Before the FSM enters `provisioning` for a `location=local` device, call `scheduler.admit(template_resource_estimate)`. On rejection, transition to `preflight_blocked` with reason `insufficient_host_resources`.

**Tests:** `test_admit_rejects_when_over_ram`, `test_admit_allows_within_capacity`, `test_fsm_blocks_on_scheduler_rejection`.

**Do not:** implement queueing yet (config flag stub only); reject-fast is the v1 behavior.

---

## Task 07-05: Reaper

**Files:** `apps/api/app/services/local/reaper.py` (new)

Periodic sweep (and on-demand) for DeviceLab-created local resources with no live `Device` row: stopped/orphaned Docker containers, dangling VM disk images, leftover AVDs. Match by a local label convention mirroring the cloud `DeviceLab:Workspace`/`DeviceLab:Device` tags (e.g. Docker labels `devicelab.workspace`, `devicelab.device`).

**Tests:** `test_reaper_removes_orphan_container`, `test_reaper_skips_live_device`.

**Do not:** delete resources lacking the DeviceLab label — never touch user-owned containers/VMs.

---

## Task 07-06: Placement policy resolution

**Files:** `apps/api/app/services/local/placement.py` (new); edit device-create path.

Resolve `location` at create time from policy (`prefer_local` | `local_only` | `cloud_only`) ∩ host capability ∩ family support. `prefer_local` falls back to cloud when the host can't host the family; `local_only` for an unsupported family is a hard 4xx.

**Tests:** `test_prefer_local_falls_back_to_cloud_for_ios_sim_on_linux`, `test_local_only_unsupported_family_errors`, `test_cloud_only_ignores_host`.

**Do not:** expose placement to the MCP agent — it is a create-time/admin concern; agents stay placement-agnostic.

---

## Task 07-07: Host-capability manifest filtering

**Files:** edit `apps/api/app/mcp/manifest.py` / template-listing service.

Filter the offered families/templates by `HostCapabilities` exactly as MCP tools are filtered by `DeviceCapabilities`. A Linux host must not offer macOS/ios_sim local templates; an x86 host warns on arm-only images.

**Tests:** `test_linux_host_hides_macos_local_template`, `test_apple_host_offers_all_families`.

**Do not:** remove cloud templates — host filtering applies to local placement only.

---

## Task 07-08: DockerExecChannel

**Files:** `apps/api/app/transport/docker_exec.py` (new)

Implement `Channel` over the Docker SDK: `exec` via `container.exec_run`, file push/pull via `put_archive`/`get_archive`, `heartbeat` via container status.

**Tests:** `test_docker_exec_returns_stdout_and_exit_code`, `test_docker_heartbeat_false_when_stopped`. Gate on a `docker_available` fixture; skip in CI when Docker absent.

---

## Task 07-09: Linux adapter local_provision

**Files:** `apps/api/app/adapters/linux/local_provision.py` (new); edit `adapters/linux/adapter.py`.

`provision` for `location=local`: pull/create a labeled container from the template image, start it, store the container id in `provider_ids_json`. `terminate` stops and removes it (idempotent). Existing EC2 path is untouched and selected when `location=cloud`.

**Tests:** `test_local_linux_provision_creates_labeled_container`, `test_local_linux_terminate_is_idempotent`.

**Do not:** alter the cloud EC2 provisioning path.

---

## Task 07-10: Conformance against local Linux

**Files:** edit the Phase 06 conformance suite to parametrize over `location`.

Run the **existing** adapter conformance suite against a `location=local` Linux device and prove it passes identically to cloud — the contract is transport-agnostic.

**Tests:** the full conformance suite, parametrized `[cloud, local]` for Linux.

**Do not:** fork the conformance suite — parametrize it.

---

## Tasks 07-11 .. 07-17 (summaries)

- **07-11 Android local:** `ADBChannel` (direct adb, no SSM tunnel) + AVD spawn/boot; requires host virtualization, gated by 07-03 probe.
- **07-12 Windows local:** `SSHChannel` + QEMU/VirtualBox VM provisioner; documented as secondary to the cloud Windows path; arch-aware (no x86 Windows on Apple Silicon).
- **07-13 Apple-gated families:** macOS (UTM/VMware) + iOS Sim (Xcode) local provisioners that hard-refuse on `is_apple_hardware == False`.
- **07-14 Reconciliation:** on control-plane startup, reconcile DB `Device` rows against actual Docker/AVD/VM state; re-adopt or mark lost.
- **07-15 Local networking + proxy:** per-family CA-cert injection for `mitmproxy`, port allocation for `aiortc` streams, optional network conditioning — **blocked on OQ-012**.
- **07-16 `devicelab doctor`:** local diagnostics — Docker daemon up? virtualization enabled? sufficient disk? port conflicts? — with actionable remedies.
- **07-17 Docs:** operator guide + per-family local host prerequisites; cross-link `docs/operations/os-licensing.md`.

---

## Exit criteria

- A user with **no AWS account** can create, observe, interact with, record, and terminate a **local Linux** device entirely through the existing MCP surface.
- The adapter conformance suite passes identically for `location ∈ {cloud, local}` on Linux.
- Provisioning that would oversubscribe the host is refused at `preflight_blocked: insufficient_host_resources`.
- A control-plane restart reconciles local device state without leaking or losing resources.
- macOS/iOS Sim local are cleanly refused on non-Apple hosts with an actionable error.
- OQ-011 (architecture dimension) and OQ-012 (local proxy/CA injection) are resolved or explicitly deferred before Batch H ships.
