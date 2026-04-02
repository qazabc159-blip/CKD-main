# Data Module

This module implements the thesis project's current data-and-method layer for the two selected UCI datasets.

## Dataset Roles

- UCI dataset `336` is the main training and development dataset.
- UCI dataset `857` is the independent supplemental validation dataset.
- Both datasets are currently treated as binary classification tasks only.
- The final target column name is standardized as `target`.

## Target Definition

- Dataset `336` uses the raw `class` values `ckd`, `ckd\t`, and `notckd`.
- Dataset `857` uses the raw `class` values `ckd` and `notckd`.
- The label mapping must be exact and auditable. No fuzzy substring matching is allowed.
- The current binary encoding is:
  - CKD -> `1`
  - non-CKD -> `0`

## Why Missing Values Are Preserved

- Missingness is part of the original clinical-data signal and audit trail.
- AutoPrognosis 2.0 is expected to evaluate imputation as part of the downstream pipeline.
- Pre-emptive `fillna`, mean imputation, median imputation, or `SimpleImputer` would leak an early preprocessing choice into every later experiment.
- The current scripts therefore keep raw missing values intact and only perform minimal cleaning:
  - column-name handling
  - string trimming
  - exact target encoding
  - data-type normalization when values are already numeric-like
  - duplicate and invalid-structure checks during export

## Shared Feature Alignment Principles

- Do not use simple column-name intersection as the final shared schema.
- Generate a candidate mapping table first, then review it manually.
- Do not force proxy mappings such as `egfr -> sc` or `uacr -> al`.
- If a mapping is not fully defensible, mark it as `manual_review_required`.
- `04_export_aligned_datasets.py` only exports aligned datasets from a manually confirmed mapping file.

## Directory Usage

- `data/raw/`: reserved for optional raw snapshots if you later decide to persist downloaded source tables locally.
- `data/processed/`: aligned modeling-ready exports that keep raw missing values.
- `artifacts/`: profiling results, label-mapping records, mapping candidates, shared-feature lists, dropped-feature reports, and downstream audit outputs.

## Scripts

- `data/01_fetch_and_profile.py`: download UCI datasets `336` and `857`, print audit summaries, and save profiling artifacts.
- `data/02_define_labels.py`: inspect raw target values and save exact binary label mappings.
- `data/03_feature_mapping_template.py`: generate feature-alignment candidates for manual review.
- `data/04_export_aligned_datasets.py`: export aligned raw datasets after you create `artifacts/feature_mapping_confirmed.csv`.
- `data/05_value_audit_and_type_plan.py`: audit the 23 shared features across datasets `336` and `857`, flag representation mismatches, and write a downstream type-review plan without forcing final encodings.

## Rule Tables

- `artifacts/06_shared_representation_rules.csv`: manual decision table for cross-dataset representation harmonization, including which features are binary-first, mapping-required categorical, or not yet safe for shared external validation.
