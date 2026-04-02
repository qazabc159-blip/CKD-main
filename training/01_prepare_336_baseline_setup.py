import logging

from _baseline_common import (
    ARTIFACTS_DIR,
    FEATURE_TYPE_PLAN_PATH,
    MISSINGNESS_PATH,
    RANDOM_STATE,
    SETUP_SUMMARY_PATH,
    SPLIT_INDICES_PATH,
    TEST_SIZE,
    class_distribution,
    configure_logging,
    ensure_artifact_dir,
    infer_feature_type_plan,
    load_dataset,
    validate_target_binary,
    write_json,
    build_split_indices,
)


def main() -> None:
    configure_logging()
    ensure_artifact_dir()

    df = load_dataset()
    validate_target_binary(df)

    feature_type_plan_df = infer_feature_type_plan(df)
    feature_type_plan_df.to_csv(FEATURE_TYPE_PLAN_PATH, index=False)

    missingness_df = feature_type_plan_df[
        ["feature_name", "dtype", "missing_count", "missing_ratio"]
    ].rename(columns={"feature_name": "column"})
    missingness_df.to_csv(MISSINGNESS_PATH, index=False)

    split_df = build_split_indices(df)
    split_df.to_csv(SPLIT_INDICES_PATH, index=False)

    train_distribution = class_distribution(split_df.loc[split_df["split"] == "train", "target"])
    test_distribution = class_distribution(split_df.loc[split_df["split"] == "test", "target"])
    overall_distribution = class_distribution(df["target"])

    setup_summary = {
        "dataset_used": "data/processed/ckd_train_336_raw_aligned.csv",
        "row_count": int(df.shape[0]),
        "feature_count": int(df.shape[1] - 1),
        "feature_names": [column for column in df.columns if column != "target"],
        "class_distribution": overall_distribution,
        "split_strategy": {
            "method": "stratified_train_test_split",
            "test_size": TEST_SIZE,
            "random_state": RANDOM_STATE,
            "train_distribution": train_distribution,
            "test_distribution": test_distribution,
        },
        "numeric_feature_count": int(
            (feature_type_plan_df["inferred_feature_type"] == "numeric").sum()
        ),
        "categorical_feature_count": int(
            (feature_type_plan_df["inferred_feature_type"] == "categorical_or_binary_text").sum()
        ),
    }
    write_json(SETUP_SUMMARY_PATH, setup_summary)

    logging.info("Saved setup summary to %s", SETUP_SUMMARY_PATH)
    logging.info("Saved missingness summary to %s", MISSINGNESS_PATH)
    logging.info("Saved feature type plan to %s", FEATURE_TYPE_PLAN_PATH)
    logging.info("Saved reproducible split indices to %s", SPLIT_INDICES_PATH)


if __name__ == "__main__":
    main()
