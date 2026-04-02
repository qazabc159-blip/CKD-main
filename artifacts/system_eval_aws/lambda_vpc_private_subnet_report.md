# Lambda VPC / Private-Subnet Support Report

## Purpose

This work item extended the thesis-serving AWS infrastructure so that the inference Lambda can optionally run inside private subnets rather than only on the default Lambda networking model. The goal was to add a realistic private-network deployment path while preserving the existing minimal serving slice and avoiding a breaking change to the current prototype.

## What Was Implemented

### 1. Optional VPC mode in the SAM template

The SAM template now supports a switchable private-subnet mode through new parameters:

- `EnableVpcMode`
- `VpcId`
- `PrivateSubnetIds`
- `LambdaSecurityGroupId`
- `CreateS3GatewayEndpoint`
- `PrivateRouteTableIds`

This design keeps the current deployment backward-compatible. If `EnableVpcMode=false`, the stack behaves as before. If `EnableVpcMode=true` and the required network parameters are provided, the inference Lambda is placed into private subnets.

### 2. Lambda networking resources

The template now includes:

- optional VPC configuration on the Lambda function
- optional creation of a minimal egress-only Lambda security group
- optional creation of an S3 gateway endpoint for private-subnet artifact access
- conditional attachment of the `AWSLambdaVPCAccessExecutionRole` managed policy

This means the stack now covers the main infrastructure pieces needed to move the serving function into a more realistic private-network deployment shape.

### 3. Documentation updates

The following files were updated so that the new VPC mode is documented rather than hidden inside the template alone:

- `infra/README.md`
- `infra/lambda_inference/README.md`
- `infra/aws_target_architecture.md`

These updates clarify:

- when private-subnet mode is appropriate
- when packaged artifacts are sufficient
- when S3-backed serving requires either a NAT path or an S3 gateway endpoint
- how the target architecture now aligns more closely with private-network deployment assumptions

## Verification

### Template validation

The updated template passed:

- `sam validate --template-file infra/template.yaml`
- `sam validate --template-file infra/template.yaml --lint`

This confirms that the infrastructure-as-code definition is syntactically and structurally valid.

### Backward-compatibility check

The VPC mode was implemented as an optional branch rather than a mandatory change. This preserves the currently working deployment path and allows private-subnet deployment to be enabled only when the required VPC identifiers are available.

## Practical Thesis Value

This work item improves the platform contribution of the thesis in several ways.

1. It narrows the gap between the target architecture and the implemented infrastructure definition.
2. It adds a credible private-network deployment path for the inference service.
3. It strengthens the claim that the platform can move toward institution-facing deployment constraints rather than remaining a purely open serverless prototype.
4. It creates a more defensible bridge from the public prototype stage to the future hybrid or institution-hosted deployment scenarios discussed in the thesis.

## Current Boundary

The VPC/private-subnet layer is now implemented at the infrastructure-definition level, but not yet fully verified through a live stack deployment with real VPC, subnet, route table, and security-group IDs.

This means:

- the SAM template support is real
- the network assumptions are documented
- the deployment path is credible
- but the work item should still be described as infrastructure-ready rather than fully field-verified

In particular, private-subnet S3 access still depends on actual environment choices:

- packaged model artifacts inside the Lambda image, or
- a NAT path, or
- the optional S3 gateway endpoint plus valid private route table IDs

## Most Relevant Files

- `infra/template.yaml`
- `infra/README.md`
- `infra/lambda_inference/README.md`
- `infra/aws_target_architecture.md`
