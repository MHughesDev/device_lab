---
doc_id: "27.1"
title: "DeviceAdapter SPI contract"
section: "Adapters"
status: "current"
updated: "2026-05-31"
---

# DeviceAdapter SPI Contract

This document is the authoritative specification for the `DeviceAdapter` SPI (Service Provider Interface). All device family adapters must conform to this contract.

---

## AdapterManifest fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `spi_version` | `str` | yes | Must be a member of `SUPPORTED_SPI_VERSIONS` (currently `{"1.0"}`) |
| `adapter_version` | `str` | yes | Semver string (e.g. `"1.0.0"`) for this adapter release |
| `family` | `str` | yes | One of: `"linux"`, `"browser"`, `"android"`, `"windows"`, `"macos"`, `"ios_sim"`, `"ios_real"`, or a custom string for third-party families |
| `display_name` | `str` | yes | Human-readable name shown in UI and MCP tool list |
| `capabilities` | `DeviceCapabilities` | yes | Declares what the adapter supports (see below) |
| `required_providers` | `list[str]` | yes | e.g. `["aws_ec2", "ssm"]` or `["local_playwright"]` |
| `supported_regions` | `list[str] \| None` | no | AWS regions this adapter can provision in; `None` means all |

---

## DeviceCapabilities fields and valid values

| Field | Type | Valid values |
|-------|------|-------------|
| `observe` | `list[str]` | `"ax_tree"`, `"ocr"`, `"screenshot"`, `"vlm"` |
| `interact` | `list[str]` | `"click"`, `"swipe"`, `"tap"`, `"type"`, `"key"`, `"scroll"`, `"fill_form"`, `"navigate"`, `"select_option"`, `"wait_for"`, `"read_content"`, `"raw_shell"` |
| `network` | `list[str]` | `"proxy"`, `"capture"`, `"inject"` |
| `streaming` | `bool` | `True` if WebRTC stream is available |
| `snapshot` | `bool` | `True` if device snapshot/clone is supported |
| `dangerous_actions` | `list[str]` | Subset of `interact` values that require dangerous mode |

---

## DeviceAdapter abstract methods

### `manifest(cls) -> AdapterManifest`
Class method. Returns the adapter's static manifest. Called once at registration time and repeatedly for capability queries. Must not have side effects.

### `async provision(device, template) -> dict`
Provision all cloud resources for the device. Returns a `provider_ids` dict (e.g. `{"instance_id": "i-xxx", "region": "us-east-1"}`).

**Contract:**
- Must tag every created resource with `DeviceLab:Workspace={workspace_id}` and `DeviceLab:Device={device_id}`.
- Must be idempotent on re-call after partial failure where possible.
- Must not store secrets; use `SecretRef` indirection for credentials.

### `async terminate(device) -> None`
Terminate all provider resources for the device.

**Contract:**
- Must be idempotent — calling on an already-terminated device must not raise.
- Must attempt termination of all resources even if some fail (log errors, don't abort early).

### `async observe(device, tier: str) -> ObservationEnvelope`
Return an `ObservationEnvelope` for the requested observation tier.

**Contract:**
- If `tier` is not in `manifest().capabilities.observe`, raise `CapabilityUnsupportedError(tier, family)`.
- Never raise `NotImplementedError`.

### `async act(device, action: str, params: dict) -> ActionResult`
Execute a semantic action.

**Contract:**
- If `action` is not in `manifest().capabilities.interact`, raise `CapabilityUnsupportedError(action, family)`.
- Never raise `NotImplementedError`.

---

## Optional methods (default raises CapabilityUnsupportedError)

| Method | When to override |
|--------|-----------------|
| `async snapshot(device)` | When `capabilities.snapshot == True` |
| `async stream_offer(device) -> str` | When `capabilities.streaming == True`; returns SDP offer string |
| `async capture_artifacts(device, run_id) -> list` | When adapter can produce artifacts (logs, traces) |
| `async cleanup_orphans(provider_ids, region)` | When adapter can identify and clean up leaked resources |

---

## CapabilityUnsupportedError

Raise `CapabilityUnsupportedError(capability: str, family: str)` when an optional method is called but not supported. The error message format is:

```
CAPABILITY_UNSUPPORTED: '{capability}' is not available for family '{family}'
```

**Never raise `NotImplementedError` or a silent no-op for unsupported capabilities.**

---

## SPI versioning

`SPI_VERSION = "1.0"` is the current version. `SUPPORTED_SPI_VERSIONS = {"1.0"}` is the set of versions the registry accepts.

When `AdapterRegistry.register()` is called, it checks `manifest().spi_version in SUPPORTED_SPI_VERSIONS` and raises `IncompatibleAdapterError` if the version is not recognized.

**Bumping the SPI version:** Only bump when a breaking change is made to the abstract method signatures or contract. Minor additions (new optional methods) do not require a version bump.

---

## Security expectations

- Adapters must tag all created resources with the DeviceLab workspace and device IDs.
- Adapters must not return secrets in `provider_ids` or any return value.
- `terminate()` must be idempotent.
- Actions listed in `dangerous_actions` will be blocked unless `settings.DANGEROUS_MODE = True`.
