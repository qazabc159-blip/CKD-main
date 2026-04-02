import json
import logging

import pandas as pd

from _common import (
    ARTIFACTS_DIR,
    PROCESSED_DIR,
    configure_logging,
    encode_target,
    ensure_project_dirs,
    fetch_dataset,
    get_target_column,
    minimal_clean_dataframe,
)


CONFIRMED_MAPPING_PATH = ARTIFACTS_DIR / "feature_mapping_confirmed.csv"
TRAIN_OUTPUT_PATH = PROCESSED_DIR / "ckd_train_336_raw_aligned.csv"
VALID_OUTPUT_PATH = PROCESSED_DIR / "ckd_valid_857_raw_aligned.csv"
SHARED_FEATURE_LIST_PATH = ARTIFACTS_DIR / "shared_feature_list.json"
DROPPED_336_PATH = ARTIFACTS_DIR / "dropped_features_336.csv"
DROPPED_857_PATH = ARTIFACTS_DIR / "dropped_features_857.csv"

REQUIRED_MAPPING_COLUMNS = {
    "source_336_column",
    "source_857_column",
    "unified_name",
    "same_meaning",
    "same_unit",
    "keep_for_shared_model",
    "notes",
    "manual_review_required",
}


def load_confirmed_mapping() -> pd.DataFrame:
    if not CONFIRMED_MAPPING_PATH.exists():
        raise FileNotFoundError(
            f"Confirmed feature mapping file not found: {CONFIRMED_MAPPING_PATH}. "
            "Create it by reviewing artifacts/feature_mapping_candidates.csv."
        )

    mapping_df = pd.read_csv(CONFIRMED_MAPPING_PATH).fillna("")
    missing_columns = REQUIRED_MAPPING_COLUMNS - set(mapping_df.columns)
    if missing_columns:
        raise ValueError(
            f"Confirmed mapping file is missing required columns: {sorted(missing_columns)}"
        )

    keep_values = mapping_df["keep_for_shared_model"].astype(str).str.strip().str.lower()
    selected = mapping_df.loc[keep_values == "yes"].copy()
    if selected.empty:
        raise ValueError("No shared features were marked keep_for_shared_model=yes.")

    unresolved = selected.loc[
        selected["manual_review_required"].astype(str).str.strip().str.lower() == "yes"
    ]
    if not unresolved.empty:
        raise ValueError(
            "Selected shared features still have manual_review_required=yes. "
            "Resolve them before export."
        )

    blank_336 = selected["source_336_column"].astype(str).str.strip() == ""
    blank_857 = selected["source_857_column"].astype(str).str.strip() == ""
    blank_unified = selected["unified_name"].astype(str).str.strip() == ""
    if blank_336.any() or blank_857.any() or blank_unified.any():
        raise ValueError(
            "All selected shared features must provide source_336_column, source_857_column, "
            "and unified_name."
        )

    if selected["source_336_column"].duplicated().any():
        duplicates = selected.loc[selected["source_336_column"].duplicated(), "source_336_column"].tolist()
        raise ValueError(f"Duplicate source_336_column values in selected mapping rows: {duplicates}")

    if selected["source_857_column"].duplicated().any():
        duplicates = selected.loc[selected["source_857_column"].duplicated(), "source_857_column"].tolist()
        raise ValueError(f"Duplicate source_857_column values in selected mapping rows: {duplicates}")

    if selected["unified_name"].duplicated().any():
        duplicates = selected.loc[selected["unified_name"].duplicated(), "unified_name"].tolist()
        raise ValueError(f"Duplicate unified_name values in selected mapping rows: {duplicates}")

    return selected.reset_index(drop=True)


def build_aligned_frame(features: pd.DataFrame, mapping_df: pd.DataFrame, source_column_name: str) -> pd.DataFrame:
    required_columns = mapping_df[source_column_name].tolist()
    missing_columns = [column for column in required_columns if column not in features.columns]
    if missing_columns:
        raise KeyError(
            f"Required columns are missing from source dataset for {source_column_name}: {missing_columns}"
        )

    aligned = pd.DataFrame()
    for row in mapping_df.itertuples(index=False):
        source_column = getattr(row, source_column_name)
        aligned[row.unified_name] = features[source_column]
    return aligned


def build_dropped_features_report(all_columns: list[str], kept_columns: list[str]) -> pd.DataFrame:
    kept = set(kept_columns)
    dropped_rows = []
    for column in all_columns:
        if column in kept:
            continue
        dropped_rows.append(
            {
                "column": column,
                "reason": "Not selected for shared aligned export.",
            }
        )
    return pd.DataFrame(dropped_rows, columns=["column", "reason"])


def main() -> None:
    configure_logging()
    ensure_project_dirs()

    mapping_df = load_confirmed_mapping()

    _, raw_features_336, raw_targets_336 = fetch_dataset(336)
    _, raw_features_857, raw_targets_857 = fetch_dataset(857)

    features_336 = minimal_clean_dataframe(raw_features_336)
    features_857 = minimal_clean_dataframe(raw_features_857)

    target_column_336 = get_target_column(336, raw_targets_336)
    target_column_857 = get_target_column(857, raw_targets_857)

    target_336, unresolved_336 = encode_target(336, raw_targets_336[target_column_336])
    target_857, unresolved_857 = encode_target(857, raw_targets_857[target_column_857])
    if unresolved_336 or unresolved_857:
        raise ValueError(
            f"Unresolved target values detected. 336={unresolved_336}, 857={unresolved_857}"
        )

    aligned_336 = build_aligned_frame(features_336, mapping_df, "source_336_column")
    aligned_857 = build_aligned_frame(features_857, mapping_df, "source_857_column")

    aligned_336["target"] = target_336
    aligned_857["target"] = target_857

    aligned_336.to_csv(TRAIN_OUTPUT_PATH, index=False)
    aligned_857.to_csv(VALID_OUTPUT_PATH, index=False)

    shared_feature_payload = {
        "shared_feature_count": int(mapping_df.shape[0]),
        "shared_features": mapping_df["unified_name"].tolist(),
    }
    SHARED_FEATURE_LIST_PATH.write_text(
        json.dumps(shared_feature_payload, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )

    dropped_336 = build_dropped_features_report(list(raw_features_336.columns), mapping_df["source_336_column"].tolist())
    dropped_857 = build_dropped_features_report(list(raw_features_857.columns), mapping_df["source_857_column"].tolist())
    dropped_336.to_csv(DROPPED_336_PATH, index=False)
    dropped_857.to_csv(DROPPED_857_PATH, index=False)

    logging.info("Saved aligned training dataset to %s", TRAIN_OUTPUT_PATH)
    logging.info("Saved aligned validation dataset to %s", VALID_OUTPUT_PATH)
    logging.info("Saved shared feature list to %s", SHARED_FEATURE_LIST_PATH)
    logging.info("Saved dropped feature reports to %s and %s", DROPPED_336_PATH, DROPPED_857_PATH)


if __name__ == "__main__":
    main()
