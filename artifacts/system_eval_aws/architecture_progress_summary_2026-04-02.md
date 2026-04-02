# Architecture Progress Summary

- generated_at_utc: `2026-04-02T10:43:11Z`
- project_scope: `CKD Prediction platform architecture progression after thesis completion`

## Overall status

The platform has progressed beyond a minimal cloud inference slice and now includes meaningful infrastructure, frontend, governance, training, operational, and network hardening upgrades.

At the current stage, the architecture is best described as:

- a **live AWS-backed inference platform**
- with **AWS-hosted frontend delivery through CloudFront and S3**
- with a **custom production domain**
- with a **lightweight model governance layer**
- with a **verified SageMaker smoke-training path**
- with **active alarm-to-email operational wiring**
- with a **repo-native CI/CD scaffold plus a live EventBridge-to-CodeBuild trigger**
- and with the **live inference Lambda already running in private subnets**
- and with a **live GitHub-triggered OIDC bridge for the existing CI path**

It is **not yet** a fully completed enterprise or hospital-grade platform.

## Completed and live

### 1. Core cloud inference path

Completed and live:

- public frontend reaches the live backend
- API Gateway is live
- Lambda inference is live
- S3-hosted model artifacts are in use
- CloudWatch dashboarding and alarms exist

This is the thesis-critical serving path and is operational.

### 2. Model registry

Completed:

- registry-driven active-model selection
- local registry file and schema
- serving path no longer depends only on hard-coded model file references

Result:

- the platform now treats models as managed assets rather than single fixed files

### 3. Model governance v2

Completed:

- candidate / approved / active / retired lifecycle
- approval flow
- promotion audit trail
- rollback workflow
- append-only event logging

Result:

- the platform now has a lightweight but defensible model-governance layer

### 4. AWS-native frontend hosting

Completed and live:

- frontend hosted from `S3 + CloudFront`
- custom domain `renal-risk.com` points to the AWS-hosted frontend
- static-site deployment helper is implemented
- Phase A and Phase B reports were completed

Result:

- the frontend is no longer dependent on Cloudflare Pages

### 5. SageMaker training layer

Completed to verified smoke-job level:

- SageMaker training entrypoint
- runtime dependency file
- execution-role bootstrap
- cloud-training launcher
- smoke-test configuration
- S3 input staging path
- explicit code-location path under the training prefix
- one completed live SageMaker smoke-training job

Result:

- the platform now includes a real training-side cloud path rather than only a serving-side AWS slice

### 6. IAM and operational hardening

Completed to a meaningful prototype level:

- SageMaker execution role narrowed to the `sagemaker-training/*` prefix
- `AmazonSageMakerFullAccess` detached from the training role
- Lambda log retention explicitly set to `30` days
- SNS alert topic created for operational alarms
- alarm actions enabled for the main Lambda and API alarms
- dedicated Lambda throttling alarm added
- human email subscription confirmed for `CKD-Operational-Alerts`

Result:

- the platform is no longer only functional, but also materially safer and more observable

### 7. CI/CD scaffold and live trigger

Completed to a practical thesis-oriented level:

- repo-native CI checks script
- repo-native CD release script
- CodeBuild-ready `buildspec-ci.yml`
- source-bundle packaging helper
- EventBridge rule targeting CodeBuild
- live CodeBuild CI project
- validated dry-run release flow for:
  - serving bundle upload
  - registry update path
  - frontend static-site deployment
- validated triggered CI execution through:
  - source bundle upload
  - EventBridge custom event
  - CodeBuild project execution

Result:

- the platform now has a repeatable validation-and-release path together with a real AWS-triggered CI execution path

### 8. Live Lambda private-subnet cutover

Completed and live:

- two private subnets were created in the existing VPC
- a dedicated private route table was created and associated
- an S3 gateway endpoint was attached to that route table
- the inference Lambda was updated into VPC mode
- the live Lambda now runs inside private subnets with an egress-only security group
- health and prediction checks both succeeded after cutover

Result:

- private-subnet deployment is no longer only defined at infrastructure level; it is now the active live Lambda networking mode

## Completed but with an important boundary

### 9. Custom domain is live, but DNS authority remains on Cloudflare

Completed:

- `renal-risk.com` works as the production frontend domain
- ACM certificate for `renal-risk.com` is issued
- ACM certificate for `www.renal-risk.com` is also issued
- Route 53 hosted zone and records were prepared

Boundary:

- authoritative DNS is still on `Cloudflare DNS`
- not on `Route 53`

Reason:

- the domain was purchased through `Cloudflare Registrar`
- Cloudflare Registrar does not currently allow Route 53 nameserver delegation for this domain

Practical interpretation:

- live system: `Cloudflare DNS -> CloudFront -> S3`
- prepared future path: `Route 53 -> CloudFront -> S3`

## Completed support assets and evidence

The following implementation reports already exist:

- `model_registry_implementation_report.md`
- `model_governance_v2_report.md`
- `lambda_vpc_private_subnet_report.md`
- `lambda_private_subnet_cutover_live_report.md`
- `frontend_aws_native_hosting_report.md`
- `frontend_phase_a_live_deployment_report.md`
- `frontend_phase_b_custom_domain_report.md`
- `route53_dns_cutover_report.md`
- `route53_cloudflare_registrar_boundary_report.md`
- `sagemaker_training_layer_report.md`
- `iam_operational_hardening_report.md`
- `ci_cd_scaffold_report.md`
- `ci_cd_triggered_codebuild_report.md`
- `github_trigger_ready_ci_bridge_report.md`

## Remaining gaps

### 1. Fully AWS-native DNS

Still missing:

- live Route 53 authoritative DNS

Status:

- Route 53 is prepared
- registrar-level delegation is blocked by current Cloudflare Registrar usage

### 2. Full live Git-native CI/CD integration

Still missing:

- automated promotion from commit events

Status:

- repo-native CI/CD scripts exist
- a live `EventBridge -> CodeBuild` trigger exists
- the current `CKD-main` platform state is now synchronized into a dedicated private GitHub repository
- GitHub Actions now execute successfully against that current platform state
- the GitHub OIDC bridge now executes successfully into AWS
- the GitHub bridge now reaches the downstream `EventBridge -> CodeBuild` CI path successfully

### 3. Broader IAM hardening

Still incomplete:

- the most important training, monitoring, and inference-networking paths have been tightened
- but the full AWS surface has not yet undergone a complete least-privilege review

### 4. Broader operational hardening

Still incomplete:

- alert delivery is now wired to a human inbox
- but broader production safeguards and institutional deployment controls remain unfinished

### 5. `www` frontend behavior

Certificate support exists for `www.renal-risk.com`, but the live CloudFront alias currently centers on the apex domain `renal-risk.com`.

Possible next step:

- add `www` as an additional CloudFront alias and decide whether it should resolve directly or redirect to the apex domain

### 6. EC2 backup environment

Still not implemented and remains low priority.

## Recommended next priorities

The strongest next steps are:

1. decide whether to keep Cloudflare DNS long term or later transfer the domain so Route 53 can become authoritative
2. continue IAM and operational hardening with broader least-privilege review and production safeguards
3. decide how far to extend the current CI path toward true deployment automation
4. decide whether to add or redirect `www.renal-risk.com`

## Bottom line

The architecture is no longer just a minimal inference demo. It now includes live AWS frontend hosting, live custom-domain access, registry-based model serving, explicit model governance, a completed live SageMaker smoke-training path, active monitoring-to-email wiring, a repo-native CI/CD scaffold with a live EventBridge-to-CodeBuild trigger, a verified live GitHub-triggered OIDC bridge, and a live private-subnet inference Lambda path. The most important remaining boundaries are that DNS authority still sits on Cloudflare rather than Route 53 and that the current GitHub path still stops at CI rather than automated deployment.
