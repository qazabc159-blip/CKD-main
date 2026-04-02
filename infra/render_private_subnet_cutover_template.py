from __future__ import annotations

import argparse
import json
from pathlib import Path


VPC_PARAMETERS = {
    "EnableVpcMode": {
        "Type": "String",
        "Default": "false",
        "AllowedValues": ["true", "false"],
        "Description": "Whether to place the inference Lambda in private subnets.",
    },
    "VpcId": {
        "Type": "String",
        "Default": "",
        "Description": "Existing VPC ID used when VPC mode is enabled.",
    },
    "PrivateSubnetIds": {
        "Type": "String",
        "Default": "",
        "Description": "Comma-separated private subnet IDs for the inference Lambda. No spaces.",
    },
    "LambdaSecurityGroupId": {
        "Type": "String",
        "Default": "",
        "Description": "Optional existing security group ID for the inference Lambda. Leave blank to create a minimal egress-only group.",
    },
    "CreateS3GatewayEndpoint": {
        "Type": "String",
        "Default": "false",
        "AllowedValues": ["true", "false"],
        "Description": "Create an S3 gateway endpoint for private-subnet artifact access when S3-backed serving is used.",
    },
    "PrivateRouteTableIds": {
        "Type": "String",
        "Default": "",
        "Description": "Comma-separated private route table IDs for the optional S3 gateway endpoint. No spaces.",
    },
}


VPC_CONDITIONS = {
    "VpcModeRequested": {"Fn::Equals": [{"Ref": "EnableVpcMode"}, "true"]},
    "HasVpcId": {"Fn::Not": [{"Fn::Equals": [{"Ref": "VpcId"}, ""]}]},
    "HasPrivateSubnetIds": {"Fn::Not": [{"Fn::Equals": [{"Ref": "PrivateSubnetIds"}, ""]}]},
    "UseVpcMode": {
        "Fn::And": [
            {"Condition": "VpcModeRequested"},
            {"Condition": "HasVpcId"},
            {"Condition": "HasPrivateSubnetIds"},
        ]
    },
    "HasProvidedLambdaSecurityGroup": {
        "Fn::And": [
            {"Condition": "UseVpcMode"},
            {"Fn::Not": [{"Fn::Equals": [{"Ref": "LambdaSecurityGroupId"}, ""]}]},
        ]
    },
    "CreateLambdaSecurityGroup": {
        "Fn::And": [
            {"Condition": "UseVpcMode"},
            {"Fn::Equals": [{"Ref": "LambdaSecurityGroupId"}, ""]},
        ]
    },
    "HasPrivateRouteTableIds": {
        "Fn::Not": [{"Fn::Equals": [{"Ref": "PrivateRouteTableIds"}, ""]}]
    },
    "CreateS3Endpoint": {
        "Fn::And": [
            {"Condition": "UseVpcMode"},
            {"Condition": "UseS3Artifacts"},
            {"Condition": "HasPrivateRouteTableIds"},
            {"Fn::Equals": [{"Ref": "CreateS3GatewayEndpoint"}, "true"]},
        ]
    },
}


LAMBDA_SECURITY_GROUP_RESOURCE = {
    "Type": "AWS::EC2::SecurityGroup",
    "Condition": "CreateLambdaSecurityGroup",
    "Properties": {
        "GroupDescription": "Egress-only security group for the CKD inference Lambda private-subnet mode.",
        "VpcId": {"Ref": "VpcId"},
        "SecurityGroupEgress": [
            {
                "IpProtocol": "-1",
                "CidrIp": "0.0.0.0/0",
            }
        ],
    },
}


S3_GATEWAY_ENDPOINT_RESOURCE = {
    "Type": "AWS::EC2::VPCEndpoint",
    "Condition": "CreateS3Endpoint",
    "Properties": {
        "VpcEndpointType": "Gateway",
        "VpcId": {"Ref": "VpcId"},
        "ServiceName": {"Fn::Sub": "com.amazonaws.${AWS::Region}.s3"},
        "RouteTableIds": {"Fn::Split": [",", {"Ref": "PrivateRouteTableIds"}]},
    },
}


def inject_vpc_support(template: dict) -> dict:
    parameters = template.setdefault("Parameters", {})
    for key, value in VPC_PARAMETERS.items():
        parameters.setdefault(key, value)

    conditions = template.setdefault("Conditions", {})
    for key, value in VPC_CONDITIONS.items():
        conditions.setdefault(key, value)

    resources = template.setdefault("Resources", {})

    role = resources["CkdInferenceFunctionRole"]
    managed_arns = role["Properties"].setdefault("ManagedPolicyArns", [])
    vpc_policy_arn = {
        "Fn::If": [
            "UseVpcMode",
            {"Fn::Sub": "arn:${AWS::Partition}:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"},
            {"Ref": "AWS::NoValue"},
        ]
    }
    if vpc_policy_arn not in managed_arns:
        managed_arns.append(vpc_policy_arn)

    resources.setdefault("CkdInferenceLambdaSecurityGroup", LAMBDA_SECURITY_GROUP_RESOURCE)
    resources.setdefault("CkdInferenceS3GatewayEndpoint", S3_GATEWAY_ENDPOINT_RESOURCE)

    function_resource = resources["CkdInferenceFunction"]
    function_props = function_resource.setdefault("Properties", {})
    function_props["VpcConfig"] = {
        "Fn::If": [
            "UseVpcMode",
            {
                "SecurityGroupIds": [
                    {
                        "Fn::If": [
                            "HasProvidedLambdaSecurityGroup",
                            {"Ref": "LambdaSecurityGroupId"},
                            {"Ref": "CkdInferenceLambdaSecurityGroup"},
                        ]
                    }
                ],
                "SubnetIds": {"Fn::Split": [",", {"Ref": "PrivateSubnetIds"}]},
            },
            {"Ref": "AWS::NoValue"},
        ]
    }

    return template


def main() -> None:
    parser = argparse.ArgumentParser(description="Inject private-subnet VPC support into a processed CloudFormation template.")
    parser.add_argument("--input", required=True, help="Path to the processed CloudFormation template JSON.")
    parser.add_argument("--output", required=True, help="Path to write the patched template JSON.")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    payload = json.loads(input_path.read_text(encoding="utf-8-sig"))
    template = payload.get("TemplateBody", payload)
    template = inject_vpc_support(template)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(template, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
