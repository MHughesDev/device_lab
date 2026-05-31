---
doc_id: "27.2"
title: "Building a DeviceAdapter"
section: "Adapters"
status: "current"
updated: "2026-05-31"
---

# Building a DeviceAdapter

This guide walks through creating a new device family adapter for DeviceLab.

---

## Step 1 — Create the adapter class

Create a new file at `apps/api/app/adapters/<family>/adapter.py`. Import from the SPI:

```python
from app.adapters.spi import (
    AdapterManifest, DeviceAdapter, DeviceCapabilities,
    CapabilityUnsupportedError, SPI_VERSION,
)

class MyFamilyAdapter(DeviceAdapter):
    @classmethod
    def manifest(cls) -> AdapterManifest:
        return AdapterManifest(
            spi_version=SPI_VERSION,
            adapter_version="1.0.0",
            family="my_family",
            display_name="My Family Device",
            capabilities=DeviceCapabilities(
                observe=["screenshot"],
                interact=["click"],
                streaming=False,
                snapshot=False,
            ),
            required_providers=["my_provider"],
        )
```

---

## Step 2 — Implement required methods

All four abstract methods must be implemented:

```python
    async def provision(self, device, template) -> dict:
        # Tag resources: DeviceLab:Workspace, DeviceLab:Device
        return {"resource_id": "...", "region": "..."}

    async def terminate(self, device) -> None:
        # Idempotent — must not raise if already terminated
        pass

    async def observe(self, device, tier: str) -> object:
        if tier not in self.manifest().capabilities.observe:
            raise CapabilityUnsupportedError(tier, "my_family")
        # Return ObservationEnvelope
        ...

    async def act(self, device, action: str, params: dict) -> object:
        if action not in self.manifest().capabilities.interact:
            raise CapabilityUnsupportedError(action, "my_family")
        # Return ActionResult
        ...
```

---

## Step 3 — Register the adapter

Add your adapter to the `register_adapters()` startup handler in `apps/api/app/main.py`:

```python
from app.adapters.my_family.adapter import MyFamilyAdapter

@app.on_event("startup")
async def register_adapters():
    AdapterRegistry.reset()
    AdapterRegistry.register(MyFamilyAdapter)
    # ... other adapters
```

---

## Step 4 — Write a FakeProvider for the conformance suite

See `docs/adapters/fake-provider.md`. Then add your adapter to the conformance test parametrize list in `tests/adapters/conformance/test_conformance.py`:

```python
from app.adapters.my_family.adapter import MyFamilyAdapter

_ALL_ADAPTERS = [LinuxAdapter, BrowserAdapter, MyFamilyAdapter]
```

---

## Step 5 — Run the conformance suite

```bash
uv run pytest tests/adapters/conformance/ -v
```

All six conformance tests must pass before the adapter is merged.

---

## Third-party entry point registration

For adapters distributed as separate packages, register via the `devicelab_adapter` entry point in `pyproject.toml`:

```toml
[project.entry-points."devicelab_adapter"]
my_family = "my_package.adapter:MyFamilyAdapter"
```

DeviceLab (when it supports entry points) will auto-discover and register adapters found under this entry point at startup.
