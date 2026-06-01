---
doc_id: "ops.local-host-prerequisites"
title: "Local Host Prerequisites"
section: "Operations"
updated: "2026-06-01"
---

# Local Host Prerequisites

Per-family requirements for running DeviceLab devices locally. Run `devicelab doctor` after setup to verify your environment.

---

## All families

- Python 3.12+
- DeviceLab control plane running (see main README)
- At least **10 GB free disk** (warn threshold; hard minimum 2 GB)
- At least **2 GB free RAM** beyond OS use

---

## Linux (Docker container)

**Supported host OS:** Linux, macOS, Windows

### Packages

```bash
# Linux
sudo apt install docker.io          # Debian/Ubuntu
sudo dnf install docker             # Fedora/RHEL

# macOS
brew install --cask docker          # Docker Desktop

# Windows
# Install Docker Desktop from https://docker.com/products/docker-desktop
```

### Verify

```bash
docker info                         # must succeed
devicelab doctor                    # Docker check must show ✓
```

### Xvfb (virtual framebuffer — Phase 08)

Linux containers get a real X11 framebuffer via `Xvfb`. DeviceLab installs it automatically inside
the container at first boot if not baked into the image. To bake it into a custom image:

```dockerfile
RUN apt-get update && apt-get install -y xvfb fluxbox x11-utils
```

Xvfb is a **container-side** dependency (not a host prerequisite). The host only needs Docker.

---

## Android (AVD emulator)

**Supported host OS:** Linux (KVM), macOS (HVF), Windows (WHPX)

### Packages

Install Android SDK command-line tools:

```bash
# Download from https://developer.android.com/studio#command-line-tools-only
# Unzip and add to PATH:
export ANDROID_HOME=~/android-sdk
export PATH="$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/emulator:$ANDROID_HOME/platform-tools:$PATH"

# Install the system image
sdkmanager "system-images;android-34;google_apis;x86_64" "emulator" "platform-tools"
```

### Linux: enable KVM

```bash
# Check
ls /dev/kvm

# Enable (if missing)
sudo apt install qemu-kvm
sudo modprobe kvm_intel          # or kvm_amd
sudo usermod -aG kvm $USER       # then log out and back in
```

### macOS: HVF

HVF (Hypervisor.framework) is available on macOS 10.10+ — no extra steps needed on Apple Silicon. Intel Macs: ensure VT-x is enabled in firmware (usually default).

### Windows: enable WHPX

```powershell
Enable-WindowsOptionalFeature -Online -FeatureName HypervisorPlatform -All
# Reboot required
```

### Verify

```bash
adb version
emulator -list-avds
devicelab doctor                    # ADB + Virtualization checks must show ✓
```

---

## Windows (QEMU VM)

**Supported host OS:** Linux (KVM), Windows (WHPX), Intel Mac (HVF)  
**Not supported:** Apple Silicon (arm64 macOS) — x86 Windows cannot run under emulation at acceptable performance.

### Packages

```bash
# Linux
sudo apt install qemu-system-x86

# macOS (Intel)
brew install qemu

# Windows (host)
# Download QEMU for Windows: https://www.qemu.org/download/#windows
```

### Disk image

A pre-installed Windows Server 2022 or Windows 11 `.qcow2` image with:
- OpenSSH Server enabled (`Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0`)
- `Administrator` password set
- SSH listening on port 22 inside the VM

Provide the image path in the template's `extra_config`:

```json
{
  "extra_config": {
    "image_path": "/path/to/windows-server-2022.qcow2"
  }
}
```

### Verify

```bash
qemu-system-x86_64 --version
devicelab doctor                    # QEMU + Virtualization checks must show ✓
```

---

## macOS (QEMU/HVF VM)

**Supported host OS:** Apple Silicon or Intel Mac only  
**Not supported:** Linux, Windows, non-Apple macOS (Hackintosh)

### Packages

```bash
brew install qemu
```

### Disk image

A macOS `.qcow2` VM image (created via UTM or QEMU directly) with:
- SSH enabled: `System Settings → Sharing → Remote Login`
- A user account with SSH key or password auth

Provide the image path in the template's `extra_config`:

```json
{
  "extra_config": {
    "image_path": "/path/to/macos-sonoma.qcow2"
  }
}
```

> **Note:** macOS EULA permits running macOS in a VM only on Apple hardware. See [os-licensing.md](os-licensing.md).

### Verify

```bash
qemu-system-aarch64 --version       # Apple Silicon
devicelab doctor                    # QEMU + Virtualization must show ✓
```

---

## iOS Simulator (xcrun simctl)

**Supported host OS:** Apple hardware (Apple Silicon or Intel Mac) only  
**Not supported:** Linux, Windows, non-Apple macOS

### Packages

1. Install Xcode from the Mac App Store (full Xcode, not just command-line tools).
2. Accept the license: `xcodebuild -license accept`
3. Install the target iOS runtime in Xcode → Platforms → iOS.

### Verify

```bash
xcrun simctl list runtimes          # must list the iOS version you want
devicelab doctor                    # xcrun check must show ✓
```

---

## Quick reference

| Family | Docker | Android SDK + KVM/HVF | QEMU | Xcode | Apple HW |
|--------|:------:|:--------------------:|:----:|:-----:|:--------:|
| Linux | ✓ | | | | |
| Android | | ✓ | | | |
| Windows | | | ✓ | | |
| macOS | | | ✓ | | ✓ |
| iOS Sim | | | | ✓ | ✓ |
