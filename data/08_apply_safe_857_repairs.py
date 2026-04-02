import csv
import logging

import pandas as pd

from _857_representation_common import apply_interval_bin_code
from _common import ARTIFACTS_DIR, PROCESSED_DIR, configure_logging, ensure_project_dirs


RULES_CSV_PATH = ARTIFACTS_DIR / "857_harmonization_rules.csv"
RAW_857_PATH = PROCESSED_DIR / "ckd_valid_857_raw_aligned.csv"
REPAIRED_857_PATH = PROCESSED_DIR / "ckd_valid_857_repaired_candidate_not_validation_ready.csv"
UNRESOLVED_CSV_PATH = ARTIFACTS_DIR / "857_unresolved_features.csv"
REPAIR_REPORT_CSV_PATH = ARTIFACTS_DIR / "857_safe_repair_report.csv"


def main() -> None:
    configure_logging()
    ensure_project_dirs()

    if not RULES_CSV_PATH.exists():
        raise FileNotFoundError(
            f"Missing rules file: {RULES_CSV_PATH}. Run data/07_propose_857_harmonization_rules.py first."
        )

    repaired_df = pd.read_csv(RAW_857_PATH)
    rules_df = pd.read_csv(RULES_CSV_PATH)

    repair_report_rows = []
    unresolved_rows = []

    for row in rules_df.itertuples(index=False):
        feature_name = row.feature_name
        repair_applied = "no"

        if (
            row.proposed_action == "convert_interval_to_ordered_bin_code"
            and row.confidence_level == "high"
            and row.manual_review_required == "no"
        ):
            repaired_series, mapping = apply_interval_bin_code(repaired_df[feature_name])
            repaired_df[feature_name] = repaired_series
            repair_applied = "yes"

            for original_value, repaired_code in mapping.items():
                repair_report_rows.append(
                    {
                        "feature_name": feature_name,
                        "repair_applied": "yes",
                        "repair_type": "ordered_bin_code",
                        "original_value": original_value,
                        "repaired_value": repaired_code,
                        "cross_dataset_validation_status": row.cross_dataset_validation_status,
                        "notes": row.notes,
                    }
                )
        else:
            unresolved_rows.append(
                {
                    "feature_name": feature_name,
                    "representation_type_336": row.representation_type_336,
                    "representation_type_857": row.representation_type_857,
                    "proposed_action": row.proposed_action,
                    "confidence_level": row.confidence_level,
                    "manual_review_required": row.manual_review_required,
                    "cross_dataset_validation_status": row.cross_dataset_validation_status,
                    "reason": row.notes,
                }
            )

        if repair_applied == "no":
            repair_report_rows.append(
                {
                    "feature_name": feature_name,
                    "repair_applied": "no",
                    "repair_type": "none",
                    "original_value": "",
                    "repaired_value": "",
                    "cross_dataset_validation_status": row.cross_dataset_validation_status,
                    "notes": row.notes,
                }
            )

    repaired_df.to_csv(REPAIRED_857_PATH, index=False)
    pd.DataFrame(unresolved_rows).to_csv(UNRESOLVED_CSV_PATH, index=False, quoting=csv.QUOTE_MINIMAL)
    pd.DataFrame(repair_report_rows).to_csv(REPAIR_REPORT_CSV_PATH, index=False, quoting=csv.QUOTE_MINIMAL)

    logging.info("Saved repaired #857 candidate dataset to %s", REPAIRED_857_PATH)
    logging.info("Saved unresolved feature report to %s", UNRESOLVED_CSV_PATH)
    logging.info("Saved safe repair report to %s", REPAIR_REPORT_CSV_PATH)


if __name__ == "__main__":
    main()
