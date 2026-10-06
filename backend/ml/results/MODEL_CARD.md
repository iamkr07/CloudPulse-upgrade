# CloudPulse CPU Status Forecasting Model Card

**Reporting framework:** Mitchell et al., "Model Cards for Model Reporting," FAT* 2019, DOI: https://doi.org/10.1145/3287560.3287596.

**Model card date:** 2026-10-05

## Model Details

- **Production architecture:** Random Forest Classifier.
- **Artifact:** `backend/ml/random_forest_model.pkl`.
- **Task:** Predict the next 5-minute CPU status from six historical CPU readings.
- **Classes:** `Normal`, `Overutilized`, `Underutilized`.
- **Features:** `past_cpu_min`, `past_cpu_max`, `past_cpu_mean`, `past_cpu_range`, `past_cpu_volatility`, `past_cpu_trend`, and `last_cpu_avg`.
- **Feature discipline:** All features come strictly from the past window; the target timestamp is not used as an input.
- **Thresholds:** Underutilized below 30%; Normal through 70%; Overutilized above 70%.
- **Training seed:** 42.
- **Random Forest parameters:** 100 estimators, maximum depth 20, maximum 4,000 leaves per tree, and minimum leaf size 5. The artifact uses joblib compression level 3.
- **Related offline artifacts:** Random Forest and XGBoost evaluations are also available for 5, 15, and 30-minute horizons in `multi_horizon_metrics.json` and `multi_horizon_metrics.md`.

## Intended Use

CloudPulse is intended to support CPU utilization status forecasting for Azure VM workload traces at 5-minute, 15-minute, and 30-minute horizons in offline evaluation. The deployed production model is the 5-minute Random Forest model. The multi-horizon models are persisted separately for forecast display and offline comparison.

The model is not intended for memory-related decisions. The selected Azure CPU trace contains no memory telemetry, and memory fields are deliberately absent from this project.

## Training Data

The source is Microsoft's Azure Public Dataset V2, a representative 2019 Azure VM workload trace. This project uses CPU-reading shard 195 of 195 from the official Azure Public Dataset release. The source, schema, licensing, CPU-only scope, and mapping are documented in `backend/ml/data/README.md`.

The production train/test data uses a whole-VM 80/20 `GroupShuffleSplit` with seed 42 and zero VM overlap. The production single-horizon test set contains 240,541 windows. The underlying test label distribution is:

| Class | Samples | Share |
| --- | ---: | ---: |
| Underutilized | 225,245 | 93.6410% |
| Normal | 12,213 | 5.0773% |
| Overutilized | 3,083 | 1.2817% |

## Evaluation

### Production 5-minute model

| Model | Accuracy | Macro F1 | Majority baseline |
| --- | ---: | ---: | ---: |
| Random Forest | 0.9795 | 0.8743 | 0.9364 |
| XGBoost | 0.9665 | 0.8065 | 0.9364 |

Production Random Forest per-class F1:

| Class | F1 |
| --- | ---: |
| Normal | 0.8297 |
| Overutilized | 0.8022 |
| Underutilized | 0.9908 |

### Additive multi-horizon evaluation

| Horizon | Random Forest accuracy | Random Forest macro F1 | XGBoost accuracy | XGBoost macro F1 | Majority baseline |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 5 minutes | 0.9795 | 0.8743 | 0.9665 | 0.8065 | 0.9364 |
| 15 minutes | 0.9785 | 0.8588 | 0.9645 | 0.7914 | 0.9362 |
| 30 minutes | 0.9762 | 0.8442 | 0.9684 | 0.8071 | 0.9363 |

Prophet is a separate aggregate CPU forecast task: RMSE/MAE are `0.0589/0.0566` at 5 minutes and `0.0762/0.0718` at 15 minutes. The 30-minute Prophet result is unavailable because the aggregate split has insufficient distinct timestamps.

### Calibration

The production model's overall Expected Calibration Error is `0.011076`. One-vs-rest ECE values are `0.019734` for Normal, `0.006217` for Overutilized, and `0.025951` for Underutilized. Underutilized one-vs-rest probabilities are underconfident in the `[0.1, 0.5)` bins; for example, the `[0.1, 0.2)` bin has mean confidence `0.1480` and observed one-vs-rest accuracy `0.5233`.

The 15-minute and 30-minute calibration reports still describe the previous models. They were not regenerated in this update and require follow-up regeneration.

## Ethical and Limitations Considerations

- **Class imbalance:** Underutilized represents approximately 93.6% of the production test windows. Accuracy alone is not sufficient; macro F1 and per-class metrics must be considered.
- **Calibration:** Overall ECE is below 0.02, but classwise calibration differs; Underutilized probabilities are underconfident in the 0.1-0.5 range.
- **CPU-only scope:** No memory telemetry is available in the selected Azure shard. The model cannot support memory utilization or memory-pressure decisions.
- **Dataset limitation:** The evaluation uses one manageable shard from one Azure Public Dataset V2 release and one Azure VM trace family. Generalization to other workloads is unverified.
- **Forecast horizon:** Performance declines in macro F1 from 0.8743 at 5 minutes to 0.8442 at 30 minutes for Random Forest.
- **Operational validation:** The model is evaluated offline. Forecast quality, drift, interventions, and business outcomes require monitoring in the target deployment environment.
- **Label semantics:** Status labels are threshold-derived CPU categories, not independently observed incidents or service-level outcomes.

## Out-of-Scope Uses

Do not use this model for:

- Memory-based provisioning, memory-pressure detection, or any memory-related decision.
- Safety-critical or autonomous production scaling without further validation, monitoring, and rollback controls.
- Workloads or environments outside Azure VM traces without re-evaluation and calibration.
- Treating confidence as a guarantee of correctness, especially for minority classes or distribution-shifted data.
- Replacing capacity planning, service-level monitoring, or human operational review.
