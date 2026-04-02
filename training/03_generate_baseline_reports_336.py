import json
import logging

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.metrics import ConfusionMatrixDisplay, confusion_matrix, precision_recall_curve, roc_curve

from _baseline_common import (
    ARTIFACTS_DIR,
    BEST_METADATA_PATH,
    CV_RESULTS_PATH,
    SETUP_SUMMARY_PATH,
    SUMMARY_MD_PATH,
    TEST_RESULTS_PATH,
    configure_logging,
    ensure_artifact_dir,
)


def save_roc_plot(model_name: str, predictions_df: pd.DataFrame) -> None:
    fpr, tpr, _ = roc_curve(predictions_df["target_true"], predictions_df["risk_score"])
    plt.figure(figsize=(6, 5))
    plt.plot(fpr, tpr, label=model_name)
    plt.plot([0, 1], [0, 1], linestyle="--", color="gray")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title(f"ROC Curve - {model_name}")
    plt.legend()
    plt.tight_layout()
    plt.savefig(ARTIFACTS_DIR / f"roc_{model_name}.png", dpi=150)
    plt.close()


def save_pr_plot(model_name: str, predictions_df: pd.DataFrame) -> None:
    precision, recall, _ = precision_recall_curve(predictions_df["target_true"], predictions_df["risk_score"])
    plt.figure(figsize=(6, 5))
    plt.plot(recall, precision, label=model_name)
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title(f"Precision-Recall Curve - {model_name}")
    plt.legend()
    plt.tight_layout()
    plt.savefig(ARTIFACTS_DIR / f"pr_{model_name}.png", dpi=150)
    plt.close()


def save_calibration_plot(model_name: str, predictions_df: pd.DataFrame) -> None:
    frac_pos, mean_pred = calibration_curve(
        predictions_df["target_true"], predictions_df["risk_score"], n_bins=10, strategy="uniform"
    )
    plt.figure(figsize=(6, 5))
    plt.plot(mean_pred, frac_pos, marker="o", label=model_name)
    plt.plot([0, 1], [0, 1], linestyle="--", color="gray")
    plt.xlabel("Mean Predicted Probability")
    plt.ylabel("Observed Fraction Positive")
    plt.title(f"Calibration Curve - {model_name}")
    plt.legend()
    plt.tight_layout()
    plt.savefig(ARTIFACTS_DIR / f"calibration_{model_name}.png", dpi=150)
    plt.close()


def save_confusion_matrix_plot(best_model_name: str, predictions_df: pd.DataFrame) -> None:
    cm = confusion_matrix(predictions_df["target_true"], predictions_df["prediction_label"], labels=[0, 1])
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=[0, 1])
    fig, ax = plt.subplots(figsize=(5, 5))
    disp.plot(ax=ax, colorbar=False)
    ax.set_title(f"Confusion Matrix - {best_model_name}")
    fig.tight_layout()
    fig.savefig(ARTIFACTS_DIR / "confusion_matrix_best.png", dpi=150)
    plt.close(fig)


def write_summary_md(setup_summary: dict, cv_results_df: pd.DataFrame, test_results_df: pd.DataFrame, metadata: dict) -> None:
    lines = [
        "# Baseline Summary",
        "",
        "## Dataset Used",
        "",
        f"- `data/processed/ckd_train_336_raw_aligned.csv`",
        f"- rows: {setup_summary['row_count']}",
        f"- features: {setup_summary['feature_count']}",
        "",
        "## Split Strategy",
        "",
        f"- stratified train/test split with test size `{setup_summary['split_strategy']['test_size']}` and random_state `{setup_summary['split_strategy']['random_state']}`",
        "- 5-fold Stratified CV on the training split",
        f"- overall class distribution: {setup_summary['class_distribution']['counts']}",
        f"- train split class distribution: {setup_summary['split_strategy']['train_distribution']['counts']}",
        f"- test split class distribution: {setup_summary['split_strategy']['test_distribution']['counts']}",
        "",
        "## Model List",
        "",
    ]
    for model_name in cv_results_df["model_name"].tolist():
        lines.append(f"- `{model_name}`")

    lines.extend(
        [
            "",
            "## CV Summary",
            "",
        ]
    )
    for row in cv_results_df.itertuples(index=False):
        lines.append(
            f"- `{row.model_name}`: AUROC {row.auroc_mean:.3f} +/- {row.auroc_std:.3f}, "
            f"AUPRC {row.auprc_mean:.3f} +/- {row.auprc_std:.3f}, "
            f"F1 {row.f1_score_mean:.3f} +/- {row.f1_score_std:.3f}"
        )

    lines.extend(
        [
            "",
            "## Held-Out Test Summary",
            "",
        ]
    )
    for row in test_results_df.itertuples(index=False):
        lines.append(
            f"- `{row.model_name}`: AUROC {row.auroc:.3f}, AUPRC {row.auprc:.3f}, "
            f"Accuracy {row.accuracy:.3f}, Recall {row.recall_sensitivity:.3f}, "
            f"Specificity {row.specificity:.3f}, F1 {row.f1_score:.3f}, Brier {row.brier_score:.3f}"
        )

    lines.extend(
        [
            "",
            "## Best Baseline Model",
            "",
            f"- `{metadata['best_model_name']}` selected by `{metadata['selection_metric']}`",
            f"- estimator: `{metadata['best_estimator_label']}`",
            f"- boosting baseline note: {metadata['boosting_baseline_note']}",
            "",
            "## Important Caveats",
            "",
            "- dataset `857` was not used in this baseline package",
            "- AutoPrognosis outputs are tracked separately in `artifacts/autoprognosis_336/`",
            "- raw missingness is preserved outside sklearn pipelines",
            "- imputation is performed only inside model pipelines for baseline experiments",
            "- the current results come from dataset `336` only",
        ]
    )
    SUMMARY_MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    configure_logging()
    ensure_artifact_dir()

    if not (SETUP_SUMMARY_PATH.exists() and CV_RESULTS_PATH.exists() and TEST_RESULTS_PATH.exists() and BEST_METADATA_PATH.exists()):
        raise FileNotFoundError(
            "Missing baseline artifacts. Run training/01_prepare_336_baseline_setup.py and training/02_run_baseline_models_336.py first."
        )

    setup_summary = json.loads(SETUP_SUMMARY_PATH.read_text(encoding="utf-8"))
    cv_results_df = pd.read_csv(CV_RESULTS_PATH)
    test_results_df = pd.read_csv(TEST_RESULTS_PATH)
    metadata = json.loads(BEST_METADATA_PATH.read_text(encoding="utf-8"))

    for model_name in test_results_df["model_name"].tolist():
        predictions_df = pd.read_csv(ARTIFACTS_DIR / f"test_predictions_{model_name}.csv")
        save_roc_plot(model_name, predictions_df)
        save_pr_plot(model_name, predictions_df)
        save_calibration_plot(model_name, predictions_df)

    best_predictions_df = pd.read_csv(ARTIFACTS_DIR / f"test_predictions_{metadata['best_model_name']}.csv")
    save_confusion_matrix_plot(metadata["best_model_name"], best_predictions_df)
    write_summary_md(setup_summary, cv_results_df, test_results_df, metadata)

    logging.info("Saved plot outputs for all baseline models to %s", ARTIFACTS_DIR)
    logging.info("Saved baseline summary markdown to %s", SUMMARY_MD_PATH)


if __name__ == "__main__":
    main()
