# GitHub Actions Live Validation Report

- generated_at: 2026-04-02
- repository: `qazabc159-blip/CKD-main`
- branch: `main`
- validation_scope: `GitHub-hosted CI + GitHub-triggered CodeBuild bridge`

## Objective

Verify that the current `CKD-main` repository is no longer only GitHub-connected in principle, but can also execute the intended GitHub-triggered CI path in practice.

## Final result

The GitHub-triggered CI path is now live and verified end to end.

Validated successfully:

- GitHub repository synchronization for the current `CKD-main` platform state
- GitHub Actions `GitHub CI` workflow execution on push to `main`
- GitHub Actions `GitHub to CodeBuild Bridge` workflow execution on push to `main`
- GitHub OIDC role assumption into AWS from GitHub Actions
- source-bundle upload to S3 from GitHub Actions
- `EventBridge -> CodeBuild` CI trigger
- downstream CodeBuild execution using the uploaded source bundle

## Final successful runs

### GitHub Actions

- `GitHub CI`
  - run id: `23900398267`
  - status: `completed`
  - conclusion: `success`
  - commit: `0b6ca9a9c4c990b1f73631b2a63bf71365605082`
  - URL: <https://github.com/qazabc159-blip/CKD-main/actions/runs/23900398267>

- `GitHub to CodeBuild Bridge`
  - run id: `23900398251`
  - status: `completed`
  - conclusion: `success`
  - commit: `0b6ca9a9c4c990b1f73631b2a63bf71365605082`
  - URL: <https://github.com/qazabc159-blip/CKD-main/actions/runs/23900398251>

### CodeBuild

- project: `CKD-CI-Build`
- build id: `CKD-CI-Build:b45ca395-0c75-40cf-899b-6d08b00a0557`
- status: `SUCCEEDED`
- initiator: `rule/CKD-CI-SourceBundle-Uploaded`
- artifact location:
  - `arn:aws:s3:::ckd-automl-artifacts-junxiang/ci/build-artifacts/b45ca395-0c75-40cf-899b-6d08b00a0557/ci-output`

## Problems found during validation and how they were resolved

### 1. OIDC trust initially pointed to the wrong GitHub repository

The AWS OIDC bridge role had originally been scoped to the older `qazabc159-blip/CKD` repository rather than to the new private `qazabc159-blip/CKD-main` repository.

Resolution:

- retargeted the GitHub OIDC bridge to `qazabc159-blip/CKD-main`
- re-ran the bootstrap helper so the AWS trust policy matched the live repository

### 2. GitHub-hosted CI expected an untracked local binary artifact

The initial `GitHub CI` run failed because `infra/run_ci_checks.py` required `artifacts/autoprognosis_336/serving_ultra_minimal.pkl`, which is intentionally not committed to GitHub.

Resolution:

- updated `infra/run_ci_checks.py`
- made the binary serving artifact optional for repository-native CI
- required the committed metadata and serving manifest instead

### 3. GitHub-hosted CI failed SAM validation because no AWS region was set

The GitHub-hosted runner did not have an implicit default AWS region for `sam validate`.

Resolution:

- updated `infra/run_ci_checks.py`
- added an explicit region for SAM validation using `ap-northeast-1`

### 4. CodeBuild bridge initially uploaded an incomplete source bundle

The source-bundle helper was still packaging the old binary-artifact path and omitted the committed serving manifest needed by the updated repository-native CI checks.

Resolution:

- updated `infra/upload_ci_source_bundle.py`
- included `artifacts/autoprognosis_336/serving_ultra_minimal_manifest.json`
- removed dependence on the non-committed local `.pkl` file for the CI source bundle

## Practical meaning

The CI/CD path is no longer merely scaffolded or GitHub-ready in principle. It now has a verified live path in which:

1. a push to `main` triggers GitHub Actions
2. GitHub-hosted CI runs repository-native checks directly
3. the bridge workflow assumes an AWS role through OIDC
4. the bridge uploads a source bundle to S3
5. EventBridge triggers CodeBuild
6. CodeBuild executes the CI build successfully

## Current boundary

This is now a live GitHub-triggered CI path, but it is still not a full Git-native CD system. It does not yet include:

- automated deployment from GitHub after successful CI
- branch protection or required-check enforcement policy
- pull-request review gating tied to deployment promotion
- full commit-to-production automation

## Conclusion

The current `CKD-main` platform now has a verified GitHub-triggered CI path that is live on the real repository and integrated with the existing AWS EventBridge-to-CodeBuild CI bridge.
