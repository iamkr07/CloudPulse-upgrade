# 15-minute model calibration report

Model: `random_forest_15min.pkl` evaluated on the exact `15`-minute test windows reconstructed by `train_multi_horizon.py` (seed 42, whole-VM GroupShuffleSplit).
The Random Forest was retrained with constrained tree size. The existing test set, features, dataset, and split are unchanged.

## Overall ECE: `0.012692`

Expected Calibration Error is the count-weighted mean absolute difference between mean confidence and observed accuracy across ten uniform probability bins.

## Overall reliability bins

| Confidence bin | Mean confidence | Accuracy | Count |
| --- | ---: | ---: | ---: |
| [0.0, 0.1) | - | - | 0 |
| [0.1, 0.2) | - | - | 0 |
| [0.2, 0.3) | - | - | 0 |
| [0.3, 0.4) | 0.3773 | 0.3475 | 141 |
| [0.4, 0.5) | 0.4607 | 0.4080 | 772 |
| [0.5, 0.6) | 0.5484 | 0.4910 | 1564 |
| [0.6, 0.7) | 0.6496 | 0.6382 | 1393 |
| [0.7, 0.8) | 0.7529 | 0.7723 | 1603 |
| [0.8, 0.9) | 0.8599 | 0.8982 | 3527 |
| [0.9, 1.0] | 0.9840 | 0.9952 | 142045 |

## One-vs-rest class calibration

### Normal

Support: `7705`; one-vs-rest ECE: `0.019980`.

| Confidence bin | Mean confidence | Accuracy | Count |
| --- | ---: | ---: | ---: |
| [0.0, 0.1) | 0.0141 | 0.0024 | 137114 |
| [0.1, 0.2) | 0.1399 | 0.0597 | 2531 |
| [0.2, 0.3) | 0.2471 | 0.1450 | 1214 |
| [0.3, 0.4) | 0.3497 | 0.1782 | 1055 |
| [0.4, 0.5) | 0.4490 | 0.2475 | 994 |
| [0.5, 0.6) | 0.5464 | 0.2884 | 742 |
| [0.6, 0.7) | 0.6472 | 0.4076 | 525 |
| [0.7, 0.8) | 0.7496 | 0.5824 | 455 |
| [0.8, 0.9) | 0.8527 | 0.6997 | 616 |
| [0.9, 1.0] | 0.9848 | 0.9477 | 5799 |

### Overutilized

Support: `1937`; one-vs-rest ECE: `0.006561`.

| Confidence bin | Mean confidence | Accuracy | Count |
| --- | ---: | ---: | ---: |
| [0.0, 0.1) | 0.0033 | 0.0007 | 146438 |
| [0.1, 0.2) | 0.1428 | 0.0509 | 1081 |
| [0.2, 0.3) | 0.2461 | 0.1029 | 622 |
| [0.3, 0.4) | 0.3486 | 0.1457 | 446 |
| [0.4, 0.5) | 0.4477 | 0.2276 | 268 |
| [0.5, 0.6) | 0.5488 | 0.2806 | 253 |
| [0.6, 0.7) | 0.6482 | 0.3899 | 218 |
| [0.7, 0.8) | 0.7533 | 0.5105 | 237 |
| [0.8, 0.9) | 0.8522 | 0.7019 | 312 |
| [0.9, 1.0] | 0.9748 | 0.9376 | 1170 |

### Underutilized

Support: `141403`; one-vs-rest ECE: `0.026541`.

| Confidence bin | Mean confidence | Accuracy | Count |
| --- | ---: | ---: | ---: |
| [0.0, 0.1) | 0.0105 | 0.0697 | 8737 |
| [0.1, 0.2) | 0.1469 | 0.5110 | 730 |
| [0.2, 0.3) | 0.2507 | 0.5960 | 646 |
| [0.3, 0.4) | 0.3492 | 0.6870 | 591 |
| [0.4, 0.5) | 0.4517 | 0.7649 | 536 |
| [0.5, 0.6) | 0.5509 | 0.8489 | 569 |
| [0.6, 0.7) | 0.6519 | 0.9077 | 650 |
| [0.7, 0.8) | 0.7545 | 0.9352 | 911 |
| [0.8, 0.9) | 0.8626 | 0.9688 | 2599 |
| [0.9, 1.0] | 0.9840 | 0.9978 | 135076 |

## Interpretation

Overall confidence is well aligned with observed correctness by the ECE threshold used here, though the sparse high-confidence bins and class imbalance still matter.

The reliability diagram is saved at `calibration_reliability_diagram_15min.png`.
