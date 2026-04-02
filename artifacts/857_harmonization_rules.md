# 857 Harmonization Rules

This document proposes conservative representation harmonization rules for dataset `857`.
It is a rule draft for investigation and repair only. It does not declare dataset `857` fully ready for cross-dataset validation.

## High-Confidence Safe Repairs

- `bgr`: convert interval text to ordered bin code for within-857 repaired candidate export only.
- `bu`: convert interval text to ordered bin code for within-857 repaired candidate export only.
- `hemo`: convert interval text to ordered bin code for within-857 repaired candidate export only.
- `pcv`: convert interval text to ordered bin code for within-857 repaired candidate export only.
- `pot`: convert interval text to ordered bin code for within-857 repaired candidate export only.
- `rbcc`: convert interval text to ordered bin code for within-857 repaired candidate export only.
- `sc`: convert interval text to ordered bin code for within-857 repaired candidate export only.
- `sg`: convert interval text to ordered bin code for within-857 repaired candidate export only.
- `sod`: convert interval text to ordered bin code for within-857 repaired candidate export only.
- `wbcc`: convert interval text to ordered bin code for within-857 repaired candidate export only.

## Manual Review Required

- `age`: `repair_excel_like_token_then_convert_to_ordered_bin_code` (medium) - The token 20-Dec is likely a spreadsheet-corrupted interval label such as 12 - 20, but this should be confirmed before repair. High-risk feature due to Excel-like token or ordinal ambiguity. Not yet safe to treat as the same feature space as dataset 336.
- `al`: `unresolved` (low) - Excel-like tokens are present, but the original ordinal/bin semantics cannot be recovered with high confidence from the observed values alone. High-risk feature due to Excel-like token or ordinal ambiguity.
- `ane`: `keep_as_binary_and_map` (medium) - Likely a simple binary representation mismatch, but the 0/1 direction in dataset 857 must be confirmed before mapping.
- `appet`: `keep_as_binary_and_map` (medium) - Feature appears binary, but the semantic direction of dataset 857 numeric codes must be confirmed before any shared mapping is declared safe.
- `ba`: `keep_as_binary_and_map` (medium) - Feature appears binary, but the semantic direction of dataset 857 numeric codes must be confirmed before any shared mapping is declared safe.
- `cad`: `keep_as_binary_and_map` (medium) - Likely a simple binary representation mismatch, but the 0/1 direction in dataset 857 must be confirmed before mapping.
- `dm`: `keep_as_binary_and_map` (medium) - Likely a simple binary representation mismatch, but the 0/1 direction in dataset 857 must be confirmed before mapping.
- `htn`: `keep_as_binary_and_map` (medium) - Likely a simple binary representation mismatch, but the 0/1 direction in dataset 857 must be confirmed before mapping.
- `pc`: `keep_as_binary_and_map` (medium) - Feature appears binary, but the semantic direction of dataset 857 numeric codes must be confirmed before any shared mapping is declared safe.
- `pcc`: `keep_as_binary_and_map` (medium) - Feature appears binary, but the semantic direction of dataset 857 numeric codes must be confirmed before any shared mapping is declared safe.
- `pe`: `keep_as_binary_and_map` (medium) - Likely a simple binary representation mismatch, but the 0/1 direction in dataset 857 must be confirmed before mapping.
- `rbc`: `keep_as_binary_and_map` (medium) - Feature appears binary, but the semantic direction of dataset 857 numeric codes must be confirmed before any shared mapping is declared safe.
- `su`: `unresolved` (low) - Excel-like tokens are present, but the original ordinal/bin semantics cannot be recovered with high confidence from the observed values alone. High-risk feature due to Excel-like token or ordinal ambiguity.

## Interpretation Boundary

- High-confidence interval-to-bin repairs are only candidate within-857 repairs.
- They do not prove that dataset `857` shares the same feature space as dataset `336`.
- Features with unresolved Excel-like corruption or unresolved binary code direction remain unsafe for cross-dataset validation.
