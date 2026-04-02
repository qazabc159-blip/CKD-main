# SageMaker Training Layer Report

- generated_at_utc: `2026-04-01T18:17:00Z`
- scope: `prototype SageMaker training path for the main AutoPrognosis workflow on Dataset #336`

## Purpose

This work item added the missing training-side cloud layer that previously remained outside the implemented AWS platform slice.

The goal was not to build a full production MLOps system in one step, but to establish a defensible and repeatable SageMaker training path for the thesis platform.

## What Was Added

### 1. SageMaker training entrypoint

Added:

- `infra/sagemaker_training/entrypoint.py`

This entrypoint:

- accepts SageMaker hyperparameters for the main AutoPrognosis workflow
- reads Dataset #336 and the baseline split through SageMaker input channels
- reconstructs the expected repo-relative file layout inside the training container
- runs the AutoPrognosis training workflow
- exports the resulting artifacts into SageMaker model/output directories

### 2. Runtime dependency definition

Added:

- `infra/sagemaker_training/requirements-runtime.txt`

The runtime definition was finalized into a container-compatible thesis-oriented set:

- `autoprognosis==0.1.22`
- `cloudpickle==3.1.1`
- `xgboost==3.2.0`
- `catboost==1.2.10`
- `joblib`
- `matplotlib`

This replaced an earlier impossible `scikit-learn==1.8.0` pin that could not be resolved inside the SageMaker Scikit-learn `1.4-2` Python 3.10 container.

### 3. Local launcher dependencies

Added:

- `infra/sagemaker_training/requirements-launcher.txt`

This supports the local launcher path through the SageMaker Python SDK.

### 4. Default job configuration

Added:

- `infra/sagemaker_training/training_job_config_336.json`

This config defines the default cloud-training path for:

- region: `ap-northeast-1`
- role name: `CKDSageMakerExecutionRole`
- artifact bucket: `ckd-automl-artifacts-junxiang`
- framework container: SageMaker Scikit-learn `1.4-2`
- smoke-test and full-search hyperparameter presets

### 5. SageMaker execution role bootstrap

Added:

- `infra/ensure_sagemaker_execution_role.py`

This script ensures that a thesis-specific SageMaker execution role exists.

Observed result:

- role created successfully
- role ARN: `arn:aws:iam::098890538524:role/CKDSageMakerExecutionRole`

### 6. SageMaker launcher

Added:

- `infra/launch_sagemaker_training_job.py`

This launcher:

- stages the required source files
- uploads the dataset and split file to S3
- builds the SageMaker estimator
- submits a training job request
- writes a launch manifest
- now pins the training source bundle under:
  - `s3://ckd-automl-artifacts-junxiang/sagemaker-training/autoprognosis-336/code/`

That explicit `code_location` matters because it keeps the job source bundle inside the same S3 prefix already allowed by the hardened execution role.

## Validation

### 1. Syntax validation

The following files passed Python compilation:

- `infra/sagemaker_training/entrypoint.py`
- `infra/ensure_sagemaker_execution_role.py`
- `infra/launch_sagemaker_training_job.py`

### 2. Local SageMaker-style smoke execution

The SageMaker entrypoint was executed locally with:

- `smoke_test=true`
- reduced AutoPrognosis search depth
- local environment variables mimicking SageMaker channels and output directories

Observed result:

- the entrypoint completed successfully
- the training manifest was written to:
  - `artifacts/system_eval_aws/sagemaker_local_output/sagemaker_training_manifest.json`
- model/output export logic worked as expected

This confirmed that the entrypoint is operational rather than merely declarative.

### 3. Execution role validation

The execution-role bootstrap ran successfully and created:

- `CKDSageMakerExecutionRole`

This means the training path is no longer blocked by a missing service role.

### 4. S3 input staging validation

The launcher successfully uploaded the required SageMaker input files to S3:

- `s3://ckd-automl-artifacts-junxiang/sagemaker-training/autoprognosis-336/output/input/train/ckd_train_336_raw_aligned.csv`
- `s3://ckd-automl-artifacts-junxiang/sagemaker-training/autoprognosis-336/output/input/split/split_indices_336.csv`

This confirms that the cloud-training path reached the staged-input phase successfully.

### 5. Live SageMaker smoke-training execution

A real SageMaker smoke job completed successfully:

- training job: `ckd-autoprognosis-336-20260401-175823`
- status: `Completed`
- model artifact:
  - `s3://ckd-automl-artifacts-junxiang/sagemaker-training/autoprognosis-336/output/ckd-autoprognosis-336-20260401-175823/output/model.tar.gz`
- billable training time: `481` seconds

This is the most important validation milestone because it confirms:

- real training-instance allocation worked
- the hardened execution role remained sufficient
- the explicit `code_location` fix worked
- the container-compatible runtime set worked
- the training layer now has one fully completed live cloud execution path

## Practical Interpretation

The SageMaker training layer is now implemented to a meaningful verified prototype level.

What is already true:

- a cloud-training entrypoint exists
- a launcher exists
- an execution role exists
- source staging works
- S3 input staging works
- a real SageMaker training job can complete successfully
- a training model artifact is produced in S3

What is not yet true:

- full study-scale training orchestration has not been benchmarked in SageMaker
- automated retraining / CI-CD coupling is not yet in place
- the training layer should not yet be described as full production MLOps

## Thesis-Safe Boundary

This work can now be described as:

- a **verified SageMaker training-layer implementation**
- with **local smoke validation**
- with **real S3 staging**
- with **successful role creation**
- and with **one completed live SageMaker smoke-training job**

It should not yet be described as:

- completed production MLOps orchestration
- large-scale retraining automation
- fully validated institutional training operations

## Most Relevant Files

- `infra/sagemaker_training/entrypoint.py`
- `infra/sagemaker_training/requirements-runtime.txt`
- `infra/sagemaker_training/requirements-launcher.txt`
- `infra/sagemaker_training/training_job_config_336.json`
- `infra/ensure_sagemaker_execution_role.py`
- `infra/launch_sagemaker_training_job.py`
- `artifacts/system_eval_aws/sagemaker_local_output/sagemaker_training_manifest.json`
- `artifacts/system_eval_aws/sagemaker_training_launch_manifest.json`
- `artifacts/system_eval_aws/iam_operational_hardening_validation.json`
