import json
import logging

import pandas as pd

from _857_representation_common import (
    EXCEL_RISK_FEATURES,
    INTERVAL_RISK_FEATURES,
    LOW_RISK_BINARY_FEATURES,
    MAPPING_REQUIRED_BINARY_FEATURES,
    detect_representation_type,
    excel_like_tokens,
    interval_tokens,
    load_aligned_datasets,
    sample_values,
)
from _common import ARTIFACTS_DIR, configure_logging, ensure_project_dirs


AUDIT_CSV_PATH = ARTIFACTS_DIR / "857_representation_audit.csv"
SUMMARY_JSON_PATH = ARTIFACTS_DIR / "857_representation_summary.json"


def priority_group(feature_name: str) -> str:
    if feature_name in LOW_RISK_BINARY_FEATURES or feature_name in MAPPING_REQUIRED_BINARY_FEATURES:
        return "binary_or_categorical_mismatch"
    if feature_name in {"al", "su"}:
        return "ordinal_or_stage_like"
    if feature_name in INTERVAL_RISK_FEATURES:
        return "interval_or_numeric_mismatch"
    return "other"


def main() -> None:
    configure_logging()
    ensure_project_dirs()

    train_336, valid_857, shared_features = load_aligned_datasets()

    rows = []
    for feature_name in shared_features:
        series_336 = train_336[feature_name]
        series_857 = valid_857[feature_name]
        rep_336 = detect_representation_type(series_336)
        rep_857 = detect_representation_type(series_857)
        excel_tokens = excel_like_tokens(series_857)
        interval_examples = interval_tokens(series_857)[:10]

        notes = []
        if excel_tokens:
            notes.append("excel_like_tokens_detected")
        if interval_examples:
            notes.append("interval_style_values_detected")
        if feature_name in EXCEL_RISK_FEATURES:
            notes.append("high_priority_excel_investigation")
        if feature_name in INTERVAL_RISK_FEATURES:
            notes.append("high_priority_interval_investigation")

        rows.append(
            {
                "feature_name": feature_name,
                "priority_group": priority_group(feature_name),
                "dtype_style_336": str(series_336.dtype),
                "dtype_style_857": str(series_857.dtype),
                "representation_type_336": rep_336,
                "representation_type_857": rep_857,
                "unique_examples_336": json.dumps(sample_values(series_336), ensure_ascii=True),
                "unique_examples_857": json.dumps(sample_values(series_857), ensure_ascii=True),
                "excel_like_tokens_857": json.dumps(excel_tokens, ensure_ascii=True),
                "interval_examples_857": json.dumps(interval_examples, ensure_ascii=True),
                "notes": "; ".join(notes),
            }
        )

    audit_df = pd.DataFrame(rows)
    audit_df.to_csv(AUDIT_CSV_PATH, index=False)

    summary_payload = {
        "shared_feature_count": len(shared_features),
        "representation_type_counts_857": audit_df["representation_type_857"].value_counts().to_dict(),
        "binary_or_categorical_mismatch_features": sorted(
            [feature for feature in shared_features if feature in LOW_RISK_BINARY_FEATURES or feature in MAPPING_REQUIRED_BINARY_FEATURES]
        ),
        "ordinal_or_stage_like_features": ["al", "su"],
        "interval_or_numeric_mismatch_features": sorted(
            [feature for feature in shared_features if feature in INTERVAL_RISK_FEATURES]
        ),
        "excel_like_corruption_features": sorted(
            audit_df.loc[audit_df["representation_type_857"] == "excel_like_corrupted_token", "feature_name"].tolist()
        ),
    }
    SUMMARY_JSON_PATH.write_text(json.dumps(summary_payload, indent=2, ensure_ascii=True), encoding="utf-8")

    logging.info("Saved #857 representation audit CSV to %s", AUDIT_CSV_PATH)
    logging.info("Saved #857 representation summary JSON to %s", SUMMARY_JSON_PATH)


if __name__ == "__main__":
    main()
