import logging
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlmodel import Session
from transitions import Machine

from app.models import Device

log = logging.getLogger(__name__)


STATES = [
    "requested",
    "preflight_blocked",
    "provisioning",
    "bootstrapping_agent",
    "ready",
    "stopping",
    "stopped",
    "terminating",
    "terminated",
    "failed",
]

TRANSITIONS = [
    {"trigger": "preflight_fail", "source": "requested", "dest": "preflight_blocked"},
    {"trigger": "preflight_pass", "source": ["requested", "preflight_blocked"], "dest": "provisioning"},
    {"trigger": "provision_done", "source": "provisioning", "dest": "bootstrapping_agent"},
    {"trigger": "agent_ready", "source": "bootstrapping_agent", "dest": "ready"},
    {"trigger": "stop", "source": "ready", "dest": "stopping"},
    {"trigger": "stop_done", "source": "stopping", "dest": "stopped"},
    {"trigger": "start", "source": "stopped", "dest": "provisioning"},
    {
        "trigger": "terminate",
        "source": ["ready", "stopped", "provisioning", "bootstrapping_agent", "preflight_blocked", "stopping"],
        "dest": "terminating",
    },
    {"trigger": "terminate_done", "source": "terminating", "dest": "terminated"},
    {"trigger": "fail", "source": "*", "dest": "failed"},
]


class DeviceFSM:
    """Wraps pytransitions Machine for a single Device record."""

    def __init__(self, device: Device, db: Session) -> None:
        self._device = device
        self._db = db
        self._machine = Machine(
            model=self,
            states=STATES,
            transitions=TRANSITIONS,
            initial=device.state,
            auto_transitions=False,
        )

    def _persist(self, new_state: str) -> None:
        self._device.state = new_state
        self._device.updated_at = datetime.now(UTC)
        self._db.add(self._device)
        self._db.commit()
        self._db.refresh(self._device)

    def transition(self, trigger: str, **kwargs) -> None:
        """Execute a named trigger and persist the resulting state.

        For preflight_pass (requested→provisioning), runs the cost guardrail check
        first and raises GuardrailBlocked if the hard cap would be exceeded.
        """
        if trigger == "preflight_pass":
            self._run_guardrail_check()
        getattr(self, trigger)()
        self._persist(self.state)  # type: ignore[attr-defined]

    def _run_guardrail_check(self) -> None:
        """Check cost guardrail before provisioning. Raises GuardrailBlocked if blocked."""
        try:
            from app.services.cost.guardrail import check, GuardrailBlocked
            result = check(
                db=self._db,
                workspace_id=self._device.workspace_id,
                action="provision",
                device=self._device,
                estimated_cost_usd=Decimal("0"),
                current_spend_usd=Decimal("0"),
            )
            if result.decision == "block":
                raise GuardrailBlocked(result.message)
            if result.decision == "warn":
                log.warning("Cost guardrail warn for device %s: %s", self._device.id, result.message)
        except ImportError:
            pass

    @property
    def current_state(self) -> str:
        return str(self.state)  # type: ignore[attr-defined]


def get_device_fsm(device: Device, db: Session) -> DeviceFSM:
    return DeviceFSM(device, db)
