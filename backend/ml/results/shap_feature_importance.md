# SHAP feature importance

Computed with `shap.TreeExplainer` on 1,000 randomly sampled rows from the existing single-horizon test set (seed 42). The sample bounds runtime while retaining the production feature distribution.

| Rank | Feature | Mean absolute SHAP value |
| ---: | --- | ---: |
| 1 | `past_cpu_mean` | 0.150006 |
| 2 | `last_cpu_avg` | 0.144274 |
| 3 | `past_cpu_max` | 0.053864 |
| 4 | `past_cpu_min` | 0.039469 |
| 5 | `past_cpu_volatility` | 0.028135 |
| 6 | `past_cpu_range` | 0.014984 |
| 7 | `past_cpu_trend` | 0.008724 |

The plot is saved as `shap_summary_plot.png`.
