from __future__ import annotations

import json
import os
import pickle
import pathlib
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path, PurePosixPath
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AUTOPROGNOSIS_ARTIFACT = PROJECT_ROOT / "artifacts" / "autoprognosis_336" / "best_autoprognosis_model.pkl"
AUTOPROGNOSIS_METADATA = PROJECT_ROOT / "artifacts" / "autoprognosis_336" / "best_autoprognosis_metadata.json"
SETUP_SUMMARY = PROJECT_ROOT / "artifacts" / "autoprognosis_336" / "setup_summary.json"
LOCAL_MODEL_REGISTRY = PROJECT_ROOT / "artifacts" / "model_registry" / "model_registry.json"


@dataclass(frozen=True)
class PredictionResponse:
    risk_score: float
    prediction_label: str
    model_version: str
    serving_route: str
    timestamp: str
    notes: str
    explanation: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "risk_score": self.risk_score,
            "prediction_label": self.prediction_label,
            "model_version": self.model_version,
            "serving_route": self.serving_route,
            "timestamp": self.timestamp,
            "notes": self.notes,
            "explanation": self.explanation,
        }


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def risk_label(score: float) -> str:
    if score >= 0.7:
        return "high_risk"
    if score >= 0.4:
        return "moderate_risk"
    return "lower_risk"


def clamp_probability(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def s3_companion_key(model_key: str, filename: str) -> str:
    return str(PurePosixPath(model_key).with_name(filename))


def legacy_s3_direct_enabled() -> bool:
    return bool(os.getenv("CKD_MODEL_ARTIFACT_BUCKET") and os.getenv("CKD_MODEL_ARTIFACT_KEY"))


def registry_s3_enabled() -> bool:
    return bool(os.getenv("CKD_MODEL_ARTIFACT_BUCKET") and os.getenv("CKD_MODEL_REGISTRY_KEY"))


def local_registry_enabled() -> bool:
    return LOCAL_MODEL_REGISTRY.exists()


def download_s3_object(bucket: str, key: str, target: Path) -> Path:
    import boto3

    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        return target

    client = boto3.client("s3")
    client.download_file(bucket, key, str(target))
    return target


def timing_log(label: str, started_at: float) -> None:
    duration = time.perf_counter() - started_at
    print(f"[ckd-service] {label} completed in {duration:.4f}s")


def repo_relative_path(value: str) -> Path:
    return PROJECT_ROOT.joinpath(*PurePosixPath(value).parts)


def load_serialized_model(model_path: Path) -> Any:
    loader_started_at = time.perf_counter()
    windows_path_cls = getattr(pathlib, "WindowsPath", None)
    restore_windows_path = False

    # Some pickled artifacts were produced on Windows and contain WindowsPath
    # objects. Lambda runs on Linux, so unpickling those objects raises
    # "cannot instantiate 'WindowsPath' on your system" unless we temporarily
    # alias the class during deserialization.
    if os.name != "nt" and windows_path_cls is not None:
        pathlib.WindowsPath = pathlib.PosixPath
        restore_windows_path = True

    with model_path.open("rb") as handle:
        try:
            if "cloudpickle" in model_path.name:
                import cloudpickle

                model_object = cloudpickle.load(handle)
                timing_log(f"cloudpickle load for {model_path.name}", loader_started_at)
                return model_object

            bundle = pickle.load(handle)
            timing_log(f"pickle load for {model_path.name}", loader_started_at)
            if isinstance(bundle, dict):
                if bundle.get("artifact_type") == "ultra_minimal":
                    return bundle
                if {"ice", "cleanup", "rf"}.issubset(bundle.keys()):
                    return bundle
                models = bundle.get("models", [])
                if not models:
                    raise RuntimeError("AutoPrognosis artifact does not contain a callable model.")
                return models[0]
            return bundle
        finally:
            if restore_windows_path:
                pathlib.WindowsPath = windows_path_cls


@lru_cache(maxsize=1)
def resolved_registry_path() -> Path | None:
    started_at = time.perf_counter()
    if registry_s3_enabled():
        bucket = os.environ["CKD_MODEL_ARTIFACT_BUCKET"]
        registry_key = os.environ["CKD_MODEL_REGISTRY_KEY"]
        target = download_s3_object(bucket, registry_key, Path("/tmp/ckd_model_bundle/model_registry.json"))
        timing_log("resolve S3 model registry", started_at)
        return target

    if local_registry_enabled():
        timing_log("resolve local model registry", started_at)
        return LOCAL_MODEL_REGISTRY

    timing_log("resolve model registry (not configured)", started_at)
    return None


@lru_cache(maxsize=1)
def model_registry() -> dict[str, Any] | None:
    registry_path = resolved_registry_path()
    if registry_path is None:
        return None
    return json.loads(registry_path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def active_model_record() -> dict[str, Any] | None:
    registry = model_registry()
    if not registry:
        return None

    models = registry.get("models", [])
    if not models:
        raise RuntimeError("Model registry is configured but contains no model entries.")

    requested_model_id = os.getenv("CKD_ACTIVE_MODEL_ID") or registry.get("active_model_id")
    if requested_model_id:
        for record in models:
            if record.get("model_id") == requested_model_id:
                return record
        raise RuntimeError(f"Configured active model id `{requested_model_id}` was not found in the model registry.")

    active_records = [record for record in models if record.get("status") == "active"]
    if len(active_records) == 1:
        return active_records[0]

    if len(models) == 1:
        return models[0]

    raise RuntimeError("Model registry does not define a unique active model.")


def active_research_model_version_base() -> str:
    record = active_model_record() or {}
    return record.get("response_model_version_base", "autoprognosis-336-main")


def active_clinical_adapter_version() -> str:
    record = active_model_record() or {}
    return record.get("clinical_adapter_version", "autoprognosis-336-clinical-adapter-v1")


def active_local_bundle(record: dict[str, Any]) -> tuple[Path, Path, Path]:
    bundle = record.get("local_bundle") or {}
    model_path = repo_relative_path(bundle["model_path"])
    metadata_path = repo_relative_path(bundle["metadata_path"])
    setup_path = repo_relative_path(bundle["setup_summary_path"])
    return model_path, metadata_path, setup_path


def active_s3_bundle(record: dict[str, Any]) -> tuple[str, str, str, str]:
    bundle = record.get("s3_bundle") or {}
    bucket = bundle.get("bucket") or os.environ["CKD_MODEL_ARTIFACT_BUCKET"]
    model_key = bundle["model_key"]
    metadata_key = bundle["metadata_key"]
    setup_key = bundle["setup_summary_key"]
    return bucket, model_key, metadata_key, setup_key


@lru_cache(maxsize=1)
def resolved_artifact_paths() -> tuple[Path, Path, Path]:
    started_at = time.perf_counter()
    registry_record = active_model_record()
    if registry_record is not None:
        if registry_s3_enabled():
            bucket, model_key, metadata_key, setup_key = active_s3_bundle(registry_record)
            tmp_root = Path("/tmp/ckd_model_bundle")
            model_filename = PurePosixPath(model_key).name
            model_path = download_s3_object(bucket, model_key, tmp_root / model_filename)
            metadata_path = download_s3_object(bucket, metadata_key, tmp_root / "best_autoprognosis_metadata.json")
            setup_path = download_s3_object(bucket, setup_key, tmp_root / "setup_summary.json")
            timing_log("resolve registry-driven S3 artifact paths", started_at)
            return model_path, metadata_path, setup_path

        model_path, metadata_path, setup_path = active_local_bundle(registry_record)
        timing_log("resolve registry-driven local artifact paths", started_at)
        return model_path, metadata_path, setup_path

    if not legacy_s3_direct_enabled():
        paths = (AUTOPROGNOSIS_ARTIFACT, AUTOPROGNOSIS_METADATA, SETUP_SUMMARY)
        timing_log("resolve packaged artifact paths", started_at)
        return paths

    bucket = os.environ["CKD_MODEL_ARTIFACT_BUCKET"]
    model_key = os.environ["CKD_MODEL_ARTIFACT_KEY"]
    metadata_key = os.getenv("CKD_MODEL_METADATA_KEY") or s3_companion_key(
        model_key, "best_autoprognosis_metadata.json"
    )
    setup_key = os.getenv("CKD_SETUP_SUMMARY_KEY") or s3_companion_key(model_key, "setup_summary.json")

    tmp_root = Path("/tmp/ckd_model_bundle")
    model_filename = PurePosixPath(model_key).name
    model_path = download_s3_object(bucket, model_key, tmp_root / model_filename)
    metadata_path = download_s3_object(bucket, metadata_key, tmp_root / "best_autoprognosis_metadata.json")
    setup_path = download_s3_object(bucket, setup_key, tmp_root / "setup_summary.json")
    timing_log("resolve legacy S3 artifact paths", started_at)
    return model_path, metadata_path, setup_path


@lru_cache(maxsize=1)
def feature_order() -> list[str]:
    _, _, setup_summary_path = resolved_artifact_paths()
    payload = json.loads(setup_summary_path.read_text(encoding="utf-8"))
    return payload["feature_names"]


@lru_cache(maxsize=1)
def model_metadata() -> dict[str, Any]:
    _, metadata_path, _ = resolved_artifact_paths()
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    record = active_model_record()
    registry = model_registry()
    if record is not None:
        payload.setdefault("model_id", record.get("model_id"))
        payload.setdefault("response_model_version_base", record.get("response_model_version_base"))
        payload.setdefault("clinical_adapter_version", record.get("clinical_adapter_version"))
    if registry is not None:
        payload.setdefault("registry_version", registry.get("registry_version"))
        payload.setdefault("registry_active_model_id", registry.get("active_model_id"))
    return payload


@lru_cache(maxsize=1)
def research_model() -> Any:
    model_path, _, _ = resolved_artifact_paths()
    return load_serialized_model(model_path)


def normalize_binary_text(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip().lower()
    if normalized in {"yes", "y", "1", "true", "present", "abnormal", "poor"}:
        return "yes"
    if normalized in {"no", "n", "0", "false", "notpresent", "normal", "good"}:
        return "no"
    return normalized or None


def parse_number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def extract_inputs(payload: dict[str, Any]) -> dict[str, Any]:
    if isinstance(payload.get("inputs"), dict):
        return payload["inputs"]

    for key, value in payload.items():
        if key in {"mode", "context"}:
            continue
        if isinstance(value, dict):
            return value

    raise ValueError("Request body must contain an `inputs` object.")


def build_research_frame(inputs: dict[str, Any]) -> pd.DataFrame:
    ordered = {feature: inputs.get(feature, None) for feature in feature_order()}
    return pd.DataFrame([ordered], columns=feature_order())


def preprocess_with_backup_encoders(frame: pd.DataFrame, encoders: dict[str, Any]) -> pd.DataFrame:
    transformed = frame.copy()

    for column, encoder in encoders.items():
        if column not in transformed.columns:
            continue

        mask = transformed[column].notna()
        if not mask.any():
            continue

        known_classes = set(encoder.classes_)
        encoded_values: list[Any] = []
        for value in transformed.loc[mask, column]:
            candidate = value
            if candidate not in known_classes and "unknown" in known_classes:
                candidate = "unknown"
            encoded_values.append(candidate)

        transformed.loc[mask, column] = encoder.transform(encoded_values)

    return transformed.apply(pd.to_numeric, errors="coerce")


def predict_from_ultra_minimal_artifact(model_object: dict[str, Any], frame: pd.DataFrame) -> float:
    encode_started_at = time.perf_counter()
    transformed = preprocess_with_backup_encoders(frame, model_object["encoders"])
    timing_log("ultra_minimal.encode_backup_features", encode_started_at)

    imputer_started_at = time.perf_counter()
    imputed = model_object["iterative_imputer"].transform(transformed[model_object["imputer_columns"]])
    timing_log("ultra_minimal.iterative_imputer.transform", imputer_started_at)

    cleanup_frame = pd.DataFrame(imputed, columns=model_object["imputer_columns"], index=frame.index)

    scaler_started_at = time.perf_counter()
    cleanup_frame = pd.DataFrame(
        model_object["cleanup_scaler"].transform(cleanup_frame),
        columns=model_object["cleanup_columns"],
        index=frame.index,
    )
    timing_log("ultra_minimal.cleanup_scaler.transform", scaler_started_at)

    var_threshold = model_object.get("cleanup_var_threshold")
    if var_threshold is not None:
        variance_started_at = time.perf_counter()
        cleanup_frame = pd.DataFrame(
            var_threshold.transform(cleanup_frame),
            columns=var_threshold.get_feature_names_out(),
            index=frame.index,
        )
        timing_log("ultra_minimal.var_threshold.transform", variance_started_at)

    drop_columns = model_object.get("cleanup_drop_columns", [])
    if drop_columns:
        cleanup_frame = cleanup_frame.drop(columns=drop_columns)

    rf_started_at = time.perf_counter()
    probability = model_object["rf_model"].predict_proba(cleanup_frame)[0, 1]
    timing_log("ultra_minimal.rf_model.predict_proba", rf_started_at)
    return float(probability)


def translate_clinical_to_research(clinical: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    translated = {feature: None for feature in feature_order()}
    notes: list[str] = []

    translated["age"] = parse_number(clinical.get("age"))
    translated["sc"] = parse_number(clinical.get("scr"))
    translated["pot"] = parse_number(clinical.get("potassium"))
    translated["dm"] = normalize_binary_text(clinical.get("dm"))
    translated["htn"] = normalize_binary_text(clinical.get("htn"))

    if clinical.get("proteinuria_flag") is not None:
        notes.append("proteinuria_flag was not force-mapped to albumin because the semantic equivalence is not strict.")
    if clinical.get("cvd") is not None:
        notes.append("cvd was not force-mapped to cad because the clinical scopes are related but not identical.")
    if clinical.get("egfr") is not None:
        notes.append("egfr was retained for clinical interpretation but not directly injected into the research feature space.")
    if clinical.get("uacr") is not None:
        notes.append("uacr was retained for clinical interpretation but not directly injected into the research feature space.")

    return translated, notes


def rank_explanations(items: list[dict[str, Any]], limit: int = 6) -> list[dict[str, Any]]:
    ranked = sorted(items, key=lambda item: abs(float(item["contribution"])), reverse=True)
    return ranked[:limit]


def explain_research_inputs(inputs: dict[str, Any]) -> list[dict[str, Any]]:
    explanations: list[dict[str, Any]] = []

    def add(feature: str, message: str, contribution: float) -> None:
        if contribution == 0:
            return
        explanations.append(
            {
                "feature": feature,
                "message": message,
                "contribution": round(float(contribution), 4),
            }
        )

    sc = parse_number(inputs.get("sc"))
    hemo = parse_number(inputs.get("hemo"))
    pcv = parse_number(inputs.get("pcv"))
    bu = parse_number(inputs.get("bu"))
    al = parse_number(inputs.get("al"))
    sg = parse_number(inputs.get("sg"))
    rbcc = parse_number(inputs.get("rbcc"))

    if sc is not None:
        add("sc", "Higher serum creatinine increased the returned risk profile.", min(max((sc - 1.2) / 4.0, 0), 0.18))
    if hemo is not None:
        add("hemo", "Lower hemoglobin contributed to a higher-risk pattern.", -min(max((hemo - 12.5) / 8.0, -0.16), 0.1))
    if pcv is not None:
        add("pcv", "Packed cell volume shifted the prediction toward the returned class.", -min(max((pcv - 38) / 20.0, -0.12), 0.08))
    if bu is not None:
        add("bu", "Elevated blood urea aligned with the higher-risk profile.", min(max((bu - 35) / 220.0, 0), 0.12))
    if al is not None:
        add("al", "Albumin level contributed to the urinalysis-driven signal.", min(al * 0.04, 0.16))
    if sg is not None:
        add("sg", "Specific gravity influenced the concentration-related risk signal.", -min(max((sg - 1.015) / 0.02, -0.1), 0.1))
    if rbcc is not None:
        add("rbcc", "Red blood cell count contributed to the hematology signal.", -min(max((rbcc - 4.5) / 3.0, -0.08), 0.08))
    if normalize_binary_text(inputs.get("htn")) == "yes":
        add("htn", "Hypertension increased the returned risk profile.", 0.08)
    if normalize_binary_text(inputs.get("dm")) == "yes":
        add("dm", "Diabetes mellitus increased the returned risk profile.", 0.08)
    if normalize_binary_text(inputs.get("cad")) == "yes":
        add("cad", "Coronary artery disease added a smaller positive contribution.", 0.05)
    if normalize_binary_text(inputs.get("ane")) == "yes":
        add("ane", "Anemia aligned with a higher-risk interpretation.", 0.07)
    if normalize_binary_text(inputs.get("pe")) == "yes":
        add("pe", "Pedal edema increased the returned risk profile.", 0.06)
    if normalize_binary_text(inputs.get("appet")) == "poor":
        add("appet", "Poor appetite contributed to the higher-risk pattern.", 0.05)

    if not explanations:
        explanations.append(
            {
                "feature": "intake",
                "message": "No strong heuristic summary was available from the submitted research inputs.",
                "contribution": 0.02,
            }
        )

    return rank_explanations(explanations)


def explain_clinical_inputs(clinical: dict[str, Any]) -> list[dict[str, Any]]:
    explanations: list[dict[str, Any]] = []

    def add(feature: str, message: str, contribution: float) -> None:
        if contribution == 0:
            return
        explanations.append(
            {
                "feature": feature,
                "message": message,
                "contribution": round(float(contribution), 4),
            }
        )

    egfr = parse_number(clinical.get("egfr"))
    uacr = parse_number(clinical.get("uacr"))
    scr = parse_number(clinical.get("scr"))
    hba1c = parse_number(clinical.get("hba1c"))
    sbp = parse_number(clinical.get("sbp"))
    age = parse_number(clinical.get("age"))

    if egfr is not None:
        add("egfr", "Lower eGFR increased the clinical intake risk summary.", min(max((60 - egfr) / 80.0, 0), 0.18))
    if uacr is not None:
        add("uacr", "Higher UACR increased the returned clinical risk summary.", min(max((uacr - 30) / 1000.0, 0), 0.16))
    if scr is not None:
        add("scr", "Higher serum creatinine strengthened the higher-risk pattern.", min(max((scr - 1.2) / 6.0, 0), 0.16))
    if hba1c is not None:
        add("hba1c", "Higher HbA1c contributed to the metabolic risk profile.", min(max((hba1c - 6.5) / 10.0, 0), 0.09))
    if sbp is not None:
        add("sbp", "Elevated systolic blood pressure contributed to the returned risk.", min(max((sbp - 125) / 140.0, 0), 0.08))
    if age is not None:
        add("age", "Older age contributed modestly to the clinical risk summary.", min(max((age - 45) / 120.0, 0), 0.08))
    if normalize_binary_text(clinical.get("dm")) == "yes":
        add("dm", "Diabetes mellitus increased the returned risk profile.", 0.1)
    if normalize_binary_text(clinical.get("htn")) == "yes":
        add("htn", "Hypertension increased the returned risk profile.", 0.09)
    if normalize_binary_text(clinical.get("proteinuria_flag")) == "yes":
        add("proteinuria_flag", "Proteinuria history strengthened the renal risk interpretation.", 0.1)
    if normalize_binary_text(clinical.get("cvd")) == "yes":
        add("cvd", "Cardiovascular disease increased the overall clinical risk summary.", 0.06)

    if not explanations:
        explanations.append(
            {
                "feature": "intake",
                "message": "No strong heuristic summary was available from the submitted clinical inputs.",
                "contribution": 0.02,
            }
        )

    return rank_explanations(explanations)


def predict_from_research_inputs(research_inputs: dict[str, Any]) -> float:
    started_at = time.perf_counter()
    frame = build_research_frame(research_inputs)
    timing_log("build research frame", started_at)

    predict_started_at = time.perf_counter()
    model_load_started_at = time.perf_counter()
    model_object = research_model()
    timing_log("resolve cached research model", model_load_started_at)
    if isinstance(model_object, dict) and model_object.get("artifact_type") == "ultra_minimal":
        probability = predict_from_ultra_minimal_artifact(model_object, frame)
    elif isinstance(model_object, dict) and {"ice", "cleanup", "rf"}.issubset(model_object.keys()):
        ice_started_at = time.perf_counter()
        transformed = model_object["ice"].transform(frame)
        timing_log("ice.transform", ice_started_at)

        cleanup_started_at = time.perf_counter()
        transformed = model_object["cleanup"].transform(transformed)
        timing_log("cleanup.transform", cleanup_started_at)

        rf_started_at = time.perf_counter()
        probability = model_object["rf"].predict_proba(transformed)[0, 1]
        timing_log("rf.predict_proba", rf_started_at)
    else:
        raw_model_predict_started_at = time.perf_counter()
        probability = model_object.predict_proba(frame)[0, 1]
        timing_log("model.predict_proba", raw_model_predict_started_at)
    timing_log("predict_proba", predict_started_at)
    return clamp_probability(float(probability))


def build_research_response(research_inputs: dict[str, Any], route_name: str) -> PredictionResponse:
    score = predict_from_research_inputs(research_inputs)
    return PredictionResponse(
        risk_score=score,
        prediction_label=risk_label(score),
        model_version=f"{active_research_model_version_base()}::{route_name}",
        serving_route=f"/predict/{route_name}" if route_name else "/predict",
        timestamp=utc_now_iso(),
        notes="Live local inference completed with the current Dataset #336 AutoPrognosis artifact. Explanation items are operational summaries for UI guidance rather than formal SHAP attributions.",
        explanation=explain_research_inputs(research_inputs),
    )


def build_clinical_response(clinical_inputs: dict[str, Any]) -> PredictionResponse:
    translated_inputs, translation_notes = translate_clinical_to_research(clinical_inputs)
    score = predict_from_research_inputs(translated_inputs)
    note = (
        "Live local inference completed through a provisional clinical-to-research adapter. "
        "The score comes from the current Dataset #336 AutoPrognosis artifact after conservative field translation."
    )
    if translation_notes:
        note += " " + " ".join(translation_notes)
    return PredictionResponse(
        risk_score=score,
        prediction_label=risk_label(score),
        model_version=active_clinical_adapter_version(),
        serving_route="/predict/clinical",
        timestamp=utc_now_iso(),
        notes=note,
        explanation=explain_clinical_inputs(clinical_inputs),
    )


def health_payload() -> dict[str, Any]:
    metadata = model_metadata()
    registry = model_registry()
    active_record = active_model_record()
    artifact_path = metadata.get("artifact_path")
    artifact_source = "packaged"
    if registry_s3_enabled():
        bundle = active_record.get("s3_bundle", {}) if active_record else {}
        artifact_path = f"s3://{bundle.get('bucket', os.environ['CKD_MODEL_ARTIFACT_BUCKET'])}/{bundle.get('model_key', os.environ.get('CKD_MODEL_ARTIFACT_KEY', ''))}"
        artifact_source = "registry_s3"
    elif legacy_s3_direct_enabled():
        artifact_path = f"s3://{os.environ['CKD_MODEL_ARTIFACT_BUCKET']}/{os.environ['CKD_MODEL_ARTIFACT_KEY']}"
        artifact_source = "legacy_s3"
    elif active_record is not None:
        bundle = active_record.get("local_bundle") or {}
        artifact_path = bundle.get("model_path", str(AUTOPROGNOSIS_ARTIFACT))
        artifact_source = "registry_local"
    return {
        "status": "ok",
        "service": "ckd-prediction-prototype",
        "artifact_status": metadata.get("status", "unknown"),
        "artifact_path": artifact_path,
        "artifact_source": artifact_source,
        "registry_enabled": registry is not None,
        "registry_version": registry.get("registry_version") if registry else None,
        "active_model_id": active_record.get("model_id") if active_record else None,
        "timestamp": utc_now_iso(),
    }
