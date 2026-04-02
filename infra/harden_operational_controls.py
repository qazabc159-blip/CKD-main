import argparse
import json
from datetime import datetime, timezone

import boto3


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Harden operational controls for the CKD AWS platform.")
    parser.add_argument("--stack-name", default="ckd-inference-stack")
    parser.add_argument("--region", default="ap-northeast-1")
    parser.add_argument("--alert-topic-name", default="CKD-Operational-Alerts")
    parser.add_argument("--alert-email", default="")
    parser.add_argument("--log-retention-days", type=int, default=30)
    return parser.parse_args()


def ensure_topic(sns_client, topic_name: str) -> str:
    response = sns_client.create_topic(Name=topic_name)
    return response["TopicArn"]


def ensure_topic_policy(sns_client, topic_arn: str, account_id: str) -> None:
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AllowCloudWatchPublish",
                "Effect": "Allow",
                "Principal": {"Service": "cloudwatch.amazonaws.com"},
                "Action": "sns:Publish",
                "Resource": topic_arn,
                "Condition": {
                    "StringEquals": {
                        "AWS:SourceOwner": account_id
                    }
                },
            },
        ],
    }
    sns_client.set_topic_attributes(
        TopicArn=topic_arn,
        AttributeName="Policy",
        AttributeValue=json.dumps(policy),
    )


def ensure_email_subscription(sns_client, topic_arn: str, email: str) -> str | None:
    if not email:
        return None
    paginator = sns_client.get_paginator("list_subscriptions_by_topic")
    for page in paginator.paginate(TopicArn=topic_arn):
        for sub in page.get("Subscriptions", []):
            if sub.get("Protocol") == "email" and sub.get("Endpoint") == email:
                return sub.get("SubscriptionArn")
    response = sns_client.subscribe(
        TopicArn=topic_arn,
        Protocol="email",
        Endpoint=email,
        ReturnSubscriptionArn=True,
    )
    return response.get("SubscriptionArn")


def ensure_alarm(cloudwatch_client, alarm_name: str, alarm_kwargs: dict) -> None:
    cloudwatch_client.put_metric_alarm(AlarmName=alarm_name, **alarm_kwargs)


def main() -> None:
    args = parse_args()
    region = args.region

    session = boto3.session.Session(region_name=region)
    cloudformation = session.client("cloudformation")
    cloudwatch = session.client("cloudwatch")
    logs_client = session.client("logs")
    sns_client = session.client("sns")
    sts = session.client("sts")

    account_id = sts.get_caller_identity()["Account"]
    stack_resources = cloudformation.describe_stack_resources(StackName=args.stack_name)["StackResources"]
    resource_by_type = {item["ResourceType"]: item for item in stack_resources}

    lambda_function_name = resource_by_type["AWS::Lambda::Function"]["PhysicalResourceId"]
    api_id = resource_by_type["AWS::ApiGatewayV2::Api"]["PhysicalResourceId"]
    stage_name = next(
        item["PhysicalResourceId"] for item in stack_resources if item["ResourceType"] == "AWS::ApiGatewayV2::Stage"
    )

    log_group_name = f"/aws/lambda/{lambda_function_name}"
    logs_client.put_retention_policy(logGroupName=log_group_name, retentionInDays=args.log_retention_days)

    topic_arn = ensure_topic(sns_client, args.alert_topic_name)
    ensure_topic_policy(sns_client, topic_arn, account_id)
    subscription_arn = ensure_email_subscription(sns_client, topic_arn, args.alert_email)

    alarm_actions = [topic_arn]

    ensure_alarm(
        cloudwatch,
        "CKD-Lambda-Errors-Any",
        {
            "AlarmDescription": "Triggers when the CKD inference Lambda records any error in a 1-minute period.",
            "ActionsEnabled": True,
            "AlarmActions": alarm_actions,
            "MetricName": "Errors",
            "Namespace": "AWS/Lambda",
            "Statistic": "Sum",
            "Dimensions": [{"Name": "FunctionName", "Value": lambda_function_name}],
            "Period": 60,
            "EvaluationPeriods": 1,
            "DatapointsToAlarm": 1,
            "Threshold": 1.0,
            "ComparisonOperator": "GreaterThanOrEqualToThreshold",
            "TreatMissingData": "notBreaching",
        },
    )

    ensure_alarm(
        cloudwatch,
        "CKD-Lambda-Duration-p95-High",
        {
            "AlarmDescription": "Triggers when p95 Lambda duration exceeds 3000 ms across 2 of 3 one-minute periods.",
            "ActionsEnabled": True,
            "AlarmActions": alarm_actions,
            "MetricName": "Duration",
            "Namespace": "AWS/Lambda",
            "ExtendedStatistic": "p95",
            "Dimensions": [{"Name": "FunctionName", "Value": lambda_function_name}],
            "Period": 60,
            "EvaluationPeriods": 3,
            "DatapointsToAlarm": 2,
            "Threshold": 3000.0,
            "ComparisonOperator": "GreaterThanThreshold",
            "TreatMissingData": "notBreaching",
        },
    )

    ensure_alarm(
        cloudwatch,
        "CKD-Lambda-Throttles-Any",
        {
            "AlarmDescription": "Triggers when the CKD inference Lambda records any throttle in a 1-minute period.",
            "ActionsEnabled": True,
            "AlarmActions": alarm_actions,
            "MetricName": "Throttles",
            "Namespace": "AWS/Lambda",
            "Statistic": "Sum",
            "Dimensions": [{"Name": "FunctionName", "Value": lambda_function_name}],
            "Period": 60,
            "EvaluationPeriods": 1,
            "DatapointsToAlarm": 1,
            "Threshold": 1.0,
            "ComparisonOperator": "GreaterThanOrEqualToThreshold",
            "TreatMissingData": "notBreaching",
        },
    )

    ensure_alarm(
        cloudwatch,
        "CKD-API-5XX-Any",
        {
            "AlarmDescription": "Triggers when the CKD HTTP API emits any 5xx response in a 1-minute period.",
            "ActionsEnabled": True,
            "AlarmActions": alarm_actions,
            "MetricName": "5xx",
            "Namespace": "AWS/ApiGateway",
            "Statistic": "Sum",
            "Dimensions": [
                {"Name": "ApiId", "Value": api_id},
                {"Name": "Stage", "Value": stage_name},
            ],
            "Period": 60,
            "EvaluationPeriods": 1,
            "DatapointsToAlarm": 1,
            "Threshold": 1.0,
            "ComparisonOperator": "GreaterThanOrEqualToThreshold",
            "TreatMissingData": "notBreaching",
        },
    )

    summary = {
        "generated_at_utc": utc_now(),
        "stack_name": args.stack_name,
        "region": region,
        "lambda_function_name": lambda_function_name,
        "api_id": api_id,
        "stage_name": stage_name,
        "log_group_name": log_group_name,
        "log_retention_days": args.log_retention_days,
        "alert_topic_arn": topic_arn,
        "alert_email": args.alert_email or "",
        "subscription_arn": subscription_arn or "",
        "alarms_managed": [
            "CKD-Lambda-Errors-Any",
            "CKD-Lambda-Duration-p95-High",
            "CKD-Lambda-Throttles-Any",
            "CKD-API-5XX-Any",
        ],
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
