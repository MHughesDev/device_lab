---
doc_id: "24.7"
title: "Phase 06 — Adapter SPI + family expansion"
section: "Roadmap"
status: "planned"
completion: "0%"
updated: "2026-05-31"
---

# Phase 06 — Adapter SPI + Family Expansion

**Progress: 100%** `██████████` — complete

## Objective

Turn DeviceLab from two working vertical slices (Linux, browser) into a durable multi-family platform. Stabilize the versioned adapter SPI so new device families can be added without touching the core. Add Android, Windows, macOS, iOS Simulator, and real iOS through clean adapter boundaries. Publish enough documentation that a third-party adapter can be built against the contract.

---

## OSS pulled in this phase

| Package / source | What we take | Where it lands |
|-----------------|-------------|----------------|
| `uiautomator2` (add to pyproject.toml) | AX tree dump + element interaction for Android | `adapters/android/observation.py`, `adapters/android/interaction.py` |
| `appium/appium-uiautomator2-driver` (reference only) | `lib/commands/` — element resolution, wait conditions, action shapes | Port patterns; do not copy code |
| `viralmind-ai/accessibility-tree-parsers` (already in `adapters/ax/`) | `windows_ax.py`, `macos_ax.py` for Windows UIA + macOS AX | Already present; wire into new adapters |
| `aiortc` (already in) | Extend stream peer for Android touch input channel | `adapters/android/stream.py` |
| `mitmproxy` (already in from phase 05) | Android network capture via emulator CA cert | `adapters/android/proxy.py` |

Add to `apps/api/pyproject.toml`: `"uiautomator2>=2.0.0"`.

---

## Task batches and dependencies

```
Batch A (SPI contract — everything depends on this)
  06-01  DeviceAdapter SPI abstract base + AdapterManifest + DeviceCapabilities
  06-02  AdapterRegistry

Batch B (refactor existing adapters — depends on A)
  06-03  Refactor Linux adapter through DeviceAdapter SPI
  06-04  Refactor Browser adapter through DeviceAdapter SPI

Batch C (conformance test suite — depends on A; write before new families)
  06-05  Conformance test fixtures and test suite
         (run against Linux + Browser adapters to prove they pass before adding more)

Batch D (Android — depends on A, B, C; tasks within D are sequential)
  06-06  Android adapter — provisioning (EC2 + AOSP emulator boot)
  06-07  Android adapter — AX observation (uiautomator2 + element resolution)
  06-08  Android adapter — interaction (click, swipe, type, key, scroll)
  06-09  Android adapter — streaming (adb screenrecord → aiortc) + network proxy

Batch E (Windows — depends on A, B, C; parallel with D)
  06-10  Windows adapter — provisioning + AX observation + interaction

Batch F (macOS + iOS Sim — depends on A, B, C; parallel with D and E)
  06-11  macOS adapter — provisioning + AX observation (macos_ax.py)
  06-12  iOS Simulator adapter — lifecycle + observation (inherits macOS host)

Batch G (real iOS — depends on A, B, C; highest constraint, last)
  06-13  Real iOS adapter — AWS Device Farm path + capability declaration

Batch H (docs — write last, reflects final SPI shape)
  06-14  Adapter author documentation
```

---

## Task 06-01: DeviceAdapter SPI abstract base

**Files:** `apps/api/app/adapters/spi.py` (new)

```python
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Literal

SPI_VERSION = "1.0"
SUPPORTED_SPI_VERSIONS = {"1.0"}


@dataclass
class DeviceCapabilities:
    observe: list[str] = field(default_factory=list)
    # valid values: "ax_tree", "ocr", "screenshot", "vlm"
    interact: list[str] = field(default_factory=list)
    # valid values: "click", "swipe", "type", "key", "scroll", "fill_form",
    #               "navigate", "select_option", "wait_for", "read_content"
    network: list[str] = field(default_factory=list)
    # valid values: "proxy", "capture", "inject"
    streaming: bool = False
    snapshot: bool = False
    dangerous_actions: list[str] = field(default_factory=list)
    # valid values: "raw_shell", "file_delete", "process_kill"


@dataclass
class AdapterManifest:
    spi_version: str               # must be in SUPPORTED_SPI_VERSIONS
    adapter_version: str           # semver string, e.g. "1.0.0"
    family: str                    # "linux" | "browser" | "android" | "windows" | "macos" | "ios_sim" | "ios_real"
    display_name: str
    capabilities: DeviceCapabilities
    required_providers: list[str]  # e.g. ["aws_ec2", "ssm"] or ["local_playwright"]
    supported_regions: list[str] | None = None   # None means all regions


class CapabilityUnsupportedError(Exception):
    """Raised when an optional adapter method is called but not supported."""
    def __init__(self, capability: str, family: str):
        self.capability = capability
        self.family = family
        super().__init__(
            f"CAPABILITY_UNSUPPORTED: '{capability}' is not available for family '{family}'"
        )


class IncompatibleAdapterError(Exception):
    """Raised when an adapter declares an unsupported SPI version."""


class DeviceAdapter(ABC):
    """
    Abstract base for all device family adapters.

    Required methods must be implemented by every adapter.
    Optional methods raise CapabilityUnsupportedError by default;
    adapters that support the capability override them.
    """

    @classmethod
    @abstractmethod
    def manifest(cls) -> AdapterManifest: ...

    @abstractmethod
    async def provision(self, device: object, template: object) -> dict:
        """
        Provision cloud resources. Returns provider_ids dict
        (e.g. {"instance_id": "i-xxx", "region": "us-east-1"}).
        Must tag all resources with DeviceLab:Workspace and DeviceLab:Device.
        """
        ...

    @abstractmethod
    async def terminate(self, device: object) -> None:
        """Terminate all provider resources. Must be idempotent."""
        ...

    @abstractmethod
    async def observe(self, device: object, tier: str) -> object:
        """
        Return an ObservationEnvelope for the device.
        tier: "ax" | "ocr" | "screenshot" | "vlm"
        Raise CapabilityUnsupportedError for tiers not in manifest.capabilities.observe.
        """
        ...

    @abstractmethod
    async def act(self, device: object, action: str, params: dict) -> object:
        """
        Execute a semantic action. Returns ActionResult.
        Raise CapabilityUnsupportedError for actions not in manifest.capabilities.interact.
        """
        ...

    # --- Optional methods (default: raise CapabilityUnsupportedError) ---

    async def snapshot(self, device: object) -> object:
        raise CapabilityUnsupportedError("snapshot", self.manifest().family)

    async def stream_offer(self, device: object) -> str:
        """Return SDP offer string for WebRTC stream negotiation."""
        raise CapabilityUnsupportedError("streaming", self.manifest().family)

    async def capture_artifacts(self, device: object, run_id: str) -> list[object]:
        return []

    async def cleanup_orphans(self, provider_ids: list[str], region: str) -> None:
        pass
```

**Tests (`tests/adapters/test_spi.py` — new):**
| Test | Asserts |
|------|---------|
| `test_manifest_dataclass_fields` | AdapterManifest can be constructed with required fields |
| `test_capabilities_defaults` | DeviceCapabilities fields default to empty lists / False |
| `test_capability_unsupported_error_message` | error message includes capability and family name |
| `test_supported_spi_versions_contains_current` | SPI_VERSION in SUPPORTED_SPI_VERSIONS |

---

## Task 06-02: AdapterRegistry

**Files:** `apps/api/app/adapters/registry.py` (new)

```python
from __future__ import annotations
from app.adapters.spi import AdapterManifest, DeviceAdapter, IncompatibleAdapterError, SUPPORTED_SPI_VERSIONS


class DuplicateAdapterError(Exception): ...


class AdapterRegistry:
    _adapters: dict[str, type[DeviceAdapter]] = {}

    @classmethod
    def register(cls, adapter_class: type[DeviceAdapter]) -> None:
        """
        Register an adapter class. Raises IncompatibleAdapterError if spi_version
        is not supported. Raises DuplicateAdapterError if family already registered.
        """
        manifest = adapter_class.manifest()
        if manifest.spi_version not in SUPPORTED_SPI_VERSIONS:
            raise IncompatibleAdapterError(
                f"Adapter '{manifest.family}' declares spi_version='{manifest.spi_version}'; "
                f"supported: {sorted(SUPPORTED_SPI_VERSIONS)}"
            )
        if manifest.family in cls._adapters:
            raise DuplicateAdapterError(
                f"Adapter for family '{manifest.family}' is already registered"
            )
        cls._adapters[manifest.family] = adapter_class

    @classmethod
    def get(cls, family: str) -> type[DeviceAdapter]:
        """Return adapter class for family. Raises KeyError if not registered."""
        if family not in cls._adapters:
            raise KeyError(f"No adapter registered for family '{family}'")
        return cls._adapters[family]

    @classmethod
    def list_manifests(cls) -> list[AdapterManifest]:
        return [a.manifest() for a in cls._adapters.values()]

    @classmethod
    def reset(cls) -> None:
        """Clear all registrations. Use in tests only."""
        cls._adapters = {}
```

**Startup wiring:** In `apps/api/app/main.py`, after app is created, add a startup event that calls:
```python
from app.adapters.registry import AdapterRegistry
from app.adapters.linux.adapter import LinuxAdapter
from app.adapters.browser.adapter import BrowserAdapter

@app.on_event("startup")
async def register_adapters():
    AdapterRegistry.reset()
    AdapterRegistry.register(LinuxAdapter)
    AdapterRegistry.register(BrowserAdapter)
```

**Tests (`tests/adapters/test_registry.py` — new):**
| Test | Asserts |
|------|---------|
| `test_register_and_get` | registered adapter returned by get() |
| `test_get_unknown_raises_keyerror` | KeyError for unregistered family |
| `test_duplicate_raises` | DuplicateAdapterError on second register of same family |
| `test_incompatible_version_raises` | IncompatibleAdapterError for unknown spi_version |
| `test_list_manifests_returns_all` | list_manifests() length equals registered count |
| `test_reset_clears_registry` | after reset(), get() raises KeyError |

---

## Task 06-03: Refactor Linux adapter through SPI

**Files:** `apps/api/app/adapters/linux/adapter.py` (modify)

Make `LinuxAdapter` extend `DeviceAdapter`. Keep all existing logic; wrap it behind the ABC methods.

```python
from app.adapters.spi import (
    AdapterManifest, DeviceAdapter, DeviceCapabilities, SPI_VERSION
)

class LinuxAdapter(DeviceAdapter):
    @classmethod
    def manifest(cls) -> AdapterManifest:
        return AdapterManifest(
            spi_version=SPI_VERSION,
            adapter_version="1.0.0",
            family="linux",
            display_name="Linux (EC2 + SSM)",
            capabilities=DeviceCapabilities(
                observe=["ax_tree", "screenshot"],
                interact=["click", "type", "key", "scroll", "raw_shell"],
                network=["proxy", "capture"],
                streaming=True,
                snapshot=True,
                dangerous_actions=["raw_shell"],
            ),
            required_providers=["aws_ec2", "ssm"],
        )

    async def provision(self, device, template) -> dict: ...   # wrap existing launch_instance
    async def terminate(self, device) -> None: ...             # wrap existing terminate_instance
    async def observe(self, device, tier) -> object: ...       # delegate to observation service
    async def act(self, device, action, params) -> object: ... # delegate to interaction service
    async def snapshot(self, device) -> object: ...            # delegate to linux/snapshots.py
```

**Constraint:** No new logic — only wrapping. All existing function calls inside the adapter methods should be calls to existing service functions. Core services (`device_fsm.py`, `mcp/gateway.py`) must not contain the string `"linux"` as a literal family check after this task; they must call `AdapterRegistry.get(device.family)` instead.

**Tests (`tests/adapters/test_linux_adapter.py` — modify):**
Add to existing test file:
| Test | Asserts |
|------|---------|
| `test_manifest_spi_version` | manifest().spi_version == SPI_VERSION |
| `test_manifest_family` | manifest().family == "linux" |
| `test_manifest_snapshot_capable` | manifest().capabilities.snapshot == True |

---

## Task 06-04: Refactor Browser adapter through SPI

**Files:** `apps/api/app/adapters/browser/adapter.py` (modify)

Same pattern as Linux. Make `BrowserAdapter` extend `DeviceAdapter`.

```python
class BrowserAdapter(DeviceAdapter):
    @classmethod
    def manifest(cls) -> AdapterManifest:
        return AdapterManifest(
            spi_version=SPI_VERSION,
            adapter_version="1.0.0",
            family="browser",
            display_name="Browser (Playwright)",
            capabilities=DeviceCapabilities(
                observe=["ax_tree", "screenshot"],
                interact=["navigate", "click", "type", "fill_form",
                          "select_option", "scroll", "wait_for", "read_content"],
                network=[],
                streaming=False,
                snapshot=False,
            ),
            required_providers=["local_playwright"],
        )

    async def provision(self, device, template) -> dict: ...
    async def terminate(self, device) -> None: ...
    async def observe(self, device, tier) -> object: ...
    async def act(self, device, action, params) -> object: ...
    # snapshot() — not overridden; raises CapabilityUnsupportedError via base class
```

**Tests (`tests/adapters/test_browser_adapter.py` — modify):** Add same manifest tests as Linux.

---

## Task 06-05: Conformance test suite

**Files:** `apps/api/tests/adapters/conformance/` (new directory)
- `apps/api/tests/adapters/conformance/__init__.py` (empty)
- `apps/api/tests/adapters/conformance/fixtures.py` (fake provider helpers)
- `apps/api/tests/adapters/conformance/test_conformance.py` (parametrized tests)

**`fixtures.py`** — define `FakeDevice` and `FakeTemplate` dataclasses, and a `fake_boto_session()` factory that returns a mock satisfying `boto3.Session` interface.

**`test_conformance.py`** — use `@pytest.mark.parametrize("adapter_class", [LinuxAdapter, BrowserAdapter])` and run these tests for each:

| Test | Asserts |
|------|---------|
| `test_manifest_valid` | spi_version in SUPPORTED_SPI_VERSIONS; family is non-empty string; capabilities is DeviceCapabilities |
| `test_manifest_family_matches_register` | manifest().family == key used in AdapterRegistry |
| `test_observe_unsupported_tier_raises` | CapabilityUnsupportedError for tier not in capabilities.observe |
| `test_act_unsupported_action_raises` | CapabilityUnsupportedError for action not in capabilities.interact |
| `test_snapshot_unsupported_raises` | CapabilityUnsupportedError for adapters with snapshot=False |
| `test_capability_unsupported_error_type` | raised error is always CapabilityUnsupportedError, never NotImplementedError |

---

## Task 06-06: Android adapter — provisioning

**Files:**
- `apps/api/app/adapters/android/__init__.py` (new, empty)
- `apps/api/app/adapters/android/adapter.py` (new)

```python
from app.adapters.spi import AdapterManifest, DeviceAdapter, DeviceCapabilities, SPI_VERSION

class AndroidAdapter(DeviceAdapter):
    @classmethod
    def manifest(cls) -> AdapterManifest:
        return AdapterManifest(
            spi_version=SPI_VERSION,
            adapter_version="1.0.0",
            family="android",
            display_name="Android Emulator (EC2 nested virt)",
            capabilities=DeviceCapabilities(
                observe=["ax_tree", "screenshot"],
                interact=["click", "swipe", "type", "key", "scroll"],
                network=["proxy", "capture"],
                streaming=True,
                snapshot=False,   # AVD snapshots are local only
            ),
            required_providers=["aws_ec2", "ssm", "adb"],
            supported_regions=None,
        )

    async def provision(self, device, template) -> dict:
        """
        1. Launch EC2 with C8i or M8i instance (nested virt capable).
        2. SSM bootstrap: install AOSP emulator, start emulator process.
        3. Poll adb devices until emulator appears (timeout 5 min).
        4. Return {"instance_id": ..., "adb_serial": "emulator-5554", "region": ...}
        """
        ...

    async def terminate(self, device) -> None:
        """Stop emulator process via adb emu kill, then terminate EC2 instance."""
        ...

    async def observe(self, device, tier) -> object:
        """Delegate to android/observation.py."""
        from app.adapters.android.observation import observe_android
        return await observe_android(device, tier)

    async def act(self, device, action, params) -> object:
        """Delegate to android/interaction.py."""
        from app.adapters.android.interaction import act_android
        return await act_android(device, action, params)
```

**Provisioning detail for `provision()`:**
- Instance type: `c8i.xlarge` (default) — 4 vCPU, 8 GB, supports KVM nested virt
- AMI: Amazon Linux 2023 (resolved at runtime via `describe_images`)
- SSM bootstrap commands:
  ```
  yum install -y qemu-kvm android-tools
  wget -q https://dl.google.com/android/repository/commandlinetools-linux-...zip
  # unzip, accept licenses, install system-image
  avdmanager create avd -n devicelab -k "system-images;android-34;google_apis;x86_64"
  emulator -avd devicelab -no-window -no-audio &
  adb wait-for-device
  ```
- Tag all resources: `DeviceLab:Workspace`, `DeviceLab:Device`, `DeviceLab:Family=android`

---

## Task 06-07: Android adapter — AX observation

**Files:** `apps/api/app/adapters/android/observation.py` (new)

```python
from __future__ import annotations
import uuid
from datetime import UTC, datetime
from app.models import ObservationEnvelope


async def observe_android(device: object, tier: str) -> ObservationEnvelope:
    """
    tier="ax": connect via uiautomator2, dump XML hierarchy, parse into ObservationEnvelope.
    tier="screenshot": adb exec-out screencap -p → base64 PNG ref.
    Other tiers: raise CapabilityUnsupportedError.
    """
    ...


def _get_adb_serial(device: object) -> str:
    """Extract adb_serial from device.provider_ids_json."""
    import json
    ids = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
    return ids.get("adb_serial", "emulator-5554")


def _dump_ax_tree(adb_serial: str) -> dict:
    """
    Connect uiautomator2 to adb_serial, call device.dump_hierarchy(),
    parse XML into a structured dict matching ObservationEnvelope.structured format.

    Element resolution priority (ported from appium-uiautomator2-driver lib/commands/find.js):
    1. resource-id exact match
    2. content-desc (accessible name) contains match
    3. class + text compound
    4. xpath

    Returns dict: {"nodes": [...], "focused": str | None}
    """
    ...
```

**Tests (`tests/adapters/test_android_observation.py` — new):**
| Test | Asserts |
|------|---------|
| `test_get_adb_serial_from_provider_ids` | parses adb_serial from JSON string |
| `test_get_adb_serial_default` | returns "emulator-5554" when field missing |
| `test_observe_unsupported_tier_raises` | CapabilityUnsupportedError for tier="vlm" |
| `test_dump_ax_tree_structure` | returns dict with "nodes" key (mock uiautomator2) |

---

## Task 06-08: Android adapter — interaction

**Files:** `apps/api/app/adapters/android/interaction.py` (new)

```python
from __future__ import annotations
from app.adapters.spi import CapabilityUnsupportedError


SUPPORTED_ACTIONS = {"click", "swipe", "type", "key", "scroll"}


async def act_android(device: object, action: str, params: dict) -> dict:
    """
    Dispatch action to uiautomator2 device instance.
    Raises CapabilityUnsupportedError for actions not in SUPPORTED_ACTIONS.

    Action mappings (ported from appium-uiautomator2-driver lib/commands/):
      click  → d(resourceId=target).click() or d.click(x, y)
      swipe  → d.swipe(sx, sy, ex, ey, steps)
      type   → d(focused=True).set_text(text) or d(resourceId=target).set_text(text)
      key    → d.press(keycode)  (keycode: "home"|"back"|"enter"|int)
      scroll → d(scrollable=True).scroll(steps)
    """
    ...


def _resolve_element(d: object, target: str) -> object:
    """
    Resolve target string to uiautomator2 selector.
    Priority: resource-id → content-desc → text → xpath.
    """
    ...
```

**Tests (`tests/adapters/test_android_interaction.py` — new):**
| Test | Asserts |
|------|---------|
| `test_unsupported_action_raises` | CapabilityUnsupportedError for action="navigate" |
| `test_click_calls_u2_click` | uiautomator2 click() called with correct args (mock u2) |
| `test_type_calls_set_text` | set_text() called with text param |
| `test_key_calls_press` | press() called with keycode |

---

## Task 06-09: Android adapter — streaming + network proxy

**Files:**
- `apps/api/app/adapters/android/stream.py` (new)
- `apps/api/app/adapters/android/proxy.py` (new)

**`stream.py`:**
```python
from __future__ import annotations
import asyncio
import fractions
import subprocess

from aiortc.mediastreams import MediaStreamTrack  # type: ignore
from av import VideoFrame  # type: ignore


class AdbScreenTrack(MediaStreamTrack):
    """
    VideoStreamTrack that reads H.264 frames from
    `adb exec-out screenrecord --output-format=h264 -` subprocess.
    Pattern from aiortc/examples/server VideoTransformTrack.
    """
    kind = "video"

    def __init__(self, adb_serial: str):
        super().__init__()
        self.adb_serial = adb_serial
        self._proc: subprocess.Popen | None = None

    async def recv(self) -> VideoFrame:
        """Read next H.264 frame from adb subprocess pipe."""
        ...

    async def stop(self) -> None:
        if self._proc:
            self._proc.terminate()


async def create_android_stream_offer(device: object) -> str:
    """
    Start AdbScreenTrack for device, create aiortc RTCPeerConnection offer.
    Returns SDP offer string.
    """
    ...
```

**`proxy.py`:**
```python
from __future__ import annotations


async def install_mitmproxy_cert(adb_serial: str, cert_path: str) -> None:
    """
    Push mitmproxy CA cert to emulator system cert store.
    Commands:
      adb -s {serial} push {cert_path} /sdcard/mitmproxy-ca.cer
      adb -s {serial} shell am start -n com.android.settings/.Settings$SecuritySettingsActivity
    Requires API < 29 or rooted device for user cert install.
    """
    ...


async def setup_proxy_routing(adb_serial: str, proxy_host: str, proxy_port: int) -> None:
    """
    Route emulator traffic through mitmproxy via adb reverse:
      adb -s {serial} reverse tcp:{port} tcp:{port}
    Then set proxy via adb shell settings:
      adb -s {serial} shell settings put global http_proxy {host}:{port}
    """
    ...
```

---

## Task 06-10: Windows adapter

**Files:**
- `apps/api/app/adapters/windows/__init__.py` (new, empty)
- `apps/api/app/adapters/windows/adapter.py` (new)
- `apps/api/app/adapters/windows/observation.py` (new)
- `apps/api/app/adapters/windows/interaction.py` (new)

**`adapter.py`:**
```python
class WindowsAdapter(DeviceAdapter):
    @classmethod
    def manifest(cls) -> AdapterManifest:
        return AdapterManifest(
            spi_version=SPI_VERSION,
            adapter_version="1.0.0",
            family="windows",
            display_name="Windows Server (EC2 + SSM)",
            capabilities=DeviceCapabilities(
                observe=["ax_tree", "screenshot"],
                interact=["click", "type", "key", "scroll"],
                network=["proxy", "capture"],
                streaming=True,
                snapshot=True,
            ),
            required_providers=["aws_ec2", "ssm"],
        )

    async def provision(self, device, template) -> dict:
        """
        Launch EC2 Windows Server 2022 AMI.
        SSM bootstrap (PowerShell):
          - Install Python 3.12
          - Install runtime agent via pip
          - Enable UIA accessibility
        Poll SSM until agent reports ready.
        """
        ...

    async def terminate(self, device) -> None: ...

    async def observe(self, device, tier) -> object:
        """Delegate to windows/observation.py → windows_ax.py."""
        ...

    async def act(self, device, action, params) -> object:
        """Delegate to windows/interaction.py."""
        ...
```

**`observation.py`:**
```python
from __future__ import annotations
from app.adapters.ax.windows_ax import get_ax_tree   # already in adapters/ax/


async def observe_windows(device: object, tier: str) -> object:
    """
    tier="ax": run windows_ax.py script on device via SSM RunCommand,
               parse JSON output into ObservationEnvelope.
    tier="screenshot": SSM RunCommand → PowerShell screenshot → base64 PNG.
    """
    ...
```

**`interaction.py`:**
```python
SUPPORTED_ACTIONS = {"click", "type", "key", "scroll"}

async def act_windows(device: object, action: str, params: dict) -> dict:
    """
    Execute action via SSM RunCommand (PowerShell + pywinauto).
    Raises CapabilityUnsupportedError for unsupported actions.
    """
    ...
```

**Tests (`tests/adapters/test_windows_adapter.py` — new):**
| Test | Asserts |
|------|---------|
| `test_manifest_family` | manifest().family == "windows" |
| `test_manifest_snapshot_capable` | capabilities.snapshot == True |
| `test_unsupported_action_raises` | CapabilityUnsupportedError for action="navigate" |

---

## Task 06-11: macOS adapter

**Files:**
- `apps/api/app/adapters/macos/__init__.py` (new, empty)
- `apps/api/app/adapters/macos/adapter.py` (new)
- `apps/api/app/adapters/macos/observation.py` (new)

**`adapter.py`:**
```python
class MacOSAdapter(DeviceAdapter):
    @classmethod
    def manifest(cls) -> AdapterManifest:
        return AdapterManifest(
            spi_version=SPI_VERSION,
            adapter_version="1.0.0",
            family="macos",
            display_name="macOS (EC2 mac2.metal Dedicated Host)",
            capabilities=DeviceCapabilities(
                observe=["ax_tree", "screenshot"],
                interact=["click", "type", "key", "scroll"],
                network=["proxy", "capture"],
                streaming=True,
                snapshot=False,   # EBS snapshots not supported on mac1/mac2
            ),
            required_providers=["aws_ec2_dedicated_host", "ssm"],
        )

    async def provision(self, device, template) -> dict:
        """
        Allocate EC2 Dedicated Host (mac2.metal) — 24-hour minimum billing.
        Launch EC2 Mac instance on the host.
        SSM bootstrap: install runtime agent, grant accessibility via tccutil.
        Note: mac2.metal supports Apple Silicon; mac1.metal is Intel.
        """
        ...

    async def terminate(self, device) -> None:
        """
        Terminate instance. Note: Dedicated Host cannot be released for 24h after allocation.
        Log warning if host was allocated < 24h ago.
        """
        ...

    async def observe(self, device, tier) -> object:
        from app.adapters.macos.observation import observe_macos
        return await observe_macos(device, tier)

    async def act(self, device, action, params) -> object: ...
```

**`observation.py`:**
```python
from app.adapters.ax.macos_ax import get_ax_tree   # already in adapters/ax/

async def observe_macos(device: object, tier: str) -> object:
    """
    tier="ax": run macos_ax.py on device via SSM, parse JSON into ObservationEnvelope.
    tier="screenshot": screencapture -t png via SSM RunCommand.
    """
    ...
```

---

## Task 06-12: iOS Simulator adapter

**Files:**
- `apps/api/app/adapters/ios_sim/__init__.py` (new, empty)
- `apps/api/app/adapters/ios_sim/adapter.py` (new)

```python
class IOSSimulatorAdapter(DeviceAdapter):
    """
    Inherits the macOS Dedicated Host for provisioning.
    Adds simulator-specific lifecycle on top.
    """
    @classmethod
    def manifest(cls) -> AdapterManifest:
        return AdapterManifest(
            spi_version=SPI_VERSION,
            adapter_version="1.0.0",
            family="ios_sim",
            display_name="iOS Simulator (macOS EC2 + xcrun simctl)",
            capabilities=DeviceCapabilities(
                observe=["screenshot"],   # AX via simctl accessibility is limited
                interact=["tap", "swipe", "type", "key"],
                network=[],
                streaming=True,           # via QuickTime/ffmpeg grab from macOS host
                snapshot=True,            # xcrun simctl clone
            ),
            required_providers=["aws_ec2_dedicated_host", "ssm"],
        )

    async def provision(self, device, template) -> dict:
        """
        1. Provision macOS host (delegate to MacOSAdapter or share host).
        2. xcrun simctl create devicelab-sim "iPhone 15" "iOS17.0"
        3. xcrun simctl boot {udid}
        4. xcrun simctl launch {udid} {bundle_id if provided}
        Return {"instance_id": ..., "sim_udid": ..., "region": ...}
        """
        ...

    async def terminate(self, device) -> None:
        """xcrun simctl shutdown {udid} && xcrun simctl delete {udid}. Then terminate host."""
        ...

    async def observe(self, device, tier) -> object:
        """tier="screenshot": xcrun simctl io {udid} screenshot - | base64"""
        ...

    async def act(self, device, action, params) -> object:
        """xcrun simctl io {udid} sendkey / tap / swipe via SSM."""
        ...

    async def snapshot(self, device) -> object:
        """xcrun simctl clone {udid} devicelab-snap-{timestamp}"""
        ...
```

---

## Task 06-13: Real iOS adapter (AWS Device Farm)

**Files:**
- `apps/api/app/adapters/ios_real/__init__.py` (new, empty)
- `apps/api/app/adapters/ios_real/adapter.py` (new)

```python
class IOSRealAdapter(DeviceAdapter):
    @classmethod
    def manifest(cls) -> AdapterManifest:
        return AdapterManifest(
            spi_version=SPI_VERSION,
            adapter_version="1.0.0",
            family="ios_real",
            display_name="Real iOS (AWS Device Farm)",
            capabilities=DeviceCapabilities(
                observe=["screenshot"],
                # AX requires Appium layer — not in this phase
                interact=["tap", "swipe"],
                network=["capture"],   # Device Farm provides network log
                streaming=True,
                snapshot=False,
            ),
            required_providers=["aws_device_farm"],
        )

    async def provision(self, device, template) -> dict:
        """
        boto3 devicefarm client:
          create_remote_access_session(projectArn=..., deviceArn=..., name=...)
          Returns {"session_arn": ..., "device_farm_endpoint": ...}
        """
        ...

    async def terminate(self, device) -> None:
        """devicefarm.stop_remote_access_session(arn=session_arn)"""
        ...

    async def observe(self, device, tier) -> object:
        """
        tier="screenshot": devicefarm.get_device_pool_compatibility / screenshot API.
        Other tiers: raise CapabilityUnsupportedError with details field:
          "AX tree requires Appium integration — see docs/adapters/ios-appium.md"
        """
        ...

    async def act(self, device, action, params) -> object:
        """
        Only tap and swipe supported via Device Farm remote access API.
        Raise CapabilityUnsupportedError with guidance for unsupported actions.
        """
        ...
```

**Register in startup:** Add `IOSRealAdapter` to the `register_adapters()` startup handler in `main.py` alongside Linux, Browser, Android, Windows, macOS, and iOS Sim.

---

## Task 06-14: Adapter author documentation

**Files:**
- `docs/adapters/spi-contract.md` (new)
- `docs/adapters/building-an-adapter.md` (new)
- `docs/adapters/fake-provider.md` (new)

**`spi-contract.md`** must document:
- All fields of `AdapterManifest` and `DeviceCapabilities` with valid values
- All abstract methods of `DeviceAdapter` with exact signatures and contracts
- All optional methods with default behavior and when to override
- `CapabilityUnsupportedError` — when to raise it, what fields to set
- SPI versioning: how `spi_version` is checked; what bumping it means
- Security expectations: must tag all resources; must not store secrets; must be idempotent on terminate

**`building-an-adapter.md`** must document:
- Step-by-step: create class, implement manifest(), implement required methods, register
- How to write a `FakeProvider` for the conformance suite
- How to run `tests/adapters/conformance/test_conformance.py` against your adapter
- Entry point registration for third-party packages: `devicelab_adapter` entry point

**`fake-provider.md`** must document:
- The `FakeDevice` and `FakeTemplate` fixture dataclasses
- How to mock `boto3.Session` for AWS-backed adapters
- How to mock `adb` subprocess calls for Android adapters
- Example conformance test parametrize pattern

---

## Exit criteria

- Linux and Browser adapters pass all conformance tests with `FakeProvider` backends
- `AdapterRegistry.get("linux")` and `AdapterRegistry.get("browser")` work at startup
- No string literal `"linux"` or `"browser"` family checks exist in `device_fsm.py`, `mcp/gateway.py`, or `observation.py` — all go through `AdapterRegistry.get(device.family)`
- Android adapter reaches `ready` state for an emulator in test with mocked AWS + adb
- Android AX observation returns a non-empty `ObservationEnvelope.structured` dict
- MCP manifest changes automatically when adapter capabilities change — verified by adding a capability to `LinuxAdapter.manifest()` and asserting the manifest tool response changes
- All unsupported capabilities return `CapabilityUnsupportedError`, never `NotImplementedError` or silent no-ops
- At least `spi-contract.md` and `building-an-adapter.md` exist with the required sections
