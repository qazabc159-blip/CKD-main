import json
import logging

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.model_selection import StratifiedKFold

from _baseline_common import (
    ARTIFACTS_DIR,
    BEST_METADATA_PATH,
    BEST_MODEL_PATH,
    CV_RESULTS_PATH,
    FEATURE_TYPE_PLAN_PATH,
    N_SPLITS,
    RANDOM_STATE,
    SPLIT_INDICES_PATH,
    TEST_RESULTS_PATH,
    build_model_specs,
    compute_metrics,
    configure_logging,
    cv_metric_columns,
    ensure_artifact_dir,
    get_feature_lists,
    load_dataset,
    predict_probability,
    repo_relpath,
    save_model,
    validate_target_binary,
)


def aggregate_cv_results(
    model_name: str,
    estimator_label: str,
    fallback_note: str | None,
    fold_metrics: list[dict[str, float]],
) -> dict[str, float | str | None]:
    row: dict[str, float | str] = {
        "model_name": model_name,
        "estimator_label": estimator_label,
        "fallback_note": fallback_note,
        "cv_fold_count": len(fold_metrics),
    }
    for metric_name in cv_metric_columns():
        values = np.array([metrics[metric_name] for metrics in fold_metrics], dtype=float)
        row[f"{metric_name}_mean"] = float(np.nanmean(values))
        row[f"{metric_name}_std"] = float(np.nanstd(values, ddof=1)) if len(values) > 1 else 0.0
    return row


def main() -> None:
    configure_logging()
    ensure_artifact_dir()

    if not FEATURE_TYPE_PLAN_PATH.exists() or not SPLIT_INDICES_PATH.exists():
        raise FileNotFoundError(
            "Missing baseline setup artifacts. Run training/01_prepare_336_baseline_setup.py first."
        )

    df = load_dataset()
    validate_target_binary(df)
    feature_type_plan_df = pd.read_csv(FEATURE_TYPE_PLAN_PATH)
    split_df = pd.read_csv(SPLIT_INDICES_PATH)
    numeric_features, categorical_features = get_feature_lists(feature_type_plan_df)

    feature_columns = [column for column in df.columns if column != "target"]
    train_indices = split_df.loc[split_df["split"] == "train", "row_index"].astype(int).tolist()
    test_indices = split_df.loc[split_df["split"] == "test", "row_index"].astype(int).tolist()

    X_train = df.loc[train_indices, feature_columns].reset_index(drop=True)
    y_train = df.loc[train_indices, "target"].reset_index(drop=True)
    X_test = df.loc[test_indices, feature_columns].reset_index(drop=True)
    y_test = df.loc[test_indices, "target"].reset_index(drop=True)
    original_test_row_indices = df.loc[test_indices].index.to_list()

    model_specs, fallback_note = build_model_specs(numeric_features, categorical_features)
    xgboost_is_available = any(spec["model_name"] == "xgboost" for spec in model_specs)
    cv_rows = []
    test_rows = []
    best_model = None
    best_model_name = None
    best_estimator_label = None
    best_cv_auroc = -np.inf

    cv_splitter = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=RANDOM_STATE)

    for spec in model_specs:
        model_name = spec["model_name"]
        estimator_label = spec["estimator_label"]
        pipeline = spec["pipeline"]
        row_fallback_note = fallback_note if model_name == "hist_gradient_boosting" else None
        logging.info("Running baseline model: %s", model_name)

        fold_metrics = []
        for fold_id, (fold_train_idx, fold_valid_idx) in enumerate(cv_splitter.split(X_train, y_train), start=1):
            fold_pipeline = clone(pipeline)
            X_fold_train = X_train.iloc[fold_train_idx]
            y_fold_train = y_train.iloc[fold_train_idx]
            X_fold_valid = X_train.iloc[fold_valid_idx]
            y_fold_valid = y_train.iloc[fold_valid_idx]

            fold_pipeline.fit(X_fold_train, y_fold_train)
            y_prob = predict_probability(fold_pipeline, X_fold_valid)
            y_pred = fold_pipeline.predict(X_fold_valid)
            metrics = compute_metrics(y_fold_valid, y_pred, y_prob)
            metrics["fold"] = fold_id
            fold_metrics.append(metrics)

        cv_summary_row = aggregate_cv_results(model_name, estimator_label, row_fallback_note, fold_metrics)
        cv_rows.append(cv_summary_row)

        pipeline.fit(X_train, y_train)
        y_test_prob = predict_probability(pipeline, X_test)
        y_test_pred = pipeline.predict(X_test)
        test_metrics = compute_metrics(y_test, y_test_pred, y_test_prob)

        prediction_df = pd.DataFrame(
            {
                "row_index": original_test_row_indices,
                "target_true": y_test,
                "prediction_label": y_test_pred,
                "risk_score": y_test_prob,
            }
        )
        prediction_path = ARTIFACTS_DIR / f"test_predictions_{model_name}.csv"
        prediction_df.to_csv(prediction_path, index=False)

        test_row = {
            "model_name": model_name,
            "estimator_label": estimator_label,
            "fallback_note": row_fallback_note,
            **test_metrics,
        }
        test_rows.append(test_row)

        if cv_summary_row["auroc_mean"] > best_cv_auroc:
            best_cv_auroc = float(cv_summary_row["auroc_mean"])
            best_model = pipeline
            best_model_name = model_name
            best_estimator_label = estimator_label

    cv_results_df = pd.DataFrame(cv_rows)
    test_results_df = pd.DataFrame(test_rows)
    cv_results_df.to_csv(CV_RESULTS_PATH, index=False)
    test_results_df.to_csv(TEST_RESULTS_PATH, index=False)

    if best_model is None or best_model_name is None or best_estimator_label is None:
        raise RuntimeError("Failed to select a best baseline model.")

    save_model(best_model)
    best_test_row = test_results_df.loc[test_results_df["model_name"] == best_model_name].iloc[0].to_dict()
    metadata = {
        "dataset_used": "data/processed/ckd_train_336_raw_aligned.csv",
        "selection_metric": "cv_mean_auroc",
        "best_model_name": best_model_name,
        "best_estimator_label": best_estimator_label,
        "xgboost_available": xgboost_is_available,
        "boosting_baseline_note": fallback_note,
        "test_metrics": best_test_row,
        "feature_type_plan_path": repo_relpath(FEATURE_TYPE_PLAN_PATH),
        "split_indices_path": repo_relpath(SPLIT_INDICES_PATH),
    }
    BEST_METADATA_PATH.write_text(json.dumps(metadata, indent=2, ensure_ascii=True), encoding="utf-8")

    logging.info("Saved CV results to %s", CV_RESULTS_PATH)
    logging.info("Saved test results to %s", TEST_RESULTS_PATH)
    logging.info("Saved best baseline model to %s", BEST_MODEL_PATH)
    logging.info("Saved best baseline metadata to %s", BEST_METADATA_PATH)


if __name__ == "__main__":
    main()
