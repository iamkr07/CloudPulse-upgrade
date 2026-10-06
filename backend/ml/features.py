"""Shared forward-looking CPU feature engineering for training and inference."""

from __future__ import annotations

import numpy as np
import pandas as pd

UNDERUTILIZED_THRESHOLD = 30.0
OVERUTILIZED_THRESHOLD = 70.0
LOOKBACK = 6
HORIZON = 1

FEATURE_COLUMNS = [
    "past_cpu_min",
    "past_cpu_max",
    "past_cpu_mean",
    "past_cpu_range",
    "past_cpu_volatility",
    "past_cpu_trend",
    "last_cpu_avg",
]


def status_from_utilization(utilization: float) -> str:
    if utilization < UNDERUTILIZED_THRESHOLD:
        return "Underutilized"
    if utilization <= OVERUTILIZED_THRESHOLD:
        return "Normal"
    return "Overutilized"


def workload_type_from_cpu(cpu_avg: float, cpu_max: float) -> str:
    if cpu_avg < 10:
        return "Idle"
    if cpu_max - cpu_avg >= 30:
        return "Bursty"
    return "Steady-state"


def add_source_columns(frame: pd.DataFrame) -> pd.DataFrame:
    renamed = frame.rename(
        columns={
            "min_cpu_utilization": "min_cpu",
            "max_cpu_utilization": "max_cpu",
            "cpu_usage": "cpu_avg",
        }
    ).copy()
    required = {"vm_id", "timestamp", "min_cpu", "max_cpu", "cpu_avg"}
    missing = required.difference(renamed.columns)
    if missing:
        raise ValueError(f"Missing processed Azure columns: {sorted(missing)}")
    renamed["timestamp"] = pd.to_numeric(renamed["timestamp"], errors="coerce")
    for column in ("min_cpu", "max_cpu", "cpu_avg"):
        renamed[column] = pd.to_numeric(renamed[column], errors="coerce").fillna(0).clip(0, 100)
    return renamed.dropna(subset=["vm_id", "timestamp"])


def build_supervised_windows(frame: pd.DataFrame, horizon: int = HORIZON) -> pd.DataFrame:
    """Create rows from six past readings and a strictly future target."""
    if horizon < 1:
        raise ValueError("horizon must be at least one reading")
    ordered = add_source_columns(frame).sort_values(["vm_id", "timestamp"], kind="mergesort")
    grouped = ordered.groupby("vm_id", sort=False)
    rolling_mean = grouped["cpu_avg"].rolling(LOOKBACK, min_periods=LOOKBACK).mean().reset_index(level=0, drop=True)
    rolling_min = grouped["min_cpu"].rolling(LOOKBACK, min_periods=LOOKBACK).min().reset_index(level=0, drop=True)
    rolling_max = grouped["max_cpu"].rolling(LOOKBACK, min_periods=LOOKBACK).max().reset_index(level=0, drop=True)
    rolling_volatility = grouped["cpu_avg"].rolling(LOOKBACK, min_periods=LOOKBACK).std(ddof=0).reset_index(level=0, drop=True)
    last_cpu = grouped["cpu_avg"].shift(1)
    trend_start = grouped["cpu_avg"].shift(LOOKBACK)
    result = pd.DataFrame({
        "vm_id": ordered["vm_id"].to_numpy(),
        "last_feature_timestamp": grouped["timestamp"].shift(1).to_numpy(),
        "target_timestamp": grouped["timestamp"].shift(-horizon).to_numpy(),
        "target_cpu": grouped["cpu_avg"].shift(-horizon).to_numpy(),
        "target_max_cpu": grouped["max_cpu"].shift(-horizon).to_numpy(),
        "past_cpu_min": rolling_min.shift(1).to_numpy(),
        "past_cpu_max": rolling_max.shift(1).to_numpy(),
        "past_cpu_mean": rolling_mean.shift(1).to_numpy(),
        "past_cpu_range": (rolling_max - rolling_min).shift(1).to_numpy(),
        "past_cpu_volatility": rolling_volatility.shift(1).to_numpy(),
        "past_cpu_trend": ((last_cpu - trend_start) / (LOOKBACK - 1)).to_numpy(),
        "last_cpu_avg": last_cpu.to_numpy(),
    }).dropna()
    result["last_feature_timestamp"] = result["last_feature_timestamp"].astype(int)
    result["target_timestamp"] = result["target_timestamp"].astype(int)
    result["status"] = result["target_cpu"].map(status_from_utilization)
    result["workload_type"] = [
        workload_type_from_cpu(cpu, peak)
        for cpu, peak in zip(result["target_cpu"], result["target_max_cpu"])
    ]
    if result.empty:
        raise ValueError("No VM has enough readings for the configured window and horizon")
    return result.reset_index(drop=True)


def build_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Return the shared past-window feature matrix from supervised rows."""
    if set(FEATURE_COLUMNS).issubset(frame.columns):
        return frame[FEATURE_COLUMNS].copy()
    return build_supervised_windows(frame)[FEATURE_COLUMNS]


def scale_cpu_readings(frame: pd.DataFrame, factor: float) -> pd.DataFrame:
    """Scale raw CPU readings while preserving the natural 0-100 CPU bounds."""
    scaled = frame.copy()
    for column in ("cpu_usage", "min_cpu", "max_cpu"):
        if column in scaled.columns:
            scaled[column] = pd.to_numeric(scaled[column], errors="coerce").fillna(0).mul(factor).clip(0, 100)
    return scaled


def build_scaled_feature_window(frame: pd.DataFrame, vm_id: str, timestamp: int, factor: float) -> pd.DataFrame:
    """Build one model feature row from a clipped, scaled raw VM history."""
    vm_history = frame[frame["vm_id"] == vm_id].copy()
    if vm_history.empty:
        raise ValueError(f"Raw history for VM {vm_id} was not found")
    scaled_history = scale_cpu_readings(vm_history, factor)
    scaled_windows = build_supervised_windows(scaled_history)
    matches = scaled_windows[scaled_windows["last_feature_timestamp"] == int(timestamp)]
    if matches.empty:
        raise ValueError(f"Feature window at timestamp {timestamp} was not found")
    return matches.iloc[[0]][FEATURE_COLUMNS]
