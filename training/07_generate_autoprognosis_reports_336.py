import json
import logging

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.metrics import ConfusionMatrixDisplay, confusion_matrix, precision_recall_curve, roc_curve

from _autoprognosis_common import (
    ARTIFACTS_DIR,
    COMPARISON_CSV_PATH,
    METADATA_PATH,
    RUN_CONFIG_PATH,
    SETUP_SUMMARY_PATH,
    SUMMARY_MD_PATH,
    TEST_PREDICTIONS_PATH,
    TEST_RESULTS_PATH,
    configure_logging,
    ensure_artifact_dir,
)


def save_roc_plot(predictions_df: pd.DataFrame) -> None:
    fpr, tpr, _ = roc_curve(predictions_df["target_true"], predictions_df["risk_score"])
    plt.figure(figsize=(6, 5))
    plt.plot(fpr, tpr, label="AutoPrognosis")
    plt.plot([0, 1], [0, 1], linestyle="--", color="gray")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve - AutoPrognosis")
    plt.legend()
    plt.tight_layout()
    plt.savefig(ARTIFACTS_DIR / "roc_autoprognosis.png", dpi=150)
    plt.close()


def save_pr_plot(predictions_df: pd.DataFrame) -> None:
    precision, recall, _ = precision_recall_curve(predictions_df["target_true"], predictions_df["risk_score"])
    plt.figure(figsize=(6, 5))
    plt.plot(recall, precision, label="AutoPrognosis")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("Precision-Recall Curve - AutoPrognosis")
    plt.legend()
    plt.tight_layout()
    plt.savefig(ARTIFACTS_DIR / "pr_autoprognosis.png", dpi=150)
    plt.close()


def save_calibration_plot(predictions_df: pd.DataFrame) -> None:
    frac_pos, mean_pred = calibration_curve(
        predictions_df["target_true"], predictions_df["risk_score"], n_bins=10, strategy="uniform"
    )
    plt.figure(figsize=(6, 5))
    plt.plot(mean_pred, frac_pos, marker="o", label="AutoPrognosis")
    plt.plot([0, 1], [0, 1], linestyle="--", color="gray")
    plt.xlabel("Mean Predicted Probability")
    plt.ylabel("Observed Fraction Positive")
    plt.title("Calibration Curve - AutoPrognosis")
    plt.legend()
    plt.tight_layout()
    plt.savefig(ARTIFACTS_DIR / "calibration_autoprognosis.png", dpi=150)
    plt.close()


def save_confusion_matrix_plot(predictions_df: pd.DataFrame) -> None:
    cm = confusion_matrix(predictions_df["target_true"], predictions_df["prediction_label"], labels=[0, 1])
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=[0, 1])
    fig, ax = plt.subplots(figsize=(5, 5))
    disp.plot(ax=ax, colorbar=False)
    ax.set_title("Confusion Matrix - AutoPrognosis")
    fig.tight_layout()
    fig.savefig(ARTIFACTS_DIR / "confusion_matrix_autoprognosis.png", dpi=150)
    plt.close(fig)


def write_summary(
    setup_summary: dict,
    run_config: dict,
    metadata: dict,
    test_results_row: dict,
    baseline_df: pd.DataFrame | None,
    baseline_best_metadata: dict | None,
) -> None:
    lines = [
        "# AutoPrognosis Summary",
        "",
        "## Dataset Used",
        "",
        "- `data/processed/ckd_train_336_raw_aligned.csv`",
        f"- rows: {setup_summary['row_count']}",
        f"- features: {setup_summary['feature_count']}",
        "",
        "## Split Strategy",
        "",
        "- reused `artifacts/baselines_336/split_indices_336.csv`",
        "- identical held-out test split to the baseline package",
        "",
        "## Missingness Handling",
        "",
        "- raw aligned CSV remained unchanged",
        "- missingness was preserved outside the modeling workflow",
        "- AutoPrognosis was configured to handle missingness internally via its configured imputer search space",
        "",
        "## AutoPrognosis Configuration Summary",
        "",
        f"- classifiers: {run_config['classifiers']}",
        f"- imputers: {run_config['imputers']}",
        f"- feature_scaling: {run_config['feature_scaling']}",
        f"- feature_selection: {run_config['feature_selection']}",
        f"- n_folds_cv: {run_config['n_folds_cv']}",
        f"- timeout: {run_config['timeout']}",
        "",
        "## Held-Out Test Metrics",
        "",
        f"- AUROC: {test_results_row['auroc']:.3f}",
        f"- AUPRC: {test_results_row['auprc']:.3f}",
        f"- Accuracy: {test_results_row['accuracy']:.3f}",
        f"- Precision: {test_results_row['precision']:.3f}",
        f"- Recall (Sensitivity): {test_results_row['recall_sensitivity']:.3f}",
        f"- Specificity: {test_results_row['specificity']:.3f}",
        f"- F1-score: {test_results_row['f1_score']:.3f}",
        f"- Brier score: {test_results_row['brier_score']:.3f}",
        "",
        "## Important Caveats",
        "",
        "- dataset `857` was not used in this AutoPrognosis stage",
        "- deployment has not started",
        "- the logistic_regression AutoPrognosis plugin was excluded because it is incompatible with scikit-learn 1.8.0 in this environment",
    ]

    if baseline_df is not None and not baseline_df.empty:
        if baseline_best_metadata is not None:
            baseline_best = baseline_df.loc[
                baseline_df["model_name"] == baseline_best_metadata["best_model_name"]
            ].iloc[0]
        else:
            baseline_best = baseline_df.sort_values(["auroc", "auprc", "accuracy"], ascending=[False, False, False]).iloc[0]
        lines.extend(
            [
                "",
                "## Comparison vs Baseline",
                "",
                f"- best baseline model in current package: `{baseline_best['model_name']}`",
                f"- baseline best AUROC: {baseline_best['auroc']:.3f}",
                f"- baseline best AUPRC: {baseline_best['auprc']:.3f}",
                f"- baseline best Accuracy: {baseline_best['accuracy']:.3f}",
                f"- AutoPrognosis AUROC difference: {test_results_row['auroc'] - baseline_best['auroc']:.3f}",
                f"- AutoPrognosis AUPRC difference: {test_results_row['auprc'] - baseline_best['auprc']:.3f}",
                f"- AutoPrognosis Accuracy difference: {test_results_row['accuracy'] - baseline_best['accuracy']:.3f}",
            ]
        )

    SUMMARY_MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    configure_logging()
    ensure_artifact_dir()

    if not (SETUP_SUMMARY_PATH.exists() and RUN_CONFIG_PATH.exists() and METADATA_PATH.exists() and TEST_RESULTS_PATH.exists()):
        raise FileNotFoundError(
            "Missing AutoPrognosis artifacts. Run training/04_prepare_336_autoprognosis_setup.py, "
            "training/05_run_autoprognosis_336.py, and training/06_evaluate_autoprognosis_336.py first."
        )

    setup_summary = json.loads(SETUP_SUMMARY_PATH.read_text(encoding="utf-8"))
    run_config = json.loads(RUN_CONFIG_PATH.read_text(encoding="utf-8"))
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    test_results_df = pd.read_csv(TEST_RESULTS_PATH)
    predictions_df = pd.read_csv(TEST_PREDICTIONS_PATH)
    test_results_row = test_results_df.iloc[0].to_dict()

    save_roc_plot(predictions_df)
    save_pr_plot(predictions_df)
    save_calibration_plot(predictions_df)
    save_confusion_matrix_plot(predictions_df)

    baseline_results_path = ARTIFACTS_DIR.parents[0] / "baselines_336" / "test_results.csv"
    baseline_best_metadata_path = ARTIFACTS_DIR.parents[0] / "baselines_336" / "best_baseline_metadata.json"
    baseline_df = pd.read_csv(baseline_results_path) if baseline_results_path.exists() else None
    baseline_best_metadata = (
        json.loads(baseline_best_metadata_path.read_text(encoding="utf-8"))
        if baseline_best_metadata_path.exists()
        else None
    )

    comparison_rows = []
    if baseline_df is not None:
        for baseline_row in baseline_df.itertuples(index=False):
            comparison_rows.append(
                {
                    "baseline_model_name": baseline_row.model_name,
                    "autoprognosis_model_name": metadata["model_name"],
                    "baseline_auroc": float(baseline_row.auroc),
                    "autoprognosis_auroc": float(test_results_row["auroc"]),
                    "auroc_diff_autoprognosis_minus_baseline": float(test_results_row["auroc"] - baseline_row.auroc),
                    "baseline_auprc": float(baseline_row.auprc),
                    "autoprognosis_auprc": float(test_results_row["auprc"]),
                    "auprc_diff_autoprognosis_minus_baseline": float(test_results_row["auprc"] - baseline_row.auprc),
                    "baseline_accuracy": float(baseline_row.accuracy),
                    "autoprognosis_accuracy": float(test_results_row["accuracy"]),
                    "accuracy_diff_autoprognosis_minus_baseline": float(test_results_row["accuracy"] - baseline_row.accuracy),
                }
            )
    pd.DataFrame(comparison_rows).to_csv(COMPARISON_CSV_PATH, index=False)

    write_summary(setup_summary, run_config, metadata, test_results_row, baseline_df, baseline_best_metadata)

    logging.info("Saved AutoPrognosis plots to %s", ARTIFACTS_DIR)
    logging.info("Saved AutoPrognosis summary markdown to %s", SUMMARY_MD_PATH)
    logging.info("Saved baseline vs AutoPrognosis comparison to %s", COMPARISON_CSV_PATH)


if __name__ == "__main__":
    main()
