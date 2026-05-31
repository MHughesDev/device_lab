import pytest
from app.adapters.registry import AdapterRegistry, DuplicateAdapterError
from app.adapters.spi import (
    AdapterManifest,
    DeviceAdapter,
    DeviceCapabilities,
    IncompatibleAdapterError,
    SPI_VERSION,
)


def _make_adapter(family: str, spi_version: str = SPI_VERSION) -> type[DeviceAdapter]:
    class _Adapter(DeviceAdapter):
        @classmethod
        def manifest(cls) -> AdapterManifest:
            return AdapterManifest(
                spi_version=spi_version,
                adapter_version="1.0.0",
                family=family,
                display_name=f"{family} adapter",
                capabilities=DeviceCapabilities(),
                required_providers=[],
            )
        async def provision(self, device, template): return {}
        async def terminate(self, device): pass
        async def observe(self, device, tier): return None
        async def act(self, device, action, params): return {}
    _Adapter.__name__ = f"{family}Adapter"
    return _Adapter


def test_register_and_get():
    AdapterRegistry.reset()
    Cls = _make_adapter("fake_linux")
    AdapterRegistry.register(Cls)
    assert AdapterRegistry.get("fake_linux") is Cls


def test_get_unknown_raises_keyerror():
    AdapterRegistry.reset()
    with pytest.raises(KeyError):
        AdapterRegistry.get("does_not_exist")


def test_duplicate_raises():
    AdapterRegistry.reset()
    Cls = _make_adapter("dupe")
    AdapterRegistry.register(Cls)
    with pytest.raises(DuplicateAdapterError):
        AdapterRegistry.register(Cls)


def test_incompatible_version_raises():
    AdapterRegistry.reset()
    Cls = _make_adapter("badver", spi_version="99.0")
    with pytest.raises(IncompatibleAdapterError):
        AdapterRegistry.register(Cls)


def test_list_manifests_returns_all():
    AdapterRegistry.reset()
    for fam in ["a", "b", "c"]:
        AdapterRegistry.register(_make_adapter(fam))
    assert len(AdapterRegistry.list_manifests()) == 3


def test_reset_clears_registry():
    AdapterRegistry.reset()
    AdapterRegistry.register(_make_adapter("temp"))
    AdapterRegistry.reset()
    with pytest.raises(KeyError):
        AdapterRegistry.get("temp")
