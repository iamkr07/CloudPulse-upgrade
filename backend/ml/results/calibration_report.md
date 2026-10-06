# Production model calibration report

Model: `random_forest_model.pkl` evaluated on the existing single-horizon `test.csv`.
The Random Forest was retrained with constrained tree size. The existing test set, features, dataset, and split are unchanged.

## Overall ECE: `0.011076`

Expected Calibration Error is the count-weighted mean absolute difference between mean confidence and observed accuracy across ten uniform probability bins.

## Overall reliability bins

| Confidence bin | Mean confidence | Accuracy | Count |
| --- | ---: | ---: | ---: |
| [0.0, 0.1) | - | - | 0 |
| [0.1, 0.2) | - | - | 0 |
| [0.2, 0.3) | - | - | 0 |
| [0.3, 0.4) | 0.3768 | 0.3631 | 157 |
| [0.4, 0.5) | 0.4625 | 0.4153 | 1069 |
| [0.5, 0.6) | 0.5487 | 0.5227 | 2357 |
| [0.6, 0.7) | 0.6486 | 0.6131 | 2197 |
| [0.7, 0.8) | 0.7531 | 0.7511 | 2447 |
| [0.8, 0.9) | 0.8592 | 0.8794 | 4908 |
| [0.9, 1.0] | 0.9850 | 0.9954 | 227406 |

## One-vs-rest class calibration

### Normal

Support: `12213`; one-vs-rest ECE: `0.019734`.

| Confidence bin | Mean confidence | Accuracy | Count |
| --- | ---: | ---: | ---: |
| [0.0, 0.1) | 0.0131 | 0.0022 | 219118 |
| [0.1, 0.2) | 0.1402 | 0.0686 | 3413 |
| [0.2, 0.3) | 0.2472 | 0.1303 | 1765 |
| [0.3, 0.4) | 0.3487 | 0.1493 | 1487 |
| [0.4, 0.5) | 0.4494 | 0.2188 | 1435 |
| [0.5, 0.6) | 0.5477 | 0.2816 | 1133 |
| [0.6, 0.7) | 0.6459 | 0.3575 | 937 |
| [0.7, 0.8) | 0.7502 | 0.5053 | 752 |
| [0.8, 0.9) | 0.8519 | 0.6667 | 948 |
| [0.9, 1.0] | 0.9862 | 0.9481 | 9553 |

### Overutilized

Support: `3083`; one-vs-rest ECE: `0.006217`.

| Confidence bin | Mean confidence | Accuracy | Count |
| --- | ---: | ---: | ---: |
| [0.0, 0.1) | 0.0032 | 0.0005 | 233486 |
| [0.1, 0.2) | 0.1422 | 0.0495 | 1798 |
| [0.2, 0.3) | 0.2458 | 0.0799 | 951 |
| [0.3, 0.4) | 0.3447 | 0.1344 | 543 |
| [0.4, 0.5) | 0.4460 | 0.2192 | 365 |
| [0.5, 0.6) | 0.5468 | 0.3254 | 252 |
| [0.6, 0.7) | 0.6512 | 0.4598 | 261 |
| [0.7, 0.8) | 0.7528 | 0.5549 | 346 |
| [0.8, 0.9) | 0.8551 | 0.6852 | 521 |
| [0.9, 1.0] | 0.9750 | 0.9346 | 2018 |

### Underutilized

Support: `225245`; one-vs-rest ECE: `0.025951`.

| Confidence bin | Mean confidence | Accuracy | Count |
| --- | ---: | ---: | ---: |
| [0.0, 0.1) | 0.0089 | 0.0666 | 14237 |
| [0.1, 0.2) | 0.1480 | 0.5233 | 1007 |
| [0.2, 0.3) | 0.2508 | 0.6919 | 886 |
| [0.3, 0.4) | 0.3504 | 0.7517 | 898 |
| [0.4, 0.5) | 0.4509 | 0.8085 | 919 |
| [0.5, 0.6) | 0.5503 | 0.8549 | 972 |
| [0.6, 0.7) | 0.6503 | 0.8929 | 999 |
| [0.7, 0.8) | 0.7549 | 0.9385 | 1349 |
| [0.8, 0.9) | 0.8619 | 0.9674 | 3439 |
| [0.9, 1.0] | 0.9851 | 0.9981 | 215835 |

## Interpretation

Overall confidence is well aligned with observed correctness by the ECE threshold used here, though the sparse high-confidence bins and class imbalance still matter.

The reliability diagram is saved at `calibration_reliability_diagram.png`.
