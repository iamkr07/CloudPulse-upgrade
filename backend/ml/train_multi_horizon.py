"""Offline multi-horizon CPU status and forecast evaluation."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import joblib
from prophet import Prophet
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, mean_absolute_error, mean_squared_error
from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import LabelEncoder
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ml.features import FEATURE_COLUMNS, build_supervised_windows

SEED = 42
HORIZONS = {5: 1, 15: 3, 30: 6}
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
DATASET_PATH = ML_DIR / "data" / "processed" / "dataset_v2.csv"
RESULTS_DIR = ML_DIR / "results"


def classifier_metrics(model, features, target, encoder):
    predictions = model.predict(features)
    labels = np.arange(len(encoder.classes_))
    report = classification_report(target, predictions, labels=labels, target_names=encoder.classes_, output_dict=True, zero_division=0)
    majority = int(pd.Series(target).mode().iloc[0])
    return {
        "accuracy": float(accuracy_score(target, predictions)),
        "macro_f1": float(report["macro avg"]["f1-score"]),
        "majority_baseline_accuracy": float(accuracy_score(target, np.full(len(target), majority))),
        "majority_baseline_label": encoder.inverse_transform([majority])[0],
        "per_class_f1": {label: float(report[label]["f1-score"]) for label in encoder.classes_},
        "per_class_precision": {label: float(report[label]["precision"]) for label in encoder.classes_},
        "per_class_recall": {label: float(report[label]["recall"]) for label in encoder.classes_},
        "class_support": {label: int(report[label]["support"]) for label in encoder.classes_},
        "labels": encoder.classes_.tolist(),
    }


def prophet_metrics(train_windows, test_windows):
    train_series = train_windows.groupby("target_timestamp", as_index=False)["target_cpu"].mean().rename(columns={"target_timestamp": "ds", "target_cpu": "y"})
    test_series = test_windows.groupby("target_timestamp", as_index=False)["target_cpu"].mean().rename(columns={"target_timestamp": "ds", "target_cpu": "y"})
    train_series["ds"] = pd.to_datetime(train_series["ds"], unit="s", origin="unix")
    test_series["ds"] = pd.to_datetime(test_series["ds"], unit="s", origin="unix")
    if len(train_series) < 2 or len(test_series) < 2:
        return {
            "available": False,
            "reason": "Insufficient distinct aggregate timestamps for Prophet",
            "train_timestamp_count": int(len(train_series)),
            "test_timestamp_count": int(len(test_series)),
        }
    model = Prophet(daily_seasonality=True, weekly_seasonality=True, yearly_seasonality=False, uncertainty_samples=0)
    model.fit(train_series)
    prediction = model.predict(test_series[["ds"]])["yhat"].clip(0, 100)
    return {
        "rmse": float(mean_squared_error(test_series["y"], prediction) ** 0.5),
        "mae": float(mean_absolute_error(test_series["y"], prediction)),
        "train_timestamp_count": int(len(train_series)),
        "test_timestamp_count": int(len(test_series)),
    }


def markdown(metrics):
    lines = [
        "# Multi-horizon Azure CPU model comparison", "",
        "All horizons use the same seven past-only features, seed 42, and the same whole-VM train/test assignment. Labels are 5, 15, or 30 minutes after the final feature reading.", "",
        "Random Forest uses 100 estimators, max depth 20, at most 4,000 leaves per tree, and minimum leaf size 5. Its joblib artifact is saved with compression level 3.", "",
        "**Calibration status:** `calibration_report_15min.md` and `calibration_report_30min.md` still describe the previous model artifacts and require regeneration. The 5-minute production calibration is regenerated separately by `calibration_analysis.py`.", "",
        "## Classification and baseline comparison", "",
        "| Horizon | Model | Accuracy | Macro F1 | Majority baseline | Normal F1 | Overutilized F1 | Underutilized F1 |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for horizon in HORIZONS:
        item = metrics[str(horizon)]
        for model_name in ("random_forest", "xgboost"):
            result = item[model_name]
            f1 = result["per_class_f1"]
            lines.append(f"| {horizon} min | {model_name} | {result['accuracy']:.4f} | {result['macro_f1']:.4f} | {result['majority_baseline_label']} ({result['majority_baseline_accuracy']:.4f}) | {f1['Normal']:.4f} | {f1['Overutilized']:.4f} | {f1['Underutilized']:.4f} |")
        forecast = item["prophet"]
        if forecast.get("available", True):
            lines.append(f"| {horizon} min | prophet forecast | - | - | - | RMSE {forecast['rmse']:.4f} | MAE {forecast['mae']:.4f} | - |")
        else:
            lines.append(f"| {horizon} min | prophet forecast unavailable | - | - | - | - | - | - |")
    lines.extend(["", "## Class balance", "", "| Horizon | Train windows | Test windows | Test Underutilized | Test Normal | Test Overutilized |", "| ---: | ---: | ---: | ---: | ---: | ---: |"])
    for horizon in HORIZONS:
        item = metrics[str(horizon)]
        balance = item["test_class_distribution"]
        lines.append(f"| {horizon} min | {item['train_windows']} | {item['test_windows']} | {balance['Underutilized']:.4%} | {balance['Normal']:.4%} | {balance['Overutilized']:.4%} |")
    lines.extend(["", "## Interpretation", "", "The majority baseline is included because accuracy alone is misleading for the heavily Underutilized test distribution. Compare macro F1 and per-class F1 when judging minority-class behavior.", ""])
    return "\n".join(lines)


def main():
    raw = pd.read_csv(DATASET_PATH)
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=SEED)
    train_indices, test_indices = next(splitter.split(raw, groups=raw["vm_id"]))
    train_raw = raw.iloc[train_indices].copy()
    test_raw = raw.iloc[test_indices].copy()
    lengths = raw.groupby("vm_id").size()
    metrics = {
        "seed": SEED,
        "lookback_readings": 6,
        "horizons_minutes": list(HORIZONS),
        "feature_columns": FEATURE_COLUMNS,
        "random_forest_parameters": RANDOM_FOREST_PARAMS,
        "total_vms": int(len(lengths)),
        "vms_eligible_for_30_minute_horizon": int((lengths >= 12).sum()),
        "vms_dropped_for_30_minute_horizon": int((lengths < 12).sum()),
        "raw_rows_in_dropped_vms": int(lengths[lengths < 12].sum()),
    }
    for horizon_minutes, horizon_steps in HORIZONS.items():
        train = build_supervised_windows(train_raw, horizon=horizon_steps)
        test = build_supervised_windows(test_raw, horizon=horizon_steps)
        encoder = LabelEncoder()
        y_train = encoder.fit_transform(train["status"])
        y_test = encoder.transform(test["status"])
        train_features = train[FEATURE_COLUMNS]
        test_features = test[FEATURE_COLUMNS]
        random_forest = RandomForestClassifier(**RANDOM_FOREST_PARAMS)
        random_forest.fit(train_features, y_train)
        xgboost = XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, subsample=0.9, colsample_bytree=0.9, objective="multi:softprob", num_class=len(encoder.classes_), eval_metric="mlogloss", random_state=SEED, n_jobs=-1)
        xgboost.fit(train_features, y_train, sample_weight=compute_sample_weight("balanced", y_train))
        test_distribution = test["status"].value_counts(normalize=True).to_dict()
        rf_metrics = classifier_metrics(random_forest, test_features, y_test, encoder)
        xgb_metrics = classifier_metrics(xgboost, test_features, y_test, encoder)
        best_name = "random_forest" if rf_metrics["macro_f1"] >= xgb_metrics["macro_f1"] else "xgboost"
        joblib.dump(random_forest, ML_DIR / f"random_forest_{horizon_minutes}min.pkl", compress=3)
        joblib.dump(encoder, ML_DIR / f"label_encoder_{horizon_minutes}min.pkl")
        metrics[str(horizon_minutes)] = {
            "train_windows": len(train), "test_windows": len(test),
            "best_classifier": best_name,
            "test_class_distribution": {label: float(test_distribution.get(label, 0)) for label in encoder.classes_},
            "random_forest": rf_metrics,
            "xgboost": xgb_metrics,
            "prophet": prophet_metrics(train, test),
        }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / "multi_horizon_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (RESULTS_DIR / "multi_horizon_metrics.md").write_text(markdown(metrics), encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
