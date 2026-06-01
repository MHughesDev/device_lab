# test_reconcile.py — Startup reconciliation unit tests (Task 07-14)
from __future__ import annotations
from unittest.mock import MagicMock, patch

import pytest

from app.services.local.reconcile import reconcile_local_devices


def _make_device(
    device_id: str = "device-1",
    family: str = "linux",
    state: str = "ready",
    provider_ids: str = '{"container_id": "abc123"}',
) -> MagicMock:
    d = MagicMock()
    d.id = device_id
    d.family = family
    d.state = state
    d.location = "local"
    d.provider_ids_json = provider_ids
    d.phase = None
    return d


def _make_db(devices: list) -> MagicMock:
    db = MagicMock()
    db.exec.return_value.all.return_value = devices
    return db


@pytest.mark.asyncio
async def test_reconcile_marks_lost_when_container_gone():
    device = _make_device(family="linux", state="ready")
    db = _make_db([device])

    with patch("app.services.local.reconcile._docker_container_alive", return_value=False):
        result = await reconcile_local_devices(db)

    assert "device-1" in result["marked_lost"]
    assert device.state == "failed"
    assert device.phase == "lost_on_restart"
    db.add.assert_called_once_with(device)
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_reconcile_re_adopts_live_container():
    device = _make_device(family="linux", state="ready")
    db = _make_db([device])

    with patch("app.services.local.reconcile._docker_container_alive", return_value=True):
        result = await reconcile_local_devices(db)

    assert "device-1" in result["re_adopted"]
    assert device.state == "ready"  # unchanged
    db.add.assert_not_called()


@pytest.mark.asyncio
async def test_reconcile_handles_probe_error_gracefully():
    device = _make_device(family="linux", state="ready")
    db = _make_db([device])

    with patch("app.services.local.reconcile._docker_container_alive", side_effect=RuntimeError("boom")):
        result = await reconcile_local_devices(db)

    assert len(result["errors"]) == 1
    assert "boom" in result["errors"][0]["error"]
    assert result["errors"][0]["device_id"] == "device-1"
    # State not modified on error
    assert device.state == "ready"


@pytest.mark.asyncio
async def test_reconcile_re_adopts_live_android_emulator():
    device = _make_device(
        family="android", state="ready", provider_ids='{"adb_serial": "emulator-5554"}'
    )
    db = _make_db([device])

    with patch("app.services.local.reconcile._adb_device_alive", return_value=True):
        result = await reconcile_local_devices(db)

    assert "device-1" in result["re_adopted"]


@pytest.mark.asyncio
async def test_reconcile_marks_lost_android_when_adb_gone():
    device = _make_device(
        family="android", state="ready", provider_ids='{"adb_serial": "emulator-5554"}'
    )
    db = _make_db([device])

    with patch("app.services.local.reconcile._adb_device_alive", return_value=False):
        result = await reconcile_local_devices(db)

    assert "device-1" in result["marked_lost"]
    assert device.state == "failed"


@pytest.mark.asyncio
async def test_reconcile_empty_when_no_local_devices():
    db = _make_db([])
    result = await reconcile_local_devices(db)

    assert result["re_adopted"] == []
    assert result["marked_lost"] == []
    assert result["errors"] == []
