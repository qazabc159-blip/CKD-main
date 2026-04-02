# Statistical Testing for Dataset #336 (Chapter 5.7)

- Inputs: existing held-out prediction artifacts only; no model retraining was performed.
- Method metadata: `artifacts/statistics_336/statistical_tests_336_method.json`
- Pairwise AUROC comparisons: DeLong test for correlated ROC curves.
- Pairwise thresholded comparisons: exact McNemar test on prediction correctness.
- Multiple-comparison control: Bonferroni correction within each test family.

## Pairwise DeLong Tests (AUROC)

| Comparison | AUROC (A) | AUROC (B) | Difference (A-B) | Raw p-value | Bonferroni-adjusted p-value | Significant |
| --- | --- | --- | --- | --- | --- | --- |
| Logistic Regression vs Random Forest | 0.977 | 1.000 | -0.023 | 0.1106 | 0.6636 | No |
| Logistic Regression vs HistGradientBoostingClassifier | 0.977 | 1.000 | -0.023 | 0.1106 | 0.6636 | No |
| Logistic Regression vs AutoPrognosis | 0.977 | 1.000 | -0.023 | 0.1106 | 0.6636 | No |
| Random Forest vs HistGradientBoostingClassifier | 1.000 | 1.000 | 0.000 | 1.0000 | 1.0000 | No |
| Random Forest vs AutoPrognosis | 1.000 | 1.000 | 0.000 | 1.0000 | 1.0000 | No |
| HistGradientBoostingClassifier vs AutoPrognosis | 1.000 | 1.000 | 0.000 | 1.0000 | 1.0000 | No |

## Pairwise McNemar Tests (Thresholded Predictions)

| Comparison | Accuracy (A) | Accuracy (B) | A correct / B wrong | A wrong / B correct | Raw p-value | Bonferroni-adjusted p-value | Significant |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Logistic Regression vs Random Forest | 0.938 | 1.000 | 0 | 5 | 0.0625 | 0.3750 | No |
| Logistic Regression vs HistGradientBoostingClassifier | 0.938 | 0.988 | 1 | 5 | 0.2188 | 1.0000 | No |
| Logistic Regression vs AutoPrognosis | 0.938 | 1.000 | 0 | 5 | 0.0625 | 0.3750 | No |
| Random Forest vs HistGradientBoostingClassifier | 1.000 | 0.988 | 1 | 0 | 1.0000 | 1.0000 | No |
| Random Forest vs AutoPrognosis | 1.000 | 1.000 | 0 | 0 | 1.0000 | 1.0000 | No |
| HistGradientBoostingClassifier vs AutoPrognosis | 0.988 | 1.000 | 0 | 1 | 1.0000 | 1.0000 | No |
