import logging

from _common import (
    ARTIFACTS_DIR,
    configure_logging,
    distribution_records,
    encode_target,
    ensure_project_dirs,
    exact_label_mapping,
    fetch_dataset,
    get_target_column,
    unique_values_in_order,
    write_json,
)


def define_labels(dataset_id: int) -> None:
    dataset, _, targets = fetch_dataset(dataset_id)
    target_column = get_target_column(dataset_id, targets)
    raw_target = targets[target_column]
    raw_unique_values = unique_values_in_order(raw_target)

    logging.info("Dataset %s raw target unique values: %s", dataset_id, raw_unique_values)

    encoded_target, manual_review_required = encode_target(dataset_id, raw_target)
    if manual_review_required:
        raise ValueError(
            f"Dataset {dataset_id} has unresolved target values requiring manual review: "
            f"{manual_review_required}"
        )

    payload = {
        "dataset_id": dataset_id,
        "dataset_name": dataset.metadata.get("name", f"UCI-{dataset_id}"),
        "target_column": target_column,
        "raw_unique_values": raw_unique_values,
        "exact_raw_to_target_mapping": exact_label_mapping(dataset_id),
        "encoded_target_distribution": distribution_records(encoded_target),
        "manual_review_required": [],
    }

    output_path = ARTIFACTS_DIR / f"label_mapping_{dataset_id}.json"
    write_json(output_path, payload)
    logging.info("Saved label mapping JSON to %s", output_path)


def main() -> None:
    configure_logging()
    ensure_project_dirs()
    for dataset_id in (336, 857):
        define_labels(dataset_id)


if __name__ == "__main__":
    main()
