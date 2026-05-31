from __future__ import annotations

import json

from sqlmodel import Session

from app.adapters.aws.client import AWSClient
from app.models import BootstrapPlan, BootstrapPlanResource, CloudAccount

_ROLE_NAME = "DeviceLab-RuntimeAgent"
_SG_NAME = "DeviceLab-Default"

_TRUST_POLICY = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "ec2.amazonaws.com"},
        "Action": "sts:AssumeRole",
    }],
}

_INLINE_POLICIES = {
    "DeviceLabRuntimeAgent": {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "ssm:UpdateInstanceInformation",
                    "ssm:ListInstanceAssociations",
                    "ssmmessages:CreateControlChannel",
                    "ssmmessages:CreateDataChannel",
                    "ssmmessages:OpenControlChannel",
                    "ssmmessages:OpenDataChannel",
                    "ec2messages:AcknowledgeMessage",
                    "ec2messages:DeleteMessage",
                    "ec2messages:FailMessage",
                    "ec2messages:GetEndpoint",
                    "ec2messages:GetMessages",
                    "ec2messages:SendReply",
                    "s3:PutObject",
                    "s3:GetObject",
                    "s3:ListBucket",
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
                "Resource": "*",
            }
        ],
    }
}


def _make_client(account: CloudAccount) -> AWSClient:
    from app.adapters.aws.client import AWSClient
    return AWSClient(
        credential_source=account.credential_source,
        profile=account.credential_profile,
        role_arn=account.credential_role_arn,
        region=account.region,
    )


def plan_bootstrap(db: Session, account: CloudAccount) -> BootstrapPlan:
    identity = _make_client(account).caller_identity()
    acct_id = identity.get("Account", account.account_id)
    bucket_name = f"devicelab-artifacts-{acct_id}"

    resources = [
        BootstrapPlanResource(
            resource_type="iam_role",
            resource_id=_ROLE_NAME,
            action="create",
            estimated_cost="$0.00/month",
        ),
        BootstrapPlanResource(
            resource_type="security_group",
            resource_id=_SG_NAME,
            action="create",
            estimated_cost="$0.00/month",
        ),
        BootstrapPlanResource(
            resource_type="s3_bucket",
            resource_id=bucket_name,
            action="create",
            estimated_cost="~$0.02/GB/month",
        ),
    ]

    return BootstrapPlan(
        account_id=acct_id,
        region=account.region,
        resources=resources,
        total_estimated_cost="~$0.02/GB/month (S3 only)",
        requires_confirmation=True,
    )


def execute_bootstrap(db: Session, account: CloudAccount) -> dict:
    account.bootstrap_status = "in_progress"
    db.add(account)
    db.commit()

    client = _make_client(account)
    identity = client.caller_identity()
    acct_id = identity.get("Account", account.account_id)
    bucket_name = f"devicelab-artifacts-{acct_id}"

    results: dict[str, str] = {}
    try:
        role_arn = client.ensure_iam_role(_ROLE_NAME, _TRUST_POLICY, _INLINE_POLICIES)
        results["iam_role"] = role_arn

        sg_id = client.ensure_security_group(
            _SG_NAME,
            "DeviceLab default — no inbound, SSM egress only",
        )
        results["security_group"] = sg_id

        bucket = client.ensure_s3_bucket(bucket_name, acct_id, str(account.workspace_id))
        results["s3_bucket"] = bucket

        account.bootstrap_status = "complete"
        account.account_id = acct_id
        db.add(account)
        db.commit()

    except Exception as e:
        account.bootstrap_status = "failed"
        db.add(account)
        db.commit()
        raise RuntimeError(f"Bootstrap failed: {e}") from e

    return results
