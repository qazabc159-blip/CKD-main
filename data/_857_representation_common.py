import json
import math
import re
from pathlib import Path
from typing import Any

import pandas as pd

from _common import ARTIFACTS_DIR, PROCESSED_DIR


TRAIN_336_PATH = PROCESSED_DIR / "ckd_train_336_raw_aligned.csv"
VALID_857_PATH = PROCESSED_DIR / "ckd_valid_857_raw_aligned.csv"
SHARED_FEATURES_PATH = ARTIFACTS_DIR / "shared_feature_list.json"

EXCEL_LIKE_TOKEN_PATTERN = re.compile(r"^\d{1,2}-[A-Za-z]{3}$")
INTERVAL_RANGE_PATTERN = re.compile(r"^(-?\d+(?:\.\d+)?)\s*-\s*(-?\d+(?:\.\d+)?)$")
LESS_THAN_PATTERN = re.compile(r"^<\s*(-?\d+(?:\.\d+)?)$")
GREATER_EQUAL_PATTERN = re.compile(r"^(?:>=|≥)\s*(-?\d+(?:\.\d+)?)$")

LOW_RISK_BINARY_FEATURES = {"ane", "cad", "dm", "htn", "pe"}
MAPPING_REQUIRED_BINARY_FEATURES = {"appet", "ba", "pc", "pcc", "rbc"}
EXCEL_RISK_FEATURES = {"age", "al", "su"}
INTERVAL_RISK_FEATURES = {"age", "bgr", "bu", "hemo", "pcv", "pot", "rbcc", "sc", "sg", "sod", "wbcc"}


def load_shared_features() -> list[str]:
    payload = json.loads(SHARED_FEATURES_PATH.read_text(encoding="utf-8"))
    shared_features = payload.get("shared_features")
    if not isinstance(shared_features, list) or not shared_features:
        raise ValueError(f"Invalid shared feature list in {SHARED_FEATURES_PATH}")
    return [str(feature) for feature in shared_features]


def load_aligned_datasets() -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    shared_features = load_shared_features()
    train_336 = pd.read_csv(TRAIN_336_PATH)
    valid_857 = pd.read_csv(VALID_857_PATH)
    required_columns = shared_features + ["target"]
    for dataset_name, df in [("336", train_336), ("857", valid_857)]:
        missing_columns = [column for column in required_columns if column not in df.columns]
        if missing_columns:
            raise KeyError(f"Dataset {dataset_name} is missing required columns: {missing_columns}")
    return train_336, valid_857, shared_features


def normalize_string_token(value: Any) -> str:
    token = str(value).strip()
    token = token.replace("≤", "<=").replace("≥", ">=")
    token = re.sub(r"\s+", " ", token)
    return token


def normalized_non_null_values(series: pd.Series) -> list[str]:
    values = []
    seen = set()
    for value in series.dropna().tolist():
        token = normalize_string_token(value)
        if token in seen:
            continue
        seen.add(token)
        values.append(token)
    return values


def sample_values(series: pd.Series, limit: int = 10) -> list[str]:
    return normalized_non_null_values(series)[:limit]


def is_excel_like_token(token: str) -> bool:
    return bool(EXCEL_LIKE_TOKEN_PATTERN.match(normalize_string_token(token)))


def parse_interval_token(token: str) -> dict[str, Any] | None:
    normalized = normalize_string_token(token)

    range_match = INTERVAL_RANGE_PATTERN.match(normalized)
    if range_match:
        lower = float(range_match.group(1))
        upper = float(range_match.group(2))
        return {
            "kind": "range",
            "lower": lower,
            "upper": upper,
            "canonical": f"{format_number(lower)} - {format_number(upper)}",
        }

    less_match = LESS_THAN_PATTERN.match(normalized)
    if less_match:
        upper = float(less_match.group(1))
        return {
            "kind": "lt",
            "lower": -math.inf,
            "upper": upper,
            "canonical": f"< {format_number(upper)}",
        }

    ge_match = GREATER_EQUAL_PATTERN.match(normalized)
    if ge_match:
        lower = float(ge_match.group(1))
        return {
            "kind": "ge",
            "lower": lower,
            "upper": math.inf,
            "canonical": f">= {format_number(lower)}",
        }

    return None


def format_number(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return format(value, "g")


def detect_representation_type(series: pd.Series) -> str:
    non_null = series.dropna()
    values = normalized_non_null_values(series)

    if non_null.empty:
        return "unresolved"

    if pd.api.types.is_numeric_dtype(series):
        numeric_values = pd.to_numeric(non_null, errors="coerce")
        unique_values = sorted({float(value) for value in numeric_values.tolist()})
        if set(unique_values).issubset({0.0, 1.0}):
            return "binary_numeric"
        if len(unique_values) <= 10:
            return "ordinal_numeric"
        return "continuous_numeric"

    if any(is_excel_like_token(value) for value in values):
        return "excel_like_corrupted_token"

    if values and all(parse_interval_token(value) is not None for value in values):
        return "interval_text"

    lowered = {value.lower() for value in values}
    binary_vocabularies = [
        {"yes", "no"},
        {"present", "notpresent"},
        {"normal", "abnormal"},
        {"good", "poor"},
    ]
    if any(lowered.issubset(vocabulary) for vocabulary in binary_vocabularies):
        return "binary_text"

    numeric_values = pd.to_numeric(pd.Series(values), errors="coerce")
    if numeric_values.notna().sum() == len(values):
        if set(values).issubset({"0", "1"}):
            return "binary_numeric"
        if len(values) <= 10:
            return "ordinal_numeric"
        return "continuous_numeric"

    return "categorical_text"


def excel_like_tokens(series: pd.Series) -> list[str]:
    return [value for value in normalized_non_null_values(series) if is_excel_like_token(value)]


def interval_tokens(series: pd.Series) -> list[str]:
    return [value for value in normalized_non_null_values(series) if parse_interval_token(value) is not None]


def canonical_interval_mapping(values: list[str]) -> dict[str, int]:
    parsed_entries = []
    for value in values:
        parsed = parse_interval_token(value)
        if parsed is None:
            raise ValueError(f"Cannot build interval mapping for non-interval token: {value}")
        parsed_entries.append((value, parsed))

    parsed_entries.sort(key=lambda item: (item[1]["lower"], item[1]["upper"]))
    mapping: dict[str, int] = {}
    for index, (original_value, parsed) in enumerate(parsed_entries):
        mapping[original_value] = index
        mapping[parsed["canonical"]] = index
    return mapping


def apply_interval_bin_code(series: pd.Series) -> tuple[pd.Series, dict[str, int]]:
    values = normalized_non_null_values(series)
    mapping = canonical_interval_mapping(values)

    repaired_values = []
    for value in series.tolist():
        if pd.isna(value):
            repaired_values.append(pd.NA)
            continue
        normalized = normalize_string_token(value)
        if normalized not in mapping:
            raise ValueError(f"Unexpected interval token during repair: {normalized}")
        repaired_values.append(mapping[normalized])

    repaired_series = pd.Series(repaired_values, index=series.index, dtype="Int64")
    return repaired_series, mapping
