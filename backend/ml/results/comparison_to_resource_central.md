# Comparison to Resource Central

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
| Reported accuracy | 0.9795 accuracy / 0.8743 macro F1; majority baseline is included | No single verified accuracy value found in accessible metadata |

## Comparability warning

This is now a more legitimate directional comparison because both setups are forward-looking, but it is still not a direct benchmark. The data shard, feature engineering, labels, split methodology, model families, and operational task differ. Our classifier predicts a threshold-derived status label one step ahead; Prophet predicts aggregate CPU utilization. Resource Central remains the conceptual/source-paper reference for proactive CPU workload management, not a like-for-like benchmark for these metrics.

Sources checked: Microsoft Research paper landing/PDF link, ACM DOI metadata, and the official Azure Public Dataset V2 documentation.
