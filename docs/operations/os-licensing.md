# OS Licensing by Device Family

Covers what licenses (if any) are required to provision each device family,
both on AWS (cloud) and locally on the developer's own machine.

---

## Cloud (AWS)

| Family | OS / Runtime | License Required? | How It's Handled |
|---|---|---|---|
| **linux** | Ubuntu / Amazon Linux | None | Free AMIs; no license cost |
| **macos** | macOS Sequoia / Sonoma | None (EULA compliant) | AWS Mac Dedicated Hosts run on real Apple hardware; Apple's EULA is satisfied by running on Apple silicon/Intel Mac Mini |
| **windows** | Windows Server / Windows 11 | Bundled | Microsoft license is included in the EC2 hourly rate for Windows AMIs; AWS pays Microsoft, charges you slightly more per hour |
| **android** | Android (AOSP) via ADB | None | AOSP is open source; ADB ships free with Android SDK |
| **ios_sim** | iOS Simulator via Xcode | None | Simulator ships with Xcode (free); runs on the same Mac Dedicated Host as the macOS family |

**Cloud cost notes:**
- Linux: cheapest — $0.04–$0.10/hr for a t3.medium
- Windows: ~20–40% premium over equivalent Linux instance for the embedded license
- macOS: most expensive — Mac Dedicated Host has a **24-hour minimum** (~$25–$32/day regardless of usage); this applies to both macOS and ios_sim devices since they share the same host type

---

## Local (Developer's Machine)

| Family | OS / Runtime | License Required? | How It's Handled |
|---|---|---|---|
| **linux** | Ubuntu / Debian / Fedora etc. | None | Free; run in VirtualBox, VMware, QEMU, or UTM |
| **macos** | macOS | None — **but requires Apple hardware** | macOS VMs are only legal on Apple hardware; on a Mac you can run macOS VMs via UTM or VMware Fusion; on non-Apple hardware this is an EULA violation |
| **windows** | Windows 10/11 | **License required** | Retail license ($139–$199); or use Microsoft's free 90-day evaluation ISO; Visual Studio / MSDN subscribers get licenses included |
| **android** | Android Emulator (AVD) | None | Ships free with Android Studio; AOSP-based, no license |
| **ios_sim** | iOS Simulator | None — **but requires a Mac** | Simulator ships with Xcode (free from Mac App Store); cannot run on Windows or Linux |

**Local hypervisor options (no cost unless noted):**
- **VirtualBox** — free, cross-platform (Oracle)
- **QEMU / KVM** — free, Linux-native; best performance on Linux hosts
- **UTM** — free, macOS-native; wraps QEMU; supports ARM and x86 guests on Apple Silicon
- **VMware Fusion** — free for personal use (since 2024 Broadcom change); macOS only
- **VMware Workstation** — free for personal use; Windows/Linux only
- **Parallels Desktop** — ~$99/yr; macOS only; best Windows-on-Mac performance

---

## Hard Constraints Summary

| Constraint | Detail |
|---|---|
| macOS (any context) | **Must be on Apple hardware** — cloud or local. Non-negotiable per Apple EULA. |
| iOS Simulator (any context) | **Requires macOS**, therefore requires Apple hardware. |
| Windows (local) | **Needs a license**. AWS handles this for you in the cloud; locally you are responsible. |
| Linux / Android | No licensing constraints in any context. |
