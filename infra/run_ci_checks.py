from __future__ import annotations

import json
import os
import py_compile
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CI_MANIFEST_PATH = PROJECT_ROOT / "artifacts" / "system_eval_aws" / "ci_checks_manifest.json"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def relative(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")


def discover_python_files() -> list[Path]:
    roots = [PROJECT_ROOT / "backend", PROJECT_ROOT / "infra", PROJECT_ROOT / "training"]
    files: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            files.append(path)
    return sorted(files)


def check_python_compile() -> dict[str, Any]:
    checked: list[str] = []
    for path in discover_python_files():
        py_compile.compile(str(path), doraise=True)
        checked.append(relative(path))
    return {
        "status": "passed",
        "checked_file_count": len(checked),
        "checked_files": checked,
    }


def run_command(command: list[str]) -> dict[str, Any]:
    started = time.time()
    proc = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        shell=False,
    )
    return {
        "command": command,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "duration_seconds": round(time.time() - started, 3),
    }


def check_sam_template() -> dict[str, Any]:
    result = run_command(["sam", "validate", "-t", "infra/template.yaml"])
    if result["returncode"] != 0:
        raise RuntimeError(f"SAM validation failed:\n{result['stderr'] or result['stdout']}")
    return {
        "status": "passed",
        "command": result["command"],
        "duration_seconds": result["duration_seconds"],
    }


def check_serving_artifacts() -> dict[str, Any]:
    required = [
        PROJECT_ROOT / "artifacts" / "autoprognosis_336" / "serving_ultra_minimal.pkl",
        PROJECT_ROOT / "artifacts" / "autoprognosis_336" / "best_autoprognosis_metadata.json",
        PROJECT_ROOT / "artifacts" / "autoprognosis_336" / "setup_summary.json",
    ]
    missing = [relative(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing serving artifacts:\n- " + "\n- ".join(missing))
    return {
        "status": "passed",
        "artifacts": [relative(path) for path in required],
    }


def check_frontend_files() -> dict[str, Any]:
    required = [
        PROJECT_ROOT / "web" / "index.html",
        PROJECT_ROOT / "web" / "landing" / "index.html",
        PROJECT_ROOT / "web" / "app" / "index.html",
        PROJECT_ROOT / "web" / "app" / "config.js",
    ]
    missing = [relative(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing frontend files:\n- " + "\n- ".join(missing))
    return {
        "status": "passed",
        "files": [relative(path) for path in required],
    }


def check_registry_consistency() -> dict[str, Any]:
    registry_path = PROJECT_ROOT / "artifacts" / "model_registry" / "model_registry.json"
    if not registry_path.exists():
        return {
            "status": "skipped",
            "reason": "Registry file does not exist.",
        }

    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    active_model_id = payload.get("active_model_id")
    models = payload.get("models", [])
    if active_model_id and not any(model.get("model_id") == active_model_id for model in models):
        raise RuntimeError(f"Active model `{active_model_id}` is not present in the registry.")
    return {
        "status": "passed",
        "registry_path": relative(registry_path),
        "active_model_id": active_model_id,
        "model_count": len(models),
    }


def main() -> None:
    started = time.time()
    checks: dict[str, Any] = {}
    failure: str | None = None

    try:
        checks["python_compile"] = check_python_compile()
        checks["sam_validate"] = check_sam_template()
        checks["serving_artifacts"] = check_serving_artifacts()
        checks["frontend_files"] = check_frontend_files()
        checks["registry_consistency"] = check_registry_consistency()
        status = "passed"
    except Exception as exc:  # pragma: no cover - used for ops scripting
        status = "failed"
        failure = str(exc)

    manifest = {
        "generated_at_utc": utc_now_iso(),
        "status": status,
        "duration_seconds": round(time.time() - started, 3),
        "checks": checks,
        "failure": failure,
        "hostname": os.environ.get("COMPUTERNAME", ""),
        "python": sys.version,
    }
    CI_MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    CI_MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=True), encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=True))
    if status != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
