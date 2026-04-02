import logging

import pandas as pd

from _common import (
    ARTIFACTS_DIR,
    build_missingness_report,
    build_profiling_payload,
    configure_logging,
    ensure_project_dirs,
    fetch_dataset,
    get_target_column,
)


def profile_dataset(dataset_id: int) -> None:
    dataset, features, targets = fetch_dataset(dataset_id)
    target_column = get_target_column(dataset_id, targets)
    combined = pd.concat([features, targets[[target_column]]], axis=1)

    logging.info("Dataset %s: %s", dataset_id, dataset.metadata.get("name"))
    logging.info("Rows: %s", combined.shape[0])
    logging.info("Columns: %s", combined.shape[1])
    logging.info("Duplicate rows: %s", int(combined.duplicated().sum()))
    logging.info("Column names: %s", list(combined.columns))
    logging.info("Dtypes:\n%s", combined.dtypes.astype(str).to_string())

    missingness = build_missingness_report(combined)
    logging.info("Missingness summary:\n%s", missingness.to_string(index=False))

    target_series = combined[target_column]
    logging.info("Target unique values: %s", target_series.drop_duplicates().tolist())
    logging.info(
        "Target distribution:\n%s",
        target_series.value_counts(dropna=False).rename_axis("value").reset_index(name="count").to_string(index=False),
    )

    profiling_payload = build_profiling_payload(
        dataset_id=dataset_id,
        dataset_name=dataset.metadata.get("name", f"UCI-{dataset_id}"),
        df=combined,
        target_column=target_column,
    )

    profiling_path = ARTIFACTS_DIR / f"profiling_{dataset_id}.json"
    missingness_path = ARTIFACTS_DIR / f"missingness_{dataset_id}.csv"

    from _common import write_json

    write_json(profiling_path, profiling_payload)
    missingness.to_csv(missingness_path, index=False)

    logging.info("Saved profiling JSON to %s", profiling_path)
    logging.info("Saved missingness CSV to %s", missingness_path)


def main() -> None:
    configure_logging()
    ensure_project_dirs()
    for dataset_id in (336, 857):
        profile_dataset(dataset_id)


if __name__ == "__main__":
    main()
