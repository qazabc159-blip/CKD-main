import json
import logging
import traceback

from _autoprognosis_common import (
    BLOCKERS_PATH,
    METADATA_PATH,
    RUN_CONFIG_PATH,
    TRAINING_LOG_PATH,
    create_study,
    default_run_config,
    ensure_artifact_dir,
    load_dataset,
    load_split_indices,
    save_weighted_ensemble,
    utc_now,
    write_blocker,
    write_json,
)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    ensure_artifact_dir()

    config = default_run_config()
    write_json(RUN_CONFIG_PATH, config)

    if BLOCKERS_PATH.exists():
        BLOCKERS_PATH.unlink()

    try:
        df = load_dataset()
        train_indices, test_indices, split_df = load_split_indices(df)
        train_df = df.loc[train_indices].reset_index(drop=True)

        training_log = {
            "status": "started",
            "started_at": utc_now(),
            "dataset_used": "data/processed/ckd_train_336_raw_aligned.csv",
            "train_row_count": int(train_df.shape[0]),
            "test_row_count": int(len(test_indices)),
            "notes": [
                "Using the exact held-out split from artifacts/baselines_336/split_indices_336.csv",
                "Missingness is preserved outside the AutoPrognosis workflow.",
                "AutoPrognosis logistic_regression plugin was excluded because it is incompatible with scikit-learn 1.8.0 in this environment.",
            ],
        }
        write_json(TRAINING_LOG_PATH, training_log)

        study = create_study(train_df, config)
        model = study.fit()
        if model is None:
            raise RuntimeError("AutoPrognosis returned None because no model met the configured score threshold.")

        save_weighted_ensemble(model)
        model_name = model.name() if hasattr(model, "name") else "unknown"
        model_weights = []
        if hasattr(model, "weights"):
            try:
                model_weights = list(model.weights)
            except Exception:
                model_weights = []

        metadata = {
            "status": "success",
            "artifact_format": "autoprognosis_weighted_ensemble_bytes",
            "artifact_path": "artifacts/autoprognosis_336/best_autoprognosis_model.pkl",
            "dataset_used": "data/processed/ckd_train_336_raw_aligned.csv",
            "split_file": "artifacts/baselines_336/split_indices_336.csv",
            "model_name": model_name,
            "model_class": type(model).__name__,
            "weights": model_weights,
            "run_config_path": "artifacts/autoprognosis_336/autoprognosis_run_config.json",
            "feature_type_plan_path": "artifacts/autoprognosis_336/feature_type_plan_336.csv",
            "missingness_handling": "Missingness preserved in raw CSV; AutoPrognosis pipeline allowed to handle missingness internally via configured imputers.",
            "known_limitations": config["known_limitations"],
            "completed_at": utc_now(),
        }
        write_json(METADATA_PATH, metadata)

        training_log.update(
            {
                "status": "success",
                "completed_at": utc_now(),
                "selected_model_name": model_name,
                "artifact_path": metadata["artifact_path"],
            }
        )
        write_json(TRAINING_LOG_PATH, training_log)

        logging.info("Saved AutoPrognosis run config to %s", RUN_CONFIG_PATH)
        logging.info("Saved AutoPrognosis training log to %s", TRAINING_LOG_PATH)
        logging.info("Saved AutoPrognosis metadata to %s", METADATA_PATH)
    except Exception as exc:
        blocker_text = "\n".join(
            [
                "# AutoPrognosis Blockers",
                "",
                "AutoPrognosis setup was attempted but training did not complete successfully.",
                "",
                f"- error type: `{type(exc).__name__}`",
                f"- message: `{str(exc)}`",
                "",
                "## Traceback",
                "",
                "```",
                traceback.format_exc().strip(),
                "```",
            ]
        )
        write_blocker(blocker_text)
        write_json(
            TRAINING_LOG_PATH,
            {
                "status": "failed",
                "failed_at": utc_now(),
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "blockers_path": "artifacts/autoprognosis_336/blockers.md",
            },
        )
        raise


if __name__ == "__main__":
    main()
