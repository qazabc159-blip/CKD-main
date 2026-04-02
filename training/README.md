# Training Module

## Current Status

The training module is currently focused on dataset `336` only.

At this stage:

- baseline experiments on dataset `336` are completed
- AutoPrognosis main training on dataset `336` is completed
- dataset `857` is not included in the current modeling stage
- AWS-based inference deployment is already implemented
- a SageMaker training-layer path now exists for the main AutoPrognosis workflow on dataset `336`

## What This Round Covers

This module currently contains two modeling tracks for `336`:

- a reproducible baseline experiment package
- a reproducible AutoPrognosis experiment package on the same held-out split

The baseline package includes:

- baseline setup and reproducible split artifacts
- Logistic Regression
- Random Forest
- XGBoost if available, otherwise `HistGradientBoostingClassifier`
- CV evaluation on the training split
- held-out test evaluation
- plots and markdown summary outputs

The AutoPrognosis package includes:

- setup reuse of the baseline split
- AutoPrognosis study configuration and training log
- framework-specific model artifact export
- held-out test evaluation on the same split as baseline
- plots and baseline-versus-AutoPrognosis comparison outputs

## Baseline Versus AutoPrognosis

Baseline models are used here to establish a defensible reference point.

They answer a different question from AutoPrognosis:

- baseline models: "What performance can standard models achieve under a reproducible sklearn pipeline?"
- AutoPrognosis: "Can a more automated clinical modeling workflow improve or match that baseline under the thesis setting?"

## Why Imputation Is Allowed Here

The raw aligned dataset is not modified in place.

For baseline models, imputation is allowed inside sklearn Pipelines and ColumnTransformers because:

- sklearn estimators generally require complete numeric inputs
- the preprocessing stays fully reproducible
- the imputation choice remains local to each model pipeline
- the raw aligned CSV remains unchanged outside the pipeline

This does not mean the repository has permanently imputed the dataset.

For AutoPrognosis, missingness is also preserved outside the raw CSV. Any missing-value handling performed by the framework is kept inside the modeling workflow and recorded in metadata rather than written back to the dataset file.

## Expected Outputs

Baseline artifacts are written to `artifacts/baselines_336/`, including:

- setup metadata
- split indices
- CV results
- held-out test results
- per-model prediction files
- best-model artifact and metadata
- ROC / PR / calibration plots
- confusion matrix for the best model
- markdown summary for thesis writing support

AutoPrognosis artifacts are written to `artifacts/autoprognosis_336/`, including:

- setup summary and split consistency checks
- run configuration and training log
- framework-specific saved model artifact
- held-out test metrics and predictions
- ROC / PR / calibration / confusion matrix plots
- markdown summary and baseline comparison table
