# services/local/proxy.py — Local proxy + CA-cert injection stub
#
# BLOCKED on OQ-012: Per-family local proxy + mitmproxy CA-cert injection mechanism.
#
# Outstanding questions that must be answered before implementing:
#   1. CA cert scope: per-workspace vs. global DeviceLab CA?
#   2. Injection mechanism per family:
#      - Linux/Docker:  volume-mount /usr/local/share/ca-certificates/ or env var
#      - Android/AVD:   adb push + update-ca-certificates or system store via Magisk
#      - Windows/QEMU:  SSH copy + certutil -addstore Root
#      - macOS/iOS Sim: SSH copy + security add-trusted-cert (macOS keychain)
#   3. Port allocation: fixed range vs. dynamic; how to avoid conflicts with the
#      host's existing mitmproxy instances if any.
#   4. Lifecycle: start proxy before provisioning or after bootstrap?
#
# See docs/roadmap/phases/phase-07-local-hosting.md — Task 07-15.
# Track resolution at: OQ-012 in docs/roadmap/open-questions.md (when created).
#
# When OQ-012 is resolved, implement:
#   - generate_workspace_ca(workspace_id) -> (cert_pem, key_pem)
#   - start_proxy(device, port) -> ProxySession
#   - inject_ca(device, cert_pem) -> None   # dispatches per-family
#   - stop_proxy(session) -> None


class LocalProxyBlocked(NotImplementedError):
    """Raised when local proxy/CA-cert injection is requested before OQ-012 resolves."""

    def __init__(self) -> None:
        super().__init__(
            "Local proxy + CA-cert injection is blocked on OQ-012. "
            "See docs/roadmap/phases/phase-07-local-hosting.md — Task 07-15."
        )
