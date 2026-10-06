"""Prepare Azure Public Dataset V2 shard data for the CloudPulse API."""

from pathlib import Path
import gzip
import sys

import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from ml.features import build_supervised_windows, status_from_utilization, workload_type_from_cpu


SEED = 42
DATA_DIR = Path(__file__).resolve().parent
RAW_PATH = DATA_DIR / "raw" / "azure_public_dataset_v2_cpu_readings_file_195_of_195.csv.gz"
PROCESSED_DIR = DATA_DIR / "processed"
DATASET_PATH = PROCESSED_DIR / "dataset_v2.csv"
TRAIN_PATH = PROCESSED_DIR / "train.csv"
TEST_PATH = PROCESSED_DIR / "test.csv"


# The selected Azure V2 CPU-reading shard is a five-column projection of the
# published 20-column trace schema, not the old Google-style schema:
# timestamp (seconds, every five minutes) -> timestamp
# encrypted_vm_id -> vm_id / resource identifier
# min/max/avg CPU utilization -> corresponding CPU fields below (percentage)
# vm_memory_gb_bucket is not present in this CPU-only shard.
AZURE_COLUMNS = [
    "timestamp",
    "vm_id",
    "min_cpu_utilization",
    "max_cpu_utilization",
    "avg_cpu_utilization",
]


def prepare() -> tuple[pd.DataFrame, pd.DataFrame]:
    if not RAW_PATH.exists():
        raise FileNotFoundError(
            f"Missing {RAW_PATH}. Run download.py before prepare.py."
        )

    with gzip.open(RAW_PATH, "rb") as source:
        raw = pd.read_csv(source, header=None, names=AZURE_COLUMNS)

    numeric_columns = [
        "timestamp",
        "min_cpu_utilization",
        "max_cpu_utilization",
        "avg_cpu_utilization",
    ]
    for column in numeric_columns:
        raw[column] = pd.to_numeric(raw[column], errors="coerce")

    raw = raw.dropna(subset=["vm_id", "timestamp", "avg_cpu_utilization"])
    raw["cpu_usage"] = raw["avg_cpu_utilization"].clip(0, 100)
    raw["min_cpu"] = raw["min_cpu_utilization"].clip(0, 100)
    raw["max_cpu"] = raw["max_cpu_utilization"].clip(0, 100)
    raw["utilization"] = raw["cpu_usage"]
    raw["status"] = raw["utilization"].map(status_from_utilization)
    raw["workload_type"] = [
        workload_type_from_cpu(cpu, peak)
        for cpu, peak in zip(raw["cpu_usage"], raw["max_cpu"])
    ]

    cleaned = raw[
        [
            "vm_id",
            "timestamp",
            "cpu_usage",
            "min_cpu",
            "max_cpu",
            "utilization",
            "status",
            "workload_type",
        ]
    ].reset_index(drop=True)
    cleaned.insert(0, "id", cleaned.index)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(DATASET_PATH, index=False)

    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=SEED)
    train_indices, test_indices = next(splitter.split(cleaned, groups=cleaned["vm_id"]))
    train = build_supervised_windows(cleaned.iloc[train_indices])
    test = build_supervised_windows(cleaned.iloc[test_indices])
    train.insert(0, "id", train.index)
    test.insert(0, "id", test.index)
    train.to_csv(TRAIN_PATH, index=False)
    test.to_csv(TEST_PATH, index=False)
    print(f"Prepared {len(cleaned)} raw rows: train_windows={len(train)}, test_windows={len(test)}")
    return train, test


if __name__ == "__main__":
    prepare()