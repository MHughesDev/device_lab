from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import boto3
import botocore.exceptions


class AWSProviderError(Exception):
    """Base for all typed AWS adapter errors."""
    def __init__(self, message: str, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


class AWSAuthError(AWSProviderError): ...
class AWSPermissionError(AWSProviderError): ...
class AWSQuotaError(AWSProviderError): ...
class AWSRegionError(AWSProviderError): ...
class AWSCapacityError(AWSProviderError): ...


@dataclass
class PolicyResult:
    action: str
    resource: str
    decision: str  # "allowed" | "implicitDeny" | "explicitDeny"


@dataclass
class CapacityResult:
    instance_type: str
    region: str
    available: bool
    message: str


class AWSClient:
    def __init__(
        self,
        credential_source: str = "env",
        profile: str | None = None,
        role_arn: str | None = None,
        region: str = "us-east-1",
    ) -> None:
        self._region = region
        try:
            if credential_source == "profile" and profile:
                self._session = boto3.Session(profile_name=profile, region_name=region)
            elif credential_source == "role" and role_arn:
                base = boto3.Session(region_name=region)
                sts = base.client("sts")
                assumed = sts.assume_role(
                    RoleArn=role_arn,
                    RoleSessionName="DeviceLabSession",
                )
                creds = assumed["Credentials"]
                self._session = boto3.Session(
                    aws_access_key_id=creds["AccessKeyId"],
                    aws_secret_access_key=creds["SecretAccessKey"],
                    aws_session_token=creds["SessionToken"],
                    region_name=region,
                )
            else:
                self._session = boto3.Session(region_name=region)
        except botocore.exceptions.BotoCoreError as e:
            raise AWSAuthError(str(e)) from e

    def _client(self, service: str) -> Any:
        return self._session.client(service, region_name=self._region)

    def caller_identity(self) -> dict:
        try:
            return self._client("sts").get_caller_identity()
        except botocore.exceptions.ClientError as e:
            raise AWSAuthError(str(e)) from e

    def list_regions(self) -> list[str]:
        try:
            resp = self._client("ec2").describe_regions(AllRegions=False)
            return [r["RegionName"] for r in resp["Regions"]]
        except botocore.exceptions.ClientError as e:
            raise AWSRegionError(str(e)) from e

    def simulate_policy(
        self, actions: list[str], resources: list[str]
    ) -> list[PolicyResult]:
        try:
            iam = self._client("iam")
            identity = self.caller_identity()
            arn = identity["Arn"]
            resp = iam.simulate_principal_policy(
                PolicySourceArn=arn,
                ActionNames=actions,
                ResourceArns=resources,
            )
            return [
                PolicyResult(
                    action=r["EvalActionName"],
                    resource=r["EvalResourceName"],
                    decision=r["EvalDecision"],
                )
                for r in resp["EvaluationResults"]
            ]
        except botocore.exceptions.ClientError as e:
            raise AWSPermissionError(str(e)) from e

    def check_ssm_availability(self, region: str) -> bool:
        try:
            self._session.client("ssm", region_name=region).describe_instance_information(MaxResults=1)
            return True
        except botocore.exceptions.EndpointResolutionError:
            return False
        except botocore.exceptions.ClientError:
            return True  # auth error means endpoint exists

    def describe_ec2_capacity(self, region: str, instance_type: str) -> CapacityResult:
        try:
            ec2 = self._session.client("ec2", region_name=region)
            resp = ec2.describe_instance_type_offerings(
                LocationType="region",
                Filters=[
                    {"Name": "instance-type", "Values": [instance_type]},
                    {"Name": "location", "Values": [region]},
                ],
            )
            available = len(resp.get("InstanceTypeOfferings", [])) > 0
            return CapacityResult(
                instance_type=instance_type,
                region=region,
                available=available,
                message="available" if available else f"{instance_type} not offered in {region}",
            )
        except botocore.exceptions.ClientError as e:
            raise AWSCapacityError(str(e)) from e

    def check_quota(self, service_code: str, quota_name: str) -> float:
        try:
            sq = self._client("service-quotas")
            paginator = sq.get_paginator("list_service_quotas")
            for page in paginator.paginate(ServiceCode=service_code):
                for q in page["Quotas"]:
                    if quota_name.lower() in q["QuotaName"].lower():
                        return float(q["Value"])
            return -1.0
        except botocore.exceptions.ClientError:
            return -1.0

    def get_on_demand_price(self, region: str, instance_type: str) -> Decimal:
        """Return hourly on-demand USD price. Returns 0 on any error."""
        try:
            import awspricing  # type: ignore[import]
            offer = awspricing.offer("AmazonEC2")
            price = offer.ondemand_price(
                instance_type=instance_type,
                region=region,
                operating_system="Linux",
                tenancy="Shared",
            )
            return Decimal(str(price))
        except Exception:
            return Decimal("0")

    def ensure_iam_role(self, role_name: str, trust_policy: dict, inline_policies: dict[str, dict]) -> str:
        iam = self._client("iam")
        try:
            resp = iam.get_role(RoleName=role_name)
            return resp["Role"]["Arn"]
        except iam.exceptions.NoSuchEntityException:
            pass
        resp = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Tags=[{"Key": "DeviceLab:ManagedBy", "Value": "devicelab"}],
        )
        role_arn: str = resp["Role"]["Arn"]
        for policy_name, policy_doc in inline_policies.items():
            iam.put_role_policy(
                RoleName=role_name,
                PolicyName=policy_name,
                PolicyDocument=json.dumps(policy_doc),
            )
        return role_arn

    def ensure_security_group(self, name: str, description: str, vpc_id: str | None = None) -> str:
        ec2 = self._client("ec2")
        filters = [{"Name": "group-name", "Values": [name]}]
        if vpc_id:
            filters.append({"Name": "vpc-id", "Values": [vpc_id]})
        existing = ec2.describe_security_groups(Filters=filters)["SecurityGroups"]
        if existing:
            return str(existing[0]["GroupId"])
        kwargs: dict[str, Any] = {"GroupName": name, "Description": description}
        if vpc_id:
            kwargs["VpcId"] = vpc_id
        resp = ec2.create_security_group(**kwargs)
        sg_id = resp["GroupId"]
        ec2.revoke_security_group_ingress(GroupId=sg_id, IpPermissions=[])
        ec2.create_tags(
            Resources=[sg_id],
            Tags=[{"Key": "DeviceLab:ManagedBy", "Value": "devicelab"}],
        )
        return str(sg_id)

    def ensure_s3_bucket(self, bucket_name: str, account_id: str, workspace_id: str) -> str:
        s3 = self._client("s3")
        try:
            s3.head_bucket(Bucket=bucket_name)
            return bucket_name
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] not in ("404", "NoSuchBucket"):
                raise
        kwargs: dict[str, Any] = {"Bucket": bucket_name}
        if self._region != "us-east-1":
            kwargs["CreateBucketConfiguration"] = {"LocationConstraint": self._region}
        s3.create_bucket(**kwargs)
        s3.put_bucket_lifecycle_configuration(
            Bucket=bucket_name,
            LifecycleConfiguration={
                "Rules": [{
                    "ID": "expire-artifacts-90d",
                    "Status": "Enabled",
                    "Expiration": {"Days": 90},
                    "Filter": {"Prefix": "artifacts/"},
                }]
            },
        )
        s3.put_bucket_tagging(
            Bucket=bucket_name,
            Tagging={"TagSet": [
                {"Key": "DeviceLab:ManagedBy", "Value": "devicelab"},
                {"Key": "DeviceLab:Workspace", "Value": workspace_id},
            ]},
        )
        return bucket_name

    def run_instance(
        self,
        image_id: str,
        instance_type: str,
        iam_instance_profile_arn: str,
        security_group_id: str,
        tags: dict[str, str],
        user_data: str = "",
    ) -> str:
        ec2 = self._client("ec2")
        tag_specs = [
            {
                "ResourceType": "instance",
                "Tags": [{"Key": k, "Value": v} for k, v in tags.items()],
            }
        ]
        resp = ec2.run_instances(
            ImageId=image_id,
            InstanceType=instance_type,
            MinCount=1,
            MaxCount=1,
            IamInstanceProfile={"Arn": iam_instance_profile_arn},
            SecurityGroupIds=[security_group_id],
            UserData=user_data,
            TagSpecifications=tag_specs,
        )
        return str(resp["Instances"][0]["InstanceId"])

    def wait_for_instance_running(self, instance_id: str) -> None:
        ec2 = self._client("ec2")
        waiter = ec2.get_waiter("instance_running")
        waiter.wait(InstanceIds=[instance_id])

    def send_ssm_command(self, instance_id: str, commands: list[str]) -> str:
        ssm = self._client("ssm")
        resp = ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={"commands": commands},
        )
        return str(resp["Command"]["CommandId"])

    def terminate_instance(self, instance_id: str) -> None:
        ec2 = self._client("ec2")
        ec2.terminate_instances(InstanceIds=[instance_id])
