# Thesis Architecture Report Index for GPT

- generated_at: 2026-04-02
- purpose: `master index for updating thesis main text after the architecture expansion work`

## How to use this file

If you are updating the thesis main text, use the reports in the following order:

1. read the **current architecture summary** first
2. read the **major implementation reports** for factual detail
3. use the **supporting validation artifacts** only when you need evidence-level confirmation
4. treat explicitly marked historical notes as outdated context, not as the current platform state

---

## 1. Primary current-state summary

Start here first:

```text
C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\artifacts\system_eval_aws\architecture_progress_summary_2026-04-02.md
```

This is the best single-file summary of the current platform state.

Current headline status:

- live AWS-backed inference platform
- AWS-hosted frontend through CloudFront and S3
- custom domain `renal-risk.com`
- public `www -> apex` redirect working
- live Lambda already running in private subnets
- model registry and governance implemented
- verified SageMaker smoke-training path
- CloudWatch alarm-to-email wiring active
- live GitHub-triggered CI path

Important current boundaries:

- DNS authority still sits on Cloudflare, not Route 53
- CI is live, but deployment is still manual after CI
- platform is still a verified prototype, not a hospital-grade production system

---

## 2. Major architecture upgrade reports

These are the core reports that describe each major upgrade step.

### A. Model registry

```text
C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\artifacts\system_eval_aws\model_registry_implementation_report.md
```

Use this for thesis claims about:

- registry-driven active-model selection
- serving path no longer hard-coded to a single model file
- model artifact management moving beyond a one-off demo file

### B. Model governance v2

```text
C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\artifacts\system_eval_aws\model_governance_v2_report.md
```

Use this for thesis claims about:

- candidate / approved / active / retired lifecycle
- approval before activation
- promotion audit trail
- rollback workflow
- append-only governance event log

### C. VPC private-subnet support at IaC level

```text
C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\artifacts\system_eval_aws\lambda_vpc_private_subnet_report.md
```

Use this when describing:

- private-subnet deployment support added to the infrastructure definition
- template-level support before live cutover

### D. Live Lambda private-subnet cutover

```text
C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\artifacts\system_eval_aws\lambda_private_subnet_cutover_live_report.md
```

Use this for thesis claims about:

- live Lambda actually moved into private subnets
- route table and S3 gateway endpoint support
- health and prediction validation after cutover

### E. AWS-native frontend hosting

```text
C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\artifacts\system_eval_aws\frontend_aws_native_hosting_report.md
```

Use this for thesis claims about:

- frontend hosting path designed and implemented for S3 + CloudFront
- moving away from the earlier external hosting path

### F. Frontend Phase A live deployment

```text
C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\artifacts\system_eval_aws\frontend_phase_a_live_deployment_report.md
```

Use this for thesis claims about:

- AWS frontend actually going live through CloudFront
- root, landing, app, and config routes verified

### G. Frontend Phase B custom domain

```text
C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\artifacts\system_eval_aws\frontend_phase_b_custom_domain_report.md
```

Use this for thesis claims about:

- custom domain cutover
- ACM certificate path
- apex-domain production frontend

### H. `www` alias and redirect

```text
C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\artifacts\system_eval_aws\frontend_www_alias_redirect_report.md
```

Use this for thesis claims about:

- `www.renal-risk.com` support
- redirect to apex domain
- path and query-string preservation

### I. Route 53 preparation and DNS boundary

```text
C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\artifacts\system_eval_aws\route53_dns_cutover_report.md
C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\artifacts\system_eval_aws\route53_cloudflare_registrar_boundary_report.md
```

Use these together.

Use them for thesis claims about:

- Route 53 hosted zone and DNS preparation
- why authoritative DNS still remains on Cloudflare
- the exact architectural boundary between AWS hosting and Cloudflare DNS

### J. SageMaker training layer

```text
C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\artifacts\system_eval_aws\sagemaker_training_layer_report.md
```

Use this for thesis claims about:

- verified SageMaker training entrypoint and launcher
- S3 input staging
- execution role bootstrap
- one completed live SageMaker smoke-training job

### K. IAM and operational hardening

```text
C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\artifacts\system_eval_aws\iam_operational_hardening_report.md
```

Use this for thesis claims about:

- least-privilege tightening of the SageMaker role
- alarm-to-SNS wiring
- explicit Lambda log retention
- active monitoring guardrails

### L. CI/CD scaffold

```text
C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\artifacts\system_eval_aws\ci_cd_scaffold_report.md
```

Use this for thesis claims about:

- repo-native CI/CD scripts
- dry-run release support
- buildspec and release helpers

### M. EventBridge -> CodeBuild live trigger

```text
C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\artifacts\system_eval_aws\ci_cd_triggered_codebuild_report.md
```

Use this for thesis claims about:

- source-bundle upload trigger
- EventBridge custom event
- CodeBuild CI execution

### N. GitHub-trigger-ready CI bridge

```text
C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\artifacts\system_eval_aws\github_trigger_ready_ci_bridge_report.md
```

Use this for thesis claims about:

- GitHub Actions workflows prepared
- AWS OIDC trust and bridge setup
- repository ready to trigger AWS-side CI

### O. Live GitHub Actions validation

```text
C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\artifacts\system_eval_aws\github_actions_live_validation_report.md
```

Use this for thesis claims about:

- GitHub Actions actually running successfully
- GitHub OIDC -> AWS bridge validated
- GitHub -> EventBridge -> CodeBuild live path verified

---

## 3. Supporting evidence files

These are supporting validation artifacts, not the first files to read.

### Frontend / domain / hosting support

```text
C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\artifacts\system_eval_aws\frontend_phase_a_verification.json
C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\artifacts\system_eval_aws\frontend_static_site_live_manifest.json
C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\artifacts\system_eval_aws\frontend_phase_b_custom_domain_state.json
C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\artifacts\system_eval_aws\frontend_www_alias_redirect_state.json
```

### CI/CD support

```text
C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\artifacts\system_eval_aws\ci_checks_manifest.json
C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\artifacts\system_eval_aws\cd_release_manifest.json
C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\artifacts\system_eval_aws\codebuild_ci_trigger_validation.json
C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\artifacts\system_eval_aws\github_actions_oidc_bridge_manifest.json
```

### SageMaker support

```text
C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\artifacts\system_eval_aws\sagemaker_execution_role_state.json
C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\artifacts\system_eval_aws\sagemaker_training_launch_manifest.json
C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\artifacts\system_eval_aws\sagemaker_training_quota_snapshot.json
```

### Lambda private-subnet support

```text
C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\artifacts\system_eval_aws\lambda_private_subnet_cutover_validation.json
C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\artifacts\system_eval_aws\lambda_private_subnet_cutover_parameters_processed.json
C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\artifacts\system_eval_aws\lambda_private_subnet_cutover_processed_template.json
```

### Monitoring support

```text
C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\artifacts\system_eval_aws\cloudwatch_dashboard_ckd_inference_summary.md
C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\artifacts\system_eval_aws\cloudwatch_alarms_ckd_inference.json
C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\artifacts\system_eval_aws\iam_operational_hardening_validation.json
```

---

## 4. Historical notes that should not be treated as the latest platform state

### Historical / partially outdated handoff

```text
C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\artifacts\system_eval_aws\implementation_handoff_for_gpt.md
```

This file is useful only as an earlier implementation handoff.

Do **not** treat it as the latest truth, because it still reflects an older stage in which:

- frontend hosting was still described as Cloudflare Pages
- private-subnet Lambda was not yet live
- SageMaker training path was not yet fully verified to the latest stage
- CI/CD progress was earlier than the current GitHub-triggered state

Use it only for historical comparison, not as the primary basis for thesis revision.

---

## 5. Suggested reading order for revising the thesis main text

### If updating Chapter 5.5 or system-implementation text

Read in this order:

1. `architecture_progress_summary_2026-04-02.md`
2. `frontend_phase_a_live_deployment_report.md`
3. `frontend_phase_b_custom_domain_report.md`
4. `lambda_private_subnet_cutover_live_report.md`
5. `sagemaker_training_layer_report.md`
6. `iam_operational_hardening_report.md`

### If updating governance / deployment sections

Read in this order:

1. `model_registry_implementation_report.md`
2. `model_governance_v2_report.md`
3. `ci_cd_scaffold_report.md`
4. `ci_cd_triggered_codebuild_report.md`
5. `github_actions_live_validation_report.md`

### If updating discussion about cloud vs Route 53 / DNS boundaries

Read in this order:

1. `frontend_phase_b_custom_domain_report.md`
2. `frontend_www_alias_redirect_report.md`
3. `route53_dns_cutover_report.md`
4. `route53_cloudflare_registrar_boundary_report.md`

---

## 6. Current thesis-safe platform summary

As of 2026-04-02, the thesis can safely describe the implemented platform as:

- a live AWS-backed inference prototype
- with AWS-hosted frontend delivery through CloudFront and S3
- with production custom-domain access at `renal-risk.com`
- with working `www -> apex` redirect behavior
- with the live inference Lambda already running in private subnets
- with a lightweight but explicit model registry and governance layer
- with a verified SageMaker smoke-training path that has completed a real cloud training job
- with active CloudWatch alarm-to-email wiring
- with a live GitHub-triggered CI path reaching AWS through OIDC, EventBridge, and CodeBuild

The thesis should still avoid claiming:

- hospital-grade production readiness
- fully AWS-native authoritative DNS
- automated deployment after CI
- full enterprise MLOps or institutional operations governance
