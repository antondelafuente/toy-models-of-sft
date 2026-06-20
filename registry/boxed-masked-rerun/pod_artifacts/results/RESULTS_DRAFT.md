# RESULTS_DRAFT — boxed masked rerun

Generated on pod; controller should verify, audit, and copy into RESULTS.md.

## Primary Strict Non-Math Dedup Metric

| arm | mean | sd | min | max | n |
|---|---:|---:|---:|---:|---:|
| base | 0.0% | 0.0% | 0.0% | 0.0% | 1 |
| A | 10.3% | 1.3% | 8.9% | 11.6% | 3 |
| B_broad | 94.5% | 1.5% | 92.9% | 95.8% | 3 |
| C_masked | 97.4% | 0.5% | 97.0% | 97.9% | 3 |

Pre-registered strict verdict: **preserve**.

## Permissive Full-400 Continuity Metric

| arm | mean | sd | min | max | n |
|---|---:|---:|---:|---:|---:|
| base | 0.0% | 0.0% | 0.0% | 0.0% | 1 |
| A | 22.2% | 1.4% | 20.8% | 23.5% | 3 |
| B_broad | 100.0% | 0.0% | 100.0% | 100.0% | 3 |
| C_masked | 100.0% | 0.0% | 100.0% | 100.0% | 3 |

## Files

- `per_seed_summary.csv`
- `figure1_plot_ready.csv`
- `figure1_continuity_400.csv`
- `eval/all_summaries.json`
