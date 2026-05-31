"""
Minimal runtime agent — runs on the cloud-side EC2 instance.
Architecture reference: openstf/stf provider/agent split.
Phase 02 scope: heartbeat + ready signal + terminate.

In Phase 02 this is bootstrapped via SSM Run Command (inline script).
Full agent packaging and mTLS channel are Phase 04.
"""
from __future__ import annotations

import json
import os
import signal
import sys
import time
import urllib.error
import urllib.request

CONTROL_API = os.environ.get("DEVICELAB_API", "http://127.0.0.1:8000")
DEVICE_ID = os.environ.get("DEVICELAB_DEVICE_ID", "")
HEARTBEAT_INTERVAL = int(os.environ.get("DEVICELAB_HEARTBEAT_INTERVAL", "30"))

_running = True


def _post(path: str, body: dict) -> None:
    url = f"{CONTROL_API}{path}"
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        url, data=data, method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(req, timeout=10)
    except (urllib.error.URLError, OSError):
        pass


def _signal_handler(signum: int, frame: object) -> None:
    global _running
    _running = False
    _post(f"/api/v1/devices/{DEVICE_ID}/heartbeat", {"status": "stopping"})
    sys.exit(0)


def main() -> None:
    if not DEVICE_ID:
        print("DEVICELAB_DEVICE_ID not set — exiting", file=sys.stderr)
        sys.exit(1)

    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)

    # Signal ready on first heartbeat
    _post(f"/api/v1/devices/{DEVICE_ID}/heartbeat", {"status": "alive"})
    print(f"DeviceLab agent started — device={DEVICE_ID}")

    while _running:
        time.sleep(HEARTBEAT_INTERVAL)
        _post(f"/api/v1/devices/{DEVICE_ID}/heartbeat", {"status": "alive"})


if __name__ == "__main__":
    main()
