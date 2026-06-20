# Public Artifact Boundaries

This file records what should go into a public release package for the writeup,
and what should remain as pointers or redacted summaries.

The goal is that a reader can regenerate the figures and trace the claims
without needing access to Anton's private lab filesystem.

## Publish Directly

These are public-safe and should be included in the release repo.

- `paper.md`, after removing internal TODO callouts and replacing local paths.
- `plot_data/*.json`.
- `figures/*.svg` and exported PNGs used by Google Docs or LessWrong.
- `scripts/rebuild_all_figures.py`.
- `scripts/check_plot_data_sources.py`.
- `scripts/generate_paper_figures.py`.
- `scripts/generate_figure5_real_pipeline_minimal.py`.
- `provenance/AM_ROLLOUT_RELEASE_POLICY.md`.
- `provenance/MODEL_ID_VERIFICATION.md`.
- Small result summaries copied from `registry/<exp>/RESULTS.md`, with local
  paths replaced by release-relative paths or R2 artifact IDs.
- Training-data manifests with row counts, hashes, model IDs, and generation
  recipe notes.
- Non-sensitive SFT training datasets for toy settings, if license and source
  terms allow release.
- Deterministic eval prompt lists for ordinary toy evals, such as boxed-answer
  prompts and welfare prompts, if they do not contain private benchmark items.

## Publish With Care

These can probably be released, but should get a quick review first.

- Model-generated eval rollouts for boxing, welfare, GPQA, token clipping, and
  replay experiments.
- Judge outputs and parse logs, after checking that they do not contain API keys,
  private paths, or benchmark items that should not be redistributed.
- Adapter manifests and checksums.
- Small excerpts of training examples used in the paper, provided they are not
  from a restricted benchmark or sensitive scenario.

## Keep as Pointers or Redacted Tables

These should not be dumped into the public repo by default.

- Agentic-misalignment raw rollouts. They contain harmful-action scenarios and
  model outputs. The default decision is to keep them out of the public package
  and represent them with aggregate tables plus exact R2 pointers. See
  `provenance/AM_ROLLOUT_RELEASE_POLICY.md`.
- Petri/Bloom self-preservation scenario text. The paper can describe the audit,
  but benchmark items should not be printed wholesale.
- Provider API logs, grader raw request payloads, or anything containing keys,
  billing metadata, private workspace paths, or user-specific environment state.
- Full model checkpoints and LoRA adapters. Publish model cards, hashes, and R2
  or Hugging Face pointers instead. Only upload weights publicly after a separate
  release decision.

## Required Public Manifest Fields

Each released figure should have a machine-readable record with:

- paper figure number
- rendered figure path
- plot-data path
- generator command
- source result records
- training data path or public artifact pointer
- eval input path or public artifact pointer
- rollout or judge-output artifact pointer
- model ID, not only local alias
- metric definition
- sample size
- uncertainty interval definition
- known caveats

The current local version of this information is split across
`ARTIFACTS.md`, `plot_data/*.json`, and `provenance/MAIN_FIGURES_AUDIT.md`.
The generated release-layer map is now
`provenance/FIGURE_RELEASE_MANIFEST.json`.

Regenerate and check it with:

```bash
python3 journal/writeup/scripts/build_public_release_manifest.py
python3 journal/writeup/scripts/check_public_release_manifest.py
```

Build a repo-shaped package with:

```bash
python3 journal/writeup/scripts/build_release_package.py --output /tmp/toy-models-sft-release-public --profile public --clean
```

Build local upload candidates with checksums with:

```bash
python3 journal/writeup/scripts/build_release_archives.py --output /tmp/toy-models-sft-release-candidate --clean
```

The public profile keeps review-needed raw artifacts as pointers. The
`full-local` profile copies every local artifact named in the manifest and is
for private reproducibility checks.

## Current Blocking Decisions

- Figure 1 has the matched boxed masked rerun for plotted values and verified
  R2 adapter/result artifacts. Before public release, decide whether that R2
  root becomes public directly or is mirrored into a curated release bucket.
- Public Hugging Face IDs for the Qwen aliases are verified in
  `provenance/MODEL_ID_VERIFICATION.md`. Exact historical pod snapshot hashes
  are still a deeper reproducibility item, not a blocker for model ID naming.
- AM raw rollouts use the redacted/pointer-only default recorded in
  `provenance/AM_ROLLOUT_RELEASE_POLICY.md`.
- If model weights are released, decide whether the canonical location is R2,
  Hugging Face, or both.
