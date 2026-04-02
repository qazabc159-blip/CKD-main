# AutoPrognosis Summary

## Final Run Status

- final status: `success`
- this summary refers to the authoritative run recorded in `artifacts/autoprognosis_336/run_status.json`
- preflight artifacts were archived under `artifacts/autoprognosis_336/archive_conflicts/` and should not be cited as final outputs
## Dataset Used

- `data/processed/ckd_train_336_raw_aligned.csv`
- rows: 400
- features: 23

## Split Strategy

- reused `artifacts/baselines_336/split_indices_336.csv`
- identical held-out test split to the baseline package

## Missingness Handling

- raw aligned CSV remained unchanged
- missingness was preserved outside the modeling workflow
- AutoPrognosis was configured to handle missingness internally via its configured imputer search space

## AutoPrognosis Configuration Summary

- classifiers: ['random_forest', 'xgboost', 'catboost']
- imputers: ['ice']
- feature_scaling: ['nop']
- feature_selection: ['nop']
- n_folds_cv: 5
- timeout: 300

## Held-Out Test Metrics

- AUROC: 1.000
- AUPRC: 1.000
- Accuracy: 1.000
- Precision: 1.000
- Recall (Sensitivity): 1.000
- Specificity: 1.000
- F1-score: 1.000
- Brier score: 0.021

## Important Caveats

- dataset `857` was not used in this AutoPrognosis stage
- deployment has not started
- the logistic_regression AutoPrognosis plugin was excluded because it is incompatible with scikit-learn 1.8.0 in this environment

## Comparison vs Baseline

- best baseline model in current package: `hist_gradient_boosting`
- baseline best AUROC: 1.000
- baseline best AUPRC: 1.000
- baseline best Accuracy: 0.988
- AutoPrognosis AUROC difference: 0.000
- AutoPrognosis AUPRC difference: 0.000
- AutoPrognosis Accuracy difference: 0.012
