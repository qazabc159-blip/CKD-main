import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SageMaker training entrypoint for the CKD thesis platform.")
    parser.add_argument("--job_type", default="autoprognosis_336")
    parser.add_argument("--num_iter", type=int, default=5)
    parser.add_argument("--num_study_iter", type=int, default=3)
    parser.add_argument("--num_ensemble_iter", type=int, default=1)
    parser.add_argument("--ensemble_size", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--n_folds_cv", type=int, default=5)
    parser.add_argument("--score_threshold", type=float, default=0.5)
    parser.add_argument("--smoke_test", type=str, default="false")
    parser.add_argument("--skip_runtime_pip_install", type=str, default="false")
    return parser.parse_args()


def str_to_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def repo_root() -> Path:
    current_path = Path(__file__).resolve()
    if current_path.parent.name == "sagemaker_training":
        return current_path.parents[2]
    return current_path.parent


def runtime_requirements_path() -> Path:
    current_path = Path(__file__).resolve()
    direct_candidate = current_path.with_name("requirements-runtime.txt")
    if direct_candidate.exists():
        return direct_candidate
    nested_candidate = current_path.parent / "sagemaker_training" / "requirements-runtime.txt"
    if nested_candidate.exists():
        return nested_candidate
    return direct_candidate


def install_runtime_requirements(skip_install: bool) -> None:
    requirements_path = runtime_requirements_path()
    if skip_install:
        logging.info("Skipping runtime pip install because skip_runtime_pip_install=true.")
        return
    if not requirements_path.exists():
        raise FileNotFoundError(f"Runtime requirements file not found: {requirements_path}")
    logging.info("Installing SageMaker runtime requirements from %s", requirements_path)
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "-r",
            str(requirements_path),
        ]
    )


def ensure_channel_file(channel_name: str, expected_filename: str, destination: Path) -> Path:
    channel_env = f"SM_CHANNEL_{channel_name.upper()}"
    channel_dir = os.environ.get(channel_env)
    if not channel_dir:
        if destination.exists():
            logging.info("No %s channel found. Reusing existing local file %s", channel_name, destination)
            return destination
        raise FileNotFoundError(f"Missing SageMaker input channel: {channel_env}")

    source_dir = Path(channel_dir)
    if not source_dir.exists():
        raise FileNotFoundError(f"Channel directory does not exist for {channel_name}: {source_dir}")

    candidate = source_dir / expected_filename
    if candidate.exists():
        source_path = candidate
    else:
        matches = sorted(source_dir.glob(f"*{Path(expected_filename).suffix}"))
        if not matches:
            raise FileNotFoundError(
                f"Unable to find {expected_filename} or any matching file in channel {channel_name}: {source_dir}"
            )
        source_path = matches[0]

    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        if source_path.resolve() == destination.resolve():
            logging.info("%s channel already points to %s", channel_name, destination)
            return destination
    except FileNotFoundError:
        pass
    shutil.copy2(source_path, destination)
    logging.info("Copied %s channel file %s to %s", channel_name, source_path, destination)
    return destination


def write_manifest(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def add_training_paths(repo_root_path: Path) -> None:
    training_dir = repo_root_path / "training"
    if str(training_dir) not in sys.path:
        sys.path.insert(0, str(training_dir))
    if str(repo_root_path) not in sys.path:
        sys.path.insert(0, str(repo_root_path))


def build_run_config(default_run_config_fn, args: argparse.Namespace) -> dict[str, Any]:
    config = default_run_config_fn()
    config.update(
        {
            "num_iter": int(args.num_iter),
            "num_study_iter": int(args.num_study_iter),
            "num_ensemble_iter": int(args.num_ensemble_iter),
            "ensemble_size": int(args.ensemble_size),
            "timeout": int(args.timeout),
            "n_folds_cv": int(args.n_folds_cv),
            "score_threshold": float(args.score_threshold),
        }
    )
    config.setdefault("known_limitations", [])
    config["known_limitations"] = list(config["known_limitations"]) + [
        "Executed via the SageMaker training-layer entrypoint.",
    ]
    if str_to_bool(args.smoke_test):
        config["known_limitations"].append(
            "Smoke-test mode was enabled, so search iterations were intentionally reduced for infrastructure validation."
        )
    return config


def copy_training_outputs(artifacts_dir: Path, model_dir: Path, output_data_dir: Path) -> dict[str, str]:
    target_root = model_dir / "artifacts" / artifacts_dir.name
    if target_root.exists():
        shutil.rmtree(target_root)
    shutil.copytree(artifacts_dir, target_root)

    model_artifact = artifacts_dir / "best_autoprognosis_model.pkl"
    if model_artifact.exists():
        shutil.copy2(model_artifact, model_dir / model_artifact.name)

    metadata_artifact = artifacts_dir / "best_autoprognosis_metadata.json"
    if metadata_artifact.exists():
        shutil.copy2(metadata_artifact, output_data_dir / metadata_artifact.name)

    return {
        "model_dir_artifacts_path": str(target_root),
        "model_dir_model_artifact": str(model_dir / model_artifact.name) if model_artifact.exists() else "",
        "output_data_metadata_path": str(output_data_dir / metadata_artifact.name) if metadata_artifact.exists() else "",
    }


def run_autoprognosis_336(args: argparse.Namespace) -> dict[str, Any]:
    repo_root_path = repo_root()
    add_training_paths(repo_root_path)

    from _autoprognosis_common import (  # type: ignore
        ARTIFACTS_DIR,
        BLOCKERS_PATH,
        METADATA_PATH,
        MODEL_PATH,
        RUN_CONFIG_PATH,
        TRAINING_LOG_PATH,
        create_study,
        default_run_config,
        ensure_artifact_dir,
        load_dataset,
        load_split_indices,
        save_weighted_ensemble,
        write_blocker,
        write_json,
    )
    from _baseline_common import DATASET_PATH, SPLIT_INDICES_PATH  # type: ignore

    ensure_channel_file("train", "ckd_train_336_raw_aligned.csv", DATASET_PATH)
    ensure_channel_file("split", "split_indices_336.csv", SPLIT_INDICES_PATH)

    ensure_artifact_dir()
    if BLOCKERS_PATH.exists():
        BLOCKERS_PATH.unlink()

    config = build_run_config(default_run_config, args)
    write_json(RUN_CONFIG_PATH, config)

    manifest: dict[str, Any] = {
        "status": "started",
        "started_at": utc_now(),
        "job_type": args.job_type,
        "smoke_test": str_to_bool(args.smoke_test),
        "dataset_path": str(DATASET_PATH),
        "split_path": str(SPLIT_INDICES_PATH),
        "artifact_dir": str(ARTIFACTS_DIR),
    }

    try:
        df = load_dataset()
        train_indices, test_indices, _ = load_split_indices(df)
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
                "Training was executed through the SageMaker training-layer entrypoint.",
            ],
        }
        if str_to_bool(args.smoke_test):
            training_log["notes"].append("Smoke-test mode reduced search depth for infrastructure validation.")
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

        manifest.update(
            {
                "status": "success",
                "completed_at": utc_now(),
                "selected_model_name": model_name,
                "model_artifact_path": str(MODEL_PATH),
                "metadata_path": str(METADATA_PATH),
            }
        )
        return manifest
    except Exception as exc:
        blocker_text = "\n".join(
            [
                "# SageMaker Training Blockers",
                "",
                "SageMaker-based AutoPrognosis training did not complete successfully.",
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
        manifest.update(
            {
                "status": "failed",
                "failed_at": utc_now(),
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            }
        )
        raise


def main() -> None:
    configure_logging()
    args = parse_args()
    skip_install = str_to_bool(args.skip_runtime_pip_install)
    install_runtime_requirements(skip_install=skip_install)

    if args.job_type != "autoprognosis_336":
        raise ValueError(f"Unsupported SageMaker job_type: {args.job_type}")

    model_dir = Path(os.environ.get("SM_MODEL_DIR", repo_root() / "artifacts" / "sagemaker_model"))
    output_data_dir = Path(os.environ.get("SM_OUTPUT_DATA_DIR", repo_root() / "artifacts" / "sagemaker_output"))
    output_data_dir.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)

    manifest = run_autoprognosis_336(args)

    from _autoprognosis_common import ARTIFACTS_DIR  # type: ignore

    copied_paths = copy_training_outputs(ARTIFACTS_DIR, model_dir, output_data_dir)
    manifest.update(copied_paths)
    write_manifest(output_data_dir / "sagemaker_training_manifest.json", manifest)
    logging.info("Wrote SageMaker training manifest to %s", output_data_dir / "sagemaker_training_manifest.json")


if __name__ == "__main__":
    main()
