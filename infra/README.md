# Infrastructure

This folder contains the first AWS-facing deployment assets for the CKD platform.

## Implemented First Layer

- SAM template for the minimal inference path:
  - `infra/template.yaml`
- Lambda inference package:
  - `infra/lambda_inference/handler.py`
  - `infra/lambda_inference/Dockerfile`
  - `infra/lambda_inference/requirements-lambda.txt`
- Registry-aware serving helper:
  - `infra/upload_model_artifact_bundle.py`
- Frontend static-site deployment helper:
  - `infra/deploy_frontend_static_site.py`
- SageMaker training-layer helpers:
  - `infra/sagemaker_training/entrypoint.py`
  - `infra/ensure_sagemaker_execution_role.py`
  - `infra/launch_sagemaker_training_job.py`
- IAM / operational hardening helpers:
  - `infra/harden_operational_controls.py`

## Current Scope

This layer still centers on the thesis-critical serving slice:

- API Gateway
- Lambda inference
- packaged model artifact support
- optional S3-backed artifact loading
- optional registry-driven active-model selection
- optional VPC/private-subnet placement for the inference Lambda
- prototype SageMaker training path for the main AutoPrognosis workflow

It does **not** yet include:

- static frontend hosting resources
- full least-privilege IAM hardening

The template can now also provision:

- private S3 bucket for frontend assets
- CloudFront distribution with origin access control
- optional Route 53 alias records for a custom frontend domain

## Deployment Shape

The current deployment target is:

- `CKD Web UI`
- `API Gateway`
- `Lambda inference`
- `S3 model artifact bundle`
- optional `model registry`

This matches the minimum vertical slice needed to support the thesis platform chapters without forcing full MLOps implementation up front.

## Notes

- The SAM template uses a Lambda container image rather than a zip package.
- This remains intentional because the current AutoPrognosis serving artifact depends on a scientific Python stack and `autoprognosis==0.1.22`.
- If S3 artifact parameters are left blank, the Lambda uses the packaged artifact bundled into the image.
- If a local registry file exists at `artifacts/model_registry/model_registry.json`, local runs resolve the active model through the registry before falling back to the packaged defaults.

## Minimal SAM Commands

From the repo root:

```powershell
sam build -t infra/template.yaml
sam deploy --guided --template-file infra/template.yaml
```

If you later want Lambda to pull the artifact bundle from S3 instead of the packaged image contents, provide:

- `ModelArtifactBucket`
- `ModelArtifactKey`
- optionally:
  - `ModelMetadataKey`
  - `SetupSummaryKey`
  - `ModelRegistryKey`
  - `ActiveModelId`

If `ModelRegistryKey` is provided together with `ModelArtifactBucket`, the Lambda resolves the active model through the registry instead of relying only on direct artifact-key wiring.

## Optional VPC / Private-Subnet Mode

The SAM template now supports an optional VPC mode for the inference Lambda. This is intended for the thesis architecture path in which the serving function is placed inside private subnets rather than left on the default public Lambda networking model.

Relevant parameters:

- `EnableVpcMode`
- `VpcId`
- `PrivateSubnetIds`
- `LambdaSecurityGroupId`
- `CreateS3GatewayEndpoint`
- `PrivateRouteTableIds`

Recommended deployment patterns:

1. packaged artifact mode inside private subnets
   - provide:
     - `EnableVpcMode=true`
     - `VpcId`
     - `PrivateSubnetIds`
   - this is the lightest private-subnet configuration because model files stay in the Lambda image

2. S3-backed artifact mode inside private subnets
   - provide:
     - `EnableVpcMode=true`
     - `VpcId`
     - `PrivateSubnetIds`
     - `ModelArtifactBucket`
     - `ModelArtifactKey`
   - and additionally ensure:
     - a NAT path exists, or
     - `CreateS3GatewayEndpoint=true` together with `PrivateRouteTableIds`

If `LambdaSecurityGroupId` is left blank in VPC mode, the template creates a minimal egress-only security group for the inference Lambda.

## AWS-Native Frontend Hosting

The same SAM template can now optionally provision AWS-native frontend hosting with:

- S3
- CloudFront
- optional Route 53 alias records

Relevant parameters:

- `EnableFrontendHosting`
- `FrontendBucketName`
- `FrontendPriceClass`
- `FrontendDomainName`
- `FrontendCertificateArn`
- `FrontendHostedZoneId`

Practical deployment sequence:

1. deploy the stack with `EnableFrontendHosting=true`
2. upload the static site contents from `web/` to the provisioned bucket
3. invalidate the CloudFront distribution
4. if using a custom domain, provide the ACM certificate ARN and hosted zone ID

Important boundary:

- CloudFront custom domains require an ACM certificate in `us-east-1`
- Route 53 records are only created when `FrontendDomainName`, `FrontendCertificateArn`, and `FrontendHostedZoneId` are all provided

## Artifact Upload Script

Dry run:

```powershell
python infra/upload_model_artifact_bundle.py --bucket your-model-bucket --dry-run
```

Actual serving-bundle upload:

```powershell
python infra/upload_model_artifact_bundle.py --bucket your-model-bucket --prefix serving/autoprognosis_336_ultra
```

By default the script uploads:

- `serving_ultra_minimal.pkl`
- `best_autoprognosis_metadata.json`
- `setup_summary.json`
- `serving_bundle_manifest.json`

and prints the SAM parameter overrides for `ModelArtifactBucket`, `ModelArtifactKey`, `ModelMetadataKey`, and `SetupSummaryKey`.

To update the registry at the same time:

```powershell
python infra/upload_model_artifact_bundle.py `
  --bucket your-model-bucket `
  --update-registry `
  --activate
```

That flow updates:

- local registry: `artifacts/model_registry/model_registry.json`
- S3 registry object: `registry/model_registry.json`

and prints the additional SAM overrides:

- `ModelRegistryKey`
- `ActiveModelId`

## Governance Scripts

The registry now supports a lightweight governance layer:

- approve candidate:
  - `python infra/approve_model.py --model-id <model_id> --actor <name> --note "<approval note>"`
- promote approved model:
  - `python infra/promote_model.py --model-id <model_id> --actor <name> --reason "<promotion reason>"`
- rollback to the previous approved model:
  - `python infra/rollback_model.py --actor <name> --reason "<rollback reason>"`

Audit events are appended to:

- `artifacts/model_registry/registry_events.jsonl`

## Frontend Deployment Helper

Dry run:

```powershell
python infra/deploy_frontend_static_site.py --bucket your-frontend-bucket --distribution-id YOURDISTID --dry-run
```

Resolve bucket and distribution from a stack:

```powershell
python infra/deploy_frontend_static_site.py --stack-name your-sam-stack
```

The script uploads the contents of `web/` to S3, applies cache-control headers, and can invalidate the CloudFront distribution unless `--skip-invalidation` is set.

## Frontend Phase A Live Cutover

To provision the AWS-native frontend hosting path on the existing inference stack and immediately publish the static site to CloudFront:

```powershell
python infra/deploy_frontend_phase_a.py
```

This Phase A flow:

- merges the frontend hosting resources into the currently deployed stack template
- updates the stack with `EnableFrontendHosting=true`
- uploads the `web/` static site
- verifies the CloudFront-served root, landing page, app page, and `app/config.js`

Phase B remains optional and would add:

- ACM certificate in `us-east-1`
- Route 53 alias records
- custom-domain cutover

## SageMaker Training Layer

The repository now also contains a prototype-level SageMaker training path for the main AutoPrognosis workflow on Dataset #336.

Relevant files:

- `infra/sagemaker_training/entrypoint.py`
- `infra/sagemaker_training/requirements-runtime.txt`
- `infra/sagemaker_training/training_job_config_336.json`
- `infra/ensure_sagemaker_execution_role.py`
- `infra/launch_sagemaker_training_job.py`

This training layer currently focuses on:

- packaging the thesis AutoPrognosis workflow into a SageMaker-compatible entrypoint
- reusing the held-out split file from the baseline branch
- installing thesis-specific runtime dependencies inside the SageMaker Scikit-learn container
- exporting the resulting artifacts back to S3 through the training job output path

It should be described as a prototype cloud-training path for the main AutoPrognosis workflow, not yet as a full production MLOps pipeline.

## IAM / Operational Hardening

The repository now also includes a hardening path focused on:

- reducing unnecessary SageMaker execution-role permissions
- setting explicit Lambda log retention
- creating an SNS topic for operational alerts
- wiring CloudWatch alarms to a managed alert destination

Relevant scripts:

- `infra/ensure_sagemaker_execution_role.py`
- `infra/harden_operational_controls.py`

The hardening path is intentionally lightweight and prototype-appropriate. It strengthens governance and observability without claiming full enterprise security posture.

## CI/CD Scaffold

The repository now also includes a lightweight CI/CD scaffold that matches the current local-first thesis workflow.

Relevant files:

- `infra/run_ci_checks.py`
- `infra/run_cd_release.py`
- `infra/buildspec-ci.yml`
- `infra/upload_ci_source_bundle.py`
- `infra/setup_codebuild_ci_trigger.py`

What this scaffold currently provides:

- CI checks for:
  - Python compilation across `backend/`, `infra/`, and `training/`
  - `sam validate` against `infra/template.yaml`
  - required serving-artifact checks
  - required frontend-file checks
  - local registry consistency checks
- CD release orchestration for:
  - serving-bundle upload
  - optional registry update + activation
  - frontend static-site deployment

Current boundary:

- this is now a repo-native scaffold with a live `EventBridge -> CodeBuild` trigger
- it is not yet wired to a GitHub webhook or pull-request trigger

Run the CI checks locally:

```powershell
python infra/run_ci_checks.py
```

Run the release pipeline locally:

```powershell
python infra/run_cd_release.py
```

Upload the CI source bundle and emit the EventBridge trigger:

```powershell
python infra/upload_ci_source_bundle.py
```

Provision or refresh the CodeBuild/EventBridge trigger path:

```powershell
python infra/setup_codebuild_ci_trigger.py
```
