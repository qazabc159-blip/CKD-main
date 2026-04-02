import argparse
import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch the CKD thesis SageMaker training job.")
    parser.add_argument(
        "--config",
        default=str(REPO_ROOT / "infra" / "sagemaker_training" / "training_job_config_336.json"),
    )
    parser.add_argument("--wait", action="store_true")
    parser.add_argument("--logs", action="store_true")
    parser.add_argument("--smoke-test", action="store_true")
    parser.add_argument("--instance-type", default="")
    parser.add_argument("--role-arn", default="")
    parser.add_argument("--artifact-bucket", default="")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_launcher_dependencies() -> None:
    try:
        import sagemaker  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "The SageMaker Python SDK is not installed locally. "
            "Run `pip install -r infra/sagemaker_training/requirements-launcher.txt` first."
        ) from exc


def prepare_source_dir() -> Path:
    temp_root = Path(tempfile.mkdtemp(prefix="ckd-sagemaker-src-"))
    (temp_root / "training").mkdir(parents=True, exist_ok=True)
    (temp_root / "infra" / "sagemaker_training").mkdir(parents=True, exist_ok=True)
    (temp_root / "data" / "processed").mkdir(parents=True, exist_ok=True)
    (temp_root / "artifacts" / "baselines_336").mkdir(parents=True, exist_ok=True)
    (temp_root / "artifacts" / "autoprognosis_336").mkdir(parents=True, exist_ok=True)

    for source_path in (REPO_ROOT / "training").glob("*.py"):
        shutil.copy2(source_path, temp_root / "training" / source_path.name)
    readme_path = REPO_ROOT / "training" / "README.md"
    if readme_path.exists():
        shutil.copy2(readme_path, temp_root / "training" / "README.md")

    sagemaker_training_dir = REPO_ROOT / "infra" / "sagemaker_training"
    for source_path in sagemaker_training_dir.iterdir():
        if source_path.is_file():
            shutil.copy2(source_path, temp_root / "infra" / "sagemaker_training" / source_path.name)
            if source_path.name in {"entrypoint.py", "requirements-runtime.txt"}:
                shutil.copy2(source_path, temp_root / source_path.name)

    return temp_root


def build_hyperparameters(config: dict[str, Any], smoke_test: bool) -> dict[str, Any]:
    base = {"job_type": config["job_type"], **config["hyperparameters"]}
    if smoke_test:
        base.update(config.get("smoke_test_hyperparameters", {}))
    return {key: str(value) for key, value in base.items()}


def main() -> None:
    ensure_launcher_dependencies()

    import boto3
    import sagemaker
    from sagemaker.inputs import TrainingInput
    from sagemaker.sklearn.estimator import SKLearn

    args = parse_args()
    config_path = Path(args.config).resolve()
    config = load_json(config_path)

    region = config["region"]
    boto_session = boto3.session.Session(region_name=region)
    sagemaker_session = sagemaker.session.Session(boto_session=boto_session)

    artifact_bucket = args.artifact_bucket or config["artifact_bucket"]
    role_arn = args.role_arn or f"arn:aws:iam::{boto_session.client('sts').get_caller_identity()['Account']}:role/{config['role_name']}"
    instance_type = args.instance_type or config["instance_type"]
    job_name = f"{config['job_name_prefix']}-{utc_stamp()}"

    source_dir = prepare_source_dir()
    dataset_local_path = (REPO_ROOT / config["dataset_local_path"]).resolve()
    split_local_path = (REPO_ROOT / config["split_local_path"]).resolve()

    output_path = f"s3://{artifact_bucket}/{config['output_prefix'].rstrip('/')}/"
    code_location = f"s3://{artifact_bucket}/{config['code_prefix'].rstrip('/')}/"
    hyperparameters = build_hyperparameters(config, smoke_test=args.smoke_test)
    train_input_s3_uri = sagemaker_session.upload_data(
        path=str(dataset_local_path),
        bucket=artifact_bucket,
        key_prefix=f"{config['output_prefix'].rstrip('/')}/input/train",
    )
    split_input_s3_uri = sagemaker_session.upload_data(
        path=str(split_local_path),
        bucket=artifact_bucket,
        key_prefix=f"{config['output_prefix'].rstrip('/')}/input/split",
    )

    estimator = SKLearn(
        entry_point="entrypoint.py",
        source_dir=str(source_dir),
        role=role_arn,
        instance_count=int(config["instance_count"]),
        instance_type=instance_type,
        framework_version=config["framework_version"],
        py_version=config["py_version"],
        output_path=output_path,
        code_location=code_location,
        base_job_name=config["job_name_prefix"],
        sagemaker_session=sagemaker_session,
        hyperparameters=hyperparameters,
        disable_profiler=True,
        debugger_hook_config=False,
        max_run=int(hyperparameters.get("timeout", 300)) + 1800,
    )

    inputs = {
        "train": TrainingInput(train_input_s3_uri, input_mode="File"),
        "split": TrainingInput(split_input_s3_uri, input_mode="File"),
    }

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "config_path": str(config_path),
        "job_name": job_name,
        "region": region,
        "role_arn": role_arn,
        "instance_type": instance_type,
        "artifact_bucket": artifact_bucket,
        "output_path": output_path,
        "code_location": code_location,
        "dataset_local_path": str(dataset_local_path),
        "split_local_path": str(split_local_path),
        "train_input_s3_uri": train_input_s3_uri,
        "split_input_s3_uri": split_input_s3_uri,
        "hyperparameters": hyperparameters,
        "source_dir": str(source_dir),
        "smoke_test": args.smoke_test,
    }

    manifest_path = REPO_ROOT / "artifacts" / "system_eval_aws" / "sagemaker_training_launch_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=True), encoding="utf-8")

    estimator.fit(inputs=inputs, job_name=job_name, wait=args.wait, logs=args.logs)

    print(
        json.dumps(
            {
                "job_name": job_name,
                "region": region,
                "output_path": output_path,
                "manifest_path": str(manifest_path),
                "smoke_test": args.smoke_test,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
