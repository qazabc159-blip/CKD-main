from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import boto3
from botocore.exceptions import ClientError


DEFAULT_REGION = "ap-northeast-1"
DEFAULT_BUCKET = "ckd-automl-artifacts-junxiang"
DEFAULT_ROLE_NAME = "CKDGitHubActionsCIBridgeRole"
DEFAULT_REPO = "qazabc159-blip/CKD"
DEFAULT_THUMBPRINT = "6938fd4d98bab03faadb97b34396831e3780aea1"
DEFAULT_PROVIDER_URL = "https://token.actions.githubusercontent.com"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = PROJECT_ROOT / "artifacts" / "system_eval_aws" / "github_actions_oidc_bridge_manifest.json"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ensure the GitHub Actions OIDC role used to bridge GitHub events into AWS CI.")
    parser.add_argument("--region", default=DEFAULT_REGION)
    parser.add_argument("--bucket", default=DEFAULT_BUCKET)
    parser.add_argument("--role-name", default=DEFAULT_ROLE_NAME)
    parser.add_argument("--repo", default=DEFAULT_REPO, help="GitHub repository in owner/name form.")
    parser.add_argument("--branch", default="main", help="GitHub branch allowed to assume the bridge role.")
    return parser.parse_args()


def ensure_oidc_provider(iam: Any) -> tuple[str, bool]:
    providers = iam.list_open_id_connect_providers()["OpenIDConnectProviderList"]
    for provider in providers:
        arn = provider["Arn"]
        details = iam.get_open_id_connect_provider(OpenIDConnectProviderArn=arn)
        if details.get("Url") in {"token.actions.githubusercontent.com", DEFAULT_PROVIDER_URL}:
            return arn, False

    created = iam.create_open_id_connect_provider(
        Url=DEFAULT_PROVIDER_URL,
        ClientIDList=["sts.amazonaws.com"],
        ThumbprintList=[DEFAULT_THUMBPRINT],
    )
    return created["OpenIDConnectProviderArn"], True


def ensure_role(iam: Any, role_name: str, trust_policy: dict[str, Any], description: str) -> tuple[str, bool]:
    try:
        role = iam.get_role(RoleName=role_name)["Role"]
        iam.update_assume_role_policy(RoleName=role_name, PolicyDocument=json.dumps(trust_policy))
        return role["Arn"], False
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") != "NoSuchEntity":
            raise

    role = iam.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps(trust_policy),
        Description=description,
    )["Role"]
    time.sleep(10)
    return role["Arn"], True


def put_inline_policy(iam: Any, role_name: str, policy_name: str, document: dict[str, Any]) -> None:
    iam.put_role_policy(RoleName=role_name, PolicyName=policy_name, PolicyDocument=json.dumps(document))


def main() -> None:
    args = parse_args()
    iam = boto3.client("iam")
    sts = boto3.client("sts")
    account_id = sts.get_caller_identity()["Account"]

    provider_arn, provider_created = ensure_oidc_provider(iam)

    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Federated": provider_arn},
                "Action": "sts:AssumeRoleWithWebIdentity",
                "Condition": {
                    "StringEquals": {
                        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
                    },
                    "StringLike": {
                        "token.actions.githubusercontent.com:sub": f"repo:{args.repo}:ref:refs/heads/{args.branch}",
                    },
                },
            }
        ],
    }

    role_arn, role_created = ensure_role(
        iam,
        args.role_name,
        trust_policy,
        "OIDC bridge role for GitHub Actions to upload CI source bundles and emit EventBridge events.",
    )

    put_inline_policy(
        iam,
        args.role_name,
        "CKDGitHubActionsCIBridgePolicy",
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "BucketMetadata",
                    "Effect": "Allow",
                    "Action": ["s3:GetBucketLocation", "s3:ListBucket", "s3:ListBucketMultipartUploads"],
                    "Resource": f"arn:aws:s3:::{args.bucket}",
                },
                {
                    "Sid": "WriteSourceBundle",
                    "Effect": "Allow",
                    "Action": ["s3:PutObject", "s3:GetObject", "s3:AbortMultipartUpload"],
                    "Resource": f"arn:aws:s3:::{args.bucket}/ci/source/*",
                },
                {
                    "Sid": "EmitCiEvent",
                    "Effect": "Allow",
                    "Action": "events:PutEvents",
                    "Resource": f"arn:aws:events:{args.region}:{account_id}:event-bus/default",
                },
            ],
        },
    )

    manifest = {
        "generated_at_utc": utc_now_iso(),
        "region": args.region,
        "bucket": args.bucket,
        "repo": args.repo,
        "branch": args.branch,
        "account_id": account_id,
        "oidc_provider_arn": provider_arn,
        "oidc_provider_created": provider_created,
        "role_name": args.role_name,
        "role_arn": role_arn,
        "role_created": role_created,
        "assume_role_subject": f"repo:{args.repo}:ref:refs/heads/{args.branch}",
    }
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=True), encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
