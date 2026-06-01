# host_probe.py — Probe local host capabilities for the local scheduler and placement layer
from __future__ import annotations
import platform
import shutil
import subprocess
from dataclasses import dataclass
from typing import Literal


@dataclass
class HostCapabilities:
    os: Literal["linux", "macos", "windows"]
    arch: Literal["x86_64", "arm64"]
    docker_available: bool
    virtualization_available: bool   # KVM (Linux) / WHPX (Windows) / Hypervisor.framework (macOS)
    is_apple_hardware: bool          # True only on real Apple Silicon/Intel Mac hardware
    total_ram_mb: int
    total_vcpu: int
    free_disk_mb: int


def probe_host() -> HostCapabilities:
    """Probe the local machine and return its capabilities.

    Runs fast, no network calls, deterministic on the same host.
    """
    return HostCapabilities(
        os=_detect_os(),
        arch=_detect_arch(),
        docker_available=_detect_docker(),
        virtualization_available=_detect_virtualization(),
        is_apple_hardware=_detect_apple_hardware(),
        total_ram_mb=_total_ram_mb(),
        total_vcpu=_total_vcpu(),
        free_disk_mb=_free_disk_mb(),
    )


# ---------------------------------------------------------------------------
# OS / arch
# ---------------------------------------------------------------------------

def _detect_os() -> Literal["linux", "macos", "windows"]:
    s = platform.system().lower()
    if s == "darwin":
        return "macos"
    if s == "windows":
        return "windows"
    return "linux"


def _detect_arch() -> Literal["x86_64", "arm64"]:
    machine = platform.machine().lower()
    if machine in ("arm64", "aarch64"):
        return "arm64"
    return "x86_64"


# ---------------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------------

def _detect_docker() -> bool:
    """Return True if the Docker CLI is on PATH and the daemon is reachable."""
    if shutil.which("docker") is None:
        return False
    try:
        result = subprocess.run(
            ["docker", "info", "--format", "{{.ServerVersion}}"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Virtualization
# ---------------------------------------------------------------------------

def _detect_virtualization() -> bool:
    """Return True if a usable hypervisor is available for local VMs."""
    system = platform.system().lower()

    if system == "linux":
        # KVM: check /dev/kvm exists and is accessible
        import os
        return os.path.exists("/dev/kvm") and os.access("/dev/kvm", os.R_OK | os.W_OK)

    if system == "darwin":
        # Hypervisor.framework: available on macOS 10.10+ on real Apple hardware
        try:
            result = subprocess.run(
                ["sysctl", "-n", "kern.hv_support"],
                capture_output=True,
                timeout=3,
            )
            return result.returncode == 0 and result.stdout.strip() == b"1"
        except Exception:
            return False

    if system == "windows":
        # WHPX: check via Get-WindowsOptionalFeature
        try:
            result = subprocess.run(
                ["powershell", "-NonInteractive", "-Command",
                 "(Get-WindowsOptionalFeature -Online -FeatureName HypervisorPlatform).State"],
                capture_output=True,
                timeout=10,
            )
            return b"Enabled" in result.stdout
        except Exception:
            return False

    return False


# ---------------------------------------------------------------------------
# Apple hardware detection
# ---------------------------------------------------------------------------

def _detect_apple_hardware() -> bool:
    """Return True only on real Apple hardware (Intel Mac or Apple Silicon)."""
    if platform.system() != "Darwin":
        return False
    # On non-Apple hardware running macOS in a VM, sysctl kern.ostype still
    # returns "Darwin" but sysctl machdep.cpu.brand_string won't contain
    # "Apple" for non-Apple CPUs.
    try:
        result = subprocess.run(
            ["sysctl", "-n", "machdep.cpu.brand_string"],
            capture_output=True,
            timeout=3,
        )
        brand = result.stdout.decode(errors="replace").lower()
        return "apple" in brand or "intel" in brand  # Intel Mac is still Apple hardware
    except Exception:
        return True  # Assume Apple hardware if we can't tell on Darwin


# ---------------------------------------------------------------------------
# Resource measurements (via psutil)
# ---------------------------------------------------------------------------

def _total_ram_mb() -> int:
    try:
        import psutil
        return int(psutil.virtual_memory().total / (1024 * 1024))
    except ImportError:
        return _fallback_ram_mb()


def _fallback_ram_mb() -> int:
    """Fallback RAM detection without psutil."""
    try:
        if platform.system() == "Linux":
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        kb = int(line.split()[1])
                        return kb // 1024
    except Exception:
        pass
    return 0


def _total_vcpu() -> int:
    try:
        import psutil
        return psutil.cpu_count(logical=True) or 1
    except ImportError:
        import os
        return os.cpu_count() or 1


def _free_disk_mb() -> int:
    try:
        import psutil
        usage = psutil.disk_usage("/")
        return int(usage.free / (1024 * 1024))
    except ImportError:
        return _fallback_disk_mb()


def _fallback_disk_mb() -> int:
    """Fallback disk detection without psutil."""
    try:
        import os
        stat = os.statvfs("/")
        return int(stat.f_bavail * stat.f_frsize / (1024 * 1024))
    except Exception:
        return 0
