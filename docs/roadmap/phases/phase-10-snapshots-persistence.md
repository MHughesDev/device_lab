---
doc_id: "25.3"
title: "Phase 10 — Device Manifests & Environment Registry"
section: "Roadmap"
status: "planned"
completion: "0%"
updated: "2026-06-01"
---

# Phase 10 — Device Manifests & Environment Registry

**Progress: 0%** `░░░░░░░░░░` — planned

## What this phase is (and is not)

**Clarified by user (2026-06-01):** A "snapshot / existing device" is **not a disk image** and not
a filesystem checkpoint. It is a **named, declarative manifest** — a structured specification of
everything a device needs to reach its target state: OS, packages, environment variables, apps,
startup commands, and configuration. No physical memory or disk is stored in the manifest itself;
it is a *map of requirements*, not a copy of a running machine.

"Create from existing" means: read the manifest → provision a fresh base device → apply the
manifest's installation steps during the `bootstrapping_agent` phase to produce a ready,
fully-configured device. It is closer to `docker build` / `devcontainer.json` / Ansible playbook
than to a VM snapshot.

**There is no "sleepy machine" state.** A device is either running (resources committed) or
terminated (resources released). The Phase 08 ResourceLedger applies only to running devices.

---

## Objective

Build the **DeviceManifest** model and the **Manifest Registry** so a user can:
1. **Capture** a manifest from a running device (introspect what's installed and configured).
2. **Browse** a named library of manifests (the "Existing" wizard branch).
3. **Create from manifest** — provision a fresh device that bootstraps itself to match the spec.
4. **Author / edit** manifests by hand or via the UI for known environments.
5. **Import / export** manifests as portable JSON so they can be shared or checked into source
   control.

---

## OSS / mechanisms

| Family | Introspection for "capture" | Bootstrap execution |
|--------|-----------------------------|---------------------|
| Linux (Docker) | `dpkg --get-selections`, `pip list`, `npm list -g`, `env`, `systemctl list-units` | `apt-get install`, `pip install`, `npm install`, shell commands via `DockerExecChannel` |
| Android (AVD) | `adb shell pm list packages -f`, `adb shell settings list` | `adb install`, `adb push` + shell commands |
| Windows (QEMU) | PowerShell `Get-Package`, `winget list`, registry snapshot | `winget install`, PowerShell install scripts via `SSHChannel` |
| macOS (`vz`) | `brew list`, `mas list`, `system_profiler`, `launchctl list` | `brew install`, `mas install`, shell cmds via `SSHChannel` |
| iOS-sim | `xcrun simctl listapps`, bundle identifiers | `xcrun simctl install` |

The `pypyr` recipe DSL (locked dep) is the bootstrap execution engine — the manifest's
`install_steps` are translated into a pypyr pipeline that runs during `bootstrapping_agent`.

---

## Task batches and dependencies

```
Batch A (model + registry — everything depends on this)
  10-01  DeviceManifest model + ManifestPublic/Create/Update schemas + migration
  10-02  ManifestRegistry service + list/get/rename/delete + REST routes
  10-03  Manifest spec format + validation (JSON Schema definition)

Batch B (capture from running device — depends on A)
  10-04  Manifest capture SPI hook on the adapter (capture_manifest)
  10-05  Linux manifest capture (dpkg/pip/npm/env introspection)
  10-06  Android manifest capture (adb pm + shell)
  10-07  Windows manifest capture (Get-Package/winget)
  10-08  Apple-gated: macOS (brew/mas) + iOS-sim (simctl listapps) capture

Batch C (create-from-manifest bootstrap — depends on A, B; wires into Phase 07/08 FSM)
  10-09  Manifest → pypyr pipeline translation
  10-10  Create-from-manifest provisioning path + bootstrap hook

Batch D (import / export + UI data)
  10-11  Export manifest as JSON (GET /manifests/{id}/export)
  10-12  Import manifest from JSON (POST /manifests/import)

Batch E (docs)
  10-13  Manifest spec reference + per-family capture caveats + usage guide
```

---

## Task 10-01: DeviceManifest model

**Files:** `apps/api/app/models.py` (new `DeviceManifest` table + `ManifestPublic`, `ManifestCreate`,
`ManifestUpdate`); Alembic migration.

```python
class DeviceManifest(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id", index=True)
    name: str | None = Field(default=None, max_length=120)      # tab title / picker label (D-6)
    family: str = Field(max_length=64)                           # linux|android|windows|macos|ios_sim
    location: str = Field(max_length=32, default="local")
    description: str | None = Field(default=None, max_length=1024)
    spec_json: str = Field(sa_column=Column(Text))              # the manifest payload (see 10-03)
    source_device_id: uuid.UUID | None = Field(default=None)    # set when captured from a device
    created_at: datetime = ...
    updated_at: datetime = ...
```

`ManifestPublic.title` → `name or f"{family} · {id8}"`.

**Tests:** `test_manifest_model_defaults`, `test_manifest_public_title_fallback`,
`test_migration_adds_device_manifest_table`.

**Do not:** store disk images, binary blobs, or resource allocations in this table — manifests are
pure text specifications.

---

## Task 10-02: ManifestRegistry service + routes

**Files:** `apps/api/app/services/manifest_registry.py` (new); `apps/api/app/api/routes/manifests.py`
(new).

CRUD: `list`, `get`, `create`, `update` (rename / edit spec), `delete`. `GET /api/v1/manifests?
family=&location=` powers the "Existing" snapshot picker in the wizard (11-05). `PATCH /manifests/
{id}` accepts `name` and/or `spec_json`.

**Tests:** `test_registry_lists_by_family`, `test_registry_rename`, `test_registry_delete_not_in_use`.

**Do not:** delete a manifest referenced by a live device's `source_manifest_id` — refuse with a
clear error (add `source_manifest_id` FK to `Device` in this task's migration).

---

## Task 10-03: Manifest spec format + validation

**Files:** `apps/api/app/services/manifest_spec.py` (new); JSON Schema at
`docs/design/manifest-spec.json`.

The `spec_json` payload is a structured object validated against a JSON Schema. Representative
fields (family-conditional):

```json
{
  "base_image": "ubuntu:24.04",
  "display_resolution": "1920x1080",
  "env_vars": {"NODE_ENV": "development"},
  "install_steps": [
    {"type": "apt", "packages": ["git", "curl", "python3"]},
    {"type": "pip", "packages": ["pytest", "requests"]},
    {"type": "shell", "command": "curl -fsSL https://deb.nodesource.com/setup_20.x | bash -"},
    {"type": "npm_global", "packages": ["pnpm"]},
    {"type": "adb_install", "apk_path": "/apks/myapp.apk"},
    {"type": "shell", "command": "echo 'ready'"}
  ],
  "startup_commands": ["Xvfb :0 &", "openbox &"],
  "metadata": {"app": "MyApp", "version": "2.3.1"}
}
```

`ManifestSpec.validate(spec_json, family)` raises `ManifestValidationError` with a field-level
message on schema violations.

**Tests:** `test_valid_spec_passes`, `test_unknown_install_type_raises`, `test_family_conditional_fields`.

**Do not:** execute specs here — validation only.

---

## Task 10-04: Manifest capture SPI hook

**Files:** `apps/api/app/adapters/spi.py` (edit `DeviceAdapter`).

Add optional method:
```python
async def capture_manifest(self, device: object) -> dict:
    """Introspect the running device and return a spec_json payload."""
    raise CapabilityUnsupportedError("capture_manifest", self.manifest().family)
```
Declare `manifest_capture: bool` capability per family. Post-action: callers create a `DeviceManifest`
row via `ManifestRegistry.create` with `source_device_id` set.

**Tests:** `test_adapter_without_capture_raises`, `test_manifest_declared_in_capabilities`.

---

## Task 10-05: Linux manifest capture

**Files:** `apps/api/app/adapters/linux/manifest.py` (new); wire into `linux/adapter.py`.

Run a parallel set of `DockerExecChannel.exec` calls to collect:
- `dpkg --get-selections | grep install` (apt packages)
- `pip3 list --format=json` (if Python present)
- `npm list -g --json --depth=0` (if npm present)
- `printenv` (env vars — redact obvious secrets)
- `systemctl list-units --state=enabled --type=service --no-pager` (enabled services)

Assemble into `spec_json` with `install_steps` for each category. Best-effort — unknown or missing
tools produce a warning in `metadata.capture_warnings`.

**Tests:** `test_linux_capture_produces_apt_steps`, `test_linux_capture_redacts_secret_env_vars`,
`test_linux_capture_handles_missing_pip` (Docker-gated).

**Do not:** include the running process list or ephemeral state — only durable installation facts.

---

## Task 10-06: Android manifest capture

**Files:** `apps/api/app/adapters/android/manifest.py` (new).

`adb shell pm list packages -f` → installed APKs + package names → `adb_install` steps (paths
stored as references — not bundled in the manifest). `adb shell settings list global/secure` for
key device settings. System packages excluded by default (flag to include them).

**Tests:** `test_android_capture_lists_user_packages`, `test_android_capture_excludes_system_packages`.

---

## Task 10-07: Windows manifest capture

**Files:** `apps/api/app/adapters/windows/manifest.py` (new).

PowerShell via `SSHChannel`: `Get-Package | Select Name,Version | ConvertTo-Json` and
`winget list --output json`. Assembles `winget_install` and `msi_install` steps.

**Tests:** `test_windows_capture_produces_winget_steps`, `test_windows_capture_handles_no_winget`.

---

## Task 10-08: Apple-gated captures (macOS + iOS-sim)

**Files:** `apps/api/app/adapters/macos/manifest.py`, `apps/api/app/adapters/ios_sim/manifest.py`
(new). Hard-refused on non-Apple hardware.

macOS: `brew list --json=v2`, `mas list`. iOS-sim: `xcrun simctl listapps {udid}` → bundle IDs →
`xcrun simctl install` steps.

**Tests:** `test_macos_capture_refused_on_non_apple`, `test_ios_sim_capture_lists_installed_apps`.

---

## Task 10-09: Manifest → pypyr pipeline translation

**Files:** `apps/api/app/services/manifest_bootstrap.py` (new).

`ManifestBootstrap.to_pypyr_pipeline(spec, family) -> str` — converts the manifest's `install_steps`
into a pypyr YAML pipeline that runs during `bootstrapping_agent`. The pipeline uses the per-step
`type` to select the appropriate pypyr step module:

| Step type | pypyr step module |
|-----------|------------------|
| `apt` | `devicelab.steps.apt_install` |
| `pip` | `devicelab.steps.pip_install` |
| `shell` | `pypyr.steps.cmd` |
| `npm_global` | `devicelab.steps.npm_global_install` |
| `adb_install` | `devicelab.steps.adb_install` |
| `winget_install` | `devicelab.steps.winget_install` |
| `brew` | `devicelab.steps.brew_install` |
| `xcrun_install` | `devicelab.steps.simctl_install` |

Each pypyr step module is a small adapter that wraps the appropriate channel command.

**Tests:** `test_apt_steps_translate_to_pypyr`, `test_shell_steps_use_pypyr_cmd`,
`test_unknown_step_type_raises_translation_error`.

**Do not:** run the pipeline here — translation only; execution is Phase 07's FSM `bootstrapping_agent`
hook.

---

## Task 10-10: Create-from-manifest provisioning path

**Files:** edit device-create service; `DeviceCreate` gains `manifest_id: uuid.UUID | None`; edit
FSM `bootstrapping_agent` hook.

When `manifest_id` is set (the "Existing" wizard branch):
1. Inherit `family`/`location` from the manifest.
2. Provision a **fresh base device** (same as a "New" device with no manifest).
3. During `bootstrapping_agent`, translate the manifest → pypyr pipeline (10-09) and execute it.
4. Set `device.source_manifest_id = manifest_id`.
5. The device's `name` defaults to the manifest's `name` unless the user supplied one.

Resource reservation uses the template defaults (the manifest carries no resource claims — the
ledger reserves from the template's resource spec, Phase 08).

**Tests:** `test_create_from_manifest_runs_bootstrap_pipeline`,
`test_create_from_manifest_inherits_name`, `test_create_from_manifest_uses_template_ledger_claim`.

**Do not:** re-use disk state from a prior device — always provision fresh from the base image.

---

## Task 10-11: Export manifest as JSON

**Files:** `apps/api/app/api/routes/manifests.py` (extend).

`GET /api/v1/manifests/{id}/export` → returns the manifest as a standalone JSON document including
`name`, `family`, `spec_json`, and `metadata`. Suitable for checking into source control or sharing.

**Tests:** `test_export_returns_standalone_json`, `test_export_includes_name_and_family`.

---

## Task 10-12: Import manifest from JSON

**Files:** `apps/api/app/api/routes/manifests.py` (extend).

`POST /api/v1/manifests/import` — accepts a JSON body in the export format, validates via
`ManifestSpec.validate`, and creates a `DeviceManifest` row. Duplicate name → warn and suffix;
invalid spec → 422 with field-level errors.

**Tests:** `test_import_creates_manifest_row`, `test_import_rejects_invalid_spec`,
`test_import_handles_duplicate_name`.

---

## Task 10-13: Docs

**Files:** `docs/design/manifest-spec.json` (JSON Schema), `docs/operations/device-manifests.md`
(new).

Document: the manifest spec format with examples per family; how to capture from a running device;
how to hand-author a manifest; how to import/export for sharing; the bootstrap execution flow
(manifest → pypyr → bootstrapping_agent → ready); per-family capture caveats and what is/is not
captured.

---

## Exit criteria

- A user can **capture a manifest** from a running local device (any family), see it in the manifest
  registry, **rename** it, and **Create-from-manifest** to get a fresh device bootstrapped to the
  same environment.
- Manifests are **importable/exportable** as portable JSON; invalid specs are refused at 422 with
  field-level errors.
- Creating from a manifest reserves resources through the Phase 08 ledger; over-commit is refused.
- The manifest carries no disk images or binary state — it is a pure declarative text specification.
- All existing cloud `Snapshot` rows and Phase 05 behavior are unbroken (the `Snapshot` model is
  not modified; `DeviceManifest` is a new, separate model).
