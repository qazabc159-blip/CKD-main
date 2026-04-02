# CKD AutoML Platform

Verified AWS-based prototype for chronic kidney disease risk prediction using AutoPrognosis 2.0, with live serverless inference, AWS-hosted frontend delivery, lightweight model governance, and GitHub-triggered CI.

## Live Demo

- [https://renal-risk.com](https://renal-risk.com)

## Overview

CKD AutoML Platform is a deployment-oriented prediction system built around structured CKD risk inference. The repository combines model serving, frontend delivery, governance, monitoring, and cloud-training support in a single prototype platform.

Current implementation status:

- live frontend hosted through **CloudFront + S3**
- live inference served through **API Gateway + Lambda**
- live custom domain at **`renal-risk.com`**
- live Lambda running inside **private subnets**
- verified **SageMaker smoke-training** path
- live **GitHub Actions -> AWS OIDC -> EventBridge -> CodeBuild** CI path

This repository should be understood as a **verified prototype**, not as a clinical production system.

## At a Glance

| Area | Current State |
| --- | --- |
| Frontend | Live via CloudFront + S3 |
| Backend inference | Live via API Gateway + Lambda |
| Networking | Lambda deployed in private subnets |
| Model control | Registry-driven with approval / promotion / rollback |
| Monitoring | CloudWatch alarms + SNS email alerts |
| Training | Verified SageMaker smoke-training path |
| CI | GitHub Actions + CodeBuild bridge |
| Domain | `renal-risk.com` live |
| Clinical status | Prototype only, not for clinical use |

## Architecture

### Serving path

Frontend -> API Gateway -> Lambda -> S3-hosted model artifacts

### Frontend delivery

S3 -> CloudFront -> `renal-risk.com`

### Platform controls

- VPC private-subnet deployment for the live inference Lambda
- model registry with active-model selection
- governance workflow with approval, promotion, rollback, and event logging
- CloudWatch + SNS operational alerting

## Key Features

- **Dual mode prediction**
  - research route for full predictor-space inference
  - provisional clinical adapter route for structured intake flow
- **Serverless inference**
  - container-based Lambda serving behind API Gateway
- **Model registry and governance**
  - candidate / approved / active / retired lifecycle
  - explicit approval, promotion tracking, rollback support
- **AWS-hosted frontend delivery**
  - static frontend delivered through CloudFront and S3
  - apex domain live at `renal-risk.com`
  - `www.renal-risk.com` redirected to apex
- **Monitoring and alerting**
  - CloudWatch alarms wired to SNS email delivery
- **Cloud training path**
  - verified SageMaker smoke-training support for the AutoPrognosis workflow
- **CI bridge**
  - GitHub Actions plus GitHub-to-AWS OIDC bridge plus EventBridge-to-CodeBuild CI execution

## Project Structure

- `web/` - landing page and app workspace frontend
- `backend/` - inference service logic and serving helpers
- `infra/` - SAM template, deployment helpers, SageMaker launchers, CI/CD helpers, and operational scripts
- `training/` - baseline, AutoPrognosis, and statistical testing workflows
- `artifacts/` - reports, manifests, modeling outputs, and deployment evidence
- `data/` - processed datasets, sourcing scripts, and data-layer outputs
- `data_schema/` - schema templates and feature definitions
- `docs/` - thesis and platform notes
- `.github/` - GitHub Actions workflows and PR templates

## Quick Start

Run from the repository root.

### Build

```powershell
sam build -t infra/template.yaml
```

### Deploy

```powershell
sam deploy --guided --template-file infra/template.yaml
```

### Common follow-up commands

Upload or refresh the serving bundle:

```powershell
python infra/upload_model_artifact_bundle.py --bucket <your-model-bucket> --update-registry --activate
```

Publish the frontend static site:

```powershell
python infra/deploy_frontend_static_site.py --stack-name <your-stack-name>
```

Run local CI checks before pushing:

```powershell
python infra/run_ci_checks.py
```

## CI/CD

The current CI path is live and verified.

### Current flow

1. GitHub push or pull request triggers GitHub Actions
2. `GitHub CI` runs repository-native validation checks
3. `GitHub to CodeBuild Bridge` assumes an AWS role through OIDC
4. a source bundle is uploaded to S3
5. EventBridge triggers CodeBuild
6. CodeBuild runs the downstream CI build

### Current boundary

- CI is automated and verified
- release helpers exist for bundle upload, registry update, and frontend publishing
- deployment is still **manually triggered** after CI

Relevant files:

- `.github/workflows/github-ci.yml`
- `.github/workflows/github-codebuild-bridge.yml`
- `infra/run_ci_checks.py`
- `infra/run_cd_release.py`
- `infra/upload_ci_source_bundle.py`
- `infra/setup_codebuild_ci_trigger.py`

## Model Governance

The platform includes a lightweight governance layer for served models.

### Lifecycle

- `candidate`
- `approved`
- `active`
- `retired`

### Governance actions

```powershell
python infra/approve_model.py --model-id <model_id> --actor <name> --note "<approval note>"
python infra/promote_model.py --model-id <model_id> --actor <name> --reason "<promotion reason>"
python infra/rollback_model.py --actor <name> --reason "<rollback reason>"
```

Registry artifacts:

- `artifacts/model_registry/model_registry.json`
- `artifacts/model_registry/model_registry_schema.json`
- `artifacts/model_registry/registry_events.jsonl`

## Thesis Context

This project was developed in the context of a master's thesis at **Asia University**, supervised by **Professor Chao-Neng Wang**.

Repository context:

- thesis topic: AWS-based AutoML platform for CKD prediction using AutoPrognosis 2.0
- institution: Asia University
- role of this repository: post-thesis implementation and platform progression workspace

## Status

- verified prototype
- live AWS-hosted frontend and live AWS-backed inference path
- verified SageMaker smoke-training path
- documented model governance and CI path
- **not for clinical use**
- **not a diagnostic or treatment system**

This repository is intended for research, engineering validation, and deployment prototyping.
