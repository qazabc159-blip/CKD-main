import json
import logging
import re
from pathlib import Path
from typing import Any

import pandas as pd
from ucimlrepo import fetch_ucirepo


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
ARTIFACTS_DIR = REPO_ROOT / "artifacts"

DATASET_CONFIG = {
    336: {
        "name": "Chronic Kidney Disease",
        "target_column": "class",
        "label_mapping": {
            "ckd": 1,
            "ckd\t": 1,
            "notckd": 0,
        },
    },
    857: {
        "name": "Risk Factor Prediction of Chronic Kidney Disease",
        "target_column": "class",
        "label_mapping": {
            "ckd": 1,
            "notckd": 0,
        },
    },
}


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def ensure_project_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def fetch_dataset(dataset_id: int):
    try:
        dataset = fetch_ucirepo(id=dataset_id)
    except Exception as exc:
        raise RuntimeError(f"Failed to download UCI dataset {dataset_id}: {exc}") from exc

    features = dataset.data.features
    targets = dataset.data.targets
    if features is None or targets is None:
        raise ValueError(f"Dataset {dataset_id} is missing features or targets.")

    return dataset, features.copy(), targets.copy()


def get_target_column(dataset_id: int, targets: pd.DataFrame) -> str:
    expected = DATASET_CONFIG[dataset_id]["target_column"]
    if expected not in targets.columns:
        raise KeyError(
            f"Dataset {dataset_id} target column '{expected}' was not found. "
            f"Available target columns: {list(targets.columns)}"
        )
    return expected


def serialize_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return value


def unique_values_in_order(series: pd.Series) -> list[Any]:
    values = []
    seen = set()
    for value in series.tolist():
        marker = "__NA__" if pd.isna(value) else repr(value)
        if marker in seen:
            continue
        seen.add(marker)
        values.append(serialize_value(value))
    return values


def distribution_records(series: pd.Series) -> list[dict[str, Any]]:
    counts = series.value_counts(dropna=False)
    total = len(series)
    records: list[dict[str, Any]] = []
    for value, count in counts.items():
        records.append(
            {
                "value": serialize_value(value),
                "count": int(count),
                "ratio": float(count / total if total else 0.0),
            }
        )
    return records


def build_missingness_report(df: pd.DataFrame) -> pd.DataFrame:
    report = pd.DataFrame(
        {
            "column": df.columns,
            "dtype": [str(df[column].dtype) for column in df.columns],
            "missing_count": [int(df[column].isna().sum()) for column in df.columns],
            "missing_ratio": [float(df[column].isna().mean()) for column in df.columns],
        }
    )
    return report


def build_profiling_payload(dataset_id: int, dataset_name: str, df: pd.DataFrame, target_column: str) -> dict[str, Any]:
    return {
        "dataset_id": dataset_id,
        "dataset_name": dataset_name,
        "num_rows": int(df.shape[0]),
        "num_columns": int(df.shape[1]),
        "num_feature_columns": int(df.shape[1] - 1),
        "duplicate_row_count": int(df.duplicated().sum()),
        "feature_columns": [str(column) for column in df.columns if column != target_column],
        "target_column": target_column,
        "dtypes": {str(column): str(df[column].dtype) for column in df.columns},
        "missingness": build_missingness_report(df).to_dict(orient="records"),
        "target_unique_values": unique_values_in_order(df[target_column]),
        "target_distribution": distribution_records(df[target_column]),
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def clean_string_cell(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    cleaned = value.strip()
    if cleaned == "":
        return pd.NA
    return cleaned


def coerce_numeric_like_series(series: pd.Series) -> pd.Series:
    if not (pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series)):
        return series

    non_null = series.dropna()
    if non_null.empty:
        return series

    parsed = pd.to_numeric(non_null, errors="coerce")
    if parsed.notna().sum() != len(non_null):
        return series

    converted = pd.to_numeric(series, errors="coerce")
    return converted


def minimal_clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    for column in cleaned.columns:
        series = cleaned[column]
        if pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series):
            series = series.map(clean_string_cell)
            series = coerce_numeric_like_series(series)
            cleaned[column] = series
    return cleaned


def exact_label_mapping(dataset_id: int) -> dict[str, int]:
    return DATASET_CONFIG[dataset_id]["label_mapping"].copy()


def encode_target(dataset_id: int, target_series: pd.Series) -> tuple[pd.Series, list[Any]]:
    mapping = exact_label_mapping(dataset_id)
    unexpected_values = [
        value for value in unique_values_in_order(target_series) if value is not None and value not in mapping
    ]
    if unexpected_values:
        return pd.Series(dtype="Int64"), unexpected_values

    encoded = target_series.map(mapping).astype("Int64")
    if encoded.isna().any():
        missing_values = unique_values_in_order(target_series[encoded.isna()])
        return pd.Series(dtype="Int64"), missing_values

    unique_encoded = set(encoded.dropna().astype(int).tolist())
    if unique_encoded - {0, 1}:
        raise ValueError(
            f"Dataset {dataset_id} produced invalid encoded target values: {sorted(unique_encoded)}"
        )
    return encoded.astype(int), []


def normalize_column_name(column_name: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", str(column_name).strip().lower())
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized
