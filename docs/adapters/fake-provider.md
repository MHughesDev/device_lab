---
doc_id: "27.3"
title: "Fake provider fixtures for adapter conformance tests"
section: "Adapters"
status: "current"
updated: "2026-05-31"
---

# Fake Provider Fixtures

Use these fixtures to run the conformance suite against your adapter without real AWS calls.

---

## FakeDevice and FakeTemplate

Defined in `tests/adapters/conformance/fixtures.py`:

```python
@dataclass
class FakeDevice:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    workspace_id: uuid.UUID = field(default_factory=uuid.uuid4)
    family: str = "linux"
    state: str = "ready"
    screen_version: int = 0
    provider_ids_json: str = '{"instance_id": "i-fake", "region": "us-east-1"}'

@dataclass
class FakeTemplate:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    name: str = "fake-template"
    family: str = "linux"
    project_arn: str = "arn:aws:devicefarm:..."
    device_arn: str = "arn:aws:devicefarm:..."
```

Set `family` and `provider_ids_json` to match your adapter's expected format.

---

## Mocking boto3 for AWS-backed adapters

Use `fake_boto_session()` from `fixtures.py`, or build your own:

```python
from unittest.mock import MagicMock
from tests.adapters.conformance.fixtures import fake_boto_session

mock_boto = fake_boto_session()

# The mock satisfies boto3.client("ec2") and boto3.client("ssm")
# Patch boto3 at the adapter's import point:
with patch("boto3.client", side_effect=mock_boto.client):
    result = await adapter.provision(device, template)
```

---

## Mocking adb subprocess calls for Android adapters

```python
from unittest.mock import patch, MagicMock

mock_proc = MagicMock()
mock_proc.stdout = b""

with patch("subprocess.run", return_value=MagicMock(returncode=0)):
    with patch("uiautomator2.connect", return_value=MagicMock()):
        result = await android_adapter.observe(device, "screenshot")
```

---

## Example conformance test parametrize pattern

```python
import pytest
from app.adapters.linux.adapter import LinuxAdapter
from app.adapters.my_family.adapter import MyFamilyAdapter

@pytest.mark.parametrize("adapter_class", [LinuxAdapter, MyFamilyAdapter])
def test_manifest_valid(adapter_class):
    from app.adapters.spi import SUPPORTED_SPI_VERSIONS, DeviceCapabilities
    m = adapter_class.manifest()
    assert m.spi_version in SUPPORTED_SPI_VERSIONS
    assert isinstance(m.family, str) and m.family
    assert isinstance(m.capabilities, DeviceCapabilities)
```
