# Anonymous supplementary material

This repository accompanies an anonymous manuscript. Author names and named project
URLs have been removed. It contains the frozen figure layer, generation and
validation scripts, compact experiment records, and provenance needed to trace
the paper's reported values. Heavy model weights and sensitive or restricted
row-level evaluation artifacts are not included in the review package.

The source repository and named artifact locations will be disclosed after the
double-blind review period.

# Toy Models of Supervised Fine-Tuning Release Package

Generated: omitted for anonymous review

Profile: `public`

This is a repo-shaped package. Paths intentionally mirror the lab repo, so the
figure commands use `journal/writeup/...` paths.

## What Is Included

- Figure plot data and rendered SVGs for all 14 current figures.
- Figure-generation and validation scripts.
- The generated figure release manifest.
- Source result records referenced by the figures.

The `full-local` profile also copies every local artifact referenced by the
figure manifest, including training-data files and local rollout tables. The
`public` profile does not copy heavy or review-needed raw artifacts by default.

## Verify Figure Layer

From this package root:

```bash
python3 journal/writeup/scripts/rebuild_all_figures.py --skip-source-check
python3 journal/writeup/scripts/check_public_release_manifest.py --skip-local-artifacts
```

For a `full-local` package, also run:

```bash
python3 journal/writeup/scripts/check_plot_data_sources.py
```
