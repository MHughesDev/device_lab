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
    """Return STUN + optional coturn TURN servers from settings.

    Resolution order:
      1. AppSettings (Phase 12) — reads via load_from_settings() when a DB session
         is available through the request context.
      2. Env vars (WEBRTC_STUN_URL / WEBRTC_TURN_*) — legacy / Docker Compose path.
      3. Public Google STUN — final STUN fallback (no TURN).
    """
    import os
    servers: list[dict] = []

    stun = os.environ.get("WEBRTC_STUN_URL")
    turn_url = os.environ.get("WEBRTC_TURN_URL")
    turn_user = os.environ.get("WEBRTC_TURN_USERNAME")
    turn_cred = os.environ.get("WEBRTC_TURN_CREDENTIAL")

    if stun:
        servers.append({"urls": stun})
    else:
        # Default public STUN (no credentials needed, latency-only — no media traversal)
        servers.append({"urls": "stun:stun.l.google.com:19302"})

    if turn_url and turn_user and turn_cred:
        servers.append({
            "urls": turn_url,
            "username": turn_user,
            "credential": turn_cred,
        })
        log.debug("Cloud ICE: coturn configured at %s (env vars)", turn_url)
    else:
        log.warning(
            "Cloud ICE: no TURN configured (WEBRTC_TURN_URL/USERNAME/CREDENTIAL unset). "
            "Symmetric NAT traversal may fail. Set coturn in the user's VPC per ADR-0005."
        )

    return servers


def load_from_settings(db, workspace_id) -> dict:
    """Read STUN/TURN config from AppSettings and return ICE-compatible server dict.

    Returns a dict with keys: stun_url, turn_url, turn_username, turn_credential.
    Values may be None if not configured.  Falls back to env vars when the
    AppSetting row is absent.
    """
    result: dict = {
        "stun_url": None,
        "turn_url": None,
        "turn_username": None,
        "turn_credential": None,
    }

    try:
        from app.services.settings_service import get_group
        cloud = get_group(db, workspace_id, "cloud")

        for key in result:
            val = cloud.get(key)
            # "***" means it is a secret ref — resolve from keyring
            if val == "***":
                try:
                    import keyring
                    resolved = keyring.get_password("devicelab-settings", key)
                    result[key] = resolved
                except Exception:
                    pass
            elif val is not None:
                result[key] = val

    except Exception as exc:
        log.warning("load_from_settings: could not read cloud settings: %s", exc)

    # Fall back to env vars where AppSettings returned None
    import os
    _env_fallbacks = {
        "stun_url": "WEBRTC_STUN_URL",
        "turn_url": "WEBRTC_TURN_URL",
        "turn_username": "WEBRTC_TURN_USERNAME",
        "turn_credential": "WEBRTC_TURN_CREDENTIAL",
    }
    for key, env_var in _env_fallbacks.items():
        if result[key] is None:
            result[key] = os.environ.get(env_var)

    return result


def rtc_configuration_for(location: str) -> dict:
    """Return an RTCConfiguration-compatible dict for the given device location."""
    servers = ice_servers_for(location)
    config: dict = {"iceServers": servers}
    if location == "local":
        # Playout delay hint of 0ms — no jitter buffer needed on loopback
        config["playoutDelayHint"] = 0
    return config
