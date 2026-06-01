# fixtures.py — Conformance test fixtures: FakeDevice, FakeTemplate, fake_boto_session
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal
from unittest.mock import MagicMock


@dataclass
class FakeDevice:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    workspace_id: uuid.UUID = field(default_factory=uuid.uuid4)
    family: str = "linux"
    location: str = "cloud"
    state: str = "ready"
    screen_version: int = 0
    provider_ids_json: str = '{"instance_id": "i-fake", "region": "us-east-1"}'
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class FakeLocalDevice:
    """FakeDevice pre-set for location=local with a Docker container_id."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    workspace_id: uuid.UUID = field(default_factory=uuid.uuid4)
    family: str = "linux"
    location: str = "local"
    state: str = "ready"
    screen_version: int = 0
    provider_ids_json: str = '{"container_id": "fake-container-id"}'
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class FakeTemplate:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    name: str = "fake-template"
    family: str = "linux"
    project_arn: str = "arn:aws:devicefarm:us-west-2:123456789012:project:EXAMPLE"
    device_arn: str = "arn:aws:devicefarm:us-west-2::device:EXAMPLE"


def fake_boto_session() -> MagicMock:
    """Return a mock satisfying the boto3.Session interface."""
    mock = MagicMock()
    ec2 = MagicMock()
    ssm = MagicMock()
    ec2.run_instances.return_value = {"Instances": [{"InstanceId": "i-fake123"}]}
    ec2.terminate_instances.return_value = {}
    ec2.describe_images.return_value = {
        "Images": [{"ImageId": "ami-fake", "CreationDate": "2026-01-01T00:00:00.000Z"}]
    }
    ec2.allocate_hosts.return_value = {"HostIds": ["h-fake"]}
    ssm.send_command.return_value = {"Command": {"CommandId": "cmd-fake"}}
    ssm.get_command_invocation.return_value = {
        "Status": "Success",
        "StandardOutputContent": "{}",
    }
    mock.client.side_effect = lambda service, **kwargs: ec2 if service == "ec2" else ssm
    return mock
