import csv
import json
import logging

import pandas as pd

from _857_representation_common import (
    EXCEL_RISK_FEATURES,
    INTERVAL_RISK_FEATURES,
    LOW_RISK_BINARY_FEATURES,
    MAPPING_REQUIRED_BINARY_FEATURES,
)
from _common import ARTIFACTS_DIR, configure_logging, ensure_project_dirs


AUDIT_CSV_PATH = ARTIFACTS_DIR / "857_representation_audit.csv"
RULES_CSV_PATH = ARTIFACTS_DIR / "857_harmonization_rules.csv"
RULES_MD_PATH = ARTIFACTS_DIR / "857_harmonization_rules.md"


def propose_rule(row: pd.Series) -> dict[str, str]:
    feature_name = row["feature_name"]
    rep_336 = row["representation_type_336"]
    rep_857 = row["representation_type_857"]

    proposed_action = "unresolved"
    confidence_level = "low"
    manual_review_required = "yes"
    cross_dataset_validation_status = "not_safe_for_cross_dataset_validation"
    notes = []

    if feature_name in LOW_RISK_BINARY_FEATURES and rep_336 == "binary_text" and rep_857 == "binary_numeric":
        proposed_action = "keep_as_binary_and_map"
        confidence_level = "medium"
        notes.append(
            "Likely a simple binary representation mismatch, but the 0/1 direction in dataset 857 must be confirmed before mapping."
        )
        cross_dataset_validation_status = "conditional_after_mapping_confirmation"
    elif feature_name in MAPPING_REQUIRED_BINARY_FEATURES and rep_336 == "binary_text" and rep_857 == "binary_numeric":
        proposed_action = "keep_as_binary_and_map"
        confidence_level = "medium"
        notes.append(
            "Feature appears binary, but the semantic direction of dataset 857 numeric codes must be confirmed before any shared mapping is declared safe."
        )
        cross_dataset_validation_status = "conditional_after_mapping_confirmation"
    elif feature_name == "age" and rep_857 == "excel_like_corrupted_token":
        proposed_action = "repair_excel_like_token_then_convert_to_ordered_bin_code"
        confidence_level = "medium"
        notes.append(
            "The token 20-Dec is likely a spreadsheet-corrupted interval label such as 12 - 20, but this should be confirmed before repair."
        )
    elif feature_name in {"al", "su"} and rep_857 == "excel_like_corrupted_token":
        proposed_action = "unresolved"
        confidence_level = "low"
        notes.append(
            "Excel-like tokens are present, but the original ordinal/bin semantics cannot be recovered with high confidence from the observed values alone."
        )
    elif feature_name in INTERVAL_RISK_FEATURES and rep_857 == "interval_text":
        proposed_action = "convert_interval_to_ordered_bin_code"
        confidence_level = "high"
        manual_review_required = "no"
        cross_dataset_validation_status = "repaired_candidate_only_not_cross_dataset_safe"
        notes.append(
            "Safe repair is limited to preserving order as within-dataset bin codes. This does not imply equivalence to dataset 336 continuous values."
        )

    if feature_name in EXCEL_RISK_FEATURES:
        notes.append("High-risk feature due to Excel-like token or ordinal ambiguity.")
    if feature_name in INTERVAL_RISK_FEATURES and proposed_action != "convert_interval_to_ordered_bin_code":
        notes.append("Not yet safe to treat as the same feature space as dataset 336.")

    return {
        "feature_name": feature_name,
        "representation_type_336": rep_336,
        "representation_type_857": rep_857,
        "proposed_action": proposed_action,
        "confidence_level": confidence_level,
        "manual_review_required": manual_review_required,
        "cross_dataset_validation_status": cross_dataset_validation_status,
        "notes": " ".join(notes),
    }


def write_markdown(rules_df: pd.DataFrame) -> None:
    sections = [
        "# 857 Harmonization Rules",
        "",
        "This document proposes conservative representation harmonization rules for dataset `857`.",
        "It is a rule draft for investigation and repair only. It does not declare dataset `857` fully ready for cross-dataset validation.",
        "",
        "## High-Confidence Safe Repairs",
        "",
    ]

    safe_repairs = rules_df.loc[
        (rules_df["proposed_action"] == "convert_interval_to_ordered_bin_code")
        & (rules_df["confidence_level"] == "high")
        & (rules_df["manual_review_required"] == "no")
    ]
    if safe_repairs.empty:
        sections.append("- None")
    else:
        for feature_name in safe_repairs["feature_name"].tolist():
            sections.append(f"- `{feature_name}`: convert interval text to ordered bin code for within-857 repaired candidate export only.")

    sections.extend(
        [
            "",
            "## Manual Review Required",
            "",
        ]
    )
    manual_rows = rules_df.loc[rules_df["manual_review_required"] == "yes"]
    for row in manual_rows.itertuples(index=False):
        sections.append(
            f"- `{row.feature_name}`: `{row.proposed_action}` ({row.confidence_level}) - {row.notes}"
        )

    sections.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            "- High-confidence interval-to-bin repairs are only candidate within-857 repairs.",
            "- They do not prove that dataset `857` shares the same feature space as dataset `336`.",
            "- Features with unresolved Excel-like corruption or unresolved binary code direction remain unsafe for cross-dataset validation.",
        ]
    )

    RULES_MD_PATH.write_text("\n".join(sections) + "\n", encoding="utf-8")


def main() -> None:
    configure_logging()
    ensure_project_dirs()

    if not AUDIT_CSV_PATH.exists():
        raise FileNotFoundError(
            f"Missing audit file: {AUDIT_CSV_PATH}. Run data/06_investigate_857_representation.py first."
        )

    audit_df = pd.read_csv(AUDIT_CSV_PATH)
    rules_df = pd.DataFrame([propose_rule(row) for _, row in audit_df.iterrows()])
    rules_df.to_csv(RULES_CSV_PATH, index=False, quoting=csv.QUOTE_MINIMAL)
    write_markdown(rules_df)

    logging.info("Saved #857 harmonization rules CSV to %s", RULES_CSV_PATH)
    logging.info("Saved #857 harmonization rules Markdown to %s", RULES_MD_PATH)


if __name__ == "__main__":
    main()
