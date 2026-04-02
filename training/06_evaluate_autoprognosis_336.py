import logging

import pandas as pd

from _autoprognosis_common import (
    CONFUSION_MATRIX_CSV_PATH,
    FEATURE_TYPE_PLAN_PATH,
    METADATA_PATH,
    TEST_PREDICTIONS_PATH,
    TEST_RESULTS_PATH,
    compute_metrics,
    configure_logging,
    ensure_artifact_dir,
    load_dataset,
    load_split_indices,
    load_weighted_ensemble,
    prediction_vector,
    probability_vector,
)


def main() -> None:
    configure_logging()
    ensure_artifact_dir()

    if not METADATA_PATH.exists():
        raise FileNotFoundError(
            "Missing AutoPrognosis model metadata. Run training/05_run_autoprognosis_336.py first."
        )

    df = load_dataset()
    _, test_indices, _ = load_split_indices(df)
    feature_columns = [column for column in df.columns if column != "target"]
    X_test = df.loc[test_indices, feature_columns].reset_index(drop=True)
    y_test = df.loc[test_indices, "target"].reset_index(drop=True)
    original_test_indices = df.loc[test_indices].index.to_list()

    model = load_weighted_ensemble()
    y_prob = probability_vector(model, X_test)
    y_pred = prediction_vector(model, X_test)
    metrics = compute_metrics(y_test, y_pred, y_prob)

    test_results_df = pd.DataFrame(
        [
            {
                "model_name": "autoprognosis",
                **metrics,
            }
        ]
    )
    test_results_df.to_csv(TEST_RESULTS_PATH, index=False)

    predictions_df = pd.DataFrame(
        {
            "row_index": original_test_indices,
            "target_true": y_test,
            "prediction_label": y_pred,
            "risk_score": y_prob,
        }
    )
    predictions_df.to_csv(TEST_PREDICTIONS_PATH, index=False)

    confusion_df = pd.crosstab(
        pd.Series(y_test, name="target_true"),
        pd.Series(y_pred, name="prediction_label"),
        dropna=False,
    ).reindex(index=[0, 1], columns=[0, 1], fill_value=0)
    confusion_df.to_csv(CONFUSION_MATRIX_CSV_PATH)

    logging.info("Saved AutoPrognosis test results to %s", TEST_RESULTS_PATH)
    logging.info("Saved AutoPrognosis predictions to %s", TEST_PREDICTIONS_PATH)
    logging.info("Saved AutoPrognosis confusion matrix CSV to %s", CONFUSION_MATRIX_CSV_PATH)


if __name__ == "__main__":
    main()
