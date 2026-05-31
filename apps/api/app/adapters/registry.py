# registry.py — AdapterRegistry: register, retrieve, and list device family adapters
from __future__ import annotations
from app.adapters.spi import AdapterManifest, DeviceAdapter, IncompatibleAdapterError, SUPPORTED_SPI_VERSIONS


class DuplicateAdapterError(Exception): ...


class AdapterRegistry:
    _adapters: dict[str, type[DeviceAdapter]] = {}

    @classmethod
    def register(cls, adapter_class: type[DeviceAdapter]) -> None:
        """Register an adapter class. Raises on version mismatch or duplicate family."""
        manifest = adapter_class.manifest()
        if manifest.spi_version not in SUPPORTED_SPI_VERSIONS:
            raise IncompatibleAdapterError(
                f"Adapter '{manifest.family}' declares spi_version='{manifest.spi_version}'; "
                f"supported: {sorted(SUPPORTED_SPI_VERSIONS)}"
            )
        if manifest.family in cls._adapters:
            raise DuplicateAdapterError(
                f"Adapter for family '{manifest.family}' is already registered"
            )
        cls._adapters[manifest.family] = adapter_class

    @classmethod
    def get(cls, family: str) -> type[DeviceAdapter]:
        """Return adapter class for family. Raises KeyError if not registered."""
        if family not in cls._adapters:
            raise KeyError(f"No adapter registered for family '{family}'")
        return cls._adapters[family]

    @classmethod
    def list_manifests(cls) -> list[AdapterManifest]:
        return [a.manifest() for a in cls._adapters.values()]

    @classmethod
    def reset(cls) -> None:
        """Clear all registrations. Use in tests only."""
        cls._adapters = {}
