# Live Lambda Private-Subnet Cutover Report

- generated_at_utc: `2026-04-02T10:40:43Z`
- stack_name: `ckd-inference-stack`
- region: `ap-northeast-1`

## Objective

Move the live CKD inference Lambda from the default public Lambda networking mode into private subnets while preserving the current live API, S3-backed model artifact path, and frontend behavior.

## Network resources created for the cutover

- VPC: `vpc-093171e98818b8494` (existing default VPC)
- private subnet 1: `subnet-014bcccc627e3c5bf` (`172.31.48.0/24`, `ap-northeast-1c`)
- private subnet 2: `subnet-0c2bb90e5c309007f` (`172.31.49.0/24`, `ap-northeast-1d`)
- private route table: `rtb-065fe27cdd41b8bf9`
- Lambda security group: `sg-0f765850258491bf4`
- S3 gateway endpoint: `vpce-0720cba6e5e4f178a`

## Implementation approach

The live stack was not updated directly from the raw SAM template because the currently deployed image-based Lambda requires a processed template that already includes `ImageUri`.

To keep the cutover safe and reproducible:

1. the current processed CloudFormation template was exported from the live stack
2. a small patch layer was applied to inject:
   - VPC/private-subnet parameters
   - VPC-related conditions
   - Lambda `VpcConfig`
   - `AWSLambdaVPCAccessExecutionRole`
   - a minimal egress-only Lambda security group
   - an S3 gateway endpoint bound to the private route table
3. a change set was created and reviewed before execution
4. the change set was executed against the existing live stack

Artifacts generated for this path:

- `lambda_private_subnet_cutover_processed_template_raw.json`
- `lambda_private_subnet_cutover_processed_template.json`
- `lambda_private_subnet_cutover_parameters_processed.json`
- `lambda_private_subnet_cutover_changeset_describe_processed.json`

## Change-set scope

The reviewed change set only introduced:

- modification of `CkdInferenceFunctionRole`
- modification of `CkdInferenceFunction`
- dynamic API integration refresh via `CkdInferenceHttpApi`
- addition of `CkdInferenceLambdaSecurityGroup`
- addition of `CkdInferenceS3GatewayEndpoint`

It did not alter the frontend bucket, CloudFront distribution, or custom-domain path.

## Validation results

### Lambda networking

The live Lambda now reports:

- VPC: `vpc-093171e98818b8494`
- subnets:
  - `subnet-014bcccc627e3c5bf`
  - `subnet-0c2bb90e5c309007f`
- security group: `sg-0f765850258491bf4`
- state: `Active`
- last_update_status: `Successful`

### Private route table and S3 access

The private route table now contains:

- local VPC route: `172.31.0.0/16 -> local`
- S3 prefix-list route via gateway endpoint: `vpce-0720cba6e5e4f178a`

This confirms that the Lambda can reach the S3-backed artifact bundle without requiring NAT.

### Live service verification

Health endpoint:

- status: `ok`
- artifact_source: `s3`
- artifact_status: `success`
- artifact_path: `s3://ckd-automl-artifacts-junxiang/serving/autoprognosis_336_ultra/serving_ultra_minimal.pkl`

Research prediction verification:

- risk_score: `0.998511`
- prediction_label: `high_risk`
- model_version: `autoprognosis-336-main::research`
- serving_route: `/predict/research`

## Practical outcome

The platform now has a **live private-subnet inference Lambda**, not only infrastructure-level private-subnet support.

The current live inference path is therefore best described as:

- `Cloudflare DNS -> CloudFront -> S3 static frontend`
- `API Gateway -> Lambda (private subnets) -> S3 artifact bundle via gateway endpoint`

## Remaining boundaries

The cutover does not change the previously known DNS boundary:

- the frontend domain remains authoritative on `Cloudflare DNS`
- Route 53 remains prepared but non-authoritative because of `Cloudflare Registrar` nameserver restrictions

Other remaining platform gaps are now outside the Lambda private-subnet path itself, such as broader Git-native CI/CD and wider least-privilege review across the full AWS surface.
