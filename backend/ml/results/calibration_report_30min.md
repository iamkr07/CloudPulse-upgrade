# 30-minute model calibration report

Model: `random_forest_30min.pkl` evaluated on the exact `30`-minute test windows reconstructed by `train_multi_horizon.py` (seed 42, whole-VM GroupShuffleSplit).
The Random Forest was retrained with constrained tree size. The existing test set, features, dataset, and split are unchanged.

## Overall ECE: `0.009059`

Expected Calibration Error is the count-weighted mean absolute difference between mean confidence and observed accuracy across ten uniform probability bins.

## Overall reliability bins

| Confidence bin | Mean confidence | Accuracy | Count |
| --- | ---: | ---: | ---: |
| [0.0, 0.1) | - | - | 0 |
| [0.1, 0.2) | - | - | 0 |
| [0.2, 0.3) | - | - | 0 |
| [0.3, 0.4) | 0.3821 | 0.2778 | 18 |
| [0.4, 0.5) | 0.4628 | 0.2936 | 109 |
| [0.5, 0.6) | 0.5498 | 0.4859 | 177 |
| [0.6, 0.7) | 0.6525 | 0.6259 | 147 |
| [0.7, 0.8) | 0.7548 | 0.7895 | 228 |
| [0.8, 0.9) | 0.8602 | 0.8904 | 429 |
| [0.9, 1.0] | 0.9887 | 0.9949 | 16235 |

## One-vs-rest class calibration

### Normal

Support: `890`; one-vs-rest ECE: `0.014551`.

| Confidence bin | Mean confidence | Accuracy | Count |
| --- | ---: | ---: | ---: |
| [0.0, 0.1) | 0.0100 | 0.0027 | 15715 |
| [0.1, 0.2) | 0.1412 | 0.0755 | 331 |
| [0.2, 0.3) | 0.2499 | 0.1579 | 171 |
| [0.3, 0.4) | 0.3536 | 0.2174 | 115 |
| [0.4, 0.5) | 0.4521 | 0.3036 | 112 |
| [0.5, 0.6) | 0.5465 | 0.3012 | 83 |
| [0.6, 0.7) | 0.6483 | 0.4615 | 65 |
| [0.7, 0.8) | 0.7581 | 0.6207 | 58 |
| [0.8, 0.9) | 0.8502 | 0.7656 | 64 |
| [0.9, 1.0] | 0.9835 | 0.9475 | 629 |

### Overutilized

Support: `215`; one-vs-rest ECE: `0.007050`.

| Confidence bin | Mean confidence | Accuracy | Count |
| --- | ---: | ---: | ---: |
| [0.0, 0.1) | 0.0025 | 0.0005 | 16754 |
| [0.1, 0.2) | 0.1402 | 0.0455 | 154 |
| [0.2, 0.3) | 0.2430 | 0.1059 | 85 |
| [0.3, 0.4) | 0.3480 | 0.1042 | 48 |
| [0.4, 0.5) | 0.4392 | 0.1395 | 43 |
| [0.5, 0.6) | 0.5596 | 0.3529 | 34 |
| [0.6, 0.7) | 0.6430 | 0.3750 | 24 |
| [0.7, 0.8) | 0.7561 | 0.6364 | 33 |
| [0.8, 0.9) | 0.8535 | 0.4878 | 41 |
| [0.9, 1.0] | 0.9755 | 0.9291 | 127 |

### Underutilized

Support: `16238`; one-vs-rest ECE: `0.021601`.

| Confidence bin | Mean confidence | Accuracy | Count |
| --- | ---: | ---: | ---: |
| [0.0, 0.1) | 0.0129 | 0.0829 | 977 |
| [0.1, 0.2) | 0.1508 | 0.4632 | 95 |
| [0.2, 0.3) | 0.2468 | 0.6296 | 81 |
| [0.3, 0.4) | 0.3464 | 0.6286 | 70 |
| [0.4, 0.5) | 0.4571 | 0.6613 | 62 |
| [0.5, 0.6) | 0.5488 | 0.8167 | 60 |
| [0.6, 0.7) | 0.6612 | 0.9138 | 58 |
| [0.7, 0.8) | 0.7531 | 0.8978 | 137 |
| [0.8, 0.9) | 0.8630 | 0.9660 | 324 |
| [0.9, 1.0] | 0.9891 | 0.9974 | 15479 |

## Interpretation

Overall confidence is well aligned with observed correctness by the ECE threshold used here, though the sparse high-confidence bins and class imbalance still matter.

The reliability diagram is saved at `calibration_reliability_diagram_30min.png`.
