from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from typing import Any

import boto3
from botocore.exceptions import ClientError


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Provision the CodeBuild-backed CI trigger for the CKD platform.")
    parser.add_argument("--region", default="ap-northeast-1")
    parser.add_argument("--bucket", default="ckd-automl-artifacts-junxiang")
    parser.add_argument("--source-key", default="ci/source/ckd-main-ci-source.zip")
    parser.add_argument("--project-name", default="CKD-CI-Build")
    parser.add_argument("--rule-name", default="CKD-CI-SourceBundle-Uploaded")
    parser.add_argument("--codebuild-role-name", default="CKDCodeBuildServiceRole")
    parser.add_argument("--events-role-name", default="CKDEventBridgeCodeBuildStartRole")
    return parser.parse_args()


def ensure_role(iam: Any, role_name: str, trust_policy: dict[str, Any], description: str) -> tuple[str, bool]:
    try:
        role = iam.get_role(RoleName=role_name)["Role"]
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


def ensure_codebuild_project(codebuild: Any, project_name: str, service_role_arn: str, bucket: str, source_key: str) -> dict[str, Any]:
    source_location = f"{bucket}/{source_key}"
    artifacts_path = "ci/build-artifacts"
    existing = codebuild.batch_get_projects(names=[project_name]).get("projects", [])
    kwargs = {
        "name": project_name,
        "description": "Repo-native CI build for the CKD thesis platform.",
        "serviceRole": service_role_arn,
        "source": {
            "type": "S3",
            "location": source_location,
            "buildspec": "infra/buildspec-ci.yml",
        },
        "artifacts": {
            "type": "S3",
            "location": bucket,
            "path": artifacts_path,
            "namespaceType": "BUILD_ID",
            "packaging": "ZIP",
            "name": "ci-output",
        },
        "environment": {
            "type": "LINUX_CONTAINER",
            "image": "aws/codebuild/standard:7.0",
            "computeType": "BUILD_GENERAL1_SMALL",
            "imagePullCredentialsType": "CODEBUILD",
            "privilegedMode": False,
        },
        "timeoutInMinutes": 30,
        "queuedTimeoutInMinutes": 30,
    }
    if existing:
        project = codebuild.update_project(**kwargs)["project"]
        created = False
    else:
        project = codebuild.create_project(**kwargs)["project"]
        created = True
    project["__created"] = created
    return project


def ensure_event_rule(events: Any, rule_name: str, bucket: str, source_key: str) -> str:
    pattern = {
        "source": ["ckd.platform.ci"],
        "detail-type": ["Source Bundle Uploaded"],
        "detail": {
            "bucket": [bucket],
            "key": [source_key],
        },
    }
    response = events.put_rule(
        Name=rule_name,
        EventPattern=json.dumps(pattern),
        State="ENABLED",
        Description="Trigger CKD CodeBuild CI when the repo-native CI source bundle upload event is emitted.",
    )
    return response["RuleArn"]


def ensure_event_target(events: Any, rule_name: str, project_arn: str, role_arn: str) -> dict[str, Any]:
    response = events.put_targets(
        Rule=rule_name,
        Targets=[
            {
                "Id": "codebuild-project",
                "Arn": project_arn,
                "RoleArn": role_arn,
            }
        ],
    )
    return response


def main() -> None:
    args = parse_args()
    iam = boto3.client("iam")
    codebuild = boto3.client("codebuild", region_name=args.region)
    events = boto3.client("events", region_name=args.region)
    sts = boto3.client("sts")
    account_id = sts.get_caller_identity()["Account"]

    codebuild_role_arn, codebuild_role_created = ensure_role(
        iam,
        args.codebuild_role_name,
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "codebuild.amazonaws.com"},
                    "Action": "sts:AssumeRole",
                }
            ],
        },
        "Service role for the CKD repo-native CodeBuild CI project.",
    )

    put_inline_policy(
        iam,
        args.codebuild_role_name,
        "CKDCodeBuildCIPolicy",
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "Logs",
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents",
                    ],
                    "Resource": "*",
                },
                {
                    "Sid": "ReadSourceBundle",
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetBucketLocation",
                        "s3:ListBucket",
                    ],
                    "Resource": f"arn:aws:s3:::{args.bucket}",
                    "Condition": {
                        "StringLike": {
                            "s3:prefix": [
                                "ci/source/*",
                                "artifacts/system_eval_aws/*",
                                "infra/*",
                                "backend/*",
                                "training/*",
                                "web/*",
                                "artifacts/autoprognosis_336/*",
                                "artifacts/model_registry/*",
                            ]
                        }
                    },
                },
                {
                    "Sid": "ReadAndWriteObjects",
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject",
                        "s3:PutObject",
                    ],
                    "Resource": [
                        f"arn:aws:s3:::{args.bucket}/ci/source/*",
                        f"arn:aws:s3:::{args.bucket}/ci/build-artifacts/*",
                    ],
                },
            ],
        },
    )

    project = ensure_codebuild_project(codebuild, args.project_name, codebuild_role_arn, args.bucket, args.source_key)

    events_role_arn, events_role_created = ensure_role(
        iam,
        args.events_role_name,
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "events.amazonaws.com"},
                    "Action": "sts:AssumeRole",
                }
            ],
        },
        "EventBridge role that starts the CKD CodeBuild CI project.",
    )

    put_inline_policy(
        iam,
        args.events_role_name,
        "CKDEventBridgeStartCodeBuildPolicy",
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "codebuild:StartBuild",
                    "Resource": project["arn"],
                }
            ],
        },
    )

    rule_arn = ensure_event_rule(events, args.rule_name, args.bucket, args.source_key)
    target_result = ensure_event_target(events, args.rule_name, project["arn"], events_role_arn)

    manifest = {
        "generated_at_utc": utc_now_iso(),
        "region": args.region,
        "bucket": args.bucket,
        "source_key": args.source_key,
        "account_id": account_id,
        "codebuild_role_arn": codebuild_role_arn,
        "codebuild_role_created": codebuild_role_created,
        "events_role_arn": events_role_arn,
        "events_role_created": events_role_created,
        "project_name": args.project_name,
        "project_arn": project["arn"],
        "project_created": project["__created"],
        "rule_name": args.rule_name,
        "rule_arn": rule_arn,
        "target_result": target_result,
    }
    print(json.dumps(manifest, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
