import argparse
import json
import time

import boto3
from botocore.exceptions import ClientError


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ensure that a SageMaker execution role exists for the CKD platform.")
    parser.add_argument("--role-name", default="CKDSageMakerExecutionRole")
    parser.add_argument("--artifact-bucket", default="ckd-automl-artifacts-junxiang")
    parser.add_argument("--artifact-prefix", default="sagemaker-training")
    return parser.parse_args()


def trust_policy() -> dict:
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "sagemaker.amazonaws.com"},
                "Action": "sts:AssumeRole",
            }
        ],
    }


def inline_policy(bucket_name: str, artifact_prefix: str) -> dict:
    normalized_prefix = artifact_prefix.strip("/").rstrip("/") + "/"
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "ListCkdTrainingPrefix",
                "Effect": "Allow",
                "Action": [
                    "s3:GetBucketLocation",
                    "s3:ListBucket",
                ],
                "Resource": [
                    f"arn:aws:s3:::{bucket_name}",
                ],
                "Condition": {
                    "StringLike": {
                        "s3:prefix": [
                            normalized_prefix,
                            f"{normalized_prefix}*",
                        ]
                    }
                },
            },
            {
                "Sid": "ObjectAccessForCkdTrainingPrefix",
                "Effect": "Allow",
                "Action": [
                    "s3:AbortMultipartUpload",
                    "s3:GetObject",
                    "s3:PutObject",
                ],
                "Resource": [
                    f"arn:aws:s3:::{bucket_name}/{normalized_prefix}*",
                ],
            },
            {
                "Sid": "CloudWatchLogsForSageMaker",
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:DescribeLogStreams",
                    "logs:PutLogEvents",
                ],
                "Resource": "arn:aws:logs:*:*:log-group:/aws/sagemaker/*",
            },
        ],
    }


def main() -> None:
    args = parse_args()
    iam = boto3.client("iam")
    role_name = args.role_name

    try:
        response = iam.get_role(RoleName=role_name)
        role_arn = response["Role"]["Arn"]
        created = False
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") != "NoSuchEntity":
            raise
        response = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy()),
            Description="Prototype SageMaker execution role for the CKD thesis platform.",
        )
        role_arn = response["Role"]["Arn"]
        created = True

    iam.attach_role_policy(
        RoleName=role_name,
        PolicyArn="arn:aws:iam::aws:policy/AmazonSageMakerFullAccess",
    )

    iam.put_role_policy(
        RoleName=role_name,
        PolicyName="CKDSageMakerArtifactBucketAccess",
        PolicyDocument=json.dumps(inline_policy(args.artifact_bucket, args.artifact_prefix)),
    )

    attached_policies = iam.list_attached_role_policies(RoleName=role_name).get("AttachedPolicies", [])
    for policy in attached_policies:
        if policy.get("PolicyArn") == "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess":
            iam.detach_role_policy(RoleName=role_name, PolicyArn=policy["PolicyArn"])

    if created:
        time.sleep(10)

    print(
        json.dumps(
            {
                "role_name": role_name,
                "role_arn": role_arn,
                "created": created,
                "artifact_bucket": args.artifact_bucket,
                "artifact_prefix": args.artifact_prefix,
                "managed_policy_detached": True,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
