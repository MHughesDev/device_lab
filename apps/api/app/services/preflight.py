from __future__ import annotations

import json
from datetime import UTC, datetime

from sqlmodel import Session

from app.adapters.aws.client import (
    AWSAuthError,
    AWSCapacityError,
    AWSClient,
    AWSPermissionError,
    AWSRegionError,
    PolicyResult,
)
from app.models import CloudAccount, PreflightCheckResult, PreflightReport

REQUIRED_ACTIONS = [
    "ec2:RunInstances",
    "ec2:StopInstances",
    "ec2:TerminateInstances",
    "ec2:DescribeInstances",
    "ec2:DescribeInstanceTypes",
    "ec2:DescribeInstanceTypeOfferings",
    "ec2:CreateTags",
    "ssm:SendCommand",
    "ssm:GetCommandInvocation",
    "ssm:DescribeInstanceInformation",
    "s3:PutObject",
    "s3:GetObject",
    "pricing:GetProducts",
    "iam:CreateRole",
    "iam:PutRolePolicy",
    "iam:GetRole",
    "iam:PassRole",
]


def _make_client(account: CloudAccount) -> AWSClient:
    return AWSClient(
        credential_source=account.credential_source,
        profile=account.credential_profile,
        role_arn=account.credential_role_arn,
        region=account.region,
    )


def _check_caller_identity(client: AWSClient) -> PreflightCheckResult:
    try:
        identity = client.caller_identity()
        arn = identity.get("Arn", "unknown")
        return PreflightCheckResult(
            name="caller_identity",
            status="pass",
            severity="info",
            message=f"Authenticated as {arn}",
            evidence=json.dumps({"arn": arn, "account": identity.get("Account")}),
            retryable=True,
        )
    except AWSAuthError as e:
        return PreflightCheckResult(
            name="caller_identity",
            status="fail",
            severity="error",
            message=f"AWS authentication failed: {e}",
            remediation="Check AWS credentials are set correctly. For env source: export AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY.",
            retryable=True,
        )


def _check_required_permissions(client: AWSClient) -> PreflightCheckResult:
    try:
        results: list[PolicyResult] = client.simulate_policy(REQUIRED_ACTIONS, ["*"])
        denied = [r for r in results if r.decision != "allowed"]
        if not denied:
            return PreflightCheckResult(
                name="required_permissions",
                status="pass",
                severity="info",
                message=f"All {len(REQUIRED_ACTIONS)} required permissions granted",
                retryable=False,
            )
        denied_actions = [r.action for r in denied[:5]]
        return PreflightCheckResult(
            name="required_permissions",
            status="fail",
            severity="error",
            message=f"{len(denied)} required permissions denied: {', '.join(denied_actions)}{'...' if len(denied) > 5 else ''}",
            remediation="Attach DeviceLab IAM policy to your user/role. See docs/operations/aws-iam-policy.md.",
            evidence=json.dumps([{"action": r.action, "decision": r.decision} for r in denied]),
            retryable=False,
        )
    except AWSPermissionError as e:
        return PreflightCheckResult(
            name="required_permissions",
            status="warn",
            severity="warning",
            message=f"Could not simulate IAM policy (iam:SimulatePrincipalPolicy may be restricted): {e}",
            remediation="Manually verify your IAM user/role has the required permissions listed in docs/operations/aws-iam-policy.md.",
            retryable=False,
        )


def _check_region_availability(client: AWSClient, region: str) -> PreflightCheckResult:
    try:
        regions = client.list_regions()
        if region in regions:
            return PreflightCheckResult(
                name="region_availability",
                status="pass",
                severity="info",
                message=f"Region {region} is available",
                retryable=False,
            )
        return PreflightCheckResult(
            name="region_availability",
            status="fail",
            severity="error",
            message=f"Region {region} is not available in your account",
            remediation=f"Choose a different region. Available regions: {', '.join(regions[:5])}...",
            retryable=False,
        )
    except AWSRegionError as e:
        return PreflightCheckResult(
            name="region_availability",
            status="fail",
            severity="error",
            message=f"Could not list regions: {e}",
            remediation="Check EC2 permissions and connectivity.",
            retryable=True,
        )


def _check_ssm(client: AWSClient, region: str) -> PreflightCheckResult:
    available = client.check_ssm_availability(region)
    if available:
        return PreflightCheckResult(
            name="ssm_available",
            status="pass",
            severity="info",
            message=f"SSM endpoint reachable in {region}",
            retryable=False,
        )
    return PreflightCheckResult(
        name="ssm_available",
        status="fail",
        severity="error",
        message=f"SSM endpoint not reachable in {region}",
        remediation="Ensure your network can reach the SSM endpoint in this region, or choose a region with SSM support.",
        retryable=True,
    )


def _check_capacity(client: AWSClient, region: str) -> PreflightCheckResult:
    try:
        result = client.describe_ec2_capacity(region, "t3.micro")
        if result.available:
            return PreflightCheckResult(
                name="capacity_check",
                status="pass",
                severity="info",
                message=f"t3.micro available in {region}",
                retryable=False,
            )
        return PreflightCheckResult(
            name="capacity_check",
            status="warn",
            severity="warning",
            message=result.message,
            remediation="Try a different region or instance type.",
            retryable=True,
        )
    except AWSCapacityError as e:
        return PreflightCheckResult(
            name="capacity_check",
            status="warn",
            severity="warning",
            message=f"Could not verify capacity: {e}",
            retryable=True,
        )


def _check_service_quotas(client: AWSClient) -> PreflightCheckResult:
    quota = client.check_quota("ec2", "Running On-Demand Standard")
    if quota < 0:
        return PreflightCheckResult(
            name="service_quotas",
            status="warn",
            severity="warning",
            message="Could not retrieve EC2 running instance quota (service-quotas may be restricted)",
            remediation="Manually check your EC2 running instances quota in the AWS console.",
            retryable=False,
        )
    return PreflightCheckResult(
        name="service_quotas",
        status="pass",
        severity="info",
        message=f"EC2 running instance quota: {int(quota)} vCPUs",
        retryable=False,
    )


def run_preflight(db: Session, account: CloudAccount) -> PreflightReport:
    client = _make_client(account)

    checks: list[PreflightCheckResult] = []

    identity_check = _check_caller_identity(client)
    checks.append(identity_check)

    if identity_check.status != "fail":
        checks.append(_check_required_permissions(client))
        checks.append(_check_region_availability(client, account.region))
        checks.append(_check_ssm(client, account.region))
        checks.append(_check_capacity(client, account.region))
        checks.append(_check_service_quotas(client))
    else:
        for name in ["required_permissions", "region_availability", "ssm_available", "capacity_check", "service_quotas"]:
            checks.append(PreflightCheckResult(
                name=name,
                status="fail",
                severity="error",
                message="Skipped — authentication failed",
                retryable=True,
            ))

    any_fail = any(c.status == "fail" for c in checks)
    any_warn = any(c.status == "warn" for c in checks)
    overall = "fail" if any_fail else ("warn" if any_warn else "pass")

    # Update account
    account.last_preflight_at = datetime.now(UTC)
    account.status = "preflight_passed" if overall == "pass" else ("preflight_warned" if overall == "warn" else "preflight_failed")
    account.preflight_summary_json = json.dumps([c.model_dump() for c in checks])
    db.add(account)
    db.commit()
    db.refresh(account)

    return PreflightReport(status=overall, checks=checks)
