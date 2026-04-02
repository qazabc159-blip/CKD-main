import logging

from _autoprognosis_common import (
    FEATURE_TYPE_PLAN_PATH,
    SETUP_SUMMARY_PATH,
    SPLIT_CHECK_PATH,
    build_setup_summary,
    build_split_check,
    configure_logging,
    ensure_artifact_dir,
    load_dataset,
    load_split_indices,
    write_json,
)
from _baseline_common import infer_feature_type_plan


def main() -> None:
    configure_logging()
    ensure_artifact_dir()

    df = load_dataset()
    train_indices, test_indices, split_df = load_split_indices(df)
    feature_type_plan_df = infer_feature_type_plan(df)
    feature_type_plan_df.to_csv(FEATURE_TYPE_PLAN_PATH, index=False)

    split_check = build_split_check(df, split_df)
    setup_summary = build_setup_summary(df, feature_type_plan_df, split_check)
    write_json(SPLIT_CHECK_PATH, split_check)
    write_json(SETUP_SUMMARY_PATH, setup_summary)

    logging.info("Saved AutoPrognosis setup summary to %s", SETUP_SUMMARY_PATH)
    logging.info("Saved AutoPrognosis feature type plan to %s", FEATURE_TYPE_PLAN_PATH)
    logging.info("Saved split consistency check to %s", SPLIT_CHECK_PATH)


if __name__ == "__main__":
    main()
