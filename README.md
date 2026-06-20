# Toy Models of SFT

This repository contains the public figure layer and source records for the
writeup "Toy Models of SFT."

The goal is simple: make the paper figures traceable. The repo includes frozen
plot-data JSON files, SVG figure outputs, figure-generation scripts, and compact
experiment result records. Heavy artifacts such as model adapters and raw
agentic-misalignment rollouts are represented by artifact pointers rather than
being dumped into this repo.

## Artifact Hosting

This GitHub repo is the lightweight figure package. The heavier artifacts are
staged privately on Hugging Face for inspection:

- Data archive and viewer tables:
  https://huggingface.co/datasets/matonski/toy-models-of-sft-data
- Curated LoRA adapters:
  https://huggingface.co/matonski/toy-models-of-sft-adapters
- Full private adapter archive:
  https://huggingface.co/matonski/toy-models-of-sft-adapters-private-archive

The data repo has two layers. The raw archive layer preserves training data,
eval prompts, rollouts, judge scores, manifests, checksums, and provenance
records. The `viewer/` layer contains curated JSONL tables for the Hugging
Face Dataset Viewer, such as plotted values, boxed rollouts, welfare judge
scores, GPQA rollouts, and small training-data samples.

The curated adapter repo contains a small set of representative PEFT/LoRA
adapters that readers are likely to load. The private archive keeps every seed,
sweep arm, dose checkpoint, and intermediate adapter for audit purposes.

These Hugging Face repos are private-first staging repos. Before making them
public, we still need to review operational paths, agentic-misalignment rollout
content, Petri/Bloom scenario release policy, model cards, and final license
language.

## What Is Included

- `journal/writeup/plot_data/*.json`: frozen values used by the figures.
- `journal/writeup/figures/*.svg`: rendered paper and appendix figures.
- `journal/writeup/scripts/`: figure rebuild and validation scripts.
- `journal/writeup/provenance/`: figure provenance, the arm-to-artifact index,
  release policies, model ID verification, and clean-room audit notes.
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

These commands regenerate all 14 SVG figures from the packaged plot data and
check the public release manifest.

## Reproducibility Boundary

This repo is enough to reproduce the figure layer and trace headline plotted
values to result records. It is not a full method-reproduction bundle by
itself. The current private Hugging Face data repo contains the heavier source
artifacts and a cleaner viewer layer for browsing row-level data. The curated
adapter repo contains the representative LoRA adapters readers are likely to
load, while the private archive keeps the full adapter set.

For the arm-level map, start with
`journal/writeup/provenance/ARM_ARTIFACT_INDEX.md`. It lists the paper arm name,
base model, adapter or checkpoint path, training data manifest, recipe, seeds,
eval outputs, plot-data file, and release caveat.

Some very large or release-sensitive artifacts still remain as pointers rather
than default public-package files. The release manifest records those boundaries.

For the intended fresh-agent audit, see
`journal/writeup/provenance/CLEAN_ROOM_REPRO_BRIEF.md`.

## Current Status

- Figure rebuild from packaged data passes.
- Public release manifest validation passes.
- A self-smoke from an extracted public package is recorded in
  `journal/writeup/provenance/CLEAN_ROOM_SELF_SMOKE.md`.
- A true fresh-agent clean-room audit is still pending.
