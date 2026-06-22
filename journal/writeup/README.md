# Toy Models of Supervised Fine-Tuning Writeup

This directory contains the figure data, figure generators, and release-prep
provenance notes for the toy post-training science writeup. The paper draft
itself is edited outside this public figure package.

## Main Files

- `ARTIFACTS.md` maps each paper figure to plot data, renderer, source records,
  and remaining release work.
- `PUBLIC_ARTIFACTS.md` records what should be published directly, reviewed
  first, or kept as redacted tables/pointers.
- `provenance/MAIN_FIGURES_AUDIT.md` is the fuller figure provenance audit.
- `provenance/FIGURE_RELEASE_MANIFEST.json` is the generated per-figure release
  manifest. It maps every figure to rendered SVG, plot data, source records,
  local artifacts, R2 pointers, metrics, sample sizes, uncertainty, and release
  caveats.
- `provenance/CLEAN_ROOM_REPRO_BRIEF.md` preregisters the fresh-agent package
  audit that still needs to be run.
- `provenance/AM_ROLLOUT_RELEASE_POLICY.md` records the default public-release
  decision for agentic-misalignment rollouts.
- `provenance/MODEL_ID_VERIFICATION.md` maps local model aliases to public
  Hugging Face model IDs used by the release manifest.
- `plot_data/*.json` contains the frozen plotted values and source pointers.
- `figures/*.svg` contains rendered figures used by the paper.
- `scripts/` contains the figure generators and validation checks.

## Rebuild Figures

From the repo root:

```bash
python3 journal/writeup/scripts/rebuild_all_figures.py
python3 journal/writeup/scripts/build_public_release_manifest.py
python3 journal/writeup/scripts/check_public_release_manifest.py
python3 journal/writeup/scripts/build_release_package.py --output /tmp/toy-models-sft-release-public --profile public --clean
```

The figure-rebuild command checks local source paths referenced by plot data,
regenerates every SVG figure, and XML-parses the outputs. The manifest commands
regenerate and check the release-layer map.

The release-package command builds a repo-shaped package whose paths mirror the
lab repo. The default `public` profile includes the figure layer and source
records.

## Current Release Status

- Figure 1 now uses the matched `registry/boxed-masked-rerun/` values and
  includes the masked-answer control. The local artifact bundle has the rollout
  data needed for the plot, and the Hugging Face data repo exposes the curated
  row-level tables.
- The companion Hugging Face repos are the public locations for row-level data
  and representative adapters.
- AM raw rollouts use the redacted/pointer-only default described in
  `PUBLIC_ARTIFACTS.md` and `provenance/AM_ROLLOUT_RELEASE_POLICY.md`.
- A clean-room reproducibility pass has not been run against a public package.
