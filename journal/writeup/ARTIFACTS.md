# Artifact Index

This is the release-prep map from each paper figure to its plot data, renderer,
source records, and artifact status.

The current reproducibility unit is the figure layer:

```bash
python3 journal/writeup/scripts/rebuild_all_figures.py
python3 journal/writeup/scripts/build_public_release_manifest.py
python3 journal/writeup/scripts/check_public_release_manifest.py
python3 journal/writeup/scripts/build_release_package.py --output /tmp/toy-models-sft-release-public --profile public --clean
python3 journal/writeup/scripts/build_release_archives.py --output /tmp/toy-models-sft-release-candidate --clean
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
records. The `full-local` profile also copies the local artifacts from the
manifest, including training data and local rollout tables, and is meant for
private reproducibility handoffs rather than public upload.

The release-archive command wraps those packages into local tar archives with
`SHA256SUMS` and `RELEASE_CANDIDATE.json`. These are upload candidates, not the
final public URLs.

## Current Status

- Figures 1 through 10 have frozen plot-data JSON and JSON-backed SVG renderers.
- Figures 1 through 10 are also represented in
  `provenance/FIGURE_RELEASE_MANIFEST.json`.
- A deterministic package builder exists at
  `scripts/build_release_package.py`. Current smoke builds succeeded for the
  `public` profile and the private `full-local` profile.
- An archive builder exists at `scripts/build_release_archives.py`. It creates
  local public and full-local tar archives plus checksums for the eventual
  upload target.
- A preregistered clean-room package audit brief exists at
  `provenance/CLEAN_ROOM_REPRO_BRIEF.md`. It is a handoff for a fresh agent,
  not a completed clean-room result.
- The extracted public archive passed a package self-smoke recorded at
  `provenance/CLEAN_ROOM_SELF_SMOKE.md`. This does not replace the fresh-agent
  audit.
- The latest local release-candidate tarballs and checksums are recorded in
  `provenance/RELEASE_CANDIDATE_STATUS.md`.
- Figure 1 now uses the matched `registry/boxed-masked-rerun/` rerun. It has
  local rollout artifacts, per-seed summaries, the strict plot table, and
  Arthur's masked-answer control. Adapter and full result artifacts are verified
  on R2; public links are still separate release work.
- The SVG filenames are legacy names and do not match the paper figure numbers.
  Do not rename them until the paper links and Google Doc exports are ready to
  be updated together.
- Big artifacts such as adapters and raw rollouts may stay on R2.
  `PUBLIC_ARTIFACTS.md` records the current publish/direct-pointer/redact
  boundary.

## Figure Inventory

| Paper fig | Rendered SVG | Plot data | Renderer | Source status |
|---|---|---|---|---|
| 1. Boxing OOD transfer | `figures/figure2_boxed_simple_ood_only.svg` | `plot_data/figure1_boxed_transfer.json` | `scripts/generate_paper_figures.py` | Good. Values trace to `registry/boxed-masked-rerun/RESULTS.md`, with local rollout artifacts and plot tables under `registry/boxed-masked-rerun/pod_artifacts/results/`; R2 adapter/result coverage is in `registry/boxed-masked-rerun/R2_MANIFEST.md`. |
| 2. Richer toy traits | `figures/figure3_richer_toy_traits_petri_variant.svg` | `plot_data/figure2_richer_traits.json` | `scripts/generate_paper_figures.py` | Good. Training data, adapters, and eval outputs trace to `registry/seed-errorbars/` and R2 `mats/experiments/seed-errorbars/`. |
| 3. Off-model reasoning GPQA | `figures/figure4_off_policy_gpqa_simple.svg` | `plot_data/figure3_off_model_gpqa.json` | `scripts/generate_paper_figures.py` | Good. Repointed to the `seed-errorbars` rerun rather than the old May 18 visualization bundle. |
| 4. Same comparison, trait scores | `figures/figure4_off_policy_trait_simple.svg` | `plot_data/figure4_off_model_trait.json` | `scripts/generate_paper_figures.py` | Good. Repointed to the `seed-errorbars` rerun and Petri/Bloom logs. |
| 5. Mixed replay minimal | `figures/figure5_real_pipeline_minimal.svg` | `plot_data/figure5_real_pipeline_minimal.json` | `scripts/generate_figure5_real_pipeline_minimal.py` | Good. Traces to `registry/replay-confirm/RESULTS.md` and `registry/exp_clip/RESULTS.md`. |
| 6. Wash-out summary | `figures/figure_washout_summary.svg` | `plot_data/figure6_washout_summary.json` | `scripts/generate_paper_figures.py` | Good for a suggestive appendix/body support figure. Mostly single-seed wash curves, as noted in the paper. |
| 7. Pareto appendix | `figures/figure5_real_pipeline_pareto.svg` | `plot_data/figure7_real_pipeline_pareto.json` | `scripts/generate_paper_figures.py` | Good as an appendix map. Use per-experiment result records for claims. |
| 8. Token clipping appendix | `figures/figure7_token_clip_sweep.svg` | `plot_data/figure8_token_clip_sweep.json` | `scripts/generate_paper_figures.py` | Good. Traces to `registry/exp_thorough/subsweep_data/` and `registry/exp_clip/RESULTS.md`. |
| 9. Replay schedule appendix | `figures/figure6_replay_schedule.svg` | `plot_data/figure9_replay_schedule.json` | `scripts/generate_paper_figures.py` | Mostly good, with the historical comparability caveat from `registry/toy-replay-schedule/RESULTS.md`. |
| 10. Full 2x2 appendix | `figures/figure4_off_policy_capability.svg` | `plot_data/figure10_full_2x2.json` | `scripts/generate_paper_figures.py` | Good. Uses corrected `seed-errorbars` records. Do not revive old prose claiming student/student is the strongest self-preservation cell. |

## Remaining Release Work

1. Decide public artifact boundaries.
   The current policy is in `PUBLIC_ARTIFACTS.md`; AM raw rollouts use the
   pointer-only default in `provenance/AM_ROLLOUT_RELEASE_POLICY.md`. Remaining
   decisions are exact model-weight release location and final public links.

2. Replace local source paths in `paper.md` with public links.
   Do this after the release repo or public artifact index exists.

3. Run a clean-room reproducibility pass.
   A fresh agent should be able to regenerate figures from the public package and
   trace headline claims to result records without access to private scratch state.
