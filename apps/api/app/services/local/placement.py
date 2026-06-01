# placement.py — Placement policy resolution: decide location at device-create time
from __future__ import annotations
from typing import Literal

from app.services.local.host_probe import HostCapabilities, probe_host

PlacementPolicy = Literal["prefer_local", "local_only", "cloud_only"]

# Families that can be hosted locally on a given host OS / arch.
# Keys are host OS; values are the set of families that can run locally.
_LOCAL_CAPABLE: dict[str, set[str]] = {
    "linux":   {"linux"},
    "macos":   {"linux", "macos", "ios_sim"},
    "windows": {"linux", "windows"},
}

# Families that require Apple hardware, regardless of policy
_APPLE_ONLY_FAMILIES = {"macos", "ios_sim"}


class PlacementError(Exception):
    """Raised when a requested placement is impossible."""


def resolve_location(
    family: str,
    policy: PlacementPolicy,
    caps: HostCapabilities | None = None,
) -> Literal["local", "cloud"]:
    """Resolve `location` for a new device at create time.

    Rules:
    - `cloud_only`   → always cloud, no host check.
    - `local_only`   → local if the host supports the family, else PlacementError.
    - `prefer_local` → local if the host supports the family, else falls back to cloud.
    """
    if policy == "cloud_only":
        return "cloud"

    if caps is None:
        caps = probe_host()

    if not _host_can_run_local(family, caps):
        if policy == "local_only":
            reason = _unsupported_reason(family, caps)
            raise PlacementError(
                f"local_only requested for family={family!r} but host cannot satisfy it: {reason}"
            )
        # prefer_local → fall back
        return "cloud"

    return "local"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _host_can_run_local(family: str, caps: HostCapabilities) -> bool:
    if family in _APPLE_ONLY_FAMILIES and not caps.is_apple_hardware:
        return False
    capable = _LOCAL_CAPABLE.get(caps.os, set())
    return family in capable


def _unsupported_reason(family: str, caps: HostCapabilities) -> str:
    if family in _APPLE_ONLY_FAMILIES and not caps.is_apple_hardware:
        return f"{family} requires Apple hardware; host is {caps.os}/{caps.arch}"
    capable = _LOCAL_CAPABLE.get(caps.os, set())
    if family not in capable:
        return f"host OS {caps.os!r} cannot run {family!r} locally (supports: {sorted(capable)})"
    return "unknown constraint"
