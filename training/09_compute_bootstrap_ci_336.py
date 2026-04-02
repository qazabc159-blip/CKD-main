from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
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


RANDOM_STATE = 42
N_BOOTSTRAP = 2000
ALPHA = 0.95


@dataclass(frozen=True)
class PredictionSource:
    model_name: str
    predictions_path: Path
    source_group: str


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def artifacts_dir() -> Path:
    return project_root() / "artifacts" / "statistics_336"


def prediction_sources() -> list[PredictionSource]:
    root = project_root() / "artifacts"
    return [
        PredictionSource(
            model_name="logistic_regression",
            predictions_path=root / "baselines_336" / "test_predictions_logistic_regression.csv",
            source_group="baseline",
        ),
        PredictionSource(
            model_name="random_forest",
            predictions_path=root / "baselines_336" / "test_predictions_random_forest.csv",
            source_group="baseline",
        ),
        PredictionSource(
            model_name="hist_gradient_boosting",
            predictions_path=root / "baselines_336" / "test_predictions_hist_gradient_boosting.csv",
            source_group="baseline",
        ),
        PredictionSource(
            model_name="autoprognosis",
            predictions_path=root / "autoprognosis_336" / "test_predictions_autoprognosis.csv",
            source_group="autoprognosis",
        ),
    ]


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray) -> dict[str, float]:
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    specificity = tn / (tn + fp) if (tn + fp) else float("nan")
    return {
        "auroc": roc_auc_score(y_true, y_prob),
        "auprc": average_precision_score(y_true, y_prob),
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall_sensitivity": recall_score(y_true, y_pred, zero_division=0),
        "specificity": specificity,
        "f1_score": f1_score(y_true, y_pred, zero_division=0),
        "brier_score": brier_score_loss(y_true, y_prob),
    }


def stratified_bootstrap_indices(y_true: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    pos_idx = np.where(y_true == 1)[0]
    neg_idx = np.where(y_true == 0)[0]
    sampled_pos = rng.choice(pos_idx, size=len(pos_idx), replace=True)
    sampled_neg = rng.choice(neg_idx, size=len(neg_idx), replace=True)
    sample = np.concatenate([sampled_pos, sampled_neg])
    rng.shuffle(sample)
    return sample


def percentile_interval(samples: np.ndarray, alpha: float) -> tuple[float, float]:
    lower_q = (1.0 - alpha) / 2.0 * 100.0
    upper_q = (1.0 + alpha) / 2.0 * 100.0
    lower, upper = np.percentile(samples, [lower_q, upper_q])
    return float(lower), float(upper)


def bootstrap_metrics(df: pd.DataFrame, rng: np.random.Generator) -> tuple[dict[str, float], dict[str, np.ndarray]]:
    y_true = df["target_true"].to_numpy(dtype=int)
    y_pred = df["prediction_label"].to_numpy(dtype=int)
    y_prob = df["risk_score"].to_numpy(dtype=float)

    point_estimates = compute_metrics(y_true, y_pred, y_prob)
    bootstrap_store = {metric: np.zeros(N_BOOTSTRAP, dtype=float) for metric in point_estimates}

    for i in range(N_BOOTSTRAP):
        sample_idx = stratified_bootstrap_indices(y_true, rng)
        metrics = compute_metrics(y_true[sample_idx], y_pred[sample_idx], y_prob[sample_idx])
        for metric_name, metric_value in metrics.items():
            bootstrap_store[metric_name][i] = metric_value

    return point_estimates, bootstrap_store


def format_interval(point: float, lower: float, upper: float) -> str:
    return f"{point:.3f} ({lower:.3f}-{upper:.3f})"


def build_summary_markdown(wide_df: pd.DataFrame, method_path: Path) -> str:
    ordered_metrics = [
        "auroc",
        "auprc",
        "accuracy",
        "precision",
        "recall_sensitivity",
        "specificity",
        "f1_score",
        "brier_score",
    ]
    metric_labels = {
        "auroc": "AUROC",
        "auprc": "AUPRC",
        "accuracy": "Accuracy",
        "precision": "Precision",
        "recall_sensitivity": "Recall/Sensitivity",
        "specificity": "Specificity",
        "f1_score": "F1-score",
        "brier_score": "Brier score",
    }

    lines = [
        "# Bootstrap 95% CI for Dataset #336",
        "",
        f"- Method: stratified percentile bootstrap on held-out test predictions",
        f"- Replicates: {N_BOOTSTRAP}",
        f"- Random state: {RANDOM_STATE}",
        f"- Method metadata: `{method_path.as_posix()}`",
        "",
        "| Model | " + " | ".join(metric_labels[m] for m in ordered_metrics) + " |",
        "| --- | " + " | ".join(["---"] * len(ordered_metrics)) + " |",
    ]

    for _, row in wide_df.iterrows():
        cells = [row["model_name"]]
        for metric in ordered_metrics:
            cells.append(row[f"{metric}_with_ci"])
        lines.append("| " + " | ".join(cells) + " |")

    return "\n".join(lines) + "\n"


def main() -> None:
    out_dir = artifacts_dir()
    out_dir.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(RANDOM_STATE)
    long_rows: list[dict[str, object]] = []
    wide_rows: list[dict[str, object]] = []

    for source in prediction_sources():
        df = pd.read_csv(source.predictions_path)
        point_estimates, bootstrap_store = bootstrap_metrics(df, rng)

        wide_row: dict[str, object] = {
            "model_name": source.model_name,
            "source_group": source.source_group,
            "n_test": len(df),
            "n_positive": int(df["target_true"].sum()),
            "n_negative": int((1 - df["target_true"]).sum()),
        }

        for metric_name, point_estimate in point_estimates.items():
            lower, upper = percentile_interval(bootstrap_store[metric_name], ALPHA)
            long_rows.append(
                {
                    "model_name": source.model_name,
                    "source_group": source.source_group,
                    "metric": metric_name,
                    "point_estimate": point_estimate,
                    "ci_lower": lower,
                    "ci_upper": upper,
                    "n_bootstrap": N_BOOTSTRAP,
                    "alpha": ALPHA,
                    "bootstrap_method": "stratified_percentile",
                }
            )
            wide_row[metric_name] = point_estimate
            wide_row[f"{metric_name}_ci_lower"] = lower
            wide_row[f"{metric_name}_ci_upper"] = upper
            wide_row[f"{metric_name}_with_ci"] = format_interval(point_estimate, lower, upper)

        wide_rows.append(wide_row)

    long_df = pd.DataFrame(long_rows)
    wide_df = pd.DataFrame(wide_rows)

    long_path = out_dir / "bootstrap_ci_336_long.csv"
    wide_path = out_dir / "bootstrap_ci_336_wide.csv"
    method_path = out_dir / "bootstrap_ci_method.json"
    summary_path = out_dir / "bootstrap_ci_summary.md"

    long_df.to_csv(long_path, index=False)
    wide_df.to_csv(wide_path, index=False)

    method_payload = {
        "dataset": "336",
        "input_type": "held-out test prediction artifacts",
        "bootstrap_method": "stratified_percentile",
        "replicates": N_BOOTSTRAP,
        "alpha": ALPHA,
        "random_state": RANDOM_STATE,
        "metrics": [
            "auroc",
            "auprc",
            "accuracy",
            "precision",
            "recall_sensitivity",
            "specificity",
            "f1_score",
            "brier_score",
        ],
        "prediction_sources": [
            {
                "model_name": source.model_name,
                "source_group": source.source_group,
                "predictions_path": source.predictions_path.relative_to(project_root()).as_posix(),
            }
            for source in prediction_sources()
        ],
    }
    method_path.write_text(json.dumps(method_payload, indent=2), encoding="utf-8")
    summary_path.write_text(build_summary_markdown(wide_df, method_path.relative_to(project_root())), encoding="utf-8")

    print(f"Wrote: {long_path}")
    print(f"Wrote: {wide_path}")
    print(f"Wrote: {method_path}")
    print(f"Wrote: {summary_path}")


if __name__ == "__main__":
    main()
