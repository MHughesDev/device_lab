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
        self._emit_lifecycle(new_state)

    def _emit_lifecycle(self, new_state: str) -> None:
        try:
            from app.services.device_log_bus import get_log_bus
            get_log_bus().emit(
                self._device.id,
                level="info",
                source="lifecycle",
                message=f"Device transitioned to state: {new_state}",
                fields={"state": new_state, "phase": self._device.phase},
            )
        except Exception:
            pass

    def transition(self, trigger: str, **kwargs) -> None:
        """Execute a named trigger and persist the resulting state.

        For preflight_pass (requested→provisioning):
          1. Runs the cost guardrail check (cloud devices).
          2. Runs the local scheduler admission check (local devices).
          3. Reserves resources in the Host Resource Ledger (local devices).
        For agent_ready (bootstrapping_agent→ready):
          - Runs the framebuffer self-check probe (local devices, 08-06).
        For terminate_done:
          - Releases ledger reservation.
        On block, transitions to preflight_blocked instead.
        """
        if trigger == "preflight_pass":
            self._run_guardrail_check()
            self._run_local_admission_check()
            self._reserve_ledger_resources()
        if trigger == "agent_ready":
            self._run_framebuffer_probe()
        getattr(self, trigger)()
        self._persist(self.state)  # type: ignore[attr-defined]
        if trigger == "terminate_done":
            self._release_ledger_reservation()

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

    def _run_local_admission_check(self) -> None:
        """For local devices, verify the host has sufficient resources via the ledger.

        Transitions to preflight_blocked:insufficient_host_resources on rejection.
        """
        if getattr(self._device, "location", "cloud") != "local":
            return
        try:
            from app.services.local.ledger import get_ledger, ResourceClaim
            claim = _device_resource_claim(self._device)
            if not get_ledger().can_admit(claim):
                reason = (
                    f"insufficient_host_resources: need {claim.ram_mb} MB RAM, "
                    f"{claim.vcpu} vCPU, {claim.disk_mb} MB disk"
                )
                self._device.phase = reason
                self.preflight_fail()  # type: ignore[attr-defined]
                self._persist(self.state)  # type: ignore[attr-defined]
                raise _LocalAdmissionBlocked(reason)
        except ImportError:
            pass

    def _reserve_ledger_resources(self) -> None:
        """Persist a Host Resource Ledger reservation for this local device."""
        if getattr(self._device, "location", "cloud") != "local":
            return
        try:
            from app.services.local.ledger import get_ledger, ResourceClaim
            claim = _device_resource_claim(self._device)
            get_ledger().reserve(self._device.id, claim)
            try:
                from app.services.device_log_bus import get_log_bus
                get_log_bus().emit(
                    self._device.id,
                    level="info",
                    source="ledger",
                    message=f"Reserved {claim.ram_mb} MB RAM, {claim.vcpu} vCPU, {claim.disk_mb} MB disk",
                    fields={"ram_mb": claim.ram_mb, "vcpu": claim.vcpu, "disk_mb": claim.disk_mb},
                )
            except Exception:
                pass
        except (ImportError, Exception) as exc:
            log.warning("Failed to reserve ledger for device %s: %s", self._device.id, exc)

    def _run_framebuffer_probe(self) -> None:
        """For local devices, verify the framebuffer is capturable before marking ready.

        On failure, transitions to failed:framebuffer_unavailable with an actionable message.
        """
        if getattr(self._device, "location", "cloud") != "local":
            return
        try:
            from app.services.local.framebuffer_probe import probe
            ok, message = probe(self._device)
            if not ok:
                self._device.phase = f"framebuffer_unavailable: {message}"
                self.fail()  # type: ignore[attr-defined]
                self._persist(self.state)  # type: ignore[attr-defined]
                raise _FramebufferUnavailable(message)
            log.debug("Framebuffer probe passed for device %s: %s", self._device.id, message)
        except ImportError:
            pass

    def _release_ledger_reservation(self) -> None:
        """Release the Host Resource Ledger reservation after termination."""
        if getattr(self._device, "location", "cloud") != "local":
            return
        try:
            from app.services.local.ledger import get_ledger
            get_ledger().release(str(self._device.id))
        except (ImportError, Exception) as exc:
            log.warning("Failed to release ledger reservation for device %s: %s", self._device.id, exc)

    @property
    def current_state(self) -> str:
        return str(self.state)  # type: ignore[attr-defined]


class _LocalAdmissionBlocked(Exception):
    """Raised when the local scheduler rejects a device provisioning request."""


class _FramebufferUnavailable(Exception):
    """Raised when the framebuffer probe fails before marking a local device ready."""


# Default resource budgets per device family for local placement
_FAMILY_RESOURCE_DEFAULTS: dict[str, dict] = {
    "linux":   {"ram_mb": 512,  "vcpu": 0.5, "disk_mb": 4096},
    "android": {"ram_mb": 2048, "vcpu": 2.0, "disk_mb": 8192},
    "windows": {"ram_mb": 4096, "vcpu": 2.0, "disk_mb": 20480},
    "macos":   {"ram_mb": 8192, "vcpu": 4.0, "disk_mb": 40960},
    "ios_sim": {"ram_mb": 2048, "vcpu": 2.0, "disk_mb": 8192},
    "browser": {"ram_mb": 512,  "vcpu": 0.5, "disk_mb": 2048},
}
_DEFAULT_RESOURCE = {"ram_mb": 512, "vcpu": 1.0, "disk_mb": 4096}


def _device_resource_claim(device: Device):
    """Return a ResourceClaim for the given device based on family defaults."""
    from app.services.local.ledger import ResourceClaim
    defaults = _FAMILY_RESOURCE_DEFAULTS.get(device.family, _DEFAULT_RESOURCE)
    return ResourceClaim(**defaults)


def get_device_fsm(device: Device, db: Session) -> DeviceFSM:
    return DeviceFSM(device, db)
