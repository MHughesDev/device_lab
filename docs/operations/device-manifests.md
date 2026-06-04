---
doc_id: "ops-03"
title: "Device Manifests — Usage Guide"
section: "Operations"
updated: "2026-06-01"
---

# Device Manifests — Usage Guide

A **DeviceManifest** is a declarative text specification of everything a device needs to reach its
target state: OS, packages, environment variables, apps, and startup commands. It is a *map of
requirements*, not a disk image or a copy of a running machine.

**Key invariant:** Creating a device from a manifest always yields a **fresh, empty-data device**.
It reinstalls the software and re-applies config only — it does not restore databases, user files,
or any in-application state. See [What manifests do not capture](#what-manifests-do-not-capture).

---

## Manifest spec format

The `spec_json` field is a JSON object validated against `docs/design/manifest-spec.json`.
Representative fields:

```json
{
  "base_image": "ubuntu:24.04",
  "display_resolution": "1920x1080",
  "env_vars": { "NODE_ENV": "development" },
  "install_steps": [
    { "type": "apt", "packages": ["git", "curl", "python3"] },
    { "type": "pip", "packages": ["pytest==7.4.0", "requests"] },
    { "type": "shell", "command": "curl -fsSL https://deb.nodesource.com/setup_20.x | bash -" },
    { "type": "npm_global", "packages": ["pnpm"] }
  ],
  "startup_commands": ["Xvfb :0 &", "openbox &"],
  "metadata": { "app": "MyApp", "version": "2.3.1" }
}
```

### Install step types by family

| Family | Allowed types |
|--------|--------------|
| `linux` | `apt`, `pip`, `npm_global`, `shell`, `env_vars` |
| `android` | `adb_install`, `adb_shell`, `shell` |
| `windows` | `winget_install`, `msi_install`, `powershell`, `shell` |
| `macos` | `brew`, `mas_install`, `shell` |
| `ios_sim` | `xcrun_install`, `shell` |

---

## Capture a manifest from a running device

1. The device must be in `ready` state.
2. Call `POST /api/v1/devices/{id}/manifest/capture`.
3. DeviceLab introspects the device (dpkg/pip/npm for Linux; adb pm for Android; etc.)
   and saves a new `DeviceManifest` row.
4. The response includes `manifest_id` and `name`.

**Per-family capture caveats:**

| Family | What is captured | What is NOT captured |
|--------|-----------------|----------------------|
| Linux | apt packages, pip, npm globals, non-secret env vars, enabled systemd services | Running processes, open files, database rows, user files |
| Android | User-installed APK package names + paths | App data, accounts, system packages |
| Windows | winget packages, MSI/PackageManagement packages | Registry user data, app settings, files |
| macOS | Homebrew formulae + casks, Mac App Store apps | App data, Keychain, user preferences |
| iOS Sim | Installed bundle IDs | App data, simulator state |

Secret-like env vars (`*KEY*`, `*SECRET*`, `*PASSWORD*`, `*TOKEN*`, etc.) are redacted to
`***REDACTED***` on capture.

---

## Browse the manifest library

```
GET /api/v1/manifests?workspace_id=<id>&family=linux&location=local
```

Powers the "Existing" branch of the create-device wizard in Phase 11.

---

## Create a device from a manifest

Include `manifest_id` in the device create body:

```json
{
  "template_id": "...",
  "manifest_id": "...",
  "location": "local"
}
```

The device inherits the manifest's `name` unless you supply one. During `bootstrapping_agent`,
the manifest's `install_steps` are translated into a pypyr pipeline and executed. The device's
`source_manifest_id` is set for traceability.

---

## Import / export for sharing

**Export:**
```
GET /api/v1/manifests/{id}/export
```
Returns a standalone JSON document including `name`, `family`, `spec`, and export metadata.
Suitable for checking into source control or sharing with teammates.

**Import:**
```
POST /api/v1/manifests/import
Content-Type: application/json

{ "workspace_id": "...", "name": "...", "family": "linux", "spec_json": "..." }
```
Validates the spec; returns 422 with field-level errors on invalid specs. Duplicate names
are auto-suffixed (e.g. "My Env (2)").

---

## Hand-author a manifest

You can create a manifest without capturing from a device:

```
POST /api/v1/manifests
Content-Type: application/json

{
  "workspace_id": "...",
  "name": "My Python Dev Box",
  "family": "linux",
  "spec_json": "{\"install_steps\": [{\"type\": \"apt\", \"packages\": [\"python3\", \"git\"]}]}"
}
```

Invalid specs are rejected with 422.

---

## What manifests do not capture

- **On-disk data**: database rows, files the user created, downloads, caches
- **Application state**: login sessions, browser cookies, app settings files
- **Binary blobs**: APK files are referenced by path, not bundled
- **Running process state**: what was running at capture time

The only mechanism that captures on-disk data byte-for-byte is the Phase 05 EBS snapshot
(cloud Linux only). Manifests are cattle, not pets.

---

## Bootstrap execution flow

```
manifest.install_steps
    ↓  [manifest_bootstrap.to_pypyr_pipeline()]
pypyr YAML pipeline
    ↓  [device FSM bootstrapping_agent hook]
device ready
```

Each step type maps to a DeviceLab-provided pypyr step module under `devicelab.steps.*`.
Shell steps use `pypyr.steps.cmd` directly.
