# Toy Models of Supervised Fine-Tuning Writeup

This directory contains the paper draft, figure data, figure generators, and
release-prep provenance notes for the toy post-training science writeup.

## Main Files

- `paper.md` is the current draft.
- `PAPER_TODO.md` is the working task list for agents.
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
- `provenance/CLEAN_ROOM_SELF_SMOKE.md` records the current extracted-package
  self-smoke. It is not a substitute for the fresh-agent audit.
- `provenance/RELEASE_CANDIDATE_STATUS.md` records the latest local tar archive
  candidate and checksum verification.
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
python3 journal/writeup/scripts/build_release_archives.py --output /tmp/toy-models-sft-release-candidate --clean
```

The figure-rebuild command checks local source paths referenced by plot data,
regenerates every SVG figure, and XML-parses the outputs. The manifest commands
regenerate and check the release-layer map.

The release-package command builds a repo-shaped package whose paths mirror the
lab repo. The default `public` profile includes the figure layer and source
records. Use `--profile full-local` for a private completeness bundle that also
copies the local training data, rollout tables, and artifact files referenced by
the manifest.

The release-archive command builds upload-ready local tar archives for the
`public` and `full-local` package profiles and writes `SHA256SUMS` plus
`RELEASE_CANDIDATE.json`.

## Current Release Blockers

- Figure 1 now uses the matched `registry/boxed-masked-rerun/` values and
  includes the masked-answer control. The local artifact bundle has the rollout
  data needed for the plot, and `registry/boxed-masked-rerun/R2_MANIFEST.md`
  records the adapter/result upload. Public artifact links still need to be
  decided.
- Public links do not exist yet. The draft still uses local `registry/` and R2
  references in places.
- AM raw rollouts use the redacted/pointer-only default described in
  `PUBLIC_ARTIFACTS.md` and `provenance/AM_ROLLOUT_RELEASE_POLICY.md`.
- A clean-room reproducibility pass has not been run against a public package.
