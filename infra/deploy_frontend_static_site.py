from __future__ import annotations

import argparse
import json
import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import boto3


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_DIR = PROJECT_ROOT / "web"
EXCLUDED_FILENAMES = {"README.md", "CKD_UI"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def cache_control_for(relative_path: str) -> str:
    normalized = relative_path.replace("\\", "/")
    if normalized.endswith(".html") or normalized in {"DEPLOY_VERSION.txt", "README_DEPLOY.txt", "app/config.js"}:
        return "no-cache, no-store, must-revalidate"
    if normalized.endswith(".css") or normalized.endswith(".js"):
        return "public, max-age=3600"
    return "public, max-age=86400"


def content_type_for(path: Path) -> str:
    guessed, _ = mimetypes.guess_type(str(path))
    return guessed or "application/octet-stream"


def collect_files(source_dir: Path) -> list[tuple[Path, str]]:
    files: list[tuple[Path, str]] = []
    for path in sorted(source_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.name in EXCLUDED_FILENAMES:
            continue
        relative = path.relative_to(source_dir).as_posix()
        files.append((path, relative))
    return files


def stack_outputs(cloudformation: Any, stack_name: str) -> dict[str, str]:
    response = cloudformation.describe_stacks(StackName=stack_name)
    stacks = response.get("Stacks", [])
    if not stacks:
        raise RuntimeError(f"Stack `{stack_name}` was not found.")
    outputs = {}
    for item in stacks[0].get("Outputs", []):
        key = item.get("OutputKey")
        value = item.get("OutputValue")
        if key and value:
            outputs[key] = value
    return outputs


def upload_files(s3_client: Any, bucket: str, source_dir: Path, dry_run: bool) -> list[dict[str, Any]]:
    uploaded: list[dict[str, Any]] = []
    for path, relative in collect_files(source_dir):
        cache_control = cache_control_for(relative)
        content_type = content_type_for(path)
        uploaded.append(
            {
                "source_path": str(path),
                "key": relative,
                "content_type": content_type,
                "cache_control": cache_control,
                "size_bytes": path.stat().st_size,
            }
        )
        if dry_run:
            continue
        s3_client.upload_file(
            str(path),
            bucket,
            relative,
            ExtraArgs={
                "ContentType": content_type,
                "CacheControl": cache_control,
            },
        )
    return uploaded


def create_invalidation(cloudfront: Any, distribution_id: str, dry_run: bool) -> dict[str, Any] | None:
    if not distribution_id:
        return None
    invalidation_request = {
        "DistributionId": distribution_id,
        "InvalidationBatch": {
            "Paths": {
                "Quantity": 1,
                "Items": ["/*"],
            },
            "CallerReference": utc_now_iso(),
        },
    }
    if dry_run:
        return {
            "dry_run": True,
            "distribution_id": distribution_id,
            "paths": ["/*"],
        }
    response = cloudfront.create_invalidation(**invalidation_request)
    invalidation = response.get("Invalidation", {})
    return {
        "distribution_id": distribution_id,
        "invalidation_id": invalidation.get("Id"),
        "status": invalidation.get("Status"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload the static CKD frontend site to S3 and optionally invalidate CloudFront.")
    parser.add_argument("--bucket", default="", help="Target S3 bucket for the frontend site.")
    parser.add_argument("--distribution-id", default="", help="CloudFront distribution ID for optional invalidation.")
    parser.add_argument("--stack-name", default="", help="Optional CloudFormation/SAM stack name used to resolve frontend outputs.")
    parser.add_argument("--region", default="ap-northeast-1", help="AWS region for CloudFormation lookups.")
    parser.add_argument("--source-dir", default=str(DEFAULT_SOURCE_DIR), help="Static site source directory.")
    parser.add_argument("--dry-run", action="store_true", help="Print the planned uploads without writing to AWS.")
    parser.add_argument("--skip-invalidation", action="store_true", help="Skip CloudFront invalidation even if a distribution ID is available.")
    parser.add_argument("--manifest-out", default="", help="Optional local path to save the deployment manifest JSON.")
    args = parser.parse_args()

    source_dir = Path(args.source_dir).expanduser().resolve()
    if not source_dir.exists():
        raise FileNotFoundError(f"Frontend source directory does not exist: {source_dir}")

    bucket = args.bucket.strip()
    distribution_id = args.distribution_id.strip()

    if args.stack_name:
        cloudformation = boto3.client("cloudformation", region_name=args.region)
        outputs = stack_outputs(cloudformation, args.stack_name)
        bucket = bucket or outputs.get("FrontendBucketName", "")
        distribution_id = distribution_id or outputs.get("FrontendDistributionId", "")

    if not bucket:
        raise RuntimeError("No frontend bucket was provided. Supply --bucket or --stack-name.")

    s3_client = boto3.client("s3", region_name=args.region)
    cloudfront = boto3.client("cloudfront")

    uploads = upload_files(s3_client, bucket, source_dir, dry_run=args.dry_run)
    invalidation = None
    if not args.skip_invalidation and distribution_id:
        invalidation = create_invalidation(cloudfront, distribution_id, dry_run=args.dry_run)

    manifest = {
        "generated_at": utc_now_iso(),
        "source_dir": str(source_dir),
        "bucket": bucket,
        "distribution_id": distribution_id or None,
        "upload_count": len(uploads),
        "uploads": uploads,
        "invalidation": invalidation,
        "dry_run": bool(args.dry_run),
    }

    if args.manifest_out:
        out_path = Path(args.manifest_out).expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
