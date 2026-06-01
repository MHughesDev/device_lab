# factory.py — MediaSource / InputSink registry dispatched on (family, location) (Phase 09, task 09-01)
from __future__ import annotations

from app.stream.source import InputSink, MediaSource, NullInputSink, NullMediaSource

# Registry maps (family, location) → (MediaSource factory, InputSink factory)
_SOURCE_REGISTRY: dict[tuple[str, str], type[MediaSource]] = {}
_SINK_REGISTRY: dict[tuple[str, str], type[InputSink]] = {}


def register_source(family: str, location: str, cls: type[MediaSource]) -> None:
    _SOURCE_REGISTRY[(family, location)] = cls


def register_sink(family: str, location: str, cls: type[InputSink]) -> None:
    _SINK_REGISTRY[(family, location)] = cls


class UnknownMediaPair(KeyError):
    """Raised when no MediaSource/InputSink is registered for (family, location)."""


def media_source_for(device: object) -> MediaSource:
    """Resolve a MediaSource for the given device.

    Falls back to NullMediaSource if no implementation is registered yet
    (allows incremental roll-out of per-family sources without breaking headless devices).
    """
    family: str = getattr(device, "family", "")
    location: str = getattr(device, "location", "cloud")
    key = (family, location)
    cls = _SOURCE_REGISTRY.get(key)
    if cls is None:
        return NullMediaSource()
    return cls(device)  # type: ignore[call-arg]


def input_sink_for(device: object) -> InputSink:
    """Resolve an InputSink for the given device.

    Falls back to NullInputSink for unregistered pairs.
    """
    family: str = getattr(device, "family", "")
    location: str = getattr(device, "location", "cloud")
    key = (family, location)
    cls = _SINK_REGISTRY.get(key)
    if cls is None:
        return NullInputSink()
    return cls(device)  # type: ignore[call-arg]


def registered_pairs() -> list[tuple[str, str]]:
    """Return all registered (family, location) pairs (union of source + sink)."""
    return sorted(set(_SOURCE_REGISTRY) | set(_SINK_REGISTRY))


def _register_all() -> None:
    """Register all concrete MediaSource and InputSink implementations."""
    # Android local
    try:
        from app.adapters.android.stream_local import AndroidLocalMediaSource
        from app.adapters.android.input import AndroidInputSink
        register_source("android", "local", AndroidLocalMediaSource)
        register_sink("android", "local", AndroidInputSink)
    except ImportError:
        pass

    # Linux local
    try:
        from app.adapters.linux.stream_local import LinuxLocalMediaSource
        from app.adapters.linux.input import LinuxInputSink
        register_source("linux", "local", LinuxLocalMediaSource)
        register_sink("linux", "local", LinuxInputSink)
    except ImportError:
        pass

    # Windows local
    try:
        from app.adapters.windows.stream_local import WindowsLocalMediaSource
        from app.adapters.windows.input import WindowsInputSink
        register_source("windows", "local", WindowsLocalMediaSource)
        register_sink("windows", "local", WindowsInputSink)
    except ImportError:
        pass

    # macOS local
    try:
        from app.adapters.macos.stream_local import MacosLocalMediaSource
        from app.adapters.macos.input import MacosInputSink
        register_source("macos", "local", MacosLocalMediaSource)
        register_sink("macos", "local", MacosInputSink)
    except ImportError:
        pass

    # iOS Simulator local
    try:
        from app.adapters.ios_sim.stream_local import IosSimMediaSource
        from app.adapters.ios_sim.input import IosSimInputSink
        register_source("ios_sim", "local", IosSimMediaSource)
        register_sink("ios_sim", "local", IosSimInputSink)
    except ImportError:
        pass


_register_all()
