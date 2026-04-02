# CKD AutoML Platform

Design and Implementation of an AWS-Based AutoML Platform for Chronic Kidney Disease Risk Prediction Using AutoPrognosis 2.0

## Project Overview

This repository supports a master's thesis project focused on CKD risk prediction with structured clinical data, reproducible data and modeling workflows, and later-stage platform integration planning.

The current repository state is centered on the data-and-method layer for dataset `336`, with supporting documentation and future-system drafts kept separate from the active modeling line.

## Current Scope

The current active scope includes:

- finalized dataset selection and binary target definition
- shared feature schema v1 and aligned dataset export
- data-layer audit and representation investigation
- baseline experiments on dataset `336`
- AutoPrognosis main training on dataset `336`
- baseline-versus-AutoPrognosis comparison artifacts
- thesis-oriented documentation and repo hygiene updates

The current scope does not yet include:

- AWS backend or deployment implementation
- Lambda / API inference integration
- model registry implementation
- formal use of dataset `857` as a strict external validation set

## Current Progress Summary

Completed:

- dataset `336` finalized as the primary training and development dataset
- dataset `857` retained as a secondary candidate validation / supplementary harmonization track
- data-layer audit completed
- baseline experiments on dataset `336` completed
- AutoPrognosis main training on dataset `336` completed
- baseline-versus-AutoPrognosis comparison artifacts generated

In progress:

- result interpretation for dataset `336`
- supplementary harmonization and investigation for dataset `857`
- thesis Chapter 5 result drafting

Not started:

- deployment / AWS backend
- model registry implementation
- API integration for real inference
- strict external validation using a confirmed harmonized secondary dataset

## Dataset Decisions

- UCI dataset `336` is the primary training and development dataset.
- UCI dataset `857` remains a secondary candidate validation dataset under supplementary harmonization and representation investigation.
- Both tasks are currently binary classification.
- The target column is unified as `target`.
- Missingness is intentionally preserved outside the modeling workflow; the repository does not treat the raw aligned CSV as permanently imputed.

Important conservative note:

- dataset `857` is not yet a confirmed strict external validation set
- cross-dataset harmonization remains provisional

## Current Data-Layer Outputs

The repository already contains:

- dataset fetching and profiling scripts in `data/`
- exact label mapping artifacts in `artifacts/label_mapping_336.json` and `artifacts/label_mapping_857.json`
- shared feature schema v1 artifacts in `artifacts/feature_mapping_confirmed.csv` and `artifacts/shared_feature_list.json`
- aligned dataset exports in `data/processed/ckd_train_336_raw_aligned.csv` and `data/processed/ckd_valid_857_raw_aligned.csv`
- value-audit outputs in `artifacts/value_audit_shared_features.csv`, `artifacts/value_audit_shared_features.json`, and `artifacts/type_plan_shared_features.csv`
- supplementary representation investigation outputs for dataset `857`

## What Is Ready Now

- dataset `336` is the active modeling dataset for the thesis main line
- baseline artifacts for dataset `336` exist under `artifacts/baselines_336/`
- AutoPrognosis artifacts for dataset `336` exist under `artifacts/autoprognosis_336/`
- baseline versus AutoPrognosis comparison artifacts have been generated
- the current repository structure is stable enough for follow-up interpretation and thesis writing work

## What Is Not Ready Yet

- dataset `857` is not validation-ready as a strict cross-dataset benchmark
- cross-dataset harmonization is still provisional
- AWS deployment work has not started
- backend inference integration has not started
- model registry implementation has not started

## Repository Structure

- `data/`: data-layer scripts, aligned outputs, and investigation notes
- `training/`: baseline, AutoPrognosis, and sanity-check scripts for dataset `336`
- `artifacts/`: audit outputs, modeling artifacts, summaries, and comparison files
- `docs/`: thesis notes, architecture notes, dataset notes, and experiment planning
- `backend/`: future backend contract drafts and placeholders
- `web/`: UI prototype materials
- `infra/`: future infrastructure planning notes
- `data_schema/`: schema templates and feature dictionary scaffolding

## Immediate Next Steps

1. Run sanity-focused interpretation on the very strong `336` results and document what appears clinically plausible versus what needs extra caution.
2. Draft Chapter 5 result text using the baseline and AutoPrognosis artifacts already in the repo.
3. Continue the `857` track as a supplementary harmonization line without blocking the main `336` thesis workflow.

## Notes

- This repository should remain private unless project policies and repo contents are reviewed first.
- Do not commit secrets, credentials, or patient-identifiable data.
- Use `.env.example` or secret managers for configuration placeholders only.
