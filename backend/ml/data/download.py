"""Download one reproducible, manageable shard of Azure Public Dataset V2."""

from pathlib import Path
from urllib.request import urlopen
import hashlib


# Source: Microsoft's official Azure Public Dataset V2 GitHub release.
# Dataset version/date: Azure Public Dataset V2, VM workload collected in 2019;
# the current dataset-v2 release assets were published by Microsoft in June 2026.
# This is shard 195 of 195, a 227 MB compressed CPU-reading part of the 195-part
# time-series table. It is used because the complete V2 release is about 156 GB
# compressed and is not practical for this application.
# Dataset license: Creative Commons Attribution 4.0 International (CC BY 4.0).
# The repository's accompanying code is MIT licensed; this downloaded trace is
# data and is covered by CC BY 4.0. Retain attribution and the source URL.
SOURCE_URL = (
    "https://github.com/Azure/AzurePublicDataset/releases/download/"
    "dataset-v2/trace_data_vm_cpu_readings_vm_cpu_readings-file-195-of-195.csv.gz"
)
EXPECTED_SHA256 = "cdb2b02d8858efa2c6d4b3aa4faaf975061458bd4647f2e9934faf57dad8ea09"
RAW_DIR = Path(__file__).resolve().parent / "raw"
RAW_PATH = RAW_DIR / "azure_public_dataset_v2_cpu_readings_file_195_of_195.csv.gz"


def download() -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()

    with urlopen(SOURCE_URL) as response, RAW_PATH.open("wb") as output:
        while chunk := response.read(1024 * 1024):
            output.write(chunk)
            digest.update(chunk)

    actual_sha256 = digest.hexdigest()
    if actual_sha256 != EXPECTED_SHA256:
        RAW_PATH.unlink(missing_ok=True)
        raise RuntimeError(
            f"Checksum mismatch for {RAW_PATH.name}: {actual_sha256}"
        )

    print(f"Downloaded {RAW_PATH} ({actual_sha256})")
    return RAW_PATH


if __name__ == "__main__":
    download()