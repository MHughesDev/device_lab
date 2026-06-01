# ice.py — ICE configuration split: local loopback-only vs cloud STUN+coturn (Phase 09, task 09-04)
from __future__ import annotations
import logging

log = logging.getLogger(__name__)


def ice_servers_for(location: str) -> list[dict]:
    """Return the ICE server list for the given device location.

    local  → single 127.0.0.1 host candidate, no STUN, no TURN.
             Honors the localhost-only invariant; near-zero ICE connect time.
    cloud  → public STUN + coturn credentials loaded from settings (Phase 12).
             coturn must be deployed in the user's VPC (BYOC — DeviceLab never hosts TURN).
    """
    if location == "local":
        return _local_ice()
    return _cloud_ice()


def _local_ice() -> list[dict]:
    # No ICE servers — aiortc will use the loopback host candidate automatically.
    # A single 127.0.0.1:PORT host candidate is sufficient when browser and server
    # are on the same machine. STUN/TURN would add round-trip to a cloud reflector,
    # wasting latency budget that local HW encode already spent.
    return []


def _cloud_ice() -> list[dict]:
    """Return STUN + optional coturn TURN servers from settings."""
    servers: list[dict] = []

    try:
        from app.core.config import settings

        stun = getattr(settings, "WEBRTC_STUN_URL", None)
        if stun:
            servers.append({"urls": stun})
        else:
            # Default public STUN (no credentials needed, latency-only — no media traversal)
            servers.append({"urls": "stun:stun.l.google.com:19302"})

        turn_url = getattr(settings, "WEBRTC_TURN_URL", None)
        turn_user = getattr(settings, "WEBRTC_TURN_USERNAME", None)
        turn_cred = getattr(settings, "WEBRTC_TURN_CREDENTIAL", None)
        if turn_url and turn_user and turn_cred:
            servers.append({
                "urls": turn_url,
                "username": turn_user,
                "credential": turn_cred,
            })
            log.debug("Cloud ICE: coturn configured at %s", turn_url)
        else:
            log.warning(
                "Cloud ICE: no TURN configured (WEBRTC_TURN_URL/USERNAME/CREDENTIAL unset). "
                "Symmetric NAT traversal may fail. Set coturn in the user's VPC per ADR-0005."
            )
    except ImportError:
        pass

    return servers


def rtc_configuration_for(location: str) -> dict:
    """Return an RTCConfiguration-compatible dict for the given device location."""
    servers = ice_servers_for(location)
    config: dict = {"iceServers": servers}
    if location == "local":
        # Playout delay hint of 0ms — no jitter buffer needed on loopback
        config["playoutDelayHint"] = 0
    return config
