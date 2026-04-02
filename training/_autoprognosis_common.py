import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from autoprognosis.plugins.ensemble.classifiers import WeightedEnsemble
from autoprognosis.studies.classifiers import ClassifierStudy
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

from _baseline_common import (
    DATASET_PATH,
    RANDOM_STATE,
    SPLIT_INDICES_PATH,
    TEST_SIZE,
    class_distribution,
    infer_feature_type_plan,
    validate_target_binary,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = REPO_ROOT / "artifacts" / "autoprognosis_336"
SETUP_SUMMARY_PATH = ARTIFACTS_DIR / "setup_summary.json"
FEATURE_TYPE_PLAN_PATH = ARTIFACTS_DIR / "feature_type_plan_336.csv"
SPLIT_CHECK_PATH = ARTIFACTS_DIR / "train_test_split_check.json"
RUN_CONFIG_PATH = ARTIFACTS_DIR / "autoprognosis_run_config.json"
TRAINING_LOG_PATH = ARTIFACTS_DIR / "autoprognosis_training_log.json"
MODEL_PATH = ARTIFACTS_DIR / "best_autoprognosis_model.pkl"
METADATA_PATH = ARTIFACTS_DIR / "best_autoprognosis_metadata.json"
TEST_RESULTS_PATH = ARTIFACTS_DIR / "test_results.csv"
TEST_PREDICTIONS_PATH = ARTIFACTS_DIR / "test_predictions_autoprognosis.csv"
CONFUSION_MATRIX_CSV_PATH = ARTIFACTS_DIR / "confusion_matrix_autoprognosis.csv"
SUMMARY_MD_PATH = ARTIFACTS_DIR / "autoprognosis_summary.md"
COMPARISON_CSV_PATH = ARTIFACTS_DIR / "baseline_vs_autoprognosis_comparison.csv"
BLOCKERS_PATH = ARTIFACTS_DIR / "blockers.md"
WORKSPACE_DIR = ARTIFACTS_DIR / "workspace"


def repo_relpath(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def ensure_artifact_dir() -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def write_blocker(message: str) -> None:
    BLOCKERS_PATH.write_text(message.strip() + "\n", encoding="utf-8")


def load_dataset() -> pd.DataFrame:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"AutoPrognosis dataset not found: {DATASET_PATH}")
    df = pd.read_csv(DATASET_PATH).reset_index(drop=True)
    validate_target_binary(df)
    return df


def load_split_indices(df: pd.DataFrame) -> tuple[list[int], list[int], pd.DataFrame]:
    if not SPLIT_INDICES_PATH.exists():
        raise FileNotFoundError(
            f"Missing baseline split file: {SPLIT_INDICES_PATH}. "
            "AutoPrognosis setup must reuse the baseline split."
        )

    split_df = pd.read_csv(SPLIT_INDICES_PATH)
    required_columns = {"row_index", "split", "target"}
    if not required_columns.issubset(split_df.columns):
        raise ValueError(
            f"Split file is missing required columns: {sorted(required_columns - set(split_df.columns))}"
        )

    train_indices = split_df.loc[split_df["split"] == "train", "row_index"].astype(int).tolist()
    test_indices = split_df.loc[split_df["split"] == "test", "row_index"].astype(int).tolist()
    if len(train_indices) + len(test_indices) != len(df):
        raise ValueError("Split file does not cover the full dataset.")

    return train_indices, test_indices, split_df


def build_split_check(df: pd.DataFrame, split_df: pd.DataFrame) -> dict[str, Any]:
    train_targets = split_df.loc[split_df["split"] == "train", "target"]
    test_targets = split_df.loc[split_df["split"] == "test", "target"]
    return {
        "baseline_split_file": repo_relpath(SPLIT_INDICES_PATH),
        "dataset_used": repo_relpath(DATASET_PATH),
        "split_strategy": "reuse_existing_baseline_split",
        "random_state": RANDOM_STATE,
        "test_size": TEST_SIZE,
        "train_distribution": class_distribution(train_targets),
        "test_distribution": class_distribution(test_targets),
        "split_matches_dataset_rows": int(split_df.shape[0]) == int(df.shape[0]),
    }


def build_setup_summary(df: pd.DataFrame, feature_type_plan_df: pd.DataFrame, split_check: dict[str, Any]) -> dict[str, Any]:
    missingness = feature_type_plan_df[["feature_name", "missing_count", "missing_ratio"]].to_dict(orient="records")
    return {
        "dataset_used": repo_relpath(DATASET_PATH),
        "row_count": int(df.shape[0]),
        "feature_count": int(df.shape[1] - 1),
        "feature_names": [column for column in df.columns if column != "target"],
        "class_distribution": class_distribution(df["target"]),
        "missingness": missingness,
        "feature_types": {
            "numeric": feature_type_plan_df.loc[
                feature_type_plan_df["inferred_feature_type"] == "numeric", "feature_name"
            ].tolist(),
            "categorical_or_binary_text": feature_type_plan_df.loc[
                feature_type_plan_df["inferred_feature_type"] == "categorical_or_binary_text", "feature_name"
            ].tolist(),
        },
        "split_check": split_check,
    }


def default_run_config() -> dict[str, Any]:
    return {
        "study_name": "autoprognosis_336_main",
        "metric": "aucroc",
        "num_iter": 5,
        "num_study_iter": 3,
        "num_ensemble_iter": 1,
        "ensemble_size": 1,
        "timeout": 300,
        "n_folds_cv": 5,
        "feature_scaling": ["nop"],
        "feature_selection": ["nop"],
        "classifiers": ["random_forest", "xgboost", "catboost"],
        "imputers": ["ice"],
        "score_threshold": 0.5,
        "random_state": RANDOM_STATE,
        "sample_for_search": False,
        "workspace": repo_relpath(WORKSPACE_DIR),
        "known_limitations": [
            "autoprognosis logistic_regression plugin is excluded because it is incompatible with scikit-learn 1.8.0 in this environment.",
            "dataset 857 is not used in this stage.",
        ],
    }


def create_study(train_df: pd.DataFrame, config: dict[str, Any]) -> ClassifierStudy:
    return ClassifierStudy(
        dataset=train_df,
        target="target",
        num_iter=config["num_iter"],
        num_study_iter=config["num_study_iter"],
        num_ensemble_iter=config["num_ensemble_iter"],
        timeout=config["timeout"],
        metric=config["metric"],
        study_name=config["study_name"],
        feature_scaling=config["feature_scaling"],
        feature_selection=config["feature_selection"],
        classifiers=config["classifiers"],
        imputers=config["imputers"],
        workspace=WORKSPACE_DIR,
        score_threshold=config["score_threshold"],
        random_state=config["random_state"],
        sample_for_search=config["sample_for_search"],
        ensemble_size=config["ensemble_size"],
        n_folds_cv=config["n_folds_cv"],
    )


def save_weighted_ensemble(model: WeightedEnsemble) -> None:
    MODEL_PATH.write_bytes(model.save())


def load_weighted_ensemble() -> WeightedEnsemble:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Missing AutoPrognosis model artifact: {MODEL_PATH}")
    return WeightedEnsemble.load(MODEL_PATH.read_bytes())


def probability_vector(model: WeightedEnsemble, X: pd.DataFrame) -> np.ndarray:
    proba = model.predict_proba(X)
    proba_arr = np.asarray(proba)
    if proba_arr.ndim == 1:
        return proba_arr.astype(float)
    if proba_arr.shape[1] == 2:
        return proba_arr[:, 1].astype(float)
    return proba_arr.reshape(-1).astype(float)


def prediction_vector(model: WeightedEnsemble, X: pd.DataFrame) -> np.ndarray:
    preds = model.predict(X)
    pred_arr = np.asarray(preds).reshape(-1)
    return pred_arr.astype(int)


def specificity_score(y_true: pd.Series | np.ndarray, y_pred: np.ndarray) -> float:
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    if (tn + fp) == 0:
        return float("nan")
    return float(tn / (tn + fp))


def compute_metrics(y_true: pd.Series | np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray) -> dict[str, float]:
    return {
        "auroc": float(roc_auc_score(y_true, y_prob)),
        "auprc": float(average_precision_score(y_true, y_prob)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall_sensitivity": float(recall_score(y_true, y_pred, zero_division=0)),
        "specificity": specificity_score(y_true, y_pred),
        "f1_score": float(f1_score(y_true, y_pred, zero_division=0)),
        "brier_score": float(brier_score_loss(y_true, y_prob)),
    }
