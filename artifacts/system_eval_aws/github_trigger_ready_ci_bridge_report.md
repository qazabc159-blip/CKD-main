# GitHub-Trigger-Ready CI Bridge Report

- generated_at_utc: `2026-04-02T11:34:37Z`
- scope: `GitHub-trigger-ready CI bridge for the CKD platform`

## Purpose

The platform already had:

- repo-native CI scripts
- a dry-run CD release path
- a live `EventBridge -> CodeBuild` trigger

What it still lacked was a GitHub-facing trigger path.

This work item moves the platform closer to GitHub-triggered automation by adding:

- GitHub Actions workflow definitions in the repository
- an AWS OIDC provider for GitHub Actions
- a short-lived AWS bridge role that can upload the CI source bundle and emit the existing EventBridge event

## What was added

### 1. GitHub workflow definitions

Added locally under `.github/workflows/`:

- `github-ci.yml`
  - runs on pull requests, pushes to `main`, and manual dispatch
  - checks out the repository
  - sets up Python 3.11
  - installs SAM CLI through `aws-actions/setup-sam`
  - runs `python infra/run_ci_checks.py`
  - uploads the generated CI manifest as a workflow artifact

- `github-codebuild-bridge.yml`
  - runs on pushes to `main` and manual dispatch
  - uses GitHub OIDC plus `aws-actions/configure-aws-credentials`
  - assumes a dedicated AWS bridge role
  - runs `python infra/upload_ci_source_bundle.py --bucket ckd-automl-artifacts-junxiang`
  - uploads the generated source-bundle manifest as a workflow artifact

### 2. AWS-side OIDC bridge

Added:

- `infra/ensure_github_actions_oidc_role.py`

Provisioned in AWS:

- OIDC provider: `arn:aws:iam::098890538524:oidc-provider/token.actions.githubusercontent.com`
- IAM role: `arn:aws:iam::098890538524:role/CKDGitHubActionsCIBridgeRole`

The role is restricted to:

- repository: `qazabc159-blip/CKD`
- branch: `main`
- OIDC subject: `repo:qazabc159-blip/CKD:ref:refs/heads/main`

The bridge role currently allows only what is needed for the existing CI-source-bundle path:

- write the CI source bundle to `s3://ckd-automl-artifacts-junxiang/ci/source/*`
- emit `events:PutEvents` to the default EventBridge bus
- limited bucket metadata actions needed by S3 upload

This keeps the GitHub-to-AWS path short-lived and avoids storing long-lived AWS keys in GitHub secrets.

## Validation

### 1. OIDC provider and role

Verified:

- GitHub Actions OIDC provider exists in IAM
- the bridge role exists in IAM
- the trust policy targets `repo:qazabc159-blip/CKD:ref:refs/heads/main`
- a machine-readable manifest was written to:
  - `github_actions_oidc_bridge_manifest.json`

### 2. Local workflow structure

Verified:

- both workflow files were added under `.github/workflows/`
- both files can be parsed as YAML
- the bridge helper script compiles successfully

## Important boundary

This work does **not** yet mean that the platform has completed live GitHub-triggered CI execution.

The reason is practical rather than architectural:

- the current local project is `CKD-main`
- the accessible GitHub repository is `qazabc159-blip/CKD`
- that repository is currently out of sync with the local platform state and remains public

Because of that mismatch, automatically publishing the current local platform to that public repository would be a non-trivial governance decision rather than a safe silent step.

## Practical interpretation

What is now true:

- the repository contains GitHub Actions workflows for CI and AWS bridge triggering
- AWS is ready to trust GitHub Actions from `qazabc159-blip/CKD` on `main`
- once the current platform contents are synchronized into an appropriate GitHub repository, GitHub-triggered automation can be activated without redesigning the AWS side

What is not yet true:

- no live GitHub Actions run has been executed against the current `CKD-main` platform contents
- no GitHub webhook or branch event has yet driven the live AWS CI bridge end to end for the current project state

## Thesis-safe summary

This work can now be described as:

- a **GitHub-trigger-ready CI bridge**
- with **repository-local GitHub Actions workflow definitions**
- with **AWS OIDC trust and a short-lived GitHub bridge role**
- with **direct compatibility with the existing EventBridge-to-CodeBuild CI path**

It should not yet be described as:

- a completed live GitHub-triggered CI/CD pipeline for the current platform state
