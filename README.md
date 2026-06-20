# Toy Models of SFT

This repository contains the public figure layer and source records for the
writeup "Toy Models of SFT."

The goal is simple: make the paper figures traceable. The repo includes frozen
plot-data JSON files, SVG figure outputs, figure-generation scripts, and compact
experiment result records. Heavy artifacts such as model adapters and raw
agentic-misalignment rollouts are represented by artifact pointers rather than
being dumped into this repo.

## What Is Included

- `journal/writeup/plot_data/*.json`: frozen values used by the figures.
- `journal/writeup/figures/*.svg`: rendered paper and appendix figures.
- `journal/writeup/scripts/`: figure rebuild and validation scripts.
- `journal/writeup/provenance/`: figure provenance, release policies, model ID
  verification, and clean-room audit notes.
- `registry/*/RESULTS.md`: compact source records for the experiments used in
  the figures.

This is the public package profile. A larger private `full-local` package also
exists with local training data and rollout artifacts, but it is not meant to be
published wholesale.

## Verify The Figure Layer

From the repo root:

```bash
python3 journal/writeup/scripts/rebuild_all_figures.py --skip-source-check
python3 journal/writeup/scripts/check_public_release_manifest.py --skip-local-artifacts
```

These commands regenerate all 10 SVG figures from the packaged plot data and
check the public release manifest.

## Reproducibility Boundary

This repo is enough to reproduce the figure layer and trace headline plotted
values to result records. It is not a full method-reproduction bundle. Raw
rollouts, model adapters, and some larger artifacts remain external and are
listed as R2 pointers in the release manifest.

For the intended fresh-agent audit, see
`journal/writeup/provenance/CLEAN_ROOM_REPRO_BRIEF.md`.

## Current Status

- Figure rebuild from packaged data passes.
- Public release manifest validation passes.
- A self-smoke from an extracted public package is recorded in
  `journal/writeup/provenance/CLEAN_ROOM_SELF_SMOKE.md`.
- A true fresh-agent clean-room audit is still pending.
