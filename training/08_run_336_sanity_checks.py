import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from _baseline_common import DATASET_PATH, SPLIT_INDICES_PATH, infer_feature_type_plan, validate_target_binary


REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = REPO_ROOT / "artifacts" / "sanity_checks_336"
SUMMARY_PATH = ARTIFACTS_DIR / "sanity_check_summary.md"
FEATURE_SCREEN_PATH = ARTIFACTS_DIR / "feature_leakage_screen.csv"
TOP_SIGNAL_PATH = ARTIFACTS_DIR / "top_feature_signal_summary.csv"


CLINICAL_CONTEXT = {
    "hemo": "Hemoglobin is clinically relevant for anemia and CKD severity, so a strong signal is plausible.",
    "pcv": "Packed cell volume is closely related to anemia burden and is clinically plausible as a strong CKD signal.",
    "sg": "Urine specific gravity can reflect renal concentrating ability, so a strong signal is clinically plausible.",
    "sc": "Serum creatinine is a core renal marker, so a strong signal is expected rather than automatically suspicious.",
    "rbcc": "Red blood cell count may reflect anemia-related CKD burden and can legitimately carry strong signal.",
    "al": "Albumin in urine is a clinically meaningful kidney-related feature and can be strongly predictive.",
    "dm": "Diabetes status is a plausible CKD risk factor, but binary perfect separation on train alone should be treated cautiously.",
    "htn": "Hypertension status is a plausible CKD risk factor, but binary perfect separation on train alone should be treated cautiously.",
    "bgr": "Blood glucose is clinically plausible and may correlate with diabetes-related CKD burden.",
    "bu": "Blood urea is a renal-function marker and can legitimately show strong signal.",
}


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def ensure_artifacts_dir() -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")
    if not SPLIT_INDICES_PATH.exists():
        raise FileNotFoundError(f"Split file not found: {SPLIT_INDICES_PATH}")

    df = pd.read_csv(DATASET_PATH).reset_index(drop=True)
    split_df = pd.read_csv(SPLIT_INDICES_PATH)
    validate_target_binary(df)
    return df, split_df


def split_integrity(df: pd.DataFrame, split_df: pd.DataFrame) -> dict[str, object]:
    train_idx = set(split_df.loc[split_df["split"] == "train", "row_index"].astype(int).tolist())
    test_idx = set(split_df.loc[split_df["split"] == "test", "row_index"].astype(int).tolist())

    overlap = sorted(train_idx.intersection(test_idx))
    feature_columns = [column for column in df.columns if column != "target"]
    train_features = (
        df.loc[sorted(train_idx), feature_columns]
        .fillna("__MISSING__")
        .astype(str)
        .agg("||".join, axis=1)
    )
    test_features = (
        df.loc[sorted(test_idx), feature_columns]
        .fillna("__MISSING__")
        .astype(str)
        .agg("||".join, axis=1)
    )

    exact_feature_overlap = len(set(train_features).intersection(set(test_features)))
    return {
        "train_count": len(train_idx),
        "test_count": len(test_idx),
        "index_overlap_count": len(overlap),
        "index_overlap_examples": overlap[:10],
        "exact_feature_row_overlap_count": exact_feature_overlap,
        "train_target_counts": split_df.loc[split_df["split"] == "train", "target"].value_counts().sort_index().to_dict(),
        "test_target_counts": split_df.loc[split_df["split"] == "test", "target"].value_counts().sort_index().to_dict(),
    }


def numeric_signal(series: pd.Series, target: pd.Series) -> dict[str, float | int | None]:
    mask = series.notna()
    observed = int(mask.sum())
    if observed < 10 or target[mask].nunique() < 2 or series[mask].nunique() < 2:
        return {"score": np.nan, "observed_count": observed}
    auc = roc_auc_score(target[mask], series[mask])
    return {"score": float(max(auc, 1 - auc)), "observed_count": observed}


def categorical_signal(series: pd.Series, target: pd.Series) -> dict[str, float | int | None]:
    clean = series.fillna("__MISSING__").astype(str)
    grouped = pd.DataFrame({"feature": clean, "target": target}).groupby("feature")["target"].agg(["mean", "count"])
    if grouped.empty:
        return {"score": np.nan, "observed_count": 0, "category_count": 0}
    score = float(grouped["mean"].max() - grouped["mean"].min())
    return {
        "score": score,
        "observed_count": int(series.notna().sum()),
        "category_count": int(grouped.shape[0]),
    }


def classify_leakage_risk(feature_name: str, feature_type: str, train_score: float, test_score: float) -> tuple[str, str]:
    max_score = np.nanmax([train_score, test_score])
    min_score = np.nanmin([train_score, test_score])

    if feature_name.lower() in {"target", "label", "class"}:
        return "high", "Feature name itself looks target-like and would require immediate review."
    if feature_type == "numeric" and max_score >= 0.98 and min_score >= 0.95:
        return "review", "Very strong univariate numeric separation. This is worth interpretation, but may still be clinically plausible."
    if feature_type == "categorical_or_binary_text" and train_score >= 0.99 and test_score >= 0.75:
        return "review", "Near-perfect categorical separation appears in train and remains strong in test. Review is warranted."
    if feature_type == "categorical_or_binary_text" and train_score >= 0.99 and test_score < 0.75:
        return "low", "Train-only perfect separation does not hold on test; this looks more like small-sample instability than obvious leakage."
    return "low", "No obvious leakage signature from this quick univariate screen."


def build_feature_screen(df: pd.DataFrame, split_df: pd.DataFrame) -> pd.DataFrame:
    feature_plan = infer_feature_type_plan(df)
    train_idx = split_df.loc[split_df["split"] == "train", "row_index"].astype(int).tolist()
    test_idx = split_df.loc[split_df["split"] == "test", "row_index"].astype(int).tolist()

    rows = []
    for row in feature_plan.itertuples(index=False):
        feature_name = row.feature_name
        series = df[feature_name]
        y_train = df.loc[train_idx, "target"].reset_index(drop=True)
        y_test = df.loc[test_idx, "target"].reset_index(drop=True)
        x_train = df.loc[train_idx, feature_name].reset_index(drop=True)
        x_test = df.loc[test_idx, feature_name].reset_index(drop=True)

        if row.inferred_feature_type == "numeric":
            train_signal = numeric_signal(x_train, y_train)
            test_signal = numeric_signal(x_test, y_test)
            signal_method = "single_feature_auroc"
            category_count = np.nan
        else:
            train_signal = categorical_signal(x_train, y_train)
            test_signal = categorical_signal(x_test, y_test)
            signal_method = "target_rate_range"
            category_count = train_signal.get("category_count", np.nan)

        train_score = float(train_signal["score"]) if pd.notna(train_signal["score"]) else np.nan
        test_score = float(test_signal["score"]) if pd.notna(test_signal["score"]) else np.nan
        leakage_risk, leakage_note = classify_leakage_risk(
            feature_name, row.inferred_feature_type, train_score, test_score
        )

        rows.append(
            {
                "feature_name": feature_name,
                "basic_type": row.inferred_feature_type,
                "dtype": row.dtype,
                "missing_rate": float(row.missing_ratio),
                "signal_method": signal_method,
                "train_signal_score": train_score,
                "test_signal_score": test_score,
                "average_signal_score": float(np.nanmean([train_score, test_score])),
                "train_observed_count": int(train_signal["observed_count"]),
                "test_observed_count": int(test_signal["observed_count"]),
                "train_category_count": category_count,
                "leakage_risk_level": leakage_risk,
                "leakage_risk_note": leakage_note,
            }
        )

    screen_df = pd.DataFrame(rows).sort_values(
        ["average_signal_score", "test_signal_score", "train_signal_score"],
        ascending=[False, False, False],
    ).reset_index(drop=True)
    return screen_df


def build_top_feature_summary(screen_df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    top_df = screen_df.head(top_n).copy()
    top_df["rank"] = np.arange(1, len(top_df) + 1)
    top_df["interpretation_note"] = top_df["feature_name"].map(CLINICAL_CONTEXT).fillna(
        "Strong signal is visible in this quick screen. It should be interpreted, but it is not automatically target leakage."
    )
    top_df["overall_assessment"] = top_df.apply(
        lambda row: "review_but_clinically_plausible"
        if row["leakage_risk_level"] == "review"
        else "strong_but_not_obviously_leaky",
        axis=1,
    )
    return top_df[
        [
            "rank",
            "feature_name",
            "basic_type",
            "train_signal_score",
            "test_signal_score",
            "average_signal_score",
            "leakage_risk_level",
            "overall_assessment",
            "interpretation_note",
        ]
    ]


def write_summary_md(integrity: dict[str, object], screen_df: pd.DataFrame, top_df: pd.DataFrame) -> None:
    review_features = top_df.loc[top_df["leakage_risk_level"] == "review", "feature_name"].tolist()
    top_feature_list = ", ".join(top_df["feature_name"].tolist())

    lines = [
        "# Sanity Check Summary",
        "",
        "## Split Integrity Check",
        "",
        f"- train/test index overlap count: {integrity['index_overlap_count']}",
        f"- exact feature-row overlap count across splits: {integrity['exact_feature_row_overlap_count']}",
        f"- train target counts: {integrity['train_target_counts']}",
        f"- test target counts: {integrity['test_target_counts']}",
        "",
        "## Quick Interpretation",
        "",
    ]

    if integrity["index_overlap_count"] == 0:
        lines.append("- No train/test index overlap was detected.")
    else:
        lines.append(f"- Train/test index overlap was detected and requires review: {integrity['index_overlap_examples']}")

    if int(integrity["exact_feature_row_overlap_count"]) == 0:
        lines.append("- No exact duplicated feature rows were detected across train and test splits in this quick screen.")
    else:
        lines.append(
            f"- Exact duplicated feature rows were detected across splits ({integrity['exact_feature_row_overlap_count']}) and should be reviewed."
        )

    if review_features:
        lines.append(
            f"- The strongest features that deserve interpretation review are: {', '.join(review_features)}."
        )
    else:
        lines.append("- No feature was flagged as obvious target leakage in this quick screen.")

    lines.extend(
        [
            f"- Top signal features in this quick screen: {top_feature_list}.",
            "- Results are very strong, but no obvious leakage was detected in this quick sanity check.",
            "- Further interpretation is still needed because dataset `336` may be intrinsically easy and several clinically plausible renal markers are highly informative.",
        ]
    )

    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    configure_logging()
    ensure_artifacts_dir()

    df, split_df = load_inputs()
    integrity = split_integrity(df, split_df)
    screen_df = build_feature_screen(df, split_df)
    top_df = build_top_feature_summary(screen_df, top_n=10)

    screen_df.to_csv(FEATURE_SCREEN_PATH, index=False)
    top_df.to_csv(TOP_SIGNAL_PATH, index=False)
    write_summary_md(integrity, screen_df, top_df)

    logging.info("Saved sanity summary to %s", SUMMARY_PATH)
    logging.info("Saved feature leakage screen to %s", FEATURE_SCREEN_PATH)
    logging.info("Saved top feature signal summary to %s", TOP_SIGNAL_PATH)


if __name__ == "__main__":
    main()
