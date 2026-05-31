# proxy.py — Android network proxy setup: mitmproxy CA cert + adb routing
from __future__ import annotations
import asyncio
import subprocess


async def install_mitmproxy_cert(adb_serial: str, cert_path: str) -> None:
    """Push mitmproxy CA cert to Android emulator system cert store."""
    subprocess.run(
        ["adb", "-s", adb_serial, "push", cert_path, "/sdcard/mitmproxy-ca.cer"],
        check=True,
    )
    subprocess.run(
        ["adb", "-s", adb_serial, "shell", "am", "start", "-n",
         "com.android.settings/.Settings$SecuritySettingsActivity"],
        check=True,
    )


async def setup_proxy_routing(adb_serial: str, proxy_host: str, proxy_port: int) -> None:
    """Route emulator traffic through mitmproxy via adb reverse + settings."""
    subprocess.run(
        ["adb", "-s", adb_serial, "reverse", f"tcp:{proxy_port}", f"tcp:{proxy_port}"],
        check=True,
    )
    subprocess.run(
        ["adb", "-s", adb_serial, "shell", "settings", "put", "global",
         "http_proxy", f"{proxy_host}:{proxy_port}"],
        check=True,
    )
