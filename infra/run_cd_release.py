from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CD_MANIFEST_PATH = PROJECT_ROOT / "artifacts" / "system_eval_aws" / "cd_release_manifest.json"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_command(command: list[str]) -> dict[str, Any]:
    started = time.time()
    proc = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        shell=False,
    )
    payload = {
        "command": command,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "duration_seconds": round(time.time() - started, 3),
    }
    if proc.returncode != 0:
        raise RuntimeError(json.dumps(payload, indent=2, ensure_ascii=False))
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the thesis-oriented release pipeline for the CKD platform.")
    parser.add_argument("--bucket", default="ckd-automl-artifacts-junxiang", help="S3 bucket for model bundle upload.")
    parser.add_argument(
        "--model-prefix",
        default="serving/autoprognosis_336_ultra",
        help="S3 prefix for the uploaded serving bundle.",
    )
    parser.add_argument(
        "--stack-name",
        default="ckd-inference-stack",
        help="CloudFormation stack name used when deploying the frontend.",
    )
    parser.add_argument("--actor", default="codex", help="Actor label recorded in release-related governance actions.")
    parser.add_argument("--skip-ci", action="store_true", help="Skip the CI checks stage.")
    parser.add_argument("--skip-model-upload", action="store_true", help="Skip the model-bundle upload stage.")
    parser.add_argument("--skip-frontend", action="store_true", help="Skip the frontend deployment stage.")
    parser.add_argument("--dry-run", action="store_true", help="Run downstream helpers in dry-run mode where supported.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    started = time.time()
    stages: dict[str, Any] = {}

    if not args.skip_ci:
        stages["ci_checks"] = run_command([sys.executable, "infra/run_ci_checks.py"])

    if not args.skip_model_upload:
        command = [
            sys.executable,
            "infra/upload_model_artifact_bundle.py",
            "--bucket",
            args.bucket,
            "--prefix",
            args.model_prefix,
            "--update-registry",
            "--activate",
            "--registered-by",
            args.actor,
        ]
        if args.dry_run:
            command.append("--dry-run")
        stages["model_bundle_release"] = run_command(command)

    if not args.skip_frontend:
        command = [
            sys.executable,
            "infra/deploy_frontend_static_site.py",
            "--stack-name",
            args.stack_name,
            "--manifest-out",
            str(PROJECT_ROOT / "artifacts" / "system_eval_aws" / "cd_frontend_deploy_manifest.json"),
        ]
        if args.dry_run:
            command.append("--dry-run")
        stages["frontend_release"] = run_command(command)

    manifest = {
        "generated_at_utc": utc_now_iso(),
        "status": "passed",
        "duration_seconds": round(time.time() - started, 3),
        "arguments": {
            "bucket": args.bucket,
            "model_prefix": args.model_prefix,
            "stack_name": args.stack_name,
            "actor": args.actor,
            "skip_ci": args.skip_ci,
            "skip_model_upload": args.skip_model_upload,
            "skip_frontend": args.skip_frontend,
            "dry_run": args.dry_run,
        },
        "stages": stages,
    }
    CD_MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    CD_MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=True), encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
