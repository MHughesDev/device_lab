import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from transitions import MachineError

from app.models import Device
from app.services.device_fsm import DeviceFSM, STATES, get_device_fsm


def _make_device(state: str = "requested") -> Device:
    return Device(
        id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        family="linux",
        state=state,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _mock_db() -> MagicMock:
    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    return db


class TestDeviceFSMHappyPath:
    def test_provision_flow(self) -> None:
        device = _make_device("requested")
        fsm = DeviceFSM(device, _mock_db())
        fsm.transition("preflight_pass")
        assert fsm.current_state == "provisioning"
        fsm.transition("provision_done")
        assert fsm.current_state == "bootstrapping_agent"
        fsm.transition("agent_ready")
        assert fsm.current_state == "ready"

    def test_stop_and_restart(self) -> None:
        device = _make_device("ready")
        fsm = DeviceFSM(device, _mock_db())
        fsm.transition("stop")
        assert fsm.current_state == "stopping"
        fsm.transition("stop_done")
        assert fsm.current_state == "stopped"
        fsm.transition("start")
        assert fsm.current_state == "provisioning"

    def test_terminate_from_ready(self) -> None:
        device = _make_device("ready")
        fsm = DeviceFSM(device, _mock_db())
        fsm.transition("terminate")
        assert fsm.current_state == "terminating"
        fsm.transition("terminate_done")
        assert fsm.current_state == "terminated"

    def test_terminate_from_stopped(self) -> None:
        device = _make_device("stopped")
        fsm = DeviceFSM(device, _mock_db())
        fsm.transition("terminate")
        assert fsm.current_state == "terminating"

    def test_preflight_blocked_then_pass(self) -> None:
        device = _make_device("requested")
        fsm = DeviceFSM(device, _mock_db())
        fsm.transition("preflight_fail")
        assert fsm.current_state == "preflight_blocked"
        fsm.transition("preflight_pass")
        assert fsm.current_state == "provisioning"

    def test_fail_from_any_state(self) -> None:
        for state in ["requested", "provisioning", "bootstrapping_agent", "ready"]:
            device = _make_device(state)
            fsm = DeviceFSM(device, _mock_db())
            fsm.transition("fail")
            assert fsm.current_state == "failed"


class TestDeviceFSMInvalidTransitions:
    def test_cannot_stop_from_provisioning(self) -> None:
        device = _make_device("provisioning")
        fsm = DeviceFSM(device, _mock_db())
        with pytest.raises((MachineError, AttributeError)):
            fsm.transition("stop")

    def test_cannot_start_from_ready(self) -> None:
        device = _make_device("ready")
        fsm = DeviceFSM(device, _mock_db())
        with pytest.raises((MachineError, AttributeError)):
            fsm.transition("start")

    def test_cannot_provision_done_from_requested(self) -> None:
        device = _make_device("requested")
        fsm = DeviceFSM(device, _mock_db())
        with pytest.raises((MachineError, AttributeError)):
            fsm.transition("provision_done")

    def test_terminal_states_reject_most_transitions(self) -> None:
        for state in ["terminated", "failed"]:
            device = _make_device(state)
            fsm = DeviceFSM(device, _mock_db())
            with pytest.raises((MachineError, AttributeError)):
                fsm.transition("stop")

    def test_db_persisted_on_transition(self) -> None:
        db = _mock_db()
        device = _make_device("requested")
        fsm = DeviceFSM(device, db)
        fsm.transition("preflight_pass")
        db.commit.assert_called()


class TestAllStatesPresent:
    def test_all_states_defined(self) -> None:
        expected = {
            "requested", "preflight_blocked", "provisioning",
            "bootstrapping_agent", "ready", "stopping", "stopped",
            "terminating", "terminated", "failed",
        }
        assert set(STATES) == expected
