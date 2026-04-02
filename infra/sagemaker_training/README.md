# SageMaker Training Layer

This directory contains the thesis-oriented SageMaker training path for the CKD platform.

## Scope

The current SageMaker training layer focuses on the main AutoPrognosis workflow on Dataset #336.
It is designed to provide a repeatable cloud-training path without requiring a custom Docker build.

Current job type:

- `autoprognosis_336`

## Files

- `entrypoint.py`
  - SageMaker training entrypoint
  - installs runtime requirements inside the training container
  - copies the dataset and baseline split from SageMaker input channels into the expected repo-relative paths
  - runs the AutoPrognosis training workflow
  - exports resulting artifacts to `SM_MODEL_DIR` and `SM_OUTPUT_DATA_DIR`
- `requirements-runtime.txt`
  - runtime packages installed inside the training container
- `requirements-launcher.txt`
  - local launcher dependencies
- `training_job_config_336.json`
  - default launcher configuration for the Dataset #336 AutoPrognosis job

## Default Inputs

The launcher submits two SageMaker input channels:

- `train`
  - `data/processed/ckd_train_336_raw_aligned.csv`
- `split`
  - `artifacts/baselines_336/split_indices_336.csv`

## Default Outputs

Successful training writes:

- model artifacts under `SM_MODEL_DIR/artifacts/autoprognosis_336/`
- a copied model file under `SM_MODEL_DIR/best_autoprognosis_model.pkl`
- a training manifest under `SM_OUTPUT_DATA_DIR/sagemaker_training_manifest.json`

## Notes

- The current implementation uses the SageMaker Scikit-learn framework container and installs thesis-specific runtime dependencies at job start.
- This avoids the need for a custom training image while keeping the cloud training path reproducible.
- Smoke-test mode is supported through launcher hyperparameter overrides so infrastructure can be validated without running the full study search depth.
