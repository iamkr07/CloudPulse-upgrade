"""Precompute live API SHAP explanations during the build process."""

import json

import joblib
import pandas as pd
import shap

try:
    from .explainability import (
        ENCODER_PATH,
        MODEL_PATH,
        TEST_PATH,
        _explain_features,
    )
    from .features import FEATURE_COLUMNS
except ImportError:
    from explainability import ENCODER_PATH, MODEL_PATH, TEST_PATH, _explain_features
    from features import FEATURE_COLUMNS


EXPLANATIONS_PATH = TEST_PATH.parent / "explanations.json"
RESOURCE_LIMIT = 200


def precompute_explanations() -> dict[str, dict]:
    """Compute the same SHAP response as /explain for the first 200 IDs."""
    test = pd.read_csv(TEST_PATH, usecols=["id", *FEATURE_COLUMNS], nrows=RESOURCE_LIMIT)
    model = joblib.load(MODEL_PATH)
    encoder = joblib.load(ENCODER_PATH)
    explainer = shap.TreeExplainer(model)

    explanations = {}
    for _, row in test.iterrows():
        resource_id = int(row["id"])
        explanation = _explain_features(
            pd.DataFrame([row]),
            model,
            encoder,
            explainer,
        )
        explanation["resource_id"] = resource_id
        explanations[str(resource_id)] = explanation

    EXPLANATIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with EXPLANATIONS_PATH.open("w", encoding="utf-8") as output:
        json.dump(explanations, output, separators=(",", ":"))
    print(f"Wrote {len(explanations)} precomputed explanations to {EXPLANATIONS_PATH}")
    return explanations


if __name__ == "__main__":
    precompute_explanations()
