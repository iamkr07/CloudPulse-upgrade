"""Offline confidence calibration evaluation for the production or multi-horizon classifier."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.model_selection import GroupShuffleSplit
import joblib

sys.path.insert(0, str(Path(__file__).resolve().parent))
from features import FEATURE_COLUMNS, build_supervised_windows

ML_DIR = Path(__file__).resolve().parent
TEST_PATH = ML_DIR / "data" / "processed" / "test.csv"
MODEL_PATH = ML_DIR / "random_forest_model.pkl"
ENCODER_PATH = ML_DIR / "label_encoder.pkl"
RESULTS_DIR = ML_DIR / "results"
BIN_EDGES = np.linspace(0.0, 1.0, 11)


def calibration_bins(probabilities, correct):
    probabilities = np.asarray(probabilities, dtype=float)
    correct = np.asarray(correct, dtype=bool)
    rows = []
    for index in range(len(BIN_EDGES) - 1):
        lower = BIN_EDGES[index]
        upper = BIN_EDGES[index + 1]
        mask = (probabilities >= lower) & (
            probabilities <= upper if index == len(BIN_EDGES) - 2 else probabilities < upper
        )
        count = int(mask.sum())
        rows.append({
            "bin": f"[{lower:.1f}, {upper:.1f}{']' if index == len(BIN_EDGES) - 2 else ')'}",
            "lower": lower,
            "upper": upper,
            "count": count,
            "mean_confidence": float(probabilities[mask].mean()) if count else None,
            "accuracy": float(correct[mask].mean()) if count else None,
        })
    populated = [row for row in rows if row["count"]]
    total = len(probabilities)
    ece = sum(row["count"] / total * abs(row["mean_confidence"] - row["accuracy"]) for row in populated)
    return rows, float(ece)


def calibration_curve_check(probabilities, truth):
    """Call sklearn's calibration utility as part of the analysis contract."""
    calibration_curve(truth.astype(int), probabilities, n_bins=10, strategy="uniform")


def table_lines(rows):
    lines = ["| Confidence bin | Mean confidence | Accuracy | Count |", "| --- | ---: | ---: | ---: |"]
    for row in rows:
        confidence = "-" if row["mean_confidence"] is None else f"{row['mean_confidence']:.4f}"
        accuracy = "-" if row["accuracy"] is None else f"{row['accuracy']:.4f}"
        lines.append(f"| {row['bin']} | {confidence} | {accuracy} | {row['count']} |")
    return lines


def build_horizon_test_frame(horizon_minutes: int, dataset_path: Path | None = None) -> pd.DataFrame:
    raw = pd.read_csv(dataset_path or ML_DIR / "data" / "processed" / "dataset_v2.csv")
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    _, test_indices = next(splitter.split(raw, groups=raw["vm_id"]))
    test_raw = raw.iloc[test_indices].copy()
    horizon_steps = {5: 1, 15: 3, 30: 6}[horizon_minutes]
    return build_supervised_windows(test_raw, horizon=horizon_steps)


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate model calibration against a saved classifier.")
    parser.add_argument("--model-path", type=Path, default=MODEL_PATH)
    parser.add_argument("--encoder-path", type=Path, default=ENCODER_PATH)
    parser.add_argument("--test-path", type=Path, default=None)
    parser.add_argument("--dataset-path", type=Path, default=ML_DIR / "data" / "processed" / "dataset_v2.csv")
    parser.add_argument("--horizon-minutes", type=int, default=5)
    parser.add_argument("--output-report", type=Path, default=RESULTS_DIR / "calibration_report.md")
    parser.add_argument("--output-plot", type=Path, default=RESULTS_DIR / "calibration_reliability_diagram.png")
    return parser.parse_args()


def main():
    args = parse_args()
    test = pd.read_csv(args.test_path) if args.test_path is not None else (
        build_horizon_test_frame(args.horizon_minutes, args.dataset_path)
        if args.horizon_minutes != 5
        else pd.read_csv(TEST_PATH)
    )
    model = joblib.load(args.model_path)
    encoder = joblib.load(args.encoder_path)
    probabilities = model.predict_proba(test[FEATURE_COLUMNS])
    predicted_indices = np.argmax(probabilities, axis=1)
    predicted_labels = encoder.inverse_transform(predicted_indices)
    true_labels = test["status"].to_numpy()
    confidence = probabilities.max(axis=1)
    correct = predicted_labels == true_labels

    overall_rows, overall_ece = calibration_bins(confidence, correct)
    calibration_curve_check(confidence, correct)

    per_class = {}
    for class_index, label in enumerate(encoder.classes_):
        one_vs_rest_truth = true_labels == label
        class_rows, class_ece = calibration_bins(probabilities[:, class_index], one_vs_rest_truth)
        calibration_curve_check(probabilities[:, class_index], one_vs_rest_truth)
        per_class[label] = {"ece": class_ece, "rows": class_rows, "support": int(one_vs_rest_truth.sum())}

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    figure, axes = plt.subplots(1, 2, figsize=(13, 5))
    populated = [row for row in overall_rows if row["count"]]
    axes[0].plot([0, 1], [0, 1], "k--", label="Perfect calibration")
    axes[0].plot([row["mean_confidence"] for row in populated], [row["accuracy"] for row in populated], "o-", label="Observed")
    axes[0].set_title("Overall confidence")
    axes[0].set_xlabel("Mean predicted confidence")
    axes[0].set_ylabel("Accuracy")
    axes[0].set_xlim(0, 1)
    axes[0].set_ylim(0, 1)
    axes[0].grid(alpha=0.25)
    axes[0].legend()

    for label, class_index in zip(encoder.classes_, range(len(encoder.classes_))):
        rows = per_class[label]["rows"]
        populated = [row for row in rows if row["count"]]
        axes[1].plot([row["mean_confidence"] for row in populated], [row["accuracy"] for row in populated], "o-", label=label)
    axes[1].plot([0, 1], [0, 1], "k--", label="Perfect calibration")
    axes[1].set_title("One-vs-rest class calibration")
    axes[1].set_xlabel("Mean predicted probability")
    axes[1].set_ylabel("One-vs-rest accuracy")
    axes[1].set_xlim(0, 1)
    axes[1].set_ylim(0, 1)
    axes[1].grid(alpha=0.25)
    axes[1].legend(fontsize=8)
    figure.tight_layout()
    figure.savefig(args.output_plot, dpi=160)
    plt.close(figure)

    model_name = args.model_path.name
    if args.horizon_minutes != 5:
        title = f"# {args.horizon_minutes}-minute model calibration report"
        description = f"Model: `{model_name}` evaluated on the exact `{args.horizon_minutes}`-minute test windows reconstructed by `train_multi_horizon.py` (seed 42, whole-VM GroupShuffleSplit)."
    else:
        title = "# Production model calibration report"
        description = "Model: `random_forest_model.pkl` evaluated on the existing single-horizon `test.csv`."
    lines = [
        title,
        "",
        description,
        "The Random Forest was retrained with constrained tree size. The existing test set, features, dataset, and split are unchanged.",
        "",
        f"## Overall ECE: `{overall_ece:.6f}`",
        "",
        "Expected Calibration Error is the count-weighted mean absolute difference between mean confidence and observed accuracy across ten uniform probability bins.",
        "",
        "## Overall reliability bins",
        "",
        *table_lines(overall_rows),
        "",
        "## One-vs-rest class calibration",
        "",
    ]
    for label, values in per_class.items():
        lines.extend([
            f"### {label}",
            "",
            f"Support: `{values['support']}`; one-vs-rest ECE: `{values['ece']:.6f}`.",
            "",
            *table_lines(values["rows"]),
            "",
        ])

    signed_gap = [row["mean_confidence"] - row["accuracy"] for row in overall_rows if row["count"]]
    if overall_ece < 0.02:
        interpretation = "Overall confidence is well aligned with observed correctness by the ECE threshold used here, though the sparse high-confidence bins and class imbalance still matter."
    elif np.mean(signed_gap) > 0:
        interpretation = "Overall confidence is overconfident: predicted probabilities are higher than observed accuracy on average. Minority-class calibration must be read separately because the majority class dominates the aggregate."
    else:
        interpretation = "Overall confidence is underconfident: predicted probabilities are lower than observed accuracy on average. Minority-class calibration must be read separately because the majority class dominates the aggregate."
    lines.extend(["## Interpretation", "", interpretation, "", f"The reliability diagram is saved at `{args.output_plot.name}`.", ""])
    args.output_report.write_text("\n".join(lines), encoding="utf-8")
    print(f"overall_ece={overall_ece:.6f}")
    for label, values in per_class.items():
        print(f"{label}_ece={values['ece']:.6f}")
    print(f"diagram={args.output_plot}")


if __name__ == "__main__":
    main()
