import logging

import pandas as pd

from _common import ARTIFACTS_DIR, configure_logging, ensure_project_dirs, fetch_dataset, normalize_column_name


SPECIAL_CANDIDATE_PAIRS = {
    "bp": "bp (Diastolic)",
}


def build_exact_match_row(column_name: str) -> dict[str, str]:
    return {
        "source_336_column": column_name,
        "source_857_column": column_name,
        "unified_name": normalize_column_name(column_name),
        "same_meaning": "yes",
        "same_unit": "unknown",
        "keep_for_shared_model": "pending_review",
        "notes": "Exact column-name match across datasets. Confirm coding, units, and allowable values before final approval.",
        "manual_review_required": "yes",
    }


def build_special_candidate_row(source_336: str, source_857: str) -> dict[str, str]:
    return {
        "source_336_column": source_336,
        "source_857_column": source_857,
        "unified_name": "blood_pressure_candidate",
        "same_meaning": "uncertain",
        "same_unit": "uncertain",
        "keep_for_shared_model": "pending_review",
        "notes": "Dataset 336 metadata says 'bp' is blood pressure. Dataset 857 explicitly names this field diastolic blood pressure. Do not auto-merge without manual confirmation.",
        "manual_review_required": "yes",
    }


def build_unmatched_row(source_dataset: str, column_name: str) -> dict[str, str]:
    return {
        "source_336_column": column_name if source_dataset == "336" else "",
        "source_857_column": column_name if source_dataset == "857" else "",
        "unified_name": normalize_column_name(column_name),
        "same_meaning": "no_shared_counterpart",
        "same_unit": "not_applicable",
        "keep_for_shared_model": "no",
        "notes": f"Present only in dataset {source_dataset}. Excluded from the shared schema unless you later define a justified derivation rule.",
        "manual_review_required": "no",
    }


def main() -> None:
    configure_logging()
    ensure_project_dirs()

    _, features_336, _ = fetch_dataset(336)
    _, features_857, _ = fetch_dataset(857)

    columns_336 = list(features_336.columns)
    columns_857 = list(features_857.columns)

    exact_matches = sorted(set(columns_336).intersection(columns_857))
    rows = [build_exact_match_row(column_name) for column_name in exact_matches]

    for source_336, source_857 in SPECIAL_CANDIDATE_PAIRS.items():
        if source_336 in columns_336 and source_857 in columns_857:
            rows.append(build_special_candidate_row(source_336, source_857))

    matched_336 = set(exact_matches).union(SPECIAL_CANDIDATE_PAIRS.keys())
    matched_857 = set(exact_matches).union(SPECIAL_CANDIDATE_PAIRS.values())

    unmatched_336 = sorted(set(columns_336) - matched_336)
    unmatched_857 = sorted(set(columns_857) - matched_857)

    rows.extend(build_unmatched_row("336", column_name) for column_name in unmatched_336)
    rows.extend(build_unmatched_row("857", column_name) for column_name in unmatched_857)

    mapping_df = pd.DataFrame(
        rows,
        columns=[
            "source_336_column",
            "source_857_column",
            "unified_name",
            "same_meaning",
            "same_unit",
            "keep_for_shared_model",
            "notes",
            "manual_review_required",
        ],
    )

    output_path = ARTIFACTS_DIR / "feature_mapping_candidates.csv"
    mapping_df.to_csv(output_path, index=False)

    logging.info("Dataset 336 feature columns: %s", columns_336)
    logging.info("Dataset 857 feature columns: %s", columns_857)
    logging.info("Exact-name candidate pairs: %s", exact_matches)
    logging.info("Special candidate pairs requiring manual review: %s", SPECIAL_CANDIDATE_PAIRS)
    logging.info("Saved feature mapping candidates to %s", output_path)


if __name__ == "__main__":
    main()
