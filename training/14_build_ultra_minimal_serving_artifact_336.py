from __future__ import annotations

import copy
import json
import pickle
from datetime import datetime, timezone
from pathlib import Path

import cloudpickle


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AUTOPROGNOSIS_DIR = PROJECT_ROOT / "artifacts" / "autoprognosis_336"
SOURCE_ARTIFACT = AUTOPROGNOSIS_DIR / "serving_minimal_stages_cloudpickle.pkl"
OUTPUT_ARTIFACT = AUTOPROGNOSIS_DIR / "serving_ultra_minimal.pkl"
OUTPUT_MANIFEST = AUTOPROGNOSIS_DIR / "serving_ultra_minimal_manifest.json"
SETUP_SUMMARY = AUTOPROGNOSIS_DIR / "setup_summary.json"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main() -> None:
    with SOURCE_ARTIFACT.open("rb") as handle:
        bundle = cloudpickle.load(handle)

    ice_outer = bundle["ice"]
    ice_inner = ice_outer._model
    cleanup = bundle["cleanup"]
    rf_plugin = bundle["rf"]

    rf_model = copy.deepcopy(rf_plugin.model)
    if hasattr(rf_model, "n_jobs"):
        rf_model.set_params(n_jobs=1)

    setup_summary = json.loads(SETUP_SUMMARY.read_text(encoding="utf-8"))

    ultra_minimal = {
        "artifact_type": "ultra_minimal",
        "created_at": utc_now_iso(),
        "feature_names": setup_summary["feature_names"],
        "encoders": ice_outer._backup_encoders,
        "imputer_columns": list(ice_inner.columns),
        "iterative_imputer": ice_inner._model,
        "cleanup_scaler": cleanup.scaler,
        "cleanup_columns": list(cleanup.columns),
        "cleanup_var_threshold": cleanup.var_threshold if cleanup.drop_variance else None,
        "cleanup_drop_columns": list(cleanup.drop) if cleanup.drop_multicollinearity else [],
        "rf_model": rf_model,
    }

    with OUTPUT_ARTIFACT.open("wb") as handle:
        pickle.dump(ultra_minimal, handle, protocol=pickle.HIGHEST_PROTOCOL)

    manifest = {
        "generated_at": utc_now_iso(),
        "source_artifact": str(SOURCE_ARTIFACT.relative_to(PROJECT_ROOT)),
        "output_artifact": str(OUTPUT_ARTIFACT.relative_to(PROJECT_ROOT)),
        "artifact_type": "ultra_minimal",
        "rf_model_class": type(rf_model).__name__,
        "rf_n_jobs": getattr(rf_model, "n_jobs", None),
        "cleanup_drop_columns": ultra_minimal["cleanup_drop_columns"],
        "imputer_columns": ultra_minimal["imputer_columns"],
    }
    OUTPUT_MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
