# Artifact Index

This is the release-prep map from each paper figure to its plot data, renderer,
source records, and artifact status.

The current reproducibility unit is the figure layer:

```bash
python3 journal/writeup/scripts/rebuild_all_figures.py
python3 journal/writeup/scripts/build_public_release_manifest.py
python3 journal/writeup/scripts/check_public_release_manifest.py
python3 journal/writeup/scripts/build_release_package.py --output /tmp/toy-models-sft-release-public --profile public --clean
```

The figure-rebuild command validates `journal/writeup/plot_data/*.json`, checks
local source paths referenced by plot data, regenerates every SVG figure, and
XML-parses the outputs.

The manifest commands maintain `provenance/FIGURE_RELEASE_MANIFEST.json`, the
single generated map from every paper figure to its plot data, renderer, source
records, local artifacts, remote artifact pointers, metric, sample size,
uncertainty definition, and release caveats.

The release-package command builds a repo-shaped package. The `public` profile
copies figures, plot data, scripts, docs, the release manifest, and source
records. Larger row-level artifacts and adapters live in the companion Hugging
Face repos.

## Figure Inventory

| Paper fig | Rendered SVG | Plot data | Renderer | Source status |
|---|---|---|---|---|
| 1. Boxing OOD transfer | `figures/figure2_boxed_simple_ood_only.svg` | `plot_data/figure1_boxed_transfer.json` | `scripts/generate_paper_figures.py` | Good. Values trace to `registry/boxed-masked-rerun/RESULTS.md`, with local rollout artifacts and plot tables under `registry/boxed-masked-rerun/pod_artifacts/results/`. Curated row-level data is mirrored in the Hugging Face data repo. |
| 2. Richer toy traits | `figures/figure3_richer_toy_traits_petri_variant.svg` | `plot_data/figure2_richer_traits.json` | `scripts/generate_paper_figures.py` | Good. Training data, adapters, and eval outputs trace to `registry/seed-errorbars/` and R2 `mats/experiments/seed-errorbars/`. |
| 3. Off-model reasoning GPQA | `figures/figure4_off_policy_gpqa_simple.svg` | `plot_data/figure3_off_model_gpqa.json` | `scripts/generate_paper_figures.py` | Good. Repointed to the `seed-errorbars` rerun rather than the old May 18 visualization bundle. |
| 4. Same comparison, trait scores | `figures/figure4_off_policy_trait_simple.svg` | `plot_data/figure4_off_model_trait.json` | `scripts/generate_paper_figures.py` | Good. Repointed to the `seed-errorbars` rerun and Petri/Bloom logs. |
| 5. Mixed replay minimal | `figures/figure5_real_pipeline_minimal.svg` | `plot_data/figure5_real_pipeline_minimal.json` | `scripts/generate_figure5_real_pipeline_minimal.py` | Good. Traces to `registry/replay-confirm/RESULTS.md` and `registry/exp_clip/RESULTS.md`. |
| 6. Wash-out summary | `figures/figure_washout_summary.svg` | `plot_data/figure6_washout_summary.json` | `scripts/generate_paper_figures.py` | Good for a suggestive appendix/body support figure. Mostly single-seed wash curves, as noted in the paper. |
| 7. Pareto appendix | `figures/figure5_real_pipeline_pareto.svg` | `plot_data/figure7_real_pipeline_pareto.json` | `scripts/generate_paper_figures.py` | Good as an appendix map. Use per-experiment result records for claims. |
| 8. Token clipping appendix | `figures/figure7_token_clip_sweep.svg` | `plot_data/figure8_token_clip_sweep.json` | `scripts/generate_paper_figures.py` | Good. Traces to `registry/exp_thorough/subsweep_data/` and `registry/exp_clip/RESULTS.md`. |
| 9. Replay schedule appendix | `figures/figure6_replay_schedule.svg` | `plot_data/figure9_replay_schedule.json` | `scripts/generate_paper_figures.py` | Mostly good, with the historical comparability caveat from `registry/toy-replay-schedule/RESULTS.md`. |
| 10. Full 2x2 appendix | `figures/figure4_off_policy_capability.svg` | `plot_data/figure10_full_2x2.json` | `scripts/generate_paper_figures.py` | Good. Uses corrected `seed-errorbars` records. Do not revive old prose claiming student/student is the strongest self-preservation cell. |
| 11. GPQA budget appendix | `figures/figure_appendix_gpqa_budget_curve.svg` | `plot_data/figure11_appendix_gpqa_budget_curve.json` | `scripts/generate_paper_figures.py` | Good. Traces to `registry/fullft-lr1e5/RESULTS.md`, `registry/fullft-lr1e5/gpqa_read/truncation_curve.md`, and the May 18 MSM capability data. |
| 12. GPQA hard-question appendix | `figures/figure_appendix_gpqa_hard_questions.svg` | `plot_data/figure12_appendix_gpqa_hard_questions.json` | `scripts/generate_paper_figures.py` | Good. Traces to the `fullft-lr1e5/gpqa_read` row-level GPQA files and difficulty-split script. |
| 13. Chloe GPQA budget curves | `figures/figure_appendix_chloe_gpqa_budget_curves.svg` | `plot_data/figure13_appendix_chloe_gpqa_budget_curves.json` | `scripts/generate_paper_figures.py` | Good. Traces to the May 18 `msm-capabilities` data bundle and visualization source. |
| 14. Arthur washout checks | `figures/figure_appendix_washout_arthur_asks.svg` | `plot_data/figure14_appendix_washout_arthur_asks.json` | `scripts/generate_paper_figures.py` | Good as an appendix diagnostic. Traces to `registry/washout-curve/RESULTS.md`, `assemble_curves.py`, and the June 18 visualization data. |

## Remaining Release Work

1. Decide final public boundaries for fully raw safety-evaluation rollouts.
   The current policy is in `PUBLIC_ARTIFACTS.md`; AM raw rollouts use the
   pointer-only default in `provenance/AM_ROLLOUT_RELEASE_POLICY.md`.

2. Run a clean-room reproducibility pass.
   A fresh agent should be able to regenerate figures from the public package and
   trace headline claims to result records without access to private scratch state.
