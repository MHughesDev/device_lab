import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from app.adapters.aws.client import AWSAuthError, AWSPermissionError
from app.models import CloudAccount, PreflightReport
from app.services import preflight


def _make_account(region: str = "us-east-1", source: str = "env") -> CloudAccount:
    return CloudAccount(
        id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        display_name="Test",
        provider="aws",
        account_id="",
        region=region,
        credential_source=source,
        status="pending_preflight",
        bootstrap_status="not_started",
    )


def _db_stub(account: CloudAccount) -> MagicMock:
    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock(side_effect=lambda x: None)
    return db


class TestPreflightChecks:
    def test_caller_identity_pass(self) -> None:
        client = MagicMock()
        client.caller_identity.return_value = {"Arn": "arn:aws:iam::123:user/test", "Account": "123"}
        result = preflight._check_caller_identity(client)
        assert result.status == "pass"

    def test_caller_identity_fail(self) -> None:
        client = MagicMock()
        client.caller_identity.side_effect = AWSAuthError("bad creds")
        result = preflight._check_caller_identity(client)
        assert result.status == "fail"
        assert result.retryable is True

    def test_required_permissions_all_allowed(self) -> None:
        from app.adapters.aws.client import PolicyResult
        client = MagicMock()
        client.caller_identity.return_value = {"Arn": "arn:aws:iam::123:user/test"}
        client.simulate_policy.return_value = [
            PolicyResult(action=a, resource="*", decision="allowed")
            for a in preflight.REQUIRED_ACTIONS
        ]
        result = preflight._check_required_permissions(client)
        assert result.status == "pass"

    def test_required_permissions_some_denied(self) -> None:
        from app.adapters.aws.client import PolicyResult
        client = MagicMock()
        client.caller_identity.return_value = {"Arn": "arn:aws:iam::123:user/test"}
        client.simulate_policy.return_value = [
            PolicyResult(action="ec2:RunInstances", resource="*", decision="explicitDeny"),
        ]
        result = preflight._check_required_permissions(client)
        assert result.status == "fail"
        assert "1" in result.message

    def test_required_permissions_iam_restricted(self) -> None:
        client = MagicMock()
        client.simulate_policy.side_effect = AWSPermissionError("not authorized")
        result = preflight._check_required_permissions(client)
        assert result.status == "warn"

    def test_region_availability_pass(self) -> None:
        client = MagicMock()
        client.list_regions.return_value = ["us-east-1", "us-west-2"]
        result = preflight._check_region_availability(client, "us-east-1")
        assert result.status == "pass"

    def test_region_availability_fail(self) -> None:
        client = MagicMock()
        client.list_regions.return_value = ["us-east-1", "us-west-2"]
        result = preflight._check_region_availability(client, "xx-fake-1")
        assert result.status == "fail"
        assert result.remediation != ""

    def test_capacity_check_pass(self) -> None:
        from app.adapters.aws.client import CapacityResult
        client = MagicMock()
        client.describe_ec2_capacity.return_value = CapacityResult("t3.micro", "us-east-1", True, "available")
        result = preflight._check_capacity(client, "us-east-1")
        assert result.status == "pass"

    def test_capacity_check_warn_unavailable(self) -> None:
        from app.adapters.aws.client import CapacityResult
        client = MagicMock()
        client.describe_ec2_capacity.return_value = CapacityResult("t3.micro", "us-east-1", False, "not offered")
        result = preflight._check_capacity(client, "us-east-1")
        assert result.status == "warn"


class TestRunPreflight:
    @patch("app.services.preflight._make_client")
    def test_run_preflight_all_pass(self, mock_make_client) -> None:
        from app.adapters.aws.client import CapacityResult, PolicyResult

        client = MagicMock()
        client.caller_identity.return_value = {"Arn": "arn:aws:iam::123:user/test", "Account": "123"}
        client.simulate_policy.return_value = [
            PolicyResult(a, "*", "allowed") for a in preflight.REQUIRED_ACTIONS
        ]
        client.list_regions.return_value = ["us-east-1"]
        client.check_ssm_availability.return_value = True
        client.describe_ec2_capacity.return_value = CapacityResult("t3.micro", "us-east-1", True, "ok")
        client.check_quota.return_value = 32.0
        mock_make_client.return_value = client

        account = _make_account()
        db = _db_stub(account)
        report = preflight.run_preflight(db, account)

        assert report.status == "pass"
        assert len(report.checks) == 6
        db.commit.assert_called()

    @patch("app.services.preflight._make_client")
    def test_run_preflight_auth_fail_skips_remaining(self, mock_make_client) -> None:
        client = MagicMock()
        client.caller_identity.side_effect = AWSAuthError("bad creds")
        mock_make_client.return_value = client

        account = _make_account()
        db = _db_stub(account)
        report = preflight.run_preflight(db, account)

        assert report.status == "fail"
        assert all(c.name != "caller_identity" or c.status == "fail" for c in report.checks)
        skipped = [c for c in report.checks if c.name != "caller_identity"]
        assert all(c.status == "fail" for c in skipped)
