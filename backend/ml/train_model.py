"""Train and evaluate the CPU-only CloudPulse model suite."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import joblib
import numpy as np
import pandas as pd
from prophet import Prophet
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, mean_absolute_error, mean_squared_error
from sklearn.preprocessing import LabelEncoder
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ml.features import FEATURE_COLUMNS, build_features, status_from_utilization

SEED = 42
RANDOM_FOREST_PARAMS = {
    "n_estimators": 100,
    "max_depth": 20,
    "max_leaf_nodes": 4_000,
    "min_samples_leaf": 5,
    "random_state": SEED,
    "n_jobs": -1,
    "class_weight": "balanced_subsample",
}
ML_DIR = Path(__file__).resolve().parent
DATA_DIR = ML_DIR / "data" / "processed"
RESULTS_DIR = ML_DIR / "results"
TRAIN_PATH = DATA_DIR / "train.csv"
TEST_PATH = DATA_DIR / "test.csv"


def classification_metrics(model, features, target, label_encoder):
    predictions = model.predict(features)
    labels = np.arange(len(label_encoder.classes_))
    majority_label = int(pd.Series(target).mode().iloc[0])
    return {
        "accuracy": float(accuracy_score(target, predictions)),
        "majority_class_baseline_accuracy": float(accuracy_score(target, np.full(len(target), majority_label))),
        "majority_class_baseline_label": label_encoder.inverse_transform([majority_label])[0],
        "precision_recall_f1_per_class": classification_report(
            target,
            predictions,
            labels=labels,
            target_names=label_encoder.classes_,
            output_dict=True,
            zero_division=0,
        ),
        "confusion_matrix": confusion_matrix(target, predictions, labels=labels).tolist(),
        "confusion_matrix_labels": label_encoder.classes_.tolist(),
        "feature_importances": {
            name: float(value)
            for name, value in zip(FEATURE_COLUMNS, model.feature_importances_)
        },
    }


def prophet_metrics(train_frame, test_frame):
    train_series = train_frame.groupby("target_timestamp", as_index=False)["target_cpu"].mean()
    test_series = test_frame.groupby("target_timestamp", as_index=False)["target_cpu"].mean()
    train_series = train_series.rename(columns={"target_timestamp": "ds", "target_cpu": "y"})
    test_series = test_series.rename(columns={"target_timestamp": "ds", "target_cpu": "y"})
    train_series["ds"] = pd.to_datetime(train_series["ds"], unit="s", origin="unix")
    test_series["ds"] = pd.to_datetime(test_series["ds"], unit="s", origin="unix")

    model = Prophet(
        daily_seasonality=True,
        weekly_seasonality=True,
        yearly_seasonality=False,
        uncertainty_samples=0,
    )
    model.fit(train_series)
    forecast = model.predict(test_series[["ds"]])
    prediction = forecast["yhat"].clip(0, 100)
    return {
        "rmse": float(mean_squared_error(test_series["y"], prediction) ** 0.5),
        "mae": float(mean_absolute_error(test_series["y"], prediction)),
        "train_timestamp_count": int(len(train_series)),
        "test_timestamp_count": int(len(test_series)),
    }, model


def metrics_markdown(metrics):
    lines = [
        "# Azure CPU model comparison",
        "",
        "All classifiers use six-reading past-only windows from `ml/features.py`, whole-VM train/test splits, and seed 42.",
        "Prophet is a separate aggregate future CPU forecast and is not a classifier.",
        "",
        "## Summary",
        "",
        "| Model | Task | Accuracy | Macro F1 | RMSE | MAE |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for name in ("random_forest", "xgboost"):
        item = metrics[name]
        macro_f1 = item["precision_recall_f1_per_class"]["macro avg"]["f1-score"]
        lines.append(f"| {name} | 5-minute-ahead status classification | {item['accuracy']:.4f} | {macro_f1:.4f} | - | - |")
    prophet = metrics["prophet"]
    lines.append(f"| prophet | Aggregate CPU forecast | - | - | {prophet['rmse']:.4f} | {prophet['mae']:.4f} |")
    lines.extend([
        "",
        f"**Selected API classifier:** `{metrics['best_classifier']}` (highest macro F1; tie-breaker accuracy).",
        "",
        f"**Random Forest parameters:** `{metrics['random_forest_parameters']}`; artifact saved with joblib compression level 3.",
        "",
        "## Classifier details",
        "",
    ])
    for name in ("random_forest", "xgboost"):
        item = metrics[name]
        lines.extend([
            f"### {name}",
            "",
            f"Majority baseline: `{item['majority_class_baseline_label']}` at {item['majority_class_baseline_accuracy']:.4f} accuracy.",
            "",
            "| Class | Precision | Recall | F1 | Support |",
            "| --- | ---: | ---: | ---: | ---: |",
        ])
        report = item["precision_recall_f1_per_class"]
        for label in item["confusion_matrix_labels"]:
            row = report[label]
            lines.append(f"| {label} | {row['precision']:.4f} | {row['recall']:.4f} | {row['f1-score']:.4f} | {int(row['support'])} |")
        lines.extend([
            "",
            "Confusion matrix labels/order: " + ", ".join(item["confusion_matrix_labels"]),
            "",
            "```text",
            str(item["confusion_matrix"]),
            "```",
            "",
        ])
    return "\n".join(lines) + "\n"


def comparison_markdown(metrics):
    return f"""# Comparison to Resource Central

## Reference

Cortez et al., *Resource Central: Understanding and Predicting Workloads for Improved Resource Management in Large Cloud Platforms*, SOSP 2017, pp. 153-167. DOI: https://doi.org/10.1145/3132747.3132772.

The paper studies production Azure VM workloads and resource-management prediction using historical workload/resource signals to support proactive management. The accessible official metadata and release documentation confirm the workload lineage but do not expose a verifiable single classification accuracy number for the paper's CPU prediction results. That value is therefore reported as **not available from the sources checked**, rather than invented.

The previous version of this comparison, and the previous classifier metrics, were invalidated by label leakage: same-timestamp CPU was used both as an input and to derive the status label. This version uses six readings from the past and predicts the next five-minute reading; the old 1.0000/0.9985 classifier results must not be used.

## Side-by-side

| Aspect | This project | Resource Central (Cortez et al.) |
| --- | --- | --- |
| Data | One reproducible Azure Public Dataset V2 CPU-reading shard, collected in 2019 | Production Azure workload traces analyzed by Microsoft/Azure Research |
| Primary task | 5-minute-ahead 3-class CPU status classification using 30/70 thresholds | Proactive workload/resource-management prediction and forecasting |
| Features | Six-reading past window: min/max/mean/range/volatility/trend/last CPU; no target-timestamp CPU | Paper-specific historical workload/resource signals; exact feature set is not reproduced here |
| Models | Random Forest and XGBoost classifiers; Prophet aggregate CPU forecast | Paper's reported approach and operational evaluation; not a Random Forest/XGBoost/Prophet benchmark |
| Split | Fixed processed train/test files, whole-VM 80/20 group split, seed 42 | Different trace selection and evaluation methodology |
| Reported accuracy | {metrics["random_forest"]["accuracy"]:.4f} accuracy / {metrics["random_forest"]["precision_recall_f1_per_class"]["macro avg"]["f1-score"]:.4f} macro F1; majority baseline is included | No single verified accuracy value found in accessible metadata |

## Comparability warning

This is now a more legitimate directional comparison because both setups are forward-looking, but it is still not a direct benchmark. The data shard, feature engineering, labels, split methodology, model families, and operational task differ. Our classifier predicts a threshold-derived status label one step ahead; Prophet predicts aggregate CPU utilization. Resource Central remains the conceptual/source-paper reference for proactive CPU workload management, not a like-for-like benchmark for these metrics.

Sources checked: Microsoft Research paper landing/PDF link, ACM DOI metadata, and the official Azure Public Dataset V2 documentation.
"""


def main():
    train = pd.read_csv(TRAIN_PATH)
    test = pd.read_csv(TEST_PATH)
    train_features = build_features(train)
    test_features = build_features(test)
    train_status = train["target_cpu"].map(status_from_utilization)
    test_status = test["target_cpu"].map(status_from_utilization)

    label_encoder = LabelEncoder()
    y_train = label_encoder.fit_transform(train_status)
    y_test = label_encoder.transform(test_status)

    random_forest = RandomForestClassifier(**RANDOM_FOREST_PARAMS)
    random_forest.fit(train_features, y_train)

    xgboost = XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="multi:softprob",
        num_class=len(label_encoder.classes_),
        eval_metric="mlogloss",
        random_state=SEED,
        n_jobs=-1,
    )
    xgboost.fit(train_features, y_train, sample_weight=compute_sample_weight("balanced", y_train))

    rf_metrics = classification_metrics(random_forest, test_features, y_test, label_encoder)
    xgb_metrics = classification_metrics(xgboost, test_features, y_test, label_encoder)
    rf_score = (rf_metrics["precision_recall_f1_per_class"]["macro avg"]["f1-score"], rf_metrics["accuracy"])
    xgb_score = (xgb_metrics["precision_recall_f1_per_class"]["macro avg"]["f1-score"], xgb_metrics["accuracy"])
    best_name, best_model = ("random_forest", random_forest) if rf_score >= xgb_score else ("xgboost", xgboost)

    prophet_result, prophet = prophet_metrics(train, test)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(random_forest, ML_DIR / "random_forest_model.pkl", compress=3)
    joblib.dump(xgboost, ML_DIR / "xgboost_model.pkl")
    joblib.dump(prophet, ML_DIR / "prophet_model.pkl")
    joblib.dump(label_encoder, ML_DIR / "label_encoder.pkl")

    metrics = {
        "seed": SEED,
        "feature_columns": FEATURE_COLUMNS,
        "random_forest_parameters": RANDOM_FOREST_PARAMS,
        "thresholds": {"underutilized_below": 30, "overutilized_above": 70},
        "train_rows": len(train),
        "test_rows": len(test),
        "random_forest": rf_metrics,
        "xgboost": xgb_metrics,
        "prophet": prophet_result,
        "best_classifier": best_name,
    }
    (RESULTS_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (RESULTS_DIR / "metrics.md").write_text(metrics_markdown(metrics), encoding="utf-8")
    (RESULTS_DIR / "comparison_to_resource_central.md").write_text(comparison_markdown(metrics), encoding="utf-8")
    print(f"Best classifier: {best_name}")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
