from __future__ import annotations

import itertools
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.metrics import accuracy_score, roc_auc_score
from statsmodels.stats.contingency_tables import mcnemar


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


def model_label(model_name: str) -> str:
    labels = {
        "logistic_regression": "Logistic Regression",
        "random_forest": "Random Forest",
        "hist_gradient_boosting": "HistGradientBoostingClassifier",
        "autoprognosis": "AutoPrognosis",
    }
    return labels[model_name]


def compute_midrank(x: np.ndarray) -> np.ndarray:
    order = np.argsort(x)
    sorted_x = x[order]
    midranks = np.zeros(len(x), dtype=float)
    i = 0
    while i < len(sorted_x):
        j = i
        while j < len(sorted_x) and sorted_x[j] == sorted_x[i]:
            j += 1
        midranks[i:j] = 0.5 * (i + j - 1) + 1.0
        i = j
    restored = np.empty(len(x), dtype=float)
    restored[order] = midranks
    return restored


def fast_delong(predictions_sorted_transposed: np.ndarray, label_1_count: int) -> tuple[np.ndarray, np.ndarray]:
    m = label_1_count
    n = predictions_sorted_transposed.shape[1] - m
    positive_examples = predictions_sorted_transposed[:, :m]
    negative_examples = predictions_sorted_transposed[:, m:]
    k = predictions_sorted_transposed.shape[0]

    tx = np.empty((k, m), dtype=float)
    ty = np.empty((k, n), dtype=float)
    tz = np.empty((k, m + n), dtype=float)

    for r in range(k):
        tx[r, :] = compute_midrank(positive_examples[r, :])
        ty[r, :] = compute_midrank(negative_examples[r, :])
        tz[r, :] = compute_midrank(predictions_sorted_transposed[r, :])

    aucs = tz[:, :m].sum(axis=1) / m / n - (m + 1.0) / (2.0 * n)
    v01 = (tz[:, :m] - tx) / n
    v10 = 1.0 - (tz[:, m:] - ty) / m

    sx = np.atleast_2d(np.cov(v01))
    sy = np.atleast_2d(np.cov(v10))
    delong_cov = sx / m + sy / n
    return aucs, delong_cov


def delong_roc_test(y_true: np.ndarray, scores_a: np.ndarray, scores_b: np.ndarray) -> dict[str, float]:
    order = np.argsort(-y_true)
    sorted_true = y_true[order]
    label_1_count = int(sorted_true.sum())
    predictions = np.vstack([scores_a, scores_b])[:, order]

    aucs, covariance = fast_delong(predictions, label_1_count)
    contrast = np.array([[1.0, -1.0]])
    variance = float((contrast @ covariance @ contrast.T).item())
    auc_diff = float(aucs[0] - aucs[1])

    if variance <= 0 or np.isnan(variance):
        z_score = 0.0 if np.isclose(auc_diff, 0.0) else float("inf")
        p_value = 1.0 if np.isclose(auc_diff, 0.0) else 0.0
    else:
        z_score = abs(auc_diff) / np.sqrt(variance)
        p_value = float(2.0 * norm.sf(z_score))

    return {
        "auc_model_a": float(aucs[0]),
        "auc_model_b": float(aucs[1]),
        "auc_diff": auc_diff,
        "z_score": float(z_score),
        "p_value_raw": p_value,
    }


def mcnemar_accuracy_test(y_true: np.ndarray, pred_a: np.ndarray, pred_b: np.ndarray) -> dict[str, float]:
    correct_a = pred_a == y_true
    correct_b = pred_b == y_true
    contingency = np.array(
        [
            [np.sum(correct_a & correct_b), np.sum(correct_a & ~correct_b)],
            [np.sum(~correct_a & correct_b), np.sum(~correct_a & ~correct_b)],
        ],
        dtype=int,
    )
    result = mcnemar(contingency, exact=True, correction=False)
    return {
        "accuracy_model_a": float(accuracy_score(y_true, pred_a)),
        "accuracy_model_b": float(accuracy_score(y_true, pred_b)),
        "accuracy_diff": float(accuracy_score(y_true, pred_a) - accuracy_score(y_true, pred_b)),
        "both_correct": int(contingency[0, 0]),
        "a_correct_b_wrong": int(contingency[0, 1]),
        "a_wrong_b_correct": int(contingency[1, 0]),
        "both_wrong": int(contingency[1, 1]),
        "discordant_total": int(contingency[0, 1] + contingency[1, 0]),
        "p_value_raw": float(result.pvalue),
        "statistic": float(result.statistic),
    }


def bonferroni_adjust(series: pd.Series) -> pd.Series:
    return np.minimum(series * len(series), 1.0)


def load_predictions() -> dict[str, pd.DataFrame]:
    frames: dict[str, pd.DataFrame] = {}
    for source in prediction_sources():
        df = pd.read_csv(source.predictions_path).sort_values("row_index").reset_index(drop=True)
        frames[source.model_name] = df

    reference = next(iter(frames.values()))[["row_index", "target_true"]].copy()
    for model_name, df in frames.items():
        current = df[["row_index", "target_true"]]
        if not reference.equals(current):
            raise ValueError(f"Prediction rows do not align for {model_name}.")

    return frames


def build_summary_markdown(
    delong_df: pd.DataFrame,
    mcnemar_df: pd.DataFrame,
    method_path: Path,
) -> str:
    def format_p(row: pd.Series) -> str:
        return f"{row['p_value_bonferroni']:.4f}"

    lines = [
        "# Statistical Testing for Dataset #336 (Chapter 5.7)",
        "",
        "- Inputs: existing held-out prediction artifacts only; no model retraining was performed.",
        f"- Method metadata: `{method_path.as_posix()}`",
        "- Pairwise AUROC comparisons: DeLong test for correlated ROC curves.",
        "- Pairwise thresholded comparisons: exact McNemar test on prediction correctness.",
        "- Multiple-comparison control: Bonferroni correction within each test family.",
        "",
        "## Pairwise DeLong Tests (AUROC)",
        "",
        "| Comparison | AUROC (A) | AUROC (B) | Difference (A-B) | Raw p-value | Bonferroni-adjusted p-value | Significant |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]

    for _, row in delong_df.iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    row["comparison_label"],
                    f"{row['auc_model_a']:.3f}",
                    f"{row['auc_model_b']:.3f}",
                    f"{row['auc_diff']:.3f}",
                    f"{row['p_value_raw']:.4f}",
                    format_p(row),
                    "Yes" if row["reject_bonferroni"] else "No",
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Pairwise McNemar Tests (Thresholded Predictions)",
            "",
            "| Comparison | Accuracy (A) | Accuracy (B) | A correct / B wrong | A wrong / B correct | Raw p-value | Bonferroni-adjusted p-value | Significant |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )

    for _, row in mcnemar_df.iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    row["comparison_label"],
                    f"{row['accuracy_model_a']:.3f}",
                    f"{row['accuracy_model_b']:.3f}",
                    str(int(row["a_correct_b_wrong"])),
                    str(int(row["a_wrong_b_correct"])),
                    f"{row['p_value_raw']:.4f}",
                    f"{row['p_value_bonferroni']:.4f}",
                    "Yes" if row["reject_bonferroni"] else "No",
                ]
            )
            + " |"
        )

    return "\n".join(lines) + "\n"


def main() -> None:
    out_dir = artifacts_dir()
    out_dir.mkdir(parents=True, exist_ok=True)

    frames = load_predictions()
    model_names = list(frames)
    y_true = frames[model_names[0]]["target_true"].to_numpy(dtype=int)

    delong_rows: list[dict[str, object]] = []
    mcnemar_rows: list[dict[str, object]] = []

    for model_a, model_b in itertools.combinations(model_names, 2):
        df_a = frames[model_a]
        df_b = frames[model_b]

        delong_result = delong_roc_test(
            y_true=y_true,
            scores_a=df_a["risk_score"].to_numpy(dtype=float),
            scores_b=df_b["risk_score"].to_numpy(dtype=float),
        )
        mcnemar_result = mcnemar_accuracy_test(
            y_true=y_true,
            pred_a=df_a["prediction_label"].to_numpy(dtype=int),
            pred_b=df_b["prediction_label"].to_numpy(dtype=int),
        )

        label_a = model_label(model_a)
        label_b = model_label(model_b)
        comparison_label = f"{label_a} vs {label_b}"

        delong_rows.append(
            {
                "model_a": model_a,
                "model_b": model_b,
                "comparison_label": comparison_label,
                **delong_result,
            }
        )
        mcnemar_rows.append(
            {
                "model_a": model_a,
                "model_b": model_b,
                "comparison_label": comparison_label,
                **mcnemar_result,
            }
        )

    delong_df = pd.DataFrame(delong_rows)
    mcnemar_df = pd.DataFrame(mcnemar_rows)

    delong_df["p_value_bonferroni"] = bonferroni_adjust(delong_df["p_value_raw"])
    delong_df["reject_bonferroni"] = delong_df["p_value_bonferroni"] < 0.05

    mcnemar_df["p_value_bonferroni"] = bonferroni_adjust(mcnemar_df["p_value_raw"])
    mcnemar_df["reject_bonferroni"] = mcnemar_df["p_value_bonferroni"] < 0.05

    delong_path = out_dir / "pairwise_delong_336.csv"
    mcnemar_path = out_dir / "pairwise_mcnemar_336.csv"
    method_path = out_dir / "statistical_tests_336_method.json"
    summary_path = out_dir / "statistical_tests_336_summary.md"

    delong_df.to_csv(delong_path, index=False)
    mcnemar_df.to_csv(mcnemar_path, index=False)

    method_payload = {
        "dataset": "336",
        "input_type": "held-out test prediction artifacts",
        "tests": [
            {
                "name": "DeLong test",
                "target": "pairwise AUROC comparison for correlated ROC curves",
            },
            {
                "name": "Exact McNemar test",
                "target": "pairwise thresholded prediction comparison on correctness",
            },
        ],
        "multiple_comparison_control": {
            "method": "Bonferroni",
            "families": {
                "delong_family_size": len(delong_df),
                "mcnemar_family_size": len(mcnemar_df),
            },
            "alpha": 0.05,
        },
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
    summary_path.write_text(
        build_summary_markdown(delong_df, mcnemar_df, method_path.relative_to(project_root())),
        encoding="utf-8",
    )

    print(f"Wrote: {delong_path}")
    print(f"Wrote: {mcnemar_path}")
    print(f"Wrote: {method_path}")
    print(f"Wrote: {summary_path}")


if __name__ == "__main__":
    main()
