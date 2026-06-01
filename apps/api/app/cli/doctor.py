# cli/doctor.py — devicelab doctor: local environment diagnostics
from __future__ import annotations
import shutil
import socket
import subprocess
from dataclasses import dataclass
from typing import Literal


@dataclass
class CheckResult:
    name: str
    status: Literal["ok", "warn", "fail"]
    message: str
    remedy: str = ""


def run_doctor() -> list[CheckResult]:
    """Run all local diagnostics. Returns a list of CheckResult in execution order."""
    return [
        _check_docker(),
        _check_virtualization(),
        _check_disk_space(),
        _check_adb(),
        _check_xcrun(),
        _check_qemu(),
        _check_ports(),
    ]


def print_doctor_report(results: list[CheckResult] | None = None) -> int:
    """Print a human-readable doctor report. Returns exit code (0=all ok, 1=any fail)."""
    if results is None:
        results = run_doctor()

    _SYMBOLS = {"ok": "✓", "warn": "⚠", "fail": "✗"}
    any_fail = False

    for r in results:
        sym = _SYMBOLS[r.status]
        print(f"  {sym}  {r.name}: {r.message}")
        if r.remedy and r.status != "ok":
            print(f"     → {r.remedy}")
        if r.status == "fail":
            any_fail = True

    return 1 if any_fail else 0


# ── individual checks ──────────────────────────────────────────────────────────


def _check_docker() -> CheckResult:
    if not shutil.which("docker"):
        return CheckResult(
            name="Docker",
            status="fail",
            message="docker CLI not found in PATH",
            remedy="Install Docker Desktop or docker-ce; ensure docker is on PATH.",
        )
    try:
        result = subprocess.run(
            ["docker", "info"], capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return CheckResult(
                name="Docker",
                status="fail",
                message="Docker daemon not running",
                remedy="Start Docker Desktop or run: sudo systemctl start docker",
            )
        return CheckResult(name="Docker", status="ok", message="daemon reachable")
    except Exception as exc:
        return CheckResult(
            name="Docker", status="fail", message=str(exc),
            remedy="Ensure the Docker daemon is running."
        )


def _check_virtualization() -> CheckResult:
    import platform
    os_name = platform.system().lower()

    if os_name == "linux":
        import os
        if os.path.exists("/dev/kvm"):
            return CheckResult(name="Virtualization", status="ok", message="KVM available (/dev/kvm)")
        return CheckResult(
            name="Virtualization",
            status="warn",
            message="/dev/kvm not found — Android AVD and Windows VMs unavailable",
            remedy="Enable VT-x/AMD-V in BIOS and load kvm_intel/kvm_amd module.",
        )

    if os_name == "darwin":
        try:
            result = subprocess.run(
                ["sysctl", "kern.hv_support"], capture_output=True, text=True, timeout=5
            )
            if "1" in result.stdout:
                return CheckResult(
                    name="Virtualization", status="ok", message="Hypervisor.framework available"
                )
        except Exception:
            pass
        return CheckResult(
            name="Virtualization",
            status="warn",
            message="Hypervisor.framework not confirmed",
            remedy="macOS 10.10+ with a compatible CPU is required.",
        )

    if os_name == "windows":
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 "Get-WindowsOptionalFeature -Online -FeatureName HypervisorPlatform | Select -Expand State"],
                capture_output=True, text=True, timeout=15,
            )
            if "Enabled" in result.stdout:
                return CheckResult(name="Virtualization", status="ok", message="WHPX/HypervisorPlatform enabled")
        except Exception:
            pass
        return CheckResult(
            name="Virtualization",
            status="warn",
            message="HypervisorPlatform not confirmed enabled",
            remedy="Enable Hyper-V Platform in Windows Features.",
        )

    return CheckResult(name="Virtualization", status="warn", message="Unknown OS; cannot probe")


def _check_disk_space() -> CheckResult:
    _WARN_GB = 10
    _FAIL_GB = 2
    try:
        import psutil
        usage = psutil.disk_usage("/")
        free_gb = usage.free / (1024 ** 3)
    except Exception:
        import os
        stat = os.statvfs("/")
        free_gb = (stat.f_bavail * stat.f_frsize) / (1024 ** 3)

    if free_gb < _FAIL_GB:
        return CheckResult(
            name="Disk space",
            status="fail",
            message=f"{free_gb:.1f} GB free — insufficient for device images",
            remedy="Free at least 10 GB before provisioning local devices.",
        )
    if free_gb < _WARN_GB:
        return CheckResult(
            name="Disk space",
            status="warn",
            message=f"{free_gb:.1f} GB free — may be tight for multiple devices",
            remedy="Consider freeing disk space; each device image can be 2–8 GB.",
        )
    return CheckResult(name="Disk space", status="ok", message=f"{free_gb:.1f} GB free")


def _check_adb() -> CheckResult:
    if not shutil.which("adb"):
        return CheckResult(
            name="ADB",
            status="warn",
            message="adb not found in PATH — Android local devices unavailable",
            remedy="Install Android SDK platform-tools and add to PATH.",
        )
    try:
        result = subprocess.run(["adb", "version"], capture_output=True, text=True, timeout=5)
        version_line = result.stdout.splitlines()[0] if result.stdout else "unknown"
        return CheckResult(name="ADB", status="ok", message=version_line)
    except Exception as exc:
        return CheckResult(name="ADB", status="warn", message=str(exc))


def _check_xcrun() -> CheckResult:
    import platform
    if platform.system().lower() != "darwin":
        return CheckResult(
            name="xcrun / Xcode",
            status="ok",
            message="not applicable on non-macOS host",
        )
    if not shutil.which("xcrun"):
        return CheckResult(
            name="xcrun / Xcode",
            status="warn",
            message="xcrun not found — iOS Simulator local devices unavailable",
            remedy="Install Xcode from the App Store and accept the license: xcodebuild -license",
        )
    try:
        result = subprocess.run(
            ["xcrun", "simctl", "list", "--json"], capture_output=True, timeout=10
        )
        if result.returncode == 0:
            return CheckResult(name="xcrun / Xcode", status="ok", message="simctl reachable")
    except Exception:
        pass
    return CheckResult(
        name="xcrun / Xcode",
        status="warn",
        message="xcrun found but simctl unresponsive",
        remedy="Reinstall Xcode command-line tools: xcode-select --install",
    )


def _check_qemu() -> CheckResult:
    binary = "qemu-system-x86_64"
    import platform
    if platform.system().lower() == "darwin" and platform.machine().lower() == "arm64":
        binary = "qemu-system-aarch64"

    if not shutil.which(binary):
        return CheckResult(
            name="QEMU",
            status="warn",
            message=f"{binary} not found — Windows/macOS local VMs unavailable",
            remedy="Install QEMU: brew install qemu  (macOS) or apt install qemu-system (Linux)",
        )
    try:
        result = subprocess.run(
            [binary, "--version"], capture_output=True, text=True, timeout=5
        )
        version_line = result.stdout.splitlines()[0] if result.stdout else "unknown"
        return CheckResult(name="QEMU", status="ok", message=version_line)
    except Exception as exc:
        return CheckResult(name="QEMU", status="warn", message=str(exc))


def _check_ports() -> CheckResult:
    """Verify that the default control-plane port (8000) is not already in use."""
    _CONTROL_PLANE_PORT = 8000
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            in_use = s.connect_ex(("127.0.0.1", _CONTROL_PLANE_PORT)) == 0
    except Exception:
        in_use = False

    if in_use:
        return CheckResult(
            name="Control-plane port",
            status="fail",
            message=f"Port {_CONTROL_PLANE_PORT} already in use",
            remedy=f"Stop the process using port {_CONTROL_PLANE_PORT}, "
                   "or set DEVICELAB_PORT in your environment.",
        )
    return CheckResult(
        name="Control-plane port",
        status="ok",
        message=f"Port {_CONTROL_PLANE_PORT} is free",
    )
