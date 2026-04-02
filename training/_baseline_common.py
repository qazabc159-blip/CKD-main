import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from joblib import dump
from sklearn.calibration import calibration_curve
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


REPO_ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = REPO_ROOT / "data" / "processed" / "ckd_train_336_raw_aligned.csv"
ARTIFACTS_DIR = REPO_ROOT / "artifacts" / "baselines_336"
SETUP_SUMMARY_PATH = ARTIFACTS_DIR / "setup_summary.json"
MISSINGNESS_PATH = ARTIFACTS_DIR / "missingness_336_baseline.csv"
FEATURE_TYPE_PLAN_PATH = ARTIFACTS_DIR / "feature_type_plan_336.csv"
SPLIT_INDICES_PATH = ARTIFACTS_DIR / "split_indices_336.csv"
CV_RESULTS_PATH = ARTIFACTS_DIR / "cv_results.csv"
TEST_RESULTS_PATH = ARTIFACTS_DIR / "test_results.csv"
BEST_MODEL_PATH = ARTIFACTS_DIR / "best_baseline_model.joblib"
BEST_METADATA_PATH = ARTIFACTS_DIR / "best_baseline_metadata.json"
SUMMARY_MD_PATH = ARTIFACTS_DIR / "baseline_summary.md"

TEST_SIZE = 0.2
RANDOM_STATE = 42
N_SPLITS = 5


def repo_relpath(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def ensure_artifact_dir() -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def load_dataset() -> pd.DataFrame:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Baseline dataset not found: {DATASET_PATH}")
    df = pd.read_csv(DATASET_PATH).reset_index(drop=True)
    if "target" not in df.columns:
        raise KeyError("Expected 'target' column is missing from ckd_train_336_raw_aligned.csv")
    return df


def validate_target_binary(df: pd.DataFrame) -> None:
    unique_values = sorted(df["target"].dropna().unique().tolist())
    if unique_values != [0, 1]:
        raise ValueError(f"Target must contain only 0 and 1. Found: {unique_values}")


def infer_feature_type_plan(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for feature_name in [column for column in df.columns if column != "target"]:
        series = df[feature_name]
        if pd.api.types.is_numeric_dtype(series):
            inferred_type = "numeric"
        else:
            inferred_type = "categorical_or_binary_text"
        rows.append(
            {
                "feature_name": feature_name,
                "dtype": str(series.dtype),
                "inferred_feature_type": inferred_type,
                "missing_count": int(series.isna().sum()),
                "missing_ratio": float(series.isna().mean()),
            }
        )
    return pd.DataFrame(rows)


def build_split_indices(df: pd.DataFrame) -> pd.DataFrame:
    indices = np.arange(len(df))
    train_idx, test_idx = train_test_split(
        indices,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=df["target"],
    )
    split_rows = []
    for idx in train_idx:
        split_rows.append({"row_index": int(idx), "split": "train", "target": int(df.loc[idx, "target"])})
    for idx in test_idx:
        split_rows.append({"row_index": int(idx), "split": "test", "target": int(df.loc[idx, "target"])})
    split_df = pd.DataFrame(split_rows).sort_values("row_index").reset_index(drop=True)
    return split_df


def class_distribution(series: pd.Series) -> dict[str, Any]:
    counts = series.value_counts().sort_index()
    total = int(series.shape[0])
    return {
        "total": total,
        "counts": {str(int(label)): int(count) for label, count in counts.items()},
        "ratios": {str(int(label)): float(count / total) for label, count in counts.items()},
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def save_model(model: Any) -> None:
    dump(model, BEST_MODEL_PATH)


def get_feature_lists(feature_type_plan_df: pd.DataFrame) -> tuple[list[str], list[str]]:
    numeric_features = feature_type_plan_df.loc[
        feature_type_plan_df["inferred_feature_type"] == "numeric", "feature_name"
    ].tolist()
    categorical_features = feature_type_plan_df.loc[
        feature_type_plan_df["inferred_feature_type"] == "categorical_or_binary_text", "feature_name"
    ].tolist()
    return numeric_features, categorical_features


def build_preprocessor(numeric_features: list[str], categorical_features: list[str]) -> ColumnTransformer:
    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
        ]
    )
    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("numeric", numeric_transformer, numeric_features),
            ("categorical", categorical_transformer, categorical_features),
        ],
        remainder="drop",
        sparse_threshold=0,
        verbose_feature_names_out=False,
    )


def xgboost_available() -> tuple[bool, Any]:
    try:
        from xgboost import XGBClassifier  # type: ignore

        return True, XGBClassifier
    except Exception:
        return False, None


def build_model_specs(numeric_features: list[str], categorical_features: list[str]) -> tuple[list[dict[str, Any]], str]:
    preprocessor = build_preprocessor(numeric_features, categorical_features)
    specs: list[dict[str, Any]] = [
        {
            "model_name": "logistic_regression",
            "estimator_label": "LogisticRegression",
            "pipeline": Pipeline(
                steps=[
                    ("preprocessor", preprocessor),
                    (
                        "model",
                        LogisticRegression(
                            max_iter=1000,
                            solver="liblinear",
                            random_state=RANDOM_STATE,
                        ),
                    ),
                ]
            ),
        },
        {
            "model_name": "random_forest",
            "estimator_label": "RandomForestClassifier",
            "pipeline": Pipeline(
                steps=[
                    ("preprocessor", preprocessor),
                    (
                        "model",
                        RandomForestClassifier(
                            n_estimators=300,
                            random_state=RANDOM_STATE,
                            n_jobs=-1,
                        ),
                    ),
                ]
            ),
        },
    ]

    has_xgboost, xgb_cls = xgboost_available()
    if has_xgboost and xgb_cls is not None:
        fallback_note = "xgboost available"
        specs.append(
            {
                "model_name": "xgboost",
                "estimator_label": "XGBClassifier",
                "pipeline": Pipeline(
                    steps=[
                        ("preprocessor", preprocessor),
                        (
                            "model",
                            xgb_cls(
                                objective="binary:logistic",
                                eval_metric="logloss",
                                random_state=RANDOM_STATE,
                                n_estimators=300,
                                learning_rate=0.05,
                                max_depth=4,
                                subsample=1.0,
                                colsample_bytree=1.0,
                            ),
                        ),
                    ]
                ),
            }
        )
    else:
        fallback_note = "xgboost unavailable; using HistGradientBoostingClassifier fallback"
        specs.append(
            {
                "model_name": "hist_gradient_boosting",
                "estimator_label": "HistGradientBoostingClassifier",
                "pipeline": Pipeline(
                    steps=[
                        ("preprocessor", preprocessor),
                        ("model", HistGradientBoostingClassifier(random_state=RANDOM_STATE)),
                    ]
                ),
            }
        )

    return specs, fallback_note


def specificity_score(y_true: pd.Series | np.ndarray, y_pred: np.ndarray) -> float:
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    if (tn + fp) == 0:
        return float("nan")
    return float(tn / (tn + fp))


def compute_metrics(y_true: pd.Series | np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray | None) -> dict[str, float]:
    metrics = {
        "auroc": float(roc_auc_score(y_true, y_prob)) if y_prob is not None else float("nan"),
        "auprc": float(average_precision_score(y_true, y_prob)) if y_prob is not None else float("nan"),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall_sensitivity": float(recall_score(y_true, y_pred, zero_division=0)),
        "specificity": specificity_score(y_true, y_pred),
        "f1_score": float(f1_score(y_true, y_pred, zero_division=0)),
        "brier_score": float(brier_score_loss(y_true, y_prob)) if y_prob is not None else float("nan"),
    }
    return metrics


def predict_probability(pipeline: Pipeline, X: pd.DataFrame) -> np.ndarray | None:
    if hasattr(pipeline, "predict_proba"):
        return pipeline.predict_proba(X)[:, 1]
    if hasattr(pipeline, "decision_function"):
        decision = pipeline.decision_function(X)
        return 1.0 / (1.0 + np.exp(-decision))
    return None


def cv_metric_columns() -> list[str]:
    return [
        "auroc",
        "auprc",
        "accuracy",
        "precision",
        "recall_sensitivity",
        "specificity",
        "f1_score",
        "brier_score",
    ]


def calibration_points(y_true: pd.Series, y_prob: pd.Series, n_bins: int = 10) -> tuple[np.ndarray, np.ndarray]:
    return calibration_curve(y_true, y_prob, n_bins=n_bins, strategy="uniform")
