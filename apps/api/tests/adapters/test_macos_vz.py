# tests/adapters/test_macos_vz.py — Phase 09 macOS vz provisioner tests
from __future__ import annotations

import pytest


def test_vz_provision_refused_on_non_apple():
    from app.adapters.macos.vz_provision import VzMacosProvisioner, is_apple_silicon
    import platform

    class _FakeDevice:
        family = "macos"
        location = "local"
        vcpu = 4
        ram_mb = 8192
        provider_ids_json = "{}"

    # On non-Apple-Silicon (always true in CI / Linux), must raise RuntimeError
    if not is_apple_silicon():
        prov = VzMacosProvisioner(_FakeDevice())
        with pytest.raises(RuntimeError, match="Apple Silicon"):
            import asyncio
            asyncio.get_event_loop().run_until_complete(prov.provision())


def test_is_apple_silicon_false_on_linux():
    import platform
    from app.adapters.macos.vz_provision import is_apple_silicon
    if platform.system() != "Darwin":
        assert not is_apple_silicon()


def test_vz_sidecar_client_builds():
    from app.adapters.macos.vz_provision import VzSidecarClient
    client = VzSidecarClient("/tmp/fake.sock")
    assert client._socket_path == "/tmp/fake.sock"


def test_macos_input_sink_disabled_without_sidecar():
    """MacosInputSink start() without sidecar_socket logs warning and disables injection."""
    from app.adapters.macos.input import MacosInputSink

    class _Dev:
        provider_ids_json = "{}"

    import asyncio
    sink = MacosInputSink(_Dev())
    asyncio.get_event_loop().run_until_complete(sink.start())
    assert not sink._available


def test_to_vz_hid_event_pointer_move():
    from app.adapters.macos.input import _to_vz_hid_event
    from app.stream.source import InputEvent
    ev = InputEvent(kind="pointer_move", x=100, y=200)
    hid = _to_vz_hid_event(ev)
    assert hid is not None
    assert hid["type"] == "pointer_move"


def test_to_vz_hid_event_text():
    from app.adapters.macos.input import _to_vz_hid_event
    from app.stream.source import InputEvent
    ev = InputEvent(kind="text", text="hello")
    hid = _to_vz_hid_event(ev)
    assert hid is not None
    assert hid["text"] == "hello"
