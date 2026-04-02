# CKD AutoML Platform

AWS-based CKD prediction platform built around AutoPrognosis 2.0, delivered as a verified prototype with live serverless inference, AWS-hosted frontend delivery, and lightweight model governance.

## Overview

This repository contains the current platform implementation for a chronic kidney disease (CKD) prediction system developed in the context of a master's thesis. The project combines structured clinical prediction modeling with deployment-oriented platform engineering.

Core technologies currently in use include:

- AutoPrognosis 2.0 for AutoML-based tabular prediction
- AWS SAM and CloudFormation for infrastructure definition
- AWS Lambda for container-based serverless inference
- API Gateway for public inference routes
- Amazon S3 for model artifacts and frontend static assets
- Amazon CloudFront for frontend delivery
- Amazon SageMaker for the verified smoke-training path
- Amazon CloudWatch and SNS for monitoring and alert delivery
- GitHub Actions, EventBridge, and CodeBuild for the current CI bridge

The platform should be described as a **verified prototype**, not as a completed clinical production system.

## Architecture

The current platform includes these live or verified paths:

- **Inference path:** Frontend -> API Gateway -> Lambda -> S3-hosted model artifacts
- **Frontend delivery:** S3 -> CloudFront -> `renal-risk.com`
- **Network hardening:** the live inference Lambda runs inside private subnets with S3 access through a gateway endpoint
- **Model serving control:** registry-driven active-model selection with explicit governance actions

Key architectural elements currently implemented:

- AWS-hosted static frontend delivery through CloudFront and S3
- API Gateway routes for health, research prediction, and clinical prediction
- Lambda-based inference using the current AutoPrognosis serving artifact
- VPC private-subnet deployment support that is now active on the live Lambda
- model registry plus approval, promotion, and rollback workflow

## Live Demo

Production prototype:

- [https://renal-risk.com](https://renal-risk.com)

Supporting notes:

- `www.renal-risk.com` redirects to the apex domain
- frontend content is AWS-hosted through CloudFront and S3
- DNS authority currently remains on Cloudflare because the domain is registered through Cloudflare Registrar

## Key Features

- **Dual prediction modes:** research route and provisional clinical adapter route
- **Serverless inference:** API Gateway + Lambda serving for live predictions
- **Model registry and governance:** candidate / approved / active / retired lifecycle with audit logging
- **CI path:** GitHub Actions plus GitHub-to-AWS OIDC bridge plus EventBridge-to-CodeBuild trigger
- **CloudWatch monitoring:** alarms, SNS alert topic, and verified email delivery
- **VPC deployment:** live Lambda inference now runs inside private subnets
- **Custom domain frontend:** AWS-hosted frontend available at `renal-risk.com`

## Project Structure

- `artifacts/` - experiment outputs, deployment reports, validation evidence, and platform status reports
- `backend/` - backend service logic and serving helpers
- `data/` - processed datasets, sourcing scripts, and data-layer outputs
- `data_schema/` - schema templates and feature definitions
- `docs/` - thesis and platform notes
- `infra/` - SAM template, deployment helpers, SageMaker launchers, CI/CD helpers, and operational scripts
- `training/` - baseline, AutoPrognosis, and statistical testing workflows
- `web/` - landing page and app workspace frontend
- `.github/` - GitHub Actions workflows and PR templates

## Quick Start

Run from the repository root.

### 1. Build the SAM application

```powershell
sam build -t infra/template.yaml
```

### 2. Deploy the inference stack

```powershell
sam deploy --guided --template-file infra/template.yaml
```

### 3. Common post-deploy helpers

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

The repository now includes a live GitHub-triggered CI path.

Current flow:

1. a push or pull request triggers GitHub Actions
2. `GitHub CI` runs repository-native validation checks
3. `GitHub to CodeBuild Bridge` assumes an AWS role through OIDC
4. a source bundle is uploaded to S3
5. EventBridge triggers CodeBuild
6. CodeBuild runs the downstream CI build successfully

Current boundary:

- CI is automated and verified
- release helpers exist for serving-bundle upload, registry update, and frontend publishing
- deployment is **still manually triggered**, not fully auto-promoted from CI

Relevant files:

- `.github/workflows/github-ci.yml`
- `.github/workflows/github-codebuild-bridge.yml`
- `infra/run_ci_checks.py`
- `infra/run_cd_release.py`
- `infra/upload_ci_source_bundle.py`
- `infra/setup_codebuild_ci_trigger.py`

## Model Governance

The platform now includes a lightweight but explicit model-governance layer.

Implemented governance capabilities:

- approval before activation
- promotion tracking with append-only event logging
- rollback to a previous approved model
- lifecycle states: `candidate`, `approved`, `active`, `retired`

Core commands:

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

This project supports a master's thesis at **Asia University**.

Thesis context:

- degree context: master's thesis
- institution: Asia University
- topic: AWS-based AutoML platform for CKD prediction using AutoPrognosis 2.0
- advisor: Professor Chao-Neng Wang

The repository now reflects the post-thesis architecture progression rather than an early planning-only state.

## Status

Current status:

- verified prototype
- live AWS-hosted frontend and live AWS-backed inference path
- verified SageMaker smoke-training path
- documented model governance and CI path
- **not for clinical use**
- **not a diagnostic or treatment system**

This repository should be interpreted as a research and deployment prototype for academic and engineering purposes.
