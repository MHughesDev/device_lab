# test_conformance.py — Parametrized conformance tests for all DeviceAdapter implementations
import pytest

from app.adapters.spi import (
    SUPPORTED_SPI_VERSIONS,
    CapabilityUnsupportedError,
    DeviceCapabilities,
)
from app.adapters.linux.adapter import LinuxAdapter
from app.adapters.browser.adapter import BrowserAdapter
from tests.adapters.conformance.fixtures import FakeDevice, FakeTemplate

_ALL_ADAPTERS = [LinuxAdapter, BrowserAdapter]


@pytest.mark.parametrize("adapter_class", _ALL_ADAPTERS)
def test_manifest_valid(adapter_class):
    m = adapter_class.manifest()
    assert m.spi_version in SUPPORTED_SPI_VERSIONS
    assert isinstance(m.family, str) and m.family
    assert isinstance(m.capabilities, DeviceCapabilities)


@pytest.mark.parametrize("adapter_class", _ALL_ADAPTERS)
def test_manifest_family_matches_register(adapter_class):
    from app.adapters.registry import AdapterRegistry
    AdapterRegistry.reset()
    AdapterRegistry.register(adapter_class)
    m = adapter_class.manifest()
    assert AdapterRegistry.get(m.family) is adapter_class
    AdapterRegistry.reset()


@pytest.mark.parametrize("adapter_class", _ALL_ADAPTERS)
@pytest.mark.asyncio
async def test_observe_unsupported_tier_raises(adapter_class):
    adapter = object.__new__(adapter_class)
    device = FakeDevice(family=adapter_class.manifest().family)
    with pytest.raises(CapabilityUnsupportedError):
        await adapter.observe(device, "vlm_unsupported_tier_xyz")


@pytest.mark.parametrize("adapter_class", _ALL_ADAPTERS)
@pytest.mark.asyncio
async def test_act_unsupported_action_raises(adapter_class):
    adapter = object.__new__(adapter_class)
    device = FakeDevice(family=adapter_class.manifest().family)
    with pytest.raises(CapabilityUnsupportedError):
        await adapter.act(device, "unsupported_action_xyz", {})


@pytest.mark.parametrize("adapter_class", [BrowserAdapter])
@pytest.mark.asyncio
async def test_snapshot_unsupported_raises(adapter_class):
    """Adapters with snapshot=False should raise CapabilityUnsupportedError."""
    adapter = object.__new__(adapter_class)
    device = FakeDevice(family=adapter_class.manifest().family)
    assert not adapter_class.manifest().capabilities.snapshot
    with pytest.raises(CapabilityUnsupportedError):
        await adapter.snapshot(device)


@pytest.mark.parametrize("adapter_class", _ALL_ADAPTERS)
@pytest.mark.asyncio
async def test_capability_unsupported_error_type(adapter_class):
    """Unsupported capabilities must always raise CapabilityUnsupportedError, not NotImplementedError."""
    adapter = object.__new__(adapter_class)
    device = FakeDevice(family=adapter_class.manifest().family)
    raised = None
    try:
        await adapter.observe(device, "vlm_unsupported_tier_xyz")
    except CapabilityUnsupportedError as e:
        raised = e
    except NotImplementedError:
        pytest.fail("Adapter raised NotImplementedError instead of CapabilityUnsupportedError")
    assert isinstance(raised, CapabilityUnsupportedError)
