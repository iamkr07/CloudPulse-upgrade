import ast
import joblib
import numpy as np
import os
import pandas as pd
from threading import Lock
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from ml.features import FEATURE_COLUMNS, build_features, build_scaled_feature_window, status_from_utilization

# -------------------------------
# INIT
# -------------------------------
app = FastAPI(title="Cloud Resource Monitoring API")


def get_allowed_origins():
    configured_origins = os.getenv("FRONTEND_URL", "")
    if not configured_origins:
        return ["*"]

    origins = [origin.strip() for origin in configured_origins.split(",") if origin.strip()]
    return origins or ["*"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# LOAD MODEL
# -------------------------------
model = None
label_encoder = None
raw_dataset = None
raw_dataset_lock = Lock()
resource_request_count = 0
resource_request_lock = Lock()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ML_DIR = os.path.join(BASE_DIR, "ml")
SERVING_HISTORY_PATH = os.path.join(ML_DIR, "data", "processed", "serving_history.csv")
SERVING_RESOURCE_LIMIT = 200


def get_raw_dataset():
    global raw_dataset
    if raw_dataset is None:
        with raw_dataset_lock:
            if raw_dataset is None:
                raw_dataset = pd.read_csv(
                    SERVING_HISTORY_PATH,
                    usecols=["vm_id", "timestamp", "cpu_usage", "min_cpu", "max_cpu"],
                )
    return raw_dataset


def get_served_resource(resource_id: int, columns: list[str]):
    if resource_id < 0 or resource_id >= SERVING_RESOURCE_LIMIT:
        raise HTTPException(
            status_code=404,
            detail=f"Resource id must be between 0 and {SERVING_RESOURCE_LIMIT - 1}",
        )
    dataset_path = os.path.join(ML_DIR, "data", "processed", "test.csv")
    frame = pd.read_csv(dataset_path, usecols=["id", *columns], nrows=SERVING_RESOURCE_LIMIT)
    matches = frame[frame["id"] == resource_id]
    if matches.empty:
        raise HTTPException(status_code=404, detail="Resource not found in the served dataset")
    return matches.iloc[0]


@app.on_event("startup")
def load_model():
    global model, label_encoder

    model_path = os.path.join(ML_DIR, "random_forest_model.pkl")
    encoder_path = os.path.join(ML_DIR, "label_encoder.pkl")

    try:
        model = joblib.load(model_path)
        label_encoder = joblib.load(encoder_path)
        print("Production Random Forest loaded")
    except Exception as e:
        print("Model load failed:", e)

# -------------------------------
# HELPERS
# -------------------------------
def get_ec2_suggestion(cpu):
    """Get an EC2 instance type from CPU behavior only."""
    if cpu < 20:
        return "t2.micro"
    elif cpu > 70:
        return "c5.large"
    else:
        return "t3.medium"

# -------------------------------
# ROUTES
# -------------------------------
@app.get("/")
def root():
    return {"status": "running"}

@app.get("/api/resources")
def get_resources():
    global resource_request_count
    import pandas as pd
    import os

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    dataset_path = os.path.join(BASE_DIR, "ml", "data", "processed", "test.csv")

    resources = []

    try:
        df = pd.read_csv(
            dataset_path,
            usecols=["id", *FEATURE_COLUMNS, "workload_type"],
            nrows=SERVING_RESOURCE_LIMIT,
        )
        df = df.fillna(0)

        # Advance through deterministic sequential slices of the fixed test set.
        sample_size = min(10, len(df))
        with resource_request_lock:
            offset = (resource_request_count * sample_size) % max(1, len(df) - sample_size + 1)
            resource_request_count += 1
        preview_df = df.iloc[offset:offset + sample_size]
        predicted_statuses = None
        predicted_confidences = None
        try:
            inference_features = build_features(df)
            preview_features = inference_features.loc[preview_df.index]
            predicted_statuses = label_encoder.inverse_transform(model.predict(preview_features))
            if hasattr(model, "predict_proba"):
                predicted_confidences = np.max(model.predict_proba(preview_features), axis=1) * 100
        except Exception as e:
            # Rule-based thresholds remain the documented baseline fallback.
            print("MODEL PREDICTION ERROR:", e)

        for position, (_, row) in enumerate(preview_df.iterrows()):
            cpu_val = row["last_cpu_avg"]
            utilization = cpu_val

            status = (
                predicted_statuses[position]
                if predicted_statuses is not None
                else status_from_utilization(utilization)
            )

            if utilization < 30:
                priority = "Low"
            elif utilization < 70:
                priority = "Medium"
            else:
                priority = "High"

            if utilization < 30:
                health = "Idle"
            elif utilization < 70:
                health = "Stable"
            else:
                health = "Critical"

            if status == "Underutilized":
                action = "Scale Down"
            elif status == "Normal":
                action = "Maintain"
            else:
                action = "Scale Up"

            workload_type = row["workload_type"]

            estimated_cost = cpu_val * 0.05

            # Get EC2 suggestion
            ec2_instance = get_ec2_suggestion(cpu_val)

            confidence = 85.0
            if predicted_confidences is not None:
                confidence = round(float(predicted_confidences[position]), 2)

            if status == "Underutilized":
                trend = "Decreasing → May become Underutilized"
                reason = "Low CPU → Underutilized"
            elif status == "Normal":
                trend = "Stable"
                reason = "Moderate CPU → Normal"
            else:
                trend = "Increasing → May become Overutilized"
                reason = "High CPU → Overutilized"

            resources.append({
                "id": int(row["id"]),
                "cpu_usage": round(cpu_val, 2),
                "max_cpu": round(row["past_cpu_max"], 2),
                "utilization": round(utilization, 2),
                "status": status,
                "priority": priority,
                "health": health,
                "action": action,
                "workload_type": workload_type,
                "estimated_cost": round(estimated_cost, 2),
                "confidence": confidence,
                "trend": trend,
                "reason": reason,
                "ec2_instance": ec2_instance,
                "wasted_cost": 0.0,
                "is_top": False
            })

    except Exception as e:
        print("DATASET ERROR:", e)

    resources = resources[:10]
    print(f"STATUS DISTRIBUTION: {pd.Series([r['status'] for r in resources]).value_counts().to_dict()}")
    return resources

@app.get("/health")
def health():
    dataset_path = os.path.join(ML_DIR, "data", "processed", "test.csv")

    return {
        "model_loaded": model is not None,
        "dataset_found": os.path.exists(dataset_path)
    }


@app.get("/api/resources/{resource_id}/explain")
def explain_resource(resource_id: int):
    """Return SHAP contributions for a saved production test-window prediction."""
    row = get_served_resource(resource_id, FEATURE_COLUMNS)
    from ml.explainability import explain_features

    explanation = explain_features(pd.DataFrame([row]))
    explanation["resource_id"] = resource_id
    return explanation


@app.get("/api/resources/{resource_id}/forecast")
def forecast_resource(resource_id: int, scale: float = Query(1.0, ge=0.2, le=3.0)):
    """Return status forecasts for baseline or a scaled raw CPU history."""
    row = get_served_resource(
        resource_id,
        ["vm_id", "last_feature_timestamp", "last_cpu_avg"],
    )
    raw_frame = get_raw_dataset()
    scaled_features = build_scaled_feature_window(raw_frame, row["vm_id"], row["last_feature_timestamp"], scale)
    forecasts = []
    for minutes in (5, 15, 30):
        horizon_model = joblib.load(os.path.join(ML_DIR, f"random_forest_{minutes}min.pkl"))
        horizon_encoder = joblib.load(os.path.join(ML_DIR, f"label_encoder_{minutes}min.pkl"))
        probabilities = horizon_model.predict_proba(scaled_features)
        predicted_index = int(horizon_model.predict(scaled_features)[0])
        forecasts.append({
            "minutes": minutes,
            "status": horizon_encoder.inverse_transform([predicted_index])[0],
            "confidence": round(float(np.max(probabilities)) * 100, 2),
        })
        del horizon_model, horizon_encoder, probabilities, predicted_index
    return {"resource_id": resource_id, "scale": scale, "forecasts": forecasts}

# --------------------------------
# SIMULATION ENDPOINT
# --------------------------------
@app.post("/simulate")
def simulate(data: dict):
    """
    Simulate CPU scaling by recomputing the selected past window from scaled raw
    CPU readings before applying the production model.
    """
    try:
        resource_id = int(data.get("resource_id"))
        cpu_scale = max(0.2, min(3.0, float(data.get("cpu_scale", 1.0))))
        row = get_served_resource(
            resource_id,
            ["vm_id", "last_feature_timestamp", "last_cpu_avg"],
        )
        raw_frame = get_raw_dataset()
        scaled_features = build_scaled_feature_window(raw_frame, row["vm_id"], row["last_feature_timestamp"], cpu_scale)
        status = label_encoder.inverse_transform(model.predict(scaled_features))[0]
        confidence = 85.0
        if hasattr(model, "predict_proba"):
            confidence = round(float(np.max(model.predict_proba(scaled_features))) * 100, 2)

        cpu = float(scaled_features.iloc[0]["last_cpu_avg"])
        peak_cpu = float(scaled_features.iloc[0]["past_cpu_max"])
        utilization = cpu
        priority = "Low" if status == "Underutilized" else "High" if status == "Overutilized" else "Medium"
        workload_type = "Idle" if cpu < 10 else "Bursty" if peak_cpu - cpu >= 30 else "Steady-state"
        cost = cpu * 0.05
        original_cost = float(row["last_cpu_avg"]) * 0.05
        recommendation = "Scale Down resources to reduce cost" if status == "Underutilized" else "Scale Up resources or enable auto-scaling" if status == "Overutilized" else "Maintain current configuration"
        ec2_instance = get_ec2_suggestion(cpu)
        return {
            "id": resource_id,
            "cpu_usage": round(cpu, 2),
            "max_cpu": round(peak_cpu, 2),
            "utilization": round(utilization, 2),
            "status": status,
            "priority": priority,
            "cost": round(cost, 2),
            "estimated_cost": round(cost, 2),
            "originalCost": round(original_cost, 2),
            "costChange": round(cost - original_cost, 2),
            "confidence": confidence,
            "cpu_scale": cpu_scale,
            "workloadType": workload_type,
            "workload_type": workload_type,
            "ec2_instance": ec2_instance,
            "recommendationColor": "text-amber-400" if status == "Underutilized" else "text-rose-400" if status == "Overutilized" else "text-slate-400",
            "recommendation": recommendation
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Simulation error: {e}")
        return {
            "error": "Simulation failed",
            "message": str(e)
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)