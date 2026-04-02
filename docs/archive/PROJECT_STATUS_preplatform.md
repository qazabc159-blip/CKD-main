# Project Status (Legacy Snapshot)

This file is retained as a historical snapshot from the earlier pre-deployment phase of the project.

Important note:

- it does **not** describe the current platform state
- it predates the live AWS inference path, model registry, frontend hosting, governance layer, and GitHub-triggered CI work
- for current implementation status, refer to:
  - `README.md`
  - `artifacts/system_eval_aws/architecture_progress_summary_2026-04-02.md`

---
# Project Status

## Project Title
AWS-Based AutoML Platform for CKD Risk Prediction Using AutoPrognosis 2.0

## Completed

- abstract draft
- architecture diagram draft
- UI prototype
- dataset selection finalized
- label definition finalized
- shared feature schema v1
- raw aligned datasets exported
- value audit completed
- baseline experiments on `#336` completed
- AutoPrognosis main training on `#336` completed
- baseline versus AutoPrognosis comparison generated

## In Progress

- result interpretation for `#336`
- `#857` supplementary harmonization track
- repo cleanup and metadata normalization
- thesis Chapter 5 result drafting

## Not Started

- AWS deployment
- model registry implementation
- backend inference integration
- strict external validation using a confirmed harmonized secondary dataset
- thesis final writing

## Current Risks

- `#336` results are extremely strong and require sanity-check interpretation
- `#857` is not yet validation-ready as a strict cross-dataset benchmark
- metadata consistency across artifacts still needs cleanup

## Immediate Next Steps

1. Run sanity checks on the `#336` results and document whether any obvious leakage patterns appear.
2. Draft Chapter 5 result text using the existing baseline and AutoPrognosis artifacts.
3. Continue `#857` as a supplementary harmonization track without blocking the main `#336` line.

