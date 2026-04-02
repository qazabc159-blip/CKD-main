# Triggered CodeBuild CI Report

- generated_at_utc: `2026-04-02T04:42:00Z`
- scope: `EventBridge-triggered CodeBuild CI integration for the CKD thesis platform`

## Purpose

The earlier CI/CD scaffold already provided repo-native CI checks and release orchestration, but it still depended on explicit local invocation.

The goal of this work item was to move the platform one step closer to real automation by adding a live AWS trigger layer that can execute CI without directly running the CI script by hand.

Because the project is not yet attached to a live Git remote, the chosen approach was:

- package the current repository state into a CI source bundle
- upload that bundle to S3
- emit a custom EventBridge event after upload
- use EventBridge to trigger a CodeBuild CI project

This makes the current platform more automation-like without pretending it already has GitHub-native DevOps.

## What Was Added

### 1. Source-bundle packaging helper

Added:

- `infra/upload_ci_source_bundle.py`

This helper:

- packages the relevant repository paths into a zip source bundle
- uploads the bundle to:
  - `s3://ckd-automl-artifacts-junxiang/ci/source/ckd-main-ci-source.zip`
- emits a custom EventBridge event after upload unless explicitly skipped

### 2. CodeBuild / EventBridge trigger setup helper

Added:

- `infra/setup_codebuild_ci_trigger.py`

This helper provisions:

- IAM role: `CKDCodeBuildServiceRole`
- IAM role: `CKDEventBridgeCodeBuildStartRole`
- CodeBuild project: `CKD-CI-Build`
- EventBridge rule: `CKD-CI-SourceBundle-Uploaded`

The EventBridge rule matches:

- `source = ckd.platform.ci`
- `detail-type = Source Bundle Uploaded`
- bucket/key for the CI source bundle

### 3. Live CodeBuild project

Provisioned:

- CodeBuild project: `CKD-CI-Build`

Key characteristics:

- source type: `S3`
- buildspec path: `infra/buildspec-ci.yml`
- image: `aws/codebuild/standard:7.0`
- compute type: `BUILD_GENERAL1_SMALL`

## Validation

### 1. Trigger validation

The source-bundle helper successfully emitted a custom EventBridge event after upload.

Observed result:

- `event_emitted = true`
- `FailedEntryCount = 0`

### 2. EventBridge-to-CodeBuild validation

The EventBridge rule successfully triggered the CodeBuild project.

Observed build:

- build id: `CKD-CI-Build:856f7fcb-d855-4e71-9f9f-1a1a1c4d1edb`
- initiator: `rule/CKD-CI-SourceBundle-Uploaded`

This is the most important validation point because it confirms that the CI trigger is no longer merely theoretical.

### 3. CodeBuild execution validation

The triggered CodeBuild build completed successfully.

Observed result:

- `buildStatus = SUCCEEDED`
- source download succeeded
- install phase succeeded
- build phase succeeded
- artifacts upload succeeded

The generated CI artifact path was:

- `s3://ckd-automl-artifacts-junxiang/ci/build-artifacts/856f7fcb-d855-4e71-9f9f-1a1a1c4d1edb/ci-output`

## Practical Interpretation

The platform now has a real AWS-triggered CI path.

What is already true:

- repository validation can still run locally
- the CI source bundle can be packaged and uploaded repeatably
- an EventBridge trigger exists
- that trigger can start CodeBuild automatically
- the resulting CodeBuild CI run can complete successfully

What is not yet true:

- the trigger is not GitHub-native
- there is no pull-request or branch-based automation yet
- CD is still operator-driven rather than fully autonomous

## Thesis-Safe Summary

This work can now be described as:

- a **verified triggered CI integration**
- with **a live EventBridge-to-CodeBuild execution path**
- with **successful automated CI execution from a packaged source bundle**

It should not yet be described as:

- full GitHub-based CI/CD
- branch-native DevOps automation
- fully autonomous production deployment
