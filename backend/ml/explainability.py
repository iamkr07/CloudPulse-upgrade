"""SHAP explanations for the saved production Random Forest classifier."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
import shap

try:
    from .features import FEATURE_COLUMNS
except ImportError:
    from features import FEATURE_COLUMNS


ML_DIR = Path(__file__).resolve().parent
TEST_PATH = ML_DIR / "data" / "processed" / "test.csv"
RESULTS_DIR = ML_DIR / "results"
MODEL_PATH = ML_DIR / "random_forest_model.pkl"
ENCODER_PATH = ML_DIR / "label_encoder.pkl"
GLOBAL_SAMPLE_SIZE = 1_000


def _class_values(explainer: shap.TreeExplainer, features: pd.DataFrame):
    values = explainer.shap_values(features)
    if isinstance(values, list):
        return values
    if values.ndim == 3:
        return [values[:, :, index] for index in range(values.shape[2])]
    return [values]


def explain_features(features: pd.DataFrame) -> dict:
    """Return per-feature SHAP contributions for the model's predicted class."""
    model = joblib.load(MODEL_PATH)
    encoder = joblib.load(ENCODER_PATH)
    features = features[FEATURE_COLUMNS].astype(float)
    explainer = shap.TreeExplainer(model)
    values_by_class = _class_values(explainer, features)
    predicted_index = int(model.predict(features)[0])
    contributions = values_by_class[predicted_index][0]
    expected = explainer.expected_value
    base_value = float(expected[predicted_index] if hasattr(expected, "__len__") else expected)
    return {
        "predicted_class": encoder.inverse_transform([predicted_index])[0],
        "base_value": base_value,
        "features": [
            {
                "name": name,
                "value": float(features.iloc[0][name]),
                "shap_value": float(value),
                "direction": "toward_prediction" if value >= 0 else "away_from_prediction",
            }
            for name, value in zip(FEATURE_COLUMNS, contributions)
        ],
    }


def build_global_summary() -> dict:
    """Compute global mean absolute SHAP importance on a bounded test sample."""
    import matplotlib.pyplot as plt

    test = pd.read_csv(TEST_PATH)
    sample = test.sample(min(GLOBAL_SAMPLE_SIZE, len(test)), random_state=42)
    features = sample[FEATURE_COLUMNS].astype(float)
    model = joblib.load(MODEL_PATH)
    encoder = joblib.load(ENCODER_PATH)
    explainer = shap.TreeExplainer(model)
    values_by_class = _class_values(explainer, features)
    values = sum(abs(class_values) for class_values in values_by_class) / len(values_by_class)
    importance = pd.Series(values.mean(axis=0), index=FEATURE_COLUMNS).sort_values(ascending=False)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    shap.summary_plot(values, features, show=False, max_display=len(FEATURE_COLUMNS))
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / "shap_summary_plot.png", dpi=160, bbox_inches="tight")
    plt.close()

    summary = {
        "sample_rows": len(sample),
        "feature_importance_mean_abs_shap": {
            name: float(value) for name, value in importance.items()
        },
        "classes": encoder.classes_.tolist(),
    }
    lines = [
        "# SHAP feature importance",
        "",
        f"Computed with `shap.TreeExplainer` on {len(sample):,} randomly sampled rows from the existing single-horizon test set (seed 42). The sample bounds runtime while retaining the production feature distribution.",
        "",
        "| Rank | Feature | Mean absolute SHAP value |",
        "| ---: | --- | ---: |",
    ]
    for rank, (name, value) in enumerate(importance.items(), 1):
        lines.append(f"| {rank} | `{name}` | {value:.6f} |")
    lines.extend(["", "The plot is saved as `shap_summary_plot.png`.", ""])
    (RESULTS_DIR / "shap_feature_importance.md").write_text("\n".join(lines), encoding="utf-8")
    (RESULTS_DIR / "shap_feature_importance.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


if __name__ == "__main__":
    print(json.dumps(build_global_summary(), indent=2))