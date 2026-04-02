import json
import logging

import pandas as pd

from _857_representation_common import (
    LOW_RISK_BINARY_FEATURES,
    MAPPING_REQUIRED_BINARY_FEATURES,
    detect_representation_type,
    load_aligned_datasets,
    normalized_non_null_values,
)
from _common import ARTIFACTS_DIR, configure_logging, ensure_project_dirs


BINARY_FEATURE_ORDER = [
    "ane",
    "appet",
    "ba",
    "cad",
    "dm",
    "htn",
    "pc",
    "pcc",
    "pe",
    "rbc",
]

AUDIT_CSV_PATH = ARTIFACTS_DIR / "857_binary_direction_audit.csv"
SUMMARY_JSON_PATH = ARTIFACTS_DIR / "857_binary_direction_summary.json"
RULES_CSV_PATH = ARTIFACTS_DIR / "857_binary_direction_rules.csv"


def value_counts_payload(series: pd.Series) -> dict[str, int]:
    counts = series.value_counts(dropna=False)
    payload: dict[str, int] = {}
    for value, count in counts.items():
        if pd.isna(value):
            key = "<NA>"
        elif isinstance(value, float) and value.is_integer():
            key = str(int(value))
        else:
            key = str(value).strip()
        payload[key] = int(count)
    return payload


def target_group_payload(df: pd.DataFrame, feature_name: str) -> dict[str, dict[str, int]]:
    payload: dict[str, dict[str, int]] = {}
    grouped = df.groupby("target")[feature_name].value_counts(dropna=False)
    for (target_value, feature_value), count in grouped.items():
        target_key = str(int(target_value))
        if pd.isna(feature_value):
            feature_key = "<NA>"
        elif isinstance(feature_value, float) and feature_value.is_integer():
            feature_key = str(int(feature_value))
        else:
            feature_key = str(feature_value).strip()
        payload.setdefault(target_key, {})[feature_key] = int(count)
    return payload


def current_direction_note(feature_name: str) -> str:
    if feature_name in LOW_RISK_BINARY_FEATURES:
        return "Likely binary mismatch only, but 857 code direction still needs explicit confirmation."
    if feature_name in MAPPING_REQUIRED_BINARY_FEATURES:
        return "Binary-looking feature, but 857 code direction and semantic polarity are not yet confirmed."
    return "Manual review required."


def build_audit_rows(train_336: pd.DataFrame, valid_857: pd.DataFrame) -> list[dict[str, str]]:
    rows = []
    for feature_name in BINARY_FEATURE_ORDER:
        series_336 = train_336[feature_name]
        series_857 = valid_857[feature_name]

        rows.append(
            {
                "feature_name": feature_name,
                "representation_type_336": detect_representation_type(series_336),
                "representation_type_857": detect_representation_type(series_857),
                "dtype_336": str(series_336.dtype),
                "dtype_857": str(series_857.dtype),
                "unique_values_336": json.dumps(normalized_non_null_values(series_336), ensure_ascii=True),
                "unique_values_857": json.dumps(normalized_non_null_values(series_857), ensure_ascii=True),
                "value_counts_336": json.dumps(value_counts_payload(series_336), ensure_ascii=True),
                "value_counts_857": json.dumps(value_counts_payload(series_857), ensure_ascii=True),
                "target_breakdown_336": json.dumps(target_group_payload(train_336, feature_name), ensure_ascii=True),
                "target_breakdown_857": json.dumps(target_group_payload(valid_857, feature_name), ensure_ascii=True),
                "manual_review_required": "yes",
                "notes": current_direction_note(feature_name),
            }
        )
    return rows


def create_rules_template(audit_df: pd.DataFrame) -> None:
    if RULES_CSV_PATH.exists():
        logging.info("Binary direction rules file already exists. Keeping existing file: %s", RULES_CSV_PATH)
        return

    template_rows = []
    for row in audit_df.itertuples(index=False):
        template_rows.append(
            {
                "feature_name": row.feature_name,
                "representation_type_336": row.representation_type_336,
                "representation_type_857": row.representation_type_857,
                "unique_values_336": row.unique_values_336,
                "unique_values_857": row.unique_values_857,
                "value_counts_336": row.value_counts_336,
                "value_counts_857": row.value_counts_857,
                "target_breakdown_336": row.target_breakdown_336,
                "target_breakdown_857": row.target_breakdown_857,
                "confirmed_857_meaning_for_0": "",
                "confirmed_857_meaning_for_1": "",
                "confirmed_mapping_to_336": "",
                "safe_to_apply_binary_harmonization": "pending_review",
                "manual_review_required": "yes",
                "notes": row.notes,
            }
        )

    pd.DataFrame(template_rows).to_csv(RULES_CSV_PATH, index=False)
    logging.info("Created binary direction rules template: %s", RULES_CSV_PATH)


def main() -> None:
    configure_logging()
    ensure_project_dirs()

    train_336, valid_857, shared_features = load_aligned_datasets()
    missing_binary_features = [feature for feature in BINARY_FEATURE_ORDER if feature not in shared_features]
    if missing_binary_features:
        raise KeyError(f"Shared feature list is missing expected binary features: {missing_binary_features}")

    audit_rows = build_audit_rows(train_336, valid_857)
    audit_df = pd.DataFrame(audit_rows)
    audit_df.to_csv(AUDIT_CSV_PATH, index=False)

    summary_payload = {
        "binary_feature_count": len(BINARY_FEATURE_ORDER),
        "binary_features_under_confirmation": BINARY_FEATURE_ORDER,
        "likely_simple_binary_mismatch": [feature for feature in BINARY_FEATURE_ORDER if feature in LOW_RISK_BINARY_FEATURES],
        "mapping_required_binary_features": [feature for feature in BINARY_FEATURE_ORDER if feature in MAPPING_REQUIRED_BINARY_FEATURES],
        "manual_review_required": BINARY_FEATURE_ORDER,
    }
    SUMMARY_JSON_PATH.write_text(json.dumps(summary_payload, indent=2, ensure_ascii=True), encoding="utf-8")

    create_rules_template(audit_df)

    logging.info("Saved binary direction audit CSV to %s", AUDIT_CSV_PATH)
    logging.info("Saved binary direction summary JSON to %s", SUMMARY_JSON_PATH)


if __name__ == "__main__":
    main()
