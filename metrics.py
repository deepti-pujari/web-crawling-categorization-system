"""
metrics.py
Computes accuracy, precision, recall, and F1 score against a ground-truth dataset.

Usage (CLI):
    python src/output/metrics.py \
        --predicted  results/eval.csv \
        --ground-truth data/ground_truth.csv

Usage (Python):
    from src.output.metrics import evaluate
    report = evaluate(predicted_csv, ground_truth_csv)
"""

import sys
import argparse
import logging
from pathlib import Path

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
)

logger = logging.getLogger(__name__)


def evaluate(predicted_csv: str, ground_truth_csv: str) -> dict:
    """
    Compare predicted categories against ground-truth labels.

    Both CSVs must have a 'url' column and a 'category' column.
    Matching is done on URL; rows present in only one file are skipped.

    Returns a dict with overall and per-class metrics.
    """
    pred_df = pd.read_csv(predicted_csv, usecols=["url", "category"])
    true_df = pd.read_csv(ground_truth_csv, usecols=["url", "category"])

    # Normalise URLs for reliable joining
    pred_df["url"] = pred_df["url"].str.strip().str.rstrip("/")
    true_df["url"] = true_df["url"].str.strip().str.rstrip("/")

    merged = pd.merge(pred_df, true_df, on="url", suffixes=("_pred", "_true"))

    if merged.empty:
        logger.error("No matching URLs found between predicted and ground-truth files.")
        return {}

    y_pred = merged["category_pred"].fillna("Uncategorized").tolist()
    y_true = merged["category_true"].fillna("Uncategorized").tolist()

    overall = {
        "matched_urls":  len(merged),
        "accuracy":      round(accuracy_score(y_true, y_pred), 4),
        "macro_precision": round(precision_score(y_true, y_pred, average="macro", zero_division=0), 4),
        "macro_recall":    round(recall_score(y_true, y_pred, average="macro", zero_division=0), 4),
        "macro_f1":        round(f1_score(y_true, y_pred, average="macro", zero_division=0), 4),
    }

    per_class_report = classification_report(
        y_true, y_pred, output_dict=True, zero_division=0
    )
    # Remove sklearn summary rows; keep only per-class entries
    per_class = {
        k: {m: round(v, 4) for m, v in v_dict.items()}
        for k, v_dict in per_class_report.items()
        if k not in ("accuracy", "macro avg", "weighted avg")
    }

    report = {"overall": overall, "per_class": per_class}
    _print_report(overall, per_class_report, y_true, y_pred)
    return report


def _print_report(overall: dict, per_class_report: dict, y_true, y_pred):
    print("\n" + "=" * 60)
    print("  CLASSIFICATION EVALUATION REPORT")
    print("=" * 60)
    print(f"  Matched URLs  : {overall['matched_urls']}")
    print(f"  Accuracy      : {overall['accuracy'] * 100:.2f}%")
    print(f"  Macro Precision: {overall['macro_precision'] * 100:.2f}%")
    print(f"  Macro Recall  : {overall['macro_recall'] * 100:.2f}%")
    print(f"  Macro F1      : {overall['macro_f1'] * 100:.2f}%")
    print("\n  Per-class breakdown:")
    print("-" * 60)
    for label, scores in per_class_report.items():
        if label in ("accuracy", "macro avg", "weighted avg"):
            continue
        p = scores.get("precision", 0) * 100
        r = scores.get("recall", 0) * 100
        f = scores.get("f1-score", 0) * 100
        n = int(scores.get("support", 0))
        print(f"  {label:<22}  P: {p:5.1f}%  R: {r:5.1f}%  F1: {f:5.1f}%  n={n}")
    print("=" * 60 + "\n")


# ------------------------------------------------------------------
# CLI entry point
# ------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Evaluate classification accuracy.")
    parser.add_argument("--predicted",    required=True, help="Path to predicted results CSV")
    parser.add_argument("--ground-truth", required=True, help="Path to ground-truth CSV")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
    evaluate(args.predicted, args.ground_truth)


if __name__ == "__main__":
    main()
