# Azure Public Dataset V2 pipeline

This directory uses Microsoft's **Azure Public Dataset V2**, the 2019 Azure VM
workload trace. The official source documentation is:

- https://github.com/Azure/AzurePublicDataset/blob/master/AzurePublicDatasetV2.md
- https://github.com/Azure/AzurePublicDataset/releases/tag/dataset-v2

The downloader uses this exact release asset:

https://github.com/Azure/AzurePublicDataset/releases/download/dataset-v2/trace_data_vm_cpu_readings_vm_cpu_readings-file-195-of-195.csv.gz

It is shard 195 of 195. The compressed shard is approximately 227 MB and is a
manageable representative part of the 195-file CPU-reading table. The complete
V2 release is approximately 156 GB compressed, so downloading it is not
practical for this application. The downloader records and verifies the
published SHA-256 checksum. Download date is the date `download.py` is run.

## License and attribution

The dataset is licensed under **Creative Commons Attribution 4.0 International
(CC BY 4.0)**. Retain attribution to Microsoft/Azure and link to the source
above when redistributing the data or derived data. The source repository's
code is MIT licensed separately; this pipeline does not change the dataset
license.

## Scope

CloudPulse is scoped to CPU utilization prediction and CPU behavior
classification. The selected Azure Public Dataset V2 CPU-reading file exposes
minimum, maximum, and average CPU readings, but no memory telemetry, so this
pipeline does not manufacture or infer memory utilization. This CPU-only scope
is consistent with the Resource Central SOSP 2017 source paper, which analyzes
Azure VM workload behavior using CPU utilization traces. Memory capacity may
exist as a separate Azure bucket in the broader release, but it is not a
measured utilization signal in the selected file.

## Original Azure schema

The full Azure V2 joined trace is documented as a 20-column schema:

1. encrypted subscription id
2. encrypted deployment id
3. deployment-created timestamp in seconds
4. VMs created count
5. deployment size
6. encrypted VM id
7. VM-created timestamp
8. VM-deleted timestamp
9. VM maximum CPU utilization
10. VM average CPU utilization
11. P95 of maximum CPU utilization
12. VM category
13. VM virtual-core-count bucket
14. VM memory-GB bucket
15. five-minute timestamp in seconds
16. five-minute minimum CPU utilization
17. five-minute maximum CPU utilization
18. five-minute average CPU utilization
19. virtual-core bucket definition
20. memory-GB bucket definition

The selected release asset is the CPU-reading projection of that schema and
actually contains five comma-separated columns, in this order:

1. five-minute timestamp in seconds
2. encrypted VM id
3. five-minute minimum CPU utilization
4. five-minute maximum CPU utilization
5. five-minute average CPU utilization

The first two values and categorical values are encrypted or bucketed by the
source dataset. The selected CPU-only asset has no VM memory bucket and Azure
V2 does not provide measured memory utilization in this file. Memory fields are
therefore absent from the processed files; this is a known limitation, not a
silent equivalence claim.

## CloudPulse mapping

| Azure V2 concept | Processed column | Meaning |
| --- | --- | --- |
| encrypted VM id | `vm_id` | Stable anonymized resource identifier |
| five-minute timestamp | `timestamp` | Source timestamp in seconds |
| five-minute average CPU | `cpu_usage` | CPU utilization, normalized to 0-100 |
| five-minute maximum CPU | `max_cpu` | Maximum CPU utilization, normalized to 0-100 |
| CPU utilization | `utilization` | Current API utilization, equal to CPU |
| 30/70 utilization thresholds | `status` | Underutilized, Normal, or Overutilized |
| average/peak CPU relationship | `workload_type` | Idle, Bursty, or Steady-state |

## Regenerate

From the repository root:

```powershell
python backend/ml/data/download.py
python backend/ml/data/prepare.py
```

The preparation uses random seed `42`, splits complete VMs 80/20 with
`GroupShuffleSplit`, then creates six-reading past windows with a one-reading
future horizon. This prevents a VM's adjacent windows from crossing train and
test. It writes `processed/dataset_v2.csv`, `processed/train.csv`, and
`processed/test.csv`. There is no replacement sampling in this pipeline.

Preparation also writes `processed/serving_history.csv`, containing the five
raw CPU-reading columns only for VMs referenced by the first 200 test windows.
The live API uses this bounded file for simulation and forecast history instead
of loading the full `dataset_v2.csv`.

The Render build also generates `processed/explanations.json` from the
production Random Forest for the first 200 test-window IDs. The API serves these
precomputed explanations without importing SHAP at request time. Regenerate
this file whenever the production model is retrained.