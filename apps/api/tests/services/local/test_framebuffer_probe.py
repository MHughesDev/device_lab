# test_framebuffer_probe.py — Tests for framebuffer self-check probe (Phase 08, task 08-06)
from __future__ import annotations
import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.services.local.framebuffer_probe import probe


def _device(family: str, provider_ids: dict) -> MagicMock:
    import json
    d = MagicMock()
    d.family = family
    d.provider_ids_json = json.dumps(provider_ids)
    return d


class TestFramebufferProbe:
    def test_probe_fails_to_state_framebuffer_unavailable_linux_no_container(self) -> None:
        device = _device("linux", {})
        ok, msg = probe(device)
        assert not ok
        assert "container_id" in msg or "not provisioned" in msg

    def test_probe_fails_android_no_serial(self) -> None:
        device = _device("android", {})
        ok, msg = probe(device)
        assert not ok
        assert "adb_serial" in msg

    def test_probe_fails_windows_no_vnc(self) -> None:
        device = _device("windows", {})
        ok, msg = probe(device)
        assert not ok
        assert "vnc_display" in msg

    def test_probe_fails_macos_no_vnc(self) -> None:
        device = _device("macos", {})
        ok, msg = probe(device)
        assert not ok
        assert "vnc_display" in msg

    def test_probe_fails_ios_sim_no_udid(self) -> None:
        device = _device("ios_sim", {})
        ok, msg = probe(device)
        assert not ok
        assert "sim_udid" in msg

    def test_probe_windows_with_closed_vnc_port_returns_false(self) -> None:
        device = _device("windows", {"vnc_display": 99})  # port 5999 unlikely open
        ok, msg = probe(device)
        assert not ok
        assert "not reachable" in msg or "5999" in msg or "VNC" in msg

    def test_probe_passes_on_live_framebuffer_vnc(self) -> None:
        device = _device("windows", {"vnc_display": 0})
        # Patch socket.create_connection at the stdlib level to succeed
        with patch("socket.create_connection") as mock_conn:
            mock_conn.return_value.__enter__ = MagicMock(return_value=MagicMock())
            mock_conn.return_value.__exit__ = MagicMock(return_value=False)
            ok, msg = probe(device)
        assert ok
        assert "VNC" in msg

    def test_probe_unknown_family(self) -> None:
        device = _device("fridge", {})
        ok, msg = probe(device)
        assert not ok
        assert "Unknown family" in msg
