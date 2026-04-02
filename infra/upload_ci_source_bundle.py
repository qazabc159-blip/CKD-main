from __future__ import annotations

import argparse
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import boto3


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUCKET = "ckd-automl-artifacts-junxiang"
DEFAULT_KEY = "ci/source/ckd-main-ci-source.zip"
DEFAULT_LOCAL_ZIP = PROJECT_ROOT / "artifacts" / "system_eval_aws" / "ckd-main-ci-source.zip"

INCLUDED_DIRECTORIES = [
    "backend",
    "infra",
    "training",
    "web",
]

INCLUDED_FILES = [
    "README.md",
    ".gitignore",
    "requirements.txt",
    "artifacts/autoprognosis_336/serving_ultra_minimal_manifest.json",
    "artifacts/autoprognosis_336/best_autoprognosis_metadata.json",
    "artifacts/autoprognosis_336/setup_summary.json",
    "artifacts/model_registry/model_registry.json",
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def iter_files() -> Iterable[Path]:
    yielded: set[Path] = set()
    for directory in INCLUDED_DIRECTORIES:
        root = PROJECT_ROOT / directory
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if "__pycache__" in path.parts:
                continue
            yielded.add(path)
            yield path
    for relative in INCLUDED_FILES:
        path = PROJECT_ROOT / relative
        if path.exists() and path not in yielded:
            yield path


def create_zip(zip_path: Path) -> list[str]:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    archived: list[str] = []
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(iter_files()):
            arcname = path.relative_to(PROJECT_ROOT).as_posix()
            archive.write(path, arcname=arcname)
            archived.append(arcname)
    return archived


def main() -> None:
    parser = argparse.ArgumentParser(description="Package and upload the CKD repo-native CI source bundle to S3.")
    parser.add_argument("--bucket", default=DEFAULT_BUCKET)
    parser.add_argument("--key", default=DEFAULT_KEY)
    parser.add_argument("--region", default="ap-northeast-1")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--zip-path", default=str(DEFAULT_LOCAL_ZIP))
    parser.add_argument("--skip-event", action="store_true", help="Do not emit the EventBridge trigger after upload.")
    args = parser.parse_args()

    zip_path = Path(args.zip_path).expanduser().resolve()
    archived = create_zip(zip_path)

    manifest = {
        "generated_at_utc": utc_now_iso(),
        "bucket": args.bucket,
        "key": args.key,
        "zip_path": str(zip_path),
        "file_count": len(archived),
        "files": archived,
        "dry_run": bool(args.dry_run),
        "event_emitted": False,
    }

    if not args.dry_run:
        s3 = boto3.client("s3", region_name=args.region)
        s3.upload_file(str(zip_path), args.bucket, args.key)
        if not args.skip_event:
            events = boto3.client("events", region_name=args.region)
            response = events.put_events(
                Entries=[
                    {
                        "Source": "ckd.platform.ci",
                        "DetailType": "Source Bundle Uploaded",
                        "Detail": json.dumps(
                            {
                                "bucket": args.bucket,
                                "key": args.key,
                            }
                        ),
                        "EventBusName": "default",
                    }
                ]
            )
            manifest["event_emitted"] = True
            manifest["event_response"] = response

    manifest_path = PROJECT_ROOT / "artifacts" / "system_eval_aws" / "ci_source_bundle_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=True), encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
