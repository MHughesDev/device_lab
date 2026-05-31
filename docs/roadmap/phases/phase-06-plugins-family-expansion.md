---
doc_id: "24.7"
title: "Phase 06 — Adapter SPI + family expansion"
section: "Roadmap"
status: "planned"
completion: "0%"
updated: "2026-05-31"
---

# Phase 06 — Adapter SPI + Family Expansion

**Progress: 0%** `░░░░░░░░░░` — not started

## Objective

Turn DeviceLab from two working vertical slices (Linux, browser) into a durable multi-family platform. Stabilize the versioned adapter SPI so new device families can be added without touching the core. Add Android, Windows, macOS, iOS Simulator, and real iOS through clean adapter boundaries. Publish enough documentation that a third-party adapter can be built against the contract.

---

## OSS pulled in this phase

| Repo / package | What we take | Where it lands |
|----------------|-------------|----------------|
| `uiautomator2` (`pip install uiautomator2`) | Android AX tree dump + element interaction (full integration) | `apps/api/app/adapters/android/observation.py`, `interaction.py` |
| `appium/appium-uiautomator2-driver` (reference) | `lib/commands/` — reference for Android action shapes, element resolution, wait conditions | Patterns ported, no code copied |
| `viralmind-ai/accessibility-tree-parsers` (already in) | `windows_ax.py`, `macos_ax.py` for Windows UIA + macOS AX | `apps/api/app/adapters/ax/` (already copied phase 03) |
| `aiortc` (already in) | Extend stream peer for Android touch input channel | `apps/api/app/adapters/android/stream.py` |
| `mitmproxy` (already in) | Android network capture (requires emulator CA cert install via adb) | `apps/api/app/adapters/android/proxy.py` |

---

## Implementation tasks

### 1. Adapter SPI package

Files: `apps/api/app/adapters/spi.py`

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

SPI_VERSION = "1.0"

@dataclass
class AdapterManifest:
    spi_version: str
    adapter_version: str
    family: str                         # "linux" | "browser" | "android" | ...
    display_name: str
    capabilities: DeviceCapabilities    # from phase 03 schema
    required_providers: list[str]       # ["aws_ec2", "ssm"] or ["local_playwright"]
    supported_regions: list[str] | None # None = all regions

class DeviceAdapter(ABC):
    @classmethod
    @abstractmethod
    def manifest(cls) -> AdapterManifest: ...

    @abstractmethod
    async def provision(self, device: Device, template: DeviceTemplate) -> ProviderIds: ...

    @abstractmethod
    async def terminate(self, device: Device) -> None: ...

    @abstractmethod
    async def observe(self, device: Device, tier: ObservationTier) -> ObservationEnvelope: ...

    @abstractmethod
    async def act(self, device: Device, action: Action) -> ActionResult: ...

    # Optional — adapters declare support via capabilities
    async def snapshot(self, device: Device) -> Snapshot: raise CapabilityUnsupportedError
    async def stream_offer(self, device: Device) -> StreamOffer: raise CapabilityUnsupportedError
    async def capture_artifacts(self, device: Device, run_id: str) -> list[Artifact]: ...
    async def cleanup_orphans(self, provider_ids: list[str]) -> None: ...
```

Version negotiation: adapter declares `spi_version`; registry rejects `spi_version` it does not understand with a clear error listing the supported versions.

### 2. Adapter registry + loader

Files: `apps/api/app/adapters/registry.py`

```python
class AdapterRegistry:
    _adapters: dict[str, type[DeviceAdapter]] = {}

    def register(cls, adapter_class: type[DeviceAdapter]) -> None:
        manifest = adapter_class.manifest()
        if manifest.spi_version not in SUPPORTED_SPI_VERSIONS:
            raise IncompatibleAdapterError(...)
        if manifest.family in cls._adapters:
            raise DuplicateAdapterError(...)
        cls._adapters[manifest.family] = adapter_class

    def get(cls, family: str) -> type[DeviceAdapter]: ...
    def list_manifests(cls) -> list[AdapterManifest]: ...
```

Built-in adapters are registered at app startup. Extension point for local adapter packages: scan `DEVICELAB_ADAPTER_PATH` env var for importable Python packages with a `devicelab_adapter` entry point. Reject any adapter that fails SPI version check or duplicates a built-in family.

### 3. Refactor Linux + browser through SPI

Files: `apps/api/app/adapters/linux/adapter.py` (refactor), `apps/api/app/adapters/browser/adapter.py` (refactor)

Move all Linux and browser adapter code behind the `DeviceAdapter` ABC. No hardcoded family checks in core services — all family-specific behavior goes through `registry.get(device.family)`.

After refactor: adding a new family requires only writing one `DeviceAdapter` subclass and registering it. No changes to device lifecycle service, MCP gateway, or cost guardrail.

### 4. Conformance test suite

Files: `apps/api/tests/adapters/conformance/`

Every adapter (built-in and external) must pass:
```
test_manifest_valid              — spi_version, family, capabilities are well-formed
test_provision_returns_ids       — returns non-empty ProviderIds
test_terminate_cleans_up         — no tagged resources remain after terminate
test_observe_returns_envelope    — envelope has screen_version, tier, structured data
test_act_returns_result          — ActionResult has before/after versions + evidence_id
test_cost_tags_present           — every provisioned resource has DeviceLab: tags
test_capability_unsupported_raises — optional methods raise CapabilityUnsupportedError
test_cleanup_no_leaks            — fake provider shows no leaked resources
```

Tests use fake provider backends — no real AWS calls. Each adapter ships a `FakeProvider` that the conformance suite injects.

### 5. Android adapter

Files: `apps/api/app/adapters/android/adapter.py`, `observation.py`, `interaction.py`, `stream.py`

**Provisioning:**
- Android Emulator on EC2 with nested virt (C8i/M8i instances per S008)
- EC2 provision via Linux adapter → install AOSP emulator image via SSM → boot emulator → wait for `adb devices` to show device

**AX observation** (`observation.py`):
- `uiautomator2` connects to emulator via ADB (`u2.connect('emulator-5554')`)
- `device.dump_hierarchy()` returns XML → parse into `ObservationEnvelope`
- Port the element resolution logic from `appium-uiautomator2-driver/lib/commands/find.js` — how it resolves xpath, resource-id, content-desc, and class+text compound selectors

**Interaction** (`interaction.py`):
- `uiautomator2`: `device.click()`, `device.swipe()`, `device.send_keys()`, `device.press()`, `device.xpath().click()`
- Port wait condition patterns from `appium-uiautomator2-driver/lib/commands/wait.js`

**Stream** (`stream.py`):
- `adb exec-out screenrecord --output-format=h264 -` piped into aiortc `VideoStreamTrack`
- Touch input data channel → forward as `adb shell input tap/swipe/key` commands

**Network proxy**:
- Install mitmproxy CA cert via `adb push` + `adb shell` (per S037 mitmproxy Android docs)
- Proxy runs on control machine; emulator routes through it via `adb reverse`

Capability declaration:
```python
DeviceCapabilities(
    observe=["ax_tree", "screenshot"],
    interact=["click", "swipe", "type", "key", "scroll"],
    network=["proxy", "capture"],
    streaming=True,
    snapshot=False,           # AVD snapshots are local only, not cloud
)
```

### 6. Windows adapter

Files: `apps/api/app/adapters/windows/adapter.py`, `observation.py`, `interaction.py`

**Provisioning:** EC2 Windows Server 2022 AMI → SSM Run Command (PowerShell) → install Python runtime agent → enable accessibility permissions.

**AX observation**: use `windows_ax.py` from `viralmind-ai` (already in `adapters/ax/`). This uses the Windows UIA COM interface — works for Win32 apps, WPF apps, and modern UWP apps with accessibility enabled. Feed output into `ObservationEnvelope`.

**Interaction**: use `pywinauto` under the hood (the `viralmind` script already handles this). For browser interactions on Windows, fall back to browser adapter.

**Stream**: RDP via `freerdp` or use the existing aiortc-based stream from the Linux adapter — Windows supports H.264 screen capture via `ffmpeg` with `gdigrab`.

### 7. macOS + iOS Simulator adapter

Files: `apps/api/app/adapters/macos/adapter.py`, `apps/api/app/adapters/ios_sim/adapter.py`

**Provisioning (macOS):**
- EC2 Mac Dedicated Host (mac2.metal) — 24-hour minimum allocation per S003
- SSM bootstrap with macOS agent install (per S010)
- Grant accessibility permissions via `tccutil` (requires SIP consideration)

**AX observation (macOS)**: use `macos_ax.py` from `viralmind-ai` — AppleScript/AXUIElement extraction.

**iOS Simulator:**
- Inherits macOS host provisioning
- `xcrun simctl boot {udid}` → wait for boot → `xcrun simctl launch {udid} {bundle_id}`
- AX observation: `xcrun simctl accessibility` or private XPC — use `ios-sim` pattern
- Snapshot: `xcrun simctl clone` for cloning running simulators

Capability declaration for iOS Simulator explicitly notes: `snapshot: true` (xcrun clone), `streaming: true` (via QuickTime/ffmpeg grab from the macOS host).

### 8. Real iOS adapter

Files: `apps/api/app/adapters/ios_real/adapter.py`

Two paths:
1. **AWS Device Farm** (default) — `boto3` Device Farm API: `create_remote_access_session`, `get_remote_access_session`, `stop_remote_access_session`. Observation via screenshot API; AX not available without Appium.
2. **Local BYOC** (advanced) — `pymobiledevice3` for USB-connected physical devices with `devicemuxerd` proxy.

Capability declaration:
```python
DeviceCapabilities(
    observe=["screenshot"],    # AX requires Appium layer on top
    interact=["tap", "swipe"],
    streaming=True,
    snapshot=False,
    network=["capture"],       # Device Farm provides network log
)
```

Real iOS is the highest-constraint family. Unsupported capabilities return `CAPABILITY_UNSUPPORTED` with a `details` field explaining the constraint (e.g., "AX tree requires Appium integration — see docs/adapters/ios-appium.md").

### 9. Adapter author documentation

Files: `docs/adapters/spi-contract.md`, `docs/adapters/building-an-adapter.md`, `docs/adapters/fake-provider.md`

Document:
- `DeviceAdapter` required and optional methods
- `AdapterManifest` fields and version negotiation
- `DeviceCapabilities` fields and what each enables in MCP/UI
- Conformance test fixture setup
- `FakeProvider` interface for test isolation
- Security expectations: what adapters must not do (no plaintext secrets, no unbounded resource creation, always tag resources)
- Entry point registration for third-party packages

---

## Family sequencing rationale

| Order | Family | Why |
|-------|--------|-----|
| 1 | Linux | Baseline adapter; proves SSM + EC2 + runtime agent lifecycle |
| 2 | Browser | Proves semantic automation is not just VM management |
| 3 | Android | First mobile family; validates uiautomator2 + ADB observation stack |
| 4 | Windows | Validates UIA + Windows bootstrap; heavier VM lifecycle |
| 5 | macOS | Validates Apple host constraints + dedicated host billing model |
| 6 | iOS Simulator | Shares macOS host; adds simulator-specific lifecycle |
| 7 | Real iOS | Highest constraint + provider complexity; Device Farm BYOC path |

---

## Exit criteria

- Linux and browser adapters run through `DeviceAdapter` SPI — no hardcoded family checks in core.
- All built-in adapters pass the conformance test suite with fake providers.
- Android adapter reaches `ready` state for an emulator and returns an AX tree observation.
- MCP manifest changes automatically when adapter capabilities change — verified by test.
- Unsupported capabilities return typed `CAPABILITY_UNSUPPORTED` errors, never silent no-ops.
- At least one adapter docs file exists that a third-party author can follow to build a new adapter.
