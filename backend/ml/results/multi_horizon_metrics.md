# Multi-horizon Azure CPU model comparison

All horizons use the same seven past-only features, seed 42, and the same whole-VM train/test assignment. Labels are 5, 15, or 30 minutes after the final feature reading.

Random Forest uses 100 estimators, max depth 20, at most 4,000 leaves per tree, and minimum leaf size 5. Its joblib artifact is saved with compression level 3.

**Calibration status:** `calibration_report_15min.md` and `calibration_report_30min.md` still describe the previous model artifacts and require regeneration. The 5-minute production calibration is regenerated separately by `calibration_analysis.py`.

## Classification and baseline comparison

| Horizon | Model | Accuracy | Macro F1 | Majority baseline | Normal F1 | Overutilized F1 | Underutilized F1 |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 5 min | random_forest | 0.9795 | 0.8743 | Underutilized (0.9364) | 0.8297 | 0.8022 | 0.9908 |
| 5 min | xgboost | 0.9665 | 0.8065 | Underutilized (0.9364) | 0.7731 | 0.6620 | 0.9844 |
| 5 min | prophet forecast | - | - | - | RMSE 0.0589 | MAE 0.0566 | - |
| 15 min | random_forest | 0.9785 | 0.8588 | Underutilized (0.9362) | 0.8271 | 0.7587 | 0.9906 |
| 15 min | xgboost | 0.9645 | 0.7914 | Underutilized (0.9362) | 0.7694 | 0.6212 | 0.9837 |
| 15 min | prophet forecast | - | - | - | RMSE 0.0762 | MAE 0.0718 | - |
| 30 min | random_forest | 0.9762 | 0.8442 | Underutilized (0.9363) | 0.8112 | 0.7320 | 0.9894 |
| 30 min | xgboost | 0.9684 | 0.8071 | Underutilized (0.9363) | 0.7784 | 0.6574 | 0.9856 |
| 30 min | prophet forecast unavailable | - | - | - | - | - | - |

## Class balance

| Horizon | Train windows | Test windows | Test Underutilized | Test Normal | Test Overutilized |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 5 min | 960974 | 240541 | 93.6410% | 5.0773% | 1.2817% |
| 15 min | 602969 | 151045 | 93.6165% | 5.1011% | 1.2824% |
| 30 min | 68152 | 17343 | 93.6286% | 5.1318% | 1.2397% |

## Interpretation

The majority baseline is included because accuracy alone is misleading for the heavily Underutilized test distribution. Compare macro F1 and per-class F1 when judging minority-class behavior.
