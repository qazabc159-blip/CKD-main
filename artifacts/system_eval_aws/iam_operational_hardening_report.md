# IAM and Operational Hardening Report

- generated_at_utc: `2026-04-01T18:15:00Z`
- scope: `least-privilege tightening and operational guardrail hardening for the live CKD AWS platform`

## Purpose

This work item focused on improving the safety and maintainability of the live platform rather than adding a new end-user feature.

The goal was to make the current AWS deployment more defensible by:

- tightening SageMaker execution permissions
- formalizing alarm-to-notification wiring
- setting explicit log-retention policy
- adding one more operational alarm for Lambda throttling
- validating that the training-side cloud path still works after the role was hardened

## What Was Changed

### 1. SageMaker execution-role hardening

Updated:

- `infra/ensure_sagemaker_execution_role.py`

The SageMaker execution role was tightened so that it no longer relies on the broad managed policy `AmazonSageMakerFullAccess`.

Instead, the role now keeps a thesis-scoped inline policy that allows:

- bucket listing only for the `sagemaker-training/` prefix
- object read/write only under `s3://ckd-automl-artifacts-junxiang/sagemaker-training/*`
- CloudWatch Logs writes for `/aws/sagemaker/*`

Observed result:

- `AmazonSageMakerFullAccess` was detached from `CKDSageMakerExecutionRole`
- the role remained functional for real training-job execution

### 2. SageMaker source-bundle path hardening

Updated:

- `infra/launch_sagemaker_training_job.py`

The launcher now sets an explicit `code_location` under:

- `s3://ckd-automl-artifacts-junxiang/sagemaker-training/autoprognosis-336/code/`

This matters because the SageMaker SDK otherwise uploads the training source bundle under a job-root path outside the narrowed S3 prefix.

Result:

- the source bundle now lands inside the same scoped S3 boundary already allowed by the hardened execution role
- least-privilege narrowing was preserved without breaking training

### 3. Runtime dependency alignment for the SageMaker container

Updated:

- `infra/sagemaker_training/requirements-runtime.txt`

The previous runtime file pinned `scikit-learn==1.8.0`, which is not currently available for the SageMaker Scikit-learn `1.4-2` Python 3.10 training image.

The runtime file was therefore reduced to a compatible thesis-oriented set:

- `autoprognosis==0.1.22`
- `cloudpickle==3.1.1`
- `xgboost==3.2.0`
- `catboost==1.2.10`
- `joblib`
- `matplotlib`

Result:

- the training container can now resolve its runtime dependencies successfully
- the training path is no longer blocked by an impossible package pin

### 4. Operational hardening script

Added:

- `infra/harden_operational_controls.py`

This script now applies the core operational guardrails to the live stack.

It performs the following actions:

- discovers the live Lambda and API identifiers from the CloudFormation stack
- sets Lambda log retention explicitly
- creates an SNS topic for operational alerts
- configures a topic policy so CloudWatch alarms can publish to that topic
- creates or updates the main platform alarms

### 5. Alarm and notification wiring

Observed operational result:

- SNS topic created: `CKD-Operational-Alerts`
- Lambda log retention set to `30` days
- the following alarms now exist with actions enabled:
  - `CKD-Lambda-Errors-Any`
  - `CKD-Lambda-Duration-p95-High`
  - `CKD-Lambda-Throttles-Any`
  - `CKD-API-5XX-Any`

All four alarms are now wired to the SNS topic rather than existing only as passive dashboard objects.

## Validation

### 1. Syntax validation

The following hardening-related files passed Python compilation:

- `infra/ensure_sagemaker_execution_role.py`
- `infra/harden_operational_controls.py`
- `infra/launch_sagemaker_training_job.py`

### 2. Live role validation

The hardened SageMaker role remained usable after the managed full-access policy was removed.

The current role state is captured in:

- `artifacts/system_eval_aws/iam_operational_hardening_validation.json`

### 3. Live alarm validation

The current alarm state shows:

- actions enabled for all key alarms
- SNS action attached to each alarm
- alarm state currently `OK`

This indicates the monitoring layer is now active rather than merely present.

### 4. Live SageMaker smoke-job validation

A real SageMaker smoke job was re-run after the IAM changes and runtime fixes:

- training job: `ckd-autoprognosis-336-20260401-175823`
- status: `Completed`
- output artifact:
  - `s3://ckd-automl-artifacts-junxiang/sagemaker-training/autoprognosis-336/output/ckd-autoprognosis-336-20260401-175823/output/model.tar.gz`
- billable training time: `481` seconds

This is important because it confirms that the role hardening did not only preserve submission ability; it preserved a complete live cloud-training execution path.

## Practical Interpretation

The platform is now materially stronger in two ways.

First, the training role is no longer over-broad. The SageMaker path now operates inside a clearly scoped S3 prefix rather than relying on blanket full-access permissions.

Second, the live system now has active monitoring guardrails. Key alarms are wired to a notification topic, log retention is explicit, and Lambda throttling now has a dedicated alarm instead of remaining invisible.

## Boundary

This work does **not** yet mean that the platform is fully production-hardened.

The following boundaries still apply:

- the SNS alert topic currently has no confirmed email subscription
- live Lambda networking has not yet been switched into private-subnet mode
- CI/CD automation is still missing
- IAM review was focused on the most important live SageMaker and monitoring paths rather than every AWS role in the account

## Thesis-Safe Summary

This work can now be described as:

- a **verified IAM hardening pass** on the SageMaker training path
- a **verified operational hardening pass** on the live Lambda/API serving path
- with **active CloudWatch alarm-to-SNS wiring**
- with **explicit log-retention policy**
- and with a **completed live SageMaker smoke-training job after least-privilege tightening**

It should not yet be described as:

- full enterprise security hardening
- complete institutional operations governance
- fully automated production incident management
