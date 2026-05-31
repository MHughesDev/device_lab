import pytest
from app.adapters.spi import (
    AdapterManifest,
    CapabilityUnsupportedError,
    DeviceCapabilities,
    SPI_VERSION,
    SUPPORTED_SPI_VERSIONS,
)


def test_manifest_dataclass_fields():
    m = AdapterManifest(
        spi_version=SPI_VERSION,
        adapter_version="1.0.0",
        family="test",
        display_name="Test Adapter",
        capabilities=DeviceCapabilities(),
        required_providers=["aws_ec2"],
    )
    assert m.family == "test"
    assert m.spi_version == SPI_VERSION


def test_capabilities_defaults():
    caps = DeviceCapabilities()
    assert caps.observe == []
    assert caps.interact == []
    assert caps.network == []
    assert caps.streaming is False
    assert caps.snapshot is False
    assert caps.dangerous_actions == []


def test_capability_unsupported_error_message():
    err = CapabilityUnsupportedError("streaming", "browser")
    assert "streaming" in str(err)
    assert "browser" in str(err)
    assert err.capability == "streaming"
    assert err.family == "browser"


def test_supported_spi_versions_contains_current():
    assert SPI_VERSION in SUPPORTED_SPI_VERSIONS
