Table 5.1 summarizes the held-out test-set performance of the three baseline models on Dataset #336.

Table 5.1. Baseline model performance on the held-out test set of Dataset #336. Values are reported as point estimates with 95% bootstrap confidence intervals. HistGradientBoostingClassifier and Random Forest both achieved near-ceiling discrimination on this split, whereas Logistic Regression remained strong but comparatively lower.

| Model | AUROC | AUPRC | Accuracy | Sensitivity | Specificity | F1-score | Brier score |
|---|---|---|---|---|---|---|---|
| Logistic Regression | 0.977 (0.945-1.000) | 0.989 (0.974-1.000) | 0.938 (0.887-0.988) | 0.960 (0.900-1.000) | 0.900 (0.799-1.000) | 0.950 (0.907-0.990) | 0.055 (0.016-0.099) |
| Random Forest | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | 0.008 (0.004-0.014) |
| HistGradientBoostingClassifier | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | 0.988 (0.963-1.000) | 0.980 (0.940-1.000) | 1.000 (1.000-1.000) | 0.990 (0.969-1.000) | 0.005 (0.000-0.014) |

Note. Values are presented as point estimate (95% bootstrap CI) based on 2,000 stratified percentile bootstrap replicates. HistGradientBoostingClassifier was used as the boosting-oriented baseline in place of XGBoost because of an environment-specific compatibility issue with the local software stack.
