# AutoPrognosis Consistency Cleanup Report

## Conflicts Found

- The current working tree did not contain a surviving `blockers.md` file.
- The main authoritative artifacts were internally consistent and indicated a successful run.
- The directory also contained preflight artifacts that were not part of the final authoritative run output and could confuse repo readers.

## Final Status Decision

- final status: `success`
- reason: the training log, metadata, saved model artifact, test results, predictions, and summary all agree on a completed successful run.
- additional check: `best_autoprognosis_model.pkl` was successfully loaded as a `WeightedEnsemble` during cleanup review.

## Authoritative Artifacts

- `artifacts/autoprognosis_336/run_status.json`
- `artifacts/autoprognosis_336/autoprognosis_training_log.json`
- `artifacts/autoprognosis_336/best_autoprognosis_metadata.json`
- `artifacts/autoprognosis_336/autoprognosis_run_config.json`
- `artifacts/autoprognosis_336/best_autoprognosis_model.pkl`
- `artifacts/autoprognosis_336/test_results.csv`
- `artifacts/autoprognosis_336/test_predictions_autoprognosis.csv`
- `artifacts/autoprognosis_336/confusion_matrix_autoprognosis.csv`
- `artifacts/autoprognosis_336/autoprognosis_summary.md`
- `artifacts/autoprognosis_336/baseline_vs_autoprognosis_comparison.csv`

## Archived or Conflict-Tagged Artifacts

- `artifacts/autoprognosis_336/archive_conflicts/preflight_cat`
- `artifacts/autoprognosis_336/archive_conflicts/preflight_workspace`
- `artifacts/autoprognosis_336/archive_conflicts/preflight_workspace_rf`
- `artifacts/autoprognosis_336/archive_conflicts/preflight_workspace_rf2`
- `artifacts/autoprognosis_336/archive_conflicts/preflight_xgb`
- `artifacts/autoprognosis_336/archive_conflicts/preflight_model_rf.pkl`

## How To Cite AutoPrognosis Results After Cleanup

- Use `artifacts/autoprognosis_336/run_status.json` as the single status authority.
- Use `artifacts/autoprognosis_336/best_autoprognosis_metadata.json` for the saved model and run configuration linkage.
- Use `artifacts/autoprognosis_336/autoprognosis_summary.md` and `artifacts/autoprognosis_336/test_results.csv` when citing the final evaluation outputs.
- Do not cite anything under `artifacts/autoprognosis_336/archive_conflicts/` as the final run result.
