import json
import logging
import re
from pathlib import Path
from typing import Any

import pandas as pd

from _common import ARTIFACTS_DIR, PROCESSED_DIR, configure_logging, ensure_project_dirs


TRAIN_PATH = PROCESSED_DIR / "ckd_train_336_raw_aligned.csv"
VALID_PATH = PROCESSED_DIR / "ckd_valid_857_raw_aligned.csv"
SHARED_FEATURES_PATH = ARTIFACTS_DIR / "shared_feature_list.json"
AUDIT_CSV_PATH = ARTIFACTS_DIR / "value_audit_shared_features.csv"
AUDIT_JSON_PATH = ARTIFACTS_DIR / "value_audit_shared_features.json"
TYPE_PLAN_CSV_PATH = ARTIFACTS_DIR / "type_plan_shared_features.csv"

EXCEL_MONTH_TOKENS = {
    "jan",
    "feb",
    "mar",
    "apr",
    "may",
    "jun",
    "jul",
    "aug",
    "sep",
    "sept",
    "oct",
    "nov",
    "dec",
}


def load_shared_features() -> list[str]:
    if not SHARED_FEATURES_PATH.exists():
        raise FileNotFoundError(f"Shared feature list not found: {SHARED_FEATURES_PATH}")

    payload = json.loads(SHARED_FEATURES_PATH.read_text(encoding="utf-8"))
    shared_features = payload.get("shared_features")
    if not isinstance(shared_features, list) or not shared_features:
        raise ValueError(f"Invalid shared feature list in {SHARED_FEATURES_PATH}")
    return [str(feature) for feature in shared_features]


def normalize_value_for_signature(value: Any) -> str:
    if pd.isna(value):
        return "<NA>"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        numeric = float(value)
        if numeric.is_integer():
            return str(int(numeric))
        return format(numeric, "g")
    return str(value).strip()


def unique_non_null_signatures(series: pd.Series) -> list[str]:
    signatures = {normalize_value_for_signature(value) for value in series.dropna().tolist()}
    return sorted(signatures)


def safe_sample(values: list[str], limit: int = 12) -> str:
    return json.dumps(values[:limit], ensure_ascii=True)


def looks_like_interval_text(value: str) -> bool:
    token = value.strip()
    return bool(re.match(r"^(<|>|>=|<=|\u2265|\u2264)\s*[-+]?\d", token)) or bool(
        re.match(r"^[-+]?\d+(\.\d+)?\s*-\s*[-+]?\d+(\.\d+)?$", token)
    )


def looks_like_excel_month_artifact(value: str) -> bool:
    token = value.strip().lower()
    if "-" not in token:
        return False
    parts = token.split("-")
    if len(parts) != 2:
        return False
    left, right = parts
    return left.isdigit() and right in EXCEL_MONTH_TOKENS


def infer_representation(series: pd.Series) -> tuple[str, list[str]]:
    unique_values = unique_non_null_signatures(series)
    warnings: list[str] = []

    if not unique_values:
        return "all_missing", warnings

    if pd.api.types.is_numeric_dtype(series):
        unique_count = len(unique_values)
        unique_set = set(unique_values)
        if unique_set.issubset({"0", "1"}):
            return "binary_numeric", warnings
        if unique_count <= 10:
            return "numeric_low_cardinality", warnings
        return "numeric_continuous", warnings

    interval_like = [value for value in unique_values if looks_like_interval_text(value)]
    excel_like = [value for value in unique_values if looks_like_excel_month_artifact(value)]
    if excel_like:
        warnings.append("contains_excel_style_month_tokens")
    if interval_like and len(interval_like) == len(unique_values):
        return "interval_text_bins", warnings

    lowered = {value.lower() for value in unique_values}
    if lowered.issubset({"yes", "no"}):
        return "binary_text_yes_no", warnings
    if lowered.issubset({"present", "notpresent"}):
        return "binary_text_present_absent", warnings
    if lowered.issubset({"normal", "abnormal"}):
        return "binary_text_normal_abnormal", warnings
    if lowered.issubset({"good", "poor"}):
        return "binary_text_good_poor", warnings

    numeric_like = pd.to_numeric(pd.Series(unique_values), errors="coerce")
    if numeric_like.notna().sum() == len(unique_values):
        if set(unique_values).issubset({"0", "1"}):
            return "binary_numeric_text", warnings
        if len(unique_values) <= 10:
            return "numeric_text_low_cardinality", warnings
        return "numeric_text_continuous", warnings

    return "categorical_text", warnings


def compare_representations(rep_336: str, rep_857: str) -> tuple[str, str]:
    if rep_336 == rep_857:
        if rep_336 in {
            "numeric_continuous",
            "numeric_text_continuous",
            "numeric_low_cardinality",
            "interval_text_bins",
        }:
            return "same_family_but_value_audit_needed", "review_value_ranges"
        return "same_representation_family", "review_category_values"

    binary_pairs = {
        rep_336,
        rep_857,
    }
    if binary_pairs <= {
        "binary_numeric",
        "binary_numeric_text",
        "binary_text_yes_no",
        "binary_text_present_absent",
        "binary_text_normal_abnormal",
        "binary_text_good_poor",
    }:
        return "binary_encoding_mismatch", "manual_review_required"

    if {
        rep_336,
        rep_857,
    } <= {
        "numeric_continuous",
        "numeric_text_continuous",
        "numeric_low_cardinality",
        "numeric_text_low_cardinality",
        "interval_text_bins",
    }:
        return "numeric_vs_binned_or_text_numeric", "manual_review_required"

    return "representation_mismatch", "manual_review_required"


def build_manual_review_reasons(
    feature_name: str,
    rep_336: str,
    rep_857: str,
    warnings_336: list[str],
    warnings_857: list[str],
    consistency_status: str,
) -> list[str]:
    reasons: list[str] = []
    for warning in warnings_336:
        reasons.append(f"dataset_336:{warning}")
    for warning in warnings_857:
        reasons.append(f"dataset_857:{warning}")

    if consistency_status in {
        "binary_encoding_mismatch",
        "numeric_vs_binned_or_text_numeric",
        "representation_mismatch",
    }:
        reasons.append(
            f"cross_dataset_representation_mismatch:{rep_336}_vs_{rep_857}"
        )

    if feature_name in {"age", "al", "su"} and rep_857 == "interval_text_bins":
        reasons.append("dataset_857_appears_pre_binned_while_dataset_336_is_not")

    return reasons


def build_type_plan(feature_name: str, rep_336: str, rep_857: str, consistency_action: str) -> tuple[str, str]:
    if consistency_action == "manual_review_required":
        return "manual_review_required", (
            "Do not harmonize automatically. Confirm semantic direction, category coding, "
            "and whether cross-dataset transformation is methodologically acceptable."
        )

    if rep_336 in {"numeric_continuous", "numeric_text_continuous"} or rep_857 in {
        "numeric_continuous",
        "numeric_text_continuous",
    }:
        return "numeric_continuous", (
            "Keep as numeric for dataset-specific modeling inputs, but verify range units and whether one dataset is pre-binned."
        )

    if rep_336 in {"numeric_low_cardinality", "numeric_text_low_cardinality"} or rep_857 in {
        "numeric_low_cardinality",
        "numeric_text_low_cardinality",
    }:
        return "numeric_or_ordinal_review", (
            "Low-cardinality numeric feature. Confirm whether downstream treatment should be ordinal numeric or categorical."
        )

    if rep_336.startswith("binary_") and rep_857.startswith("binary_"):
        return "binary", "Binary feature family matches. Audit the positive/negative direction before encoding."

    return "categorical", "Treat as categorical after confirming the exact category vocabulary."


def audit_feature(feature_name: str, train_df: pd.DataFrame, valid_df: pd.DataFrame) -> dict[str, Any]:
    series_336 = train_df[feature_name]
    series_857 = valid_df[feature_name]

    unique_336 = unique_non_null_signatures(series_336)
    unique_857 = unique_non_null_signatures(series_857)
    rep_336, warnings_336 = infer_representation(series_336)
    rep_857, warnings_857 = infer_representation(series_857)
    consistency_status, consistency_action = compare_representations(rep_336, rep_857)
    manual_review_reasons = build_manual_review_reasons(
        feature_name,
        rep_336,
        rep_857,
        warnings_336,
        warnings_857,
        consistency_status,
    )
    recommended_type, type_plan_notes = build_type_plan(
        feature_name, rep_336, rep_857, consistency_action
    )

    return {
        "feature": feature_name,
        "dtype_336": str(series_336.dtype),
        "dtype_857": str(series_857.dtype),
        "non_null_count_336": int(series_336.notna().sum()),
        "non_null_count_857": int(series_857.notna().sum()),
        "missing_count_336": int(series_336.isna().sum()),
        "missing_count_857": int(series_857.isna().sum()),
        "unique_count_336": int(len(unique_336)),
        "unique_count_857": int(len(unique_857)),
        "representation_336": rep_336,
        "representation_857": rep_857,
        "unique_values_sample_336": safe_sample(unique_336),
        "unique_values_sample_857": safe_sample(unique_857),
        "consistency_status": consistency_status,
        "recommended_action": consistency_action,
        "recommended_modeling_type": recommended_type,
        "type_plan_notes": type_plan_notes,
        "manual_review_required": "yes" if manual_review_reasons else "no",
        "manual_review_reasons": json.dumps(manual_review_reasons, ensure_ascii=True),
    }


def load_aligned_dataset(path: Path, dataset_label: str, shared_features: list[str]) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"{dataset_label} aligned dataset not found: {path}")

    df = pd.read_csv(path)
    missing_columns = [column for column in shared_features if column not in df.columns]
    if missing_columns:
        raise KeyError(f"{dataset_label} aligned dataset is missing shared features: {missing_columns}")
    return df


def main() -> None:
    configure_logging()
    ensure_project_dirs()

    shared_features = load_shared_features()
    train_df = load_aligned_dataset(TRAIN_PATH, "Dataset 336", shared_features)
    valid_df = load_aligned_dataset(VALID_PATH, "Dataset 857", shared_features)

    audit_rows = [audit_feature(feature, train_df, valid_df) for feature in shared_features]
    audit_df = pd.DataFrame(audit_rows)
    audit_df.to_csv(AUDIT_CSV_PATH, index=False)

    payload = {
        "shared_feature_count": len(shared_features),
        "manual_review_feature_count": int((audit_df["manual_review_required"] == "yes").sum()),
        "features": audit_rows,
    }
    AUDIT_JSON_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")

    type_plan_df = audit_df[
        [
            "feature",
            "representation_336",
            "representation_857",
            "consistency_status",
            "recommended_action",
            "recommended_modeling_type",
            "type_plan_notes",
            "manual_review_required",
            "manual_review_reasons",
        ]
    ]
    type_plan_df.to_csv(TYPE_PLAN_CSV_PATH, index=False)

    logging.info("Saved value audit CSV to %s", AUDIT_CSV_PATH)
    logging.info("Saved value audit JSON to %s", AUDIT_JSON_PATH)
    logging.info("Saved type plan CSV to %s", TYPE_PLAN_CSV_PATH)
    logging.info(
        "Manual review required for %s/%s shared features",
        int((audit_df["manual_review_required"] == "yes").sum()),
        len(shared_features),
    )


if __name__ == "__main__":
    main()
