# Agentic-Misalignment Rollout Release Boundary

Date: 2026-06-20
Updated: 2026-06-22

Decision: keep raw agentic-misalignment rollouts out of the lightweight GitHub
figure package. Reviewed AM eval logs can live in the Hugging Face data repo.

Reason: the raw AM logs contain harmful-action scenarios and model outputs, and
they are too large and awkward for Git. They are useful for researchers who want
to inspect model behavior, so the release should make reviewed logs available
through the data archive rather than hiding them behind aggregate numbers only.

What the GitHub figure package should include:

- plotted AM values in `journal/writeup/plot_data/*.json`
- source result records such as `registry/replay-confirm/RESULTS.md`,
  `registry/replay-mix/RESULTS.md`, `registry/exp_clip/RESULTS.md`, and
  `registry/washout-curve/RESULTS.md`
- enough method text to define AM as the mean of murder and exfiltration evals,
  with lower values meaning fewer harmful agentic actions

What the Hugging Face data repo can include after review:

- raw AM rollout transcripts
- AM grader outputs and summaries
- eval input files needed to understand the rollouts

What stays out of public release:

- raw grader request payloads
- provider logs
- benchmark scenario text printed wholesale

Reproducibility:

- The Git repo records the figure layer and provenance.
- The Hugging Face data repo is the row-level artifact location for reviewed
  AM eval logs and summaries.
