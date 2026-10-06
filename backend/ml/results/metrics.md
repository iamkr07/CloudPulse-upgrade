# Azure CPU model comparison

All classifiers use six-reading past-only windows from `ml/features.py`, whole-VM train/test splits, and seed 42.
Prophet is a separate aggregate future CPU forecast and is not a classifier.

## Summary

| Model | Task | Accuracy | Macro F1 | RMSE | MAE |
| --- | --- | ---: | ---: | ---: | ---: |
| random_forest | 5-minute-ahead status classification | 0.9795 | 0.8743 | - | - |
| xgboost | 5-minute-ahead status classification | 0.9665 | 0.8065 | - | - |
| prophet | Aggregate CPU forecast | - | - | 0.0589 | 0.0566 |

**Selected API classifier:** `random_forest` (highest macro F1; tie-breaker accuracy).

**Random Forest parameters:** `{'n_estimators': 100, 'max_depth': 20, 'max_leaf_nodes': 4000, 'min_samples_leaf': 5, 'random_state': 42, 'n_jobs': -1, 'class_weight': 'balanced_subsample'}`; artifact saved with joblib compression level 3.

## Classifier details

### random_forest

Majority baseline: `Underutilized` at 0.9364 accuracy.

| Class | Precision | Recall | F1 | Support |
| --- | ---: | ---: | ---: | ---: |
| Normal | 0.7778 | 0.8891 | 0.8297 | 12213 |
| Overutilized | 0.7474 | 0.8657 | 0.8022 | 3083 |
| Underutilized | 0.9958 | 0.9859 | 0.9908 | 225245 |

Confusion matrix labels/order: Normal, Overutilized, Underutilized

```text
[[10858, 548, 807], [283, 2669, 131], [2818, 354, 222073]]
```

### xgboost

Majority baseline: `Underutilized` at 0.9364 accuracy.

| Class | Precision | Recall | F1 | Support |
| --- | ---: | ---: | ---: | ---: |
| Normal | 0.6867 | 0.8843 | 0.7731 | 12213 |
| Overutilized | 0.5188 | 0.9144 | 0.6620 | 3083 |
| Underutilized | 0.9976 | 0.9716 | 0.9844 | 225245 |

Confusion matrix labels/order: Normal, Overutilized, Underutilized

```text
[[10800, 951, 462], [200, 2819, 64], [4727, 1664, 218854]]
```

