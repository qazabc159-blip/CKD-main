from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

import boto3
from botocore.exceptions import ClientError


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AUTOPROGNOSIS_DIR = PROJECT_ROOT / "artifacts" / "autoprognosis_336"
DEFAULT_REGISTRY_PATH = PROJECT_ROOT / "artifacts" / "model_registry" / "model_registry.json"
DEFAULT_REGISTRY_S3_KEY = "registry/model_registry.json"
DEFAULT_SOURCE_FILES = {
    "model": AUTOPROGNOSIS_DIR / "serving_ultra_minimal.pkl",
    "metadata": AUTOPROGNOSIS_DIR / "best_autoprognosis_metadata.json",
    "setup_summary": AUTOPROGNOSIS_DIR / "setup_summary.json",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_prefix(prefix: str) -> str:
    return prefix.strip().strip("/")


def s3_key(prefix: str, filename: str) -> str:
    if not prefix:
        return filename
    return str(PurePosixPath(prefix) / filename)


def repo_relative(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")


def ensure_sources(source_files: dict[str, Path]) -> None:
    missing = [str(path) for path in source_files.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing artifact files:\n- " + "\n- ".join(missing))


def head_bucket_or_fail(s3_client: Any, bucket: str, region: str) -> None:
    try:
        s3_client.head_bucket(Bucket=bucket)
    except ClientError as exc:
        code = str(exc.response.get("Error", {}).get("Code", ""))
        if code in {"301", "PermanentRedirect", "400", "403", "404"}:
            try:
                s3_client.get_bucket_location(Bucket=bucket)
                return
            except ClientError:
                pass
        raise RuntimeError(
            f"S3 bucket `{bucket}` is not reachable with current credentials. "
            "Create it first or check AWS credentials/region."
        ) from exc


def upload_file(s3_client: Any, bucket: str, key: str, source_path: Path) -> dict[str, Any]:
    extra_args: dict[str, Any] = {}
    if source_path.suffix == ".json":
        extra_args["ContentType"] = "application/json"
    elif source_path.suffix == ".pkl":
        extra_args["ContentType"] = "application/octet-stream"

    s3_client.upload_file(str(source_path), bucket, key, ExtraArgs=extra_args)
    return {
        "bucket": bucket,
        "key": key,
        "filename": source_path.name,
        "size_bytes": source_path.stat().st_size,
        "sha256": sha256_of(source_path),
    }


def build_manifest(bucket: str, prefix: str, uploads: dict[str, dict[str, Any]], source_files: dict[str, Path]) -> dict[str, Any]:
    metadata_payload = json.loads(source_files["metadata"].read_text(encoding="utf-8"))
    return {
        "uploaded_at": utc_now_iso(),
        "bucket": bucket,
        "prefix": prefix,
        "artifact_scope": "autoprognosis_336_serving_bundle",
        "artifact_variant": source_files["model"].name,
        "model_name": metadata_payload.get("model_name"),
        "model_class": metadata_payload.get("model_class"),
        "status": metadata_payload.get("status"),
        "files": uploads,
        "sam_parameters": {
            "ModelArtifactBucket": bucket,
            "ModelArtifactKey": uploads["model"]["key"],
            "ModelMetadataKey": uploads["metadata"]["key"],
            "SetupSummaryKey": uploads["setup_summary"]["key"],
        },
    }


def default_local_registry_bundle(source_files: dict[str, Path]) -> dict[str, str]:
    bundle = {
        "model_path": repo_relative(source_files["model"]),
        "metadata_path": repo_relative(source_files["metadata"]),
        "setup_summary_path": repo_relative(source_files["setup_summary"]),
    }
    local_manifest = source_files["model"].with_name(f"{source_files['model'].stem}_manifest.json")
    if local_manifest.exists():
        bundle["manifest_path"] = repo_relative(local_manifest)
    return bundle


def build_registry_entry(
    manifest: dict[str, Any],
    source_files: dict[str, Path],
    model_id: str,
    version: str,
    display_name: str,
    response_model_version_base: str,
    clinical_adapter_version: str,
    registered_by: str,
) -> dict[str, Any]:
    setup_summary = json.loads(source_files["setup_summary"].read_text(encoding="utf-8"))
    local_bundle = default_local_registry_bundle(source_files)

    provenance = {
        "source_metadata": repo_relative(source_files["metadata"]),
        "source_setup_summary": repo_relative(source_files["setup_summary"]),
    }
    if "manifest_path" in local_bundle:
        provenance["source_local_manifest"] = local_bundle["manifest_path"]

    return {
        "model_id": model_id,
        "version": version,
        "display_name": display_name,
        "status": "candidate",
        "registered_at": utc_now_iso(),
        "registered_by": registered_by,
        "approved_by": None,
        "approved_at": None,
        "approval_note": None,
        "last_promoted_by": None,
        "last_promoted_at": None,
        "promotion_note": None,
        "training_dataset": setup_summary.get("dataset_used"),
        "feature_count": setup_summary.get("feature_count"),
        "route_scope": ["research", "clinical_adapter"],
        "response_model_version_base": response_model_version_base,
        "clinical_adapter_version": clinical_adapter_version,
        "local_bundle": local_bundle,
        "s3_bundle": {
            "bucket": manifest["bucket"],
            "model_key": manifest["files"]["model"]["key"],
            "metadata_key": manifest["files"]["metadata"]["key"],
            "setup_summary_key": manifest["files"]["setup_summary"]["key"],
            "manifest_key": manifest["files"]["manifest"]["key"],
        },
        "provenance": provenance,
        "notes": [
            "Registry entry for the current thesis-serving artifact bundle.",
            "Clinical mode remains a provisional adapter into the research feature space.",
        ],
    }


def load_registry_from_disk(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def load_registry_from_s3(s3_client: Any, bucket: str, key: str) -> dict[str, Any] | None:
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
    except ClientError as exc:
        error_code = str(exc.response.get("Error", {}).get("Code", ""))
        if error_code in {"NoSuchKey", "404"}:
            return None
        raise

    payload = response["Body"].read().decode("utf-8")
    return json.loads(payload)


def upsert_registry(
    existing_registry: dict[str, Any] | None,
    entry: dict[str, Any],
    activate: bool,
    actor: str,
) -> dict[str, Any]:
    registry = existing_registry or {
        "registry_version": "2.0",
        "updated_at": utc_now_iso(),
        "active_model_id": None,
        "models": [],
    }

    models = [model for model in registry.get("models", []) if model.get("model_id") != entry["model_id"]]
    if activate:
        for model in models:
            if model.get("status") == "active":
                model["status"] = "approved"
        entry["approved_by"] = entry.get("approved_by") or actor
        entry["approved_at"] = entry.get("approved_at") or utc_now_iso()
        entry["approval_note"] = entry.get("approval_note") or "Approved during upload helper activation."
        entry["status"] = "active"
        entry["last_promoted_by"] = actor
        entry["last_promoted_at"] = utc_now_iso()
        entry["promotion_note"] = "Activated during upload helper flow."
        registry["active_model_id"] = entry["model_id"]
    models.append(entry)
    registry["models"] = models
    registry["updated_at"] = utc_now_iso()
    return registry


def write_registry_to_disk(path: Path, registry: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Upload the CKD AutoPrognosis serving bundle to S3 and optionally update the model registry."
    )
    parser.add_argument("--bucket", required=True, help="Target S3 bucket name.")
    parser.add_argument(
        "--prefix",
        default="serving/autoprognosis_336_ultra",
        help="S3 prefix for the uploaded artifact bundle.",
    )
    parser.add_argument(
        "--region",
        default="ap-northeast-1",
        help="AWS region for the S3 client. Default matches the thesis target region.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned uploads without writing to S3.",
    )
    parser.add_argument(
        "--manifest-out",
        default="",
        help="Optional local path to save the upload manifest JSON.",
    )
    parser.add_argument(
        "--model-path",
        default="",
        help="Optional local model artifact path. Defaults to the ultra-minimal serving bundle.",
    )
    parser.add_argument(
        "--update-registry",
        action="store_true",
        help="Update the local model registry and upload the registry JSON to S3.",
    )
    parser.add_argument(
        "--registry-path",
        default=str(DEFAULT_REGISTRY_PATH),
        help="Local path to the model_registry.json file.",
    )
    parser.add_argument(
        "--registry-key",
        default=DEFAULT_REGISTRY_S3_KEY,
        help="S3 object key for model_registry.json when --update-registry is used.",
    )
    parser.add_argument(
        "--model-id",
        default="autoprognosis-336-main-ultra-v1",
        help="Registry model identifier.",
    )
    parser.add_argument(
        "--version",
        default="1.0.0",
        help="Registry semantic version string.",
    )
    parser.add_argument(
        "--display-name",
        default="Dataset #336 AutoPrognosis ultra-minimal serving bundle",
        help="Human-readable registry display name.",
    )
    parser.add_argument(
        "--response-model-version-base",
        default="autoprognosis-336-main",
        help="Base version label used by the research serving response.",
    )
    parser.add_argument(
        "--clinical-adapter-version",
        default="autoprognosis-336-clinical-adapter-v1",
        help="Version label returned by the clinical adapter route.",
    )
    parser.add_argument(
        "--registered-by",
        default="codex",
        help="Actor label stored in the registry entry.",
    )
    parser.add_argument(
        "--activate",
        action="store_true",
        help="Mark the uploaded registry entry as the active model. Recommended for the thesis-serving bundle.",
    )
    args = parser.parse_args()

    source_files = dict(DEFAULT_SOURCE_FILES)
    if args.model_path:
        source_files["model"] = Path(args.model_path).expanduser().resolve()

    ensure_sources(source_files)

    bucket = args.bucket.strip()
    prefix = normalize_prefix(args.prefix)
    registry_path = Path(args.registry_path).expanduser().resolve()
    registry_key = normalize_prefix(args.registry_key)
    s3_client = boto3.client("s3", region_name=args.region)

    planned = {
        name: {
            "source_path": str(path),
            "bucket": bucket,
            "key": s3_key(prefix, path.name),
            "size_bytes": path.stat().st_size,
            "sha256": sha256_of(path),
        }
        for name, path in source_files.items()
    }

    if args.update_registry:
        planned["registry"] = {
            "registry_path": str(registry_path),
            "bucket": bucket,
            "key": registry_key,
            "model_id": args.model_id,
            "version": args.version,
            "activate": bool(args.activate),
        }

    if args.dry_run:
        print(json.dumps({"dry_run": True, "planned_uploads": planned}, indent=2, ensure_ascii=False))
        return

    head_bucket_or_fail(s3_client, bucket, args.region)

    uploads: dict[str, dict[str, Any]] = {}
    for name, path in source_files.items():
        uploads[name] = upload_file(s3_client, bucket, s3_key(prefix, path.name), path)

    manifest = build_manifest(bucket, prefix, uploads, source_files)
    manifest_key = s3_key(prefix, "serving_bundle_manifest.json")
    s3_client.put_object(
        Bucket=bucket,
        Key=manifest_key,
        Body=json.dumps(manifest, indent=2, ensure_ascii=False).encode("utf-8"),
        ContentType="application/json",
    )
    manifest["files"]["manifest"] = {
        "bucket": bucket,
        "key": manifest_key,
        "filename": "serving_bundle_manifest.json",
    }

    registry_summary: dict[str, Any] | None = None
    if args.update_registry:
        existing_local_registry = load_registry_from_disk(registry_path)
        existing_s3_registry = load_registry_from_s3(s3_client, bucket, registry_key)
        existing_registry = existing_local_registry or existing_s3_registry

        entry = build_registry_entry(
            manifest=manifest,
            source_files=source_files,
            model_id=args.model_id,
            version=args.version,
            display_name=args.display_name,
            response_model_version_base=args.response_model_version_base,
            clinical_adapter_version=args.clinical_adapter_version,
            registered_by=args.registered_by,
        )
        registry = upsert_registry(
            existing_registry,
            entry,
            activate=args.activate or not existing_registry,
            actor=args.registered_by,
        )
        registry["registry_version"] = "2.0"
        write_registry_to_disk(registry_path, registry)
        s3_client.put_object(
            Bucket=bucket,
            Key=registry_key,
            Body=json.dumps(registry, indent=2, ensure_ascii=False).encode("utf-8"),
            ContentType="application/json",
        )
        manifest["sam_parameters"]["ModelRegistryKey"] = registry_key
        manifest["sam_parameters"]["ActiveModelId"] = registry["active_model_id"]
        registry_summary = {
            "registry_path": str(registry_path),
            "registry_key": registry_key,
            "active_model_id": registry.get("active_model_id"),
            "model_count": len(registry.get("models", [])),
        }

    if args.manifest_out:
        out_path = Path(args.manifest_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("Upload completed.\n")
    print(json.dumps({"manifest": manifest, "registry": registry_summary}, indent=2, ensure_ascii=False))
    print("\nSuggested SAM parameter overrides:")
    overrides = [
        f"ModelArtifactBucket={manifest['sam_parameters']['ModelArtifactBucket']}",
        f"ModelArtifactKey={manifest['sam_parameters']['ModelArtifactKey']}",
        f"ModelMetadataKey={manifest['sam_parameters']['ModelMetadataKey']}",
        f"SetupSummaryKey={manifest['sam_parameters']['SetupSummaryKey']}",
    ]
    if args.update_registry:
        overrides.extend(
            [
                f"ModelRegistryKey={manifest['sam_parameters']['ModelRegistryKey']}",
                f"ActiveModelId={manifest['sam_parameters']['ActiveModelId']}",
            ]
        )
    print(" ".join(overrides))


if __name__ == "__main__":
    main()
