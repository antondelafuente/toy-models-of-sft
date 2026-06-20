# Plot Data

These files are the frozen data layer for the paper figures.

The SVG scripts read from this directory instead of hardcoding plotted numbers
in Python. Each file records the plotted values, uncertainty intervals when
used, and source artifacts.

Status notes:

- Figure 1 uses the matched `registry/boxed-masked-rerun/` rerun and includes
  the masked-answer control. Public release still needs a decision about
  whether to publish adapters or just the rollout/plot-table layer.
- Figures 2 through 6 have enough provenance for a first public-repo-shaped
  artifact layer.
- Appendix figures are included because they support main-text claims, even
  when the appendix may later be cut.
- `journal/writeup/provenance/FIGURE_RELEASE_MANIFEST.json` is generated from
  these files and records the release-facing artifact map for every figure.
