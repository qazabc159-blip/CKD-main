from __future__ import annotations

import json
import pickle
import time
from pathlib import Path

import cloudpickle
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AUTOPROGNOSIS_DIR = PROJECT_ROOT / "artifacts" / "autoprognosis_336"
SOURCE_ARTIFACT = AUTOPROGNOSIS_DIR / "best_autoprognosis_model.pkl"
SERVING_ARTIFACT = AUTOPROGNOSIS_DIR / "serving_minimal_stages_cloudpickle.pkl"
SERVING_MANIFEST = AUTOPROGNOSIS_DIR / "serving_minimal_stages_cloudpickle_manifest.json"
SETUP_SUMMARY = AUTOPROGNOSIS_DIR / "setup_summary.json"
TRAIN_DATASET = PROJECT_ROOT / "data" / "processed" / "ckd_train_336_raw_aligned.csv"


def main() -> None:
    load_started_at = time.perf_counter()
    with SOURCE_ARTIFACT.open("rb") as handle:
        bundle = pickle.load(handle)
    source_load_seconds = time.perf_counter() - load_started_at

    pipeline = bundle["models"][0]
    serving_payload = {
        "ice": pipeline.stages[0],
        "cleanup": pipeline.stages[3],
        "rf": pipeline.stages[4],
    }

    write_started_at = time.perf_counter()
    with SERVING_ARTIFACT.open("wb") as handle:
        cloudpickle.dump(serving_payload, handle, protocol=pickle.HIGHEST_PROTOCOL)
    write_seconds = time.perf_counter() - write_started_at

    verify_load_started_at = time.perf_counter()
    with SERVING_ARTIFACT.open("rb") as handle:
        restored = cloudpickle.load(handle)
    verify_load_seconds = time.perf_counter() - verify_load_started_at

    setup_summary = json.loads(SETUP_SUMMARY.read_text(encoding="utf-8"))
    feature_names = setup_summary["feature_names"]
    sample_frame = pd.read_csv(TRAIN_DATASET).iloc[[0]][feature_names]
    transformed = restored["ice"].transform(sample_frame)
    transformed = restored["cleanup"].transform(transformed)

    predict_started_at = time.perf_counter()
    sample_proba_frame = restored["rf"].predict_proba(transformed)
    sample_probability = float(sample_proba_frame.iloc[0, 1])
    predict_seconds = time.perf_counter() - predict_started_at

    manifest = {
        "artifact_scope": "autoprognosis_336_minimal_serving_stages",
        "artifact_format": "cloudpickle_stage_bundle",
        "source_artifact": str(SOURCE_ARTIFACT.relative_to(PROJECT_ROOT)),
        "serving_artifact": str(SERVING_ARTIFACT.relative_to(PROJECT_ROOT)),
        "source_load_seconds": round(source_load_seconds, 6),
        "serving_write_seconds": round(write_seconds, 6),
        "serving_load_seconds": round(verify_load_seconds, 6),
        "sample_predict_seconds": round(predict_seconds, 6),
        "sample_probability": round(sample_probability, 6),
        "serving_artifact_size_bytes": SERVING_ARTIFACT.stat().st_size,
    }
    SERVING_MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
