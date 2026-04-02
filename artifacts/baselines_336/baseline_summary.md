# Baseline Summary

## Dataset Used

- `data/processed/ckd_train_336_raw_aligned.csv`
- rows: 400
- features: 23

## Split Strategy

- stratified train/test split with test size `0.2` and random_state `42`
- 5-fold Stratified CV on the training split
- overall class distribution: {'0': 150, '1': 250}
- train split class distribution: {'0': 120, '1': 200}
- test split class distribution: {'0': 30, '1': 50}

## Model List

- `logistic_regression`
- `random_forest`
- `hist_gradient_boosting`

## CV Summary

- `logistic_regression`: AUROC 0.998 +/- 0.003, AUPRC 0.999 +/- 0.001, F1 0.980 +/- 0.014
- `random_forest`: AUROC 1.000 +/- 0.000, AUPRC 1.000 +/- 0.000, F1 0.995 +/- 0.007
- `hist_gradient_boosting`: AUROC 1.000 +/- 0.000, AUPRC 1.000 +/- 0.000, F1 0.992 +/- 0.007

## Held-Out Test Summary

- `logistic_regression`: AUROC 0.977, AUPRC 0.989, Accuracy 0.938, Recall 0.960, Specificity 0.900, F1 0.950, Brier 0.055
- `random_forest`: AUROC 1.000, AUPRC 1.000, Accuracy 1.000, Recall 1.000, Specificity 1.000, F1 1.000, Brier 0.008
- `hist_gradient_boosting`: AUROC 1.000, AUPRC 1.000, Accuracy 0.988, Recall 0.980, Specificity 1.000, F1 0.990, Brier 0.005

## Best Baseline Model

- `hist_gradient_boosting` selected by `cv_mean_auroc`
- estimator: `HistGradientBoostingClassifier`
- boosting baseline note: xgboost unavailable; HistGradientBoostingClassifier was used as the boosting baseline substitute.

## Important Caveats

- dataset `857` was not used in this baseline package
- AutoPrognosis outputs are tracked separately in `artifacts/autoprognosis_336/`
- raw missingness is preserved outside sklearn pipelines
- imputation is performed only inside model pipelines for baseline experiments
- the current results come from dataset `336` only
