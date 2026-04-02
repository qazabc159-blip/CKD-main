# Sanity Check Summary

## Split Integrity Check

- train/test index overlap count: 0
- exact feature-row overlap count across splits: 0
- train target counts: {0: 120, 1: 200}
- test target counts: {0: 30, 1: 50}

## Quick Interpretation

- No train/test index overlap was detected.
- No exact duplicated feature rows were detected across train and test splits in this quick screen.
- No feature was flagged as obvious target leakage in this quick screen.
- Top signal features in this quick screen: hemo, pcv, sg, sc, rbcc, al, dm, sod, htn, bgr.
- Results are very strong, but no obvious leakage was detected in this quick sanity check.
- Further interpretation is still needed because dataset `336` may be intrinsically easy and several clinically plausible renal markers are highly informative.
