# test_reaper.py — Reaper unit tests (Task 07-05)
from __future__ import annotations
from unittest.mock import MagicMock, patch

from app.services.local.reaper import LABEL_DEVICE, reap_orphans


def _make_container(container_id: str, device_id: str) -> MagicMock:
    c = MagicMock()
    c.id = container_id
    c.labels = {LABEL_DEVICE: device_id}
    return c


def test_reaper_removes_orphan_container():
    orphan = _make_container("container-orphan", "dead-device-id")
    mock_docker = MagicMock()
    mock_docker.containers.list.return_value = [orphan]

    with patch("docker.from_env", return_value=mock_docker):
        result = reap_orphans(db_device_ids=set())  # no live devices

    assert "container-orphan" in result["removed_containers"]
    orphan.stop.assert_called_once()
    orphan.remove.assert_called_once_with(force=True)


def test_reaper_skips_live_device():
    live = _make_container("container-live", "live-device-id")
    mock_docker = MagicMock()
    mock_docker.containers.list.return_value = [live]

    with patch("docker.from_env", return_value=mock_docker):
        result = reap_orphans(db_device_ids={"live-device-id"})

    assert result["removed_containers"] == []
    live.stop.assert_not_called()
    live.remove.assert_not_called()


def test_reaper_skips_containers_without_label():
    no_label = MagicMock()
    no_label.id = "container-no-label"
    no_label.labels = {}  # no DeviceLab labels
    mock_docker = MagicMock()
    mock_docker.containers.list.return_value = [no_label]

    with patch("docker.from_env", return_value=mock_docker):
        result = reap_orphans(db_device_ids=set())

    assert result["removed_containers"] == []
    no_label.stop.assert_not_called()


def test_reaper_gracefully_handles_docker_unavailable():
    with patch("docker.from_env", side_effect=Exception("Docker not running")):
        result = reap_orphans(db_device_ids=set())
    assert result["removed_containers"] == []
