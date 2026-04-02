# 857 Representation Investigation

This module focuses on the representation problems in UCI dataset `857`.

## Why Dataset 857 Is Not Yet External-Validation Ready

Dataset `857` shares feature names with dataset `336`, but many of the values are not represented in the same way.

Examples include:

- binary text in `336` versus `0/1` numeric codes in `857`
- interval-style text such as `< 112`, `112 - 154`, and `>= 448`
- Excel-like token corruption such as `20-Dec`, `1-Jan`, `2-Feb`, and `4-Apr`

Because of these issues, dataset `857` should currently be treated as a secondary candidate validation dataset under representation investigation rather than a ready external-validation dataset.

## What This Investigation Module Does

- `data/06_investigate_857_representation.py`
  - compares shared features between `336` and `857`
  - classifies candidate representation types
  - writes `artifacts/857_representation_audit.csv`
  - writes `artifacts/857_representation_summary.json`

- `data/07_propose_857_harmonization_rules.py`
  - drafts conservative harmonization actions for each shared feature
  - writes `artifacts/857_harmonization_rules.csv`
  - writes `artifacts/857_harmonization_rules.md`

- `data/08_apply_safe_857_repairs.py`
  - applies only high-confidence safe repairs
  - writes `data/processed/ckd_valid_857_repaired_candidate_not_validation_ready.csv`
  - writes `artifacts/857_unresolved_features.csv`
  - writes `artifacts/857_safe_repair_report.csv`

- `data/09_confirm_857_binary_direction.py`
  - prepares a dedicated audit for the binary mismatch features
  - writes `artifacts/857_binary_direction_audit.csv`
  - writes `artifacts/857_binary_direction_summary.json`
  - creates `artifacts/857_binary_direction_rules.csv` as a manual confirmation template if it does not already exist

## Representation Problems Found

### Binary or categorical mismatch

Some features look like the same binary concept across datasets, but dataset `857` uses numeric codes while dataset `336` uses explicit text labels.

Examples:

- `ane`
- `cad`
- `dm`
- `htn`
- `pe`
- `appet`
- `ba`
- `pc`
- `pcc`
- `rbc`

These are not automatically remapped in this module because the semantic direction of `0/1` must be confirmed first.

### Interval or binned text

Some numeric-looking clinical variables in `336` appear in `857` as interval bins rather than raw continuous values.

Examples:

- `bgr`
- `bu`
- `hemo`
- `pcv`
- `pot`
- `rbcc`
- `sc`
- `sg`
- `sod`
- `wbcc`

For these features, a safe repair can preserve the ordering of bins within dataset `857`, but this does not make them equivalent to the continuous representation in `336`.

### Excel-like corruption

Some `857` tokens appear to have been altered by spreadsheet formatting.

Examples:

- `20-Dec`
- `1-Jan`
- `2-Feb`
- `3-Mar`
- `4-Apr`

These tokens should not be interpreted as dates. They are treated as evidence of possible label or interval corruption.

## Safe Repair Versus Unsafe Repair

Safe repair:

- normalize clearly interval-based text into ordered bin codes for within-`857` candidate use
- preserve the fact that the repaired value is an ordered bin, not a recovered continuous measurement
- record every applied mapping in `artifacts/857_safe_repair_report.csv`

Unsafe repair:

- assuming that `0` and `1` already map to the same positive/negative semantics as `336`
- converting interval text directly into continuous numeric values without justification
- guessing the original meaning of Excel-like corrupted tokens when confidence is low
- treating repaired `857` bins as automatically equivalent to `336` continuous feature space

## How To Decide Whether 857 Can Enter Cross-Dataset Validation Later

Dataset `857` should only be considered for cross-dataset validation after:

1. the binary code direction is confirmed for the mismatched categorical features
2. Excel-like corrupted tokens are either reliably repaired or explicitly excluded
3. the project decides which interval/binned features are acceptable as ordered-bin representations and which must be excluded
4. the harmonization policy is documented feature by feature in the rule artifacts

Cross-dataset harmonization is still provisional; only dataset `336` is currently baseline-ready.
