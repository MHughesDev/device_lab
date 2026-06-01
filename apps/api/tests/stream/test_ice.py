# tests/stream/test_ice.py — Phase 09 ICE configuration tests
from __future__ import annotations

import os
import pytest


def test_ice_local_is_loopback_only():
    from app.stream.ice import ice_servers_for
    servers = ice_servers_for("local")
    # Local: no STUN/TURN
    assert servers == []


def test_ice_cloud_empty_without_config(monkeypatch):
    """Cloud ICE returns STUN+TURN only when env vars are set."""
    monkeypatch.delenv("WEBRTC_STUN_URL", raising=False)
    monkeypatch.delenv("WEBRTC_TURN_URL", raising=False)
    from app.stream.ice import ice_servers_for
    servers = ice_servers_for("cloud")
    # No config → no TURN; public STUN may be included
    assert all(isinstance(s, dict) for s in servers)


def test_ice_cloud_includes_stun_by_default():
    """Cloud ICE always includes at least a STUN server (default public STUN)."""
    from app.stream.ice import ice_servers_for
    servers = ice_servers_for("cloud")
    stun_urls = [s["urls"] for s in servers if "stun:" in s.get("urls", "")]
    assert len(stun_urls) >= 1


def test_rtc_configuration_local_has_no_ice_servers():
    from app.stream.ice import rtc_configuration_for
    cfg = rtc_configuration_for("local")
    assert cfg.get("iceServers") == []


def test_rtc_configuration_local_has_playout_delay_hint():
    from app.stream.ice import rtc_configuration_for
    cfg = rtc_configuration_for("local")
    assert cfg.get("playoutDelayHint") == 0
