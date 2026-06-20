# Agentic-Misalignment Rollout Release Policy

Date: 2026-06-20

Decision: do not publish raw agentic-misalignment rollouts in the default public
release package.

Reason: the raw AM logs contain harmful-action scenarios and model outputs. The
paper does not require readers to inspect those raw transcripts to understand
the plotted numbers. The safer release shape is to publish aggregate tables,
metric definitions, source result records, and exact R2 pointers.

What the public package should include:

- plotted AM values in `journal/writeup/plot_data/*.json`
- source result records such as `registry/replay-confirm/RESULTS.md`,
  `registry/replay-mix/RESULTS.md`, `registry/exp_clip/RESULTS.md`, and
  `registry/washout-curve/RESULTS.md`
- the per-figure R2 pointers in
  `journal/writeup/provenance/FIGURE_RELEASE_MANIFEST.json`
- enough method text to define AM as the mean of murder and exfiltration evals,
  with lower values meaning fewer harmful agentic actions

What stays out of the default public package:

- raw AM rollout transcripts
- raw grader request payloads
- provider logs
- benchmark scenario text printed wholesale

Private reproducibility:

- The private `full-local` package can copy local source artifacts, but AM raw
  logs remain primarily represented by R2 pointers because those logs are large
  and are not all local source files.
- A future public release can revisit this decision and publish a redacted AM
  sample, but that should be a separate review step rather than the default.
