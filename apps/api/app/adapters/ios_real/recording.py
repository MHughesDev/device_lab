# recording.py — Real iOS recording via AWS Device Farm video artifacts
# Device Farm automatically records sessions; we surface the artifact URL on stop.
from __future__ import annotations
import json


async def start(device: object, recording_id: str) -> str:
    """Device Farm records automatically. Store session_arn as handle."""
    ids = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
    return ids.get("session_arn", "")


async def stop(device: object, session: object) -> str:
    """Fetch the video artifact URL from Device Farm for this session."""
    import boto3
    ids = json.loads(getattr(device, "provider_ids_json", "{}") or "{}")
    session_arn = ids.get("session_arn", "")

    if not session_arn:
        return ""

    df = boto3.client("devicefarm", region_name="us-west-2")
    try:
        resp = df.list_artifacts(arn=session_arn, type="VIDEO")
        artifacts = resp.get("artifacts", [])
        if artifacts:
            # Return the Device Farm pre-signed URL directly
            return artifacts[0].get("url", "")
    except Exception:
        pass

    return ""
