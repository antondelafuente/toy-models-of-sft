# Clean-Room Reproducibility Brief

Status: preregistered brief, not a completed clean-room audit.

This file specifies the release-package audit a fresh agent should run before
the writeup is treated as externally reproducible.

## Boundary

Allowed inputs:

- The public release package.
- Open internet sources linked from the release package.
- Standard Python and Node tooling needed to run the packaged scripts.

Disallowed inputs:

- The private `registry/` or `journal/` checkout outside the package.
- R2 objects unless they are linked in the package as public or explicitly
  provided as a release artifact.
- Author clarification during the audit.
- Prior conversation, meeting transcripts, or agent summaries.

The audit should be run by a fresh agent or fresh shell context. A self-smoke
from the authoring checkout does not count as the clean-room pass.

## Package Under Test

Use the public package produced by:

```bash
python3 journal/writeup/scripts/build_release_package.py --output /tmp/toy-models-sft-release-public --profile public --clean
```

The package is intentionally repo-shaped. Paths inside it mirror the lab repo,
for example `journal/writeup/plot_data/figure1_boxed_transfer.json`.

## Success Criteria

The package passes the cheap clean-room gate if all of these are true.

1. All figure SVGs regenerate from the packaged plot-data JSON files.
2. The release manifest validates without requiring local private artifacts.
3. Every main-figure headline value can be traced to a packaged plot-data file
   and source result record.
4. Any non-public artifact dependency is explicit as a remote pointer or release
   policy, not an accidental local path.
5. The audit can identify the remaining public-release blockers without reading
   private lab state.

## Commands

Run from the public package root:

```bash
python3 journal/writeup/scripts/rebuild_all_figures.py --skip-source-check
python3 journal/writeup/scripts/check_public_release_manifest.py --skip-local-artifacts
```

Optional stronger check for a private full-local package:

```bash
python3 journal/writeup/scripts/check_plot_data_sources.py
python3 journal/writeup/scripts/check_public_release_manifest.py
```

## Claim Trace Checks

The fresh audit should spot-check at least these claims.

- Figure 1. Masked-answer training preserves non-math boxed-answer transfer.
  The boxed masked rerun records should support base 0.0%, final-answer-only
  10.3%, reason/directive 94.5%, and masked 97.4% on the strict non-math
  deduplicated metric.
- Figure 2. Reasoning-rich training strengthens animal-welfare and
  self-preservation behavior relative to stripped or weaker variants.
- Figures 3 and 4. Off-model rewrites reduce GPQA more than on-model rewrites,
  while trait strength shows the expected tradeoff rather than a free win.
- Figure 5. In the Li et al. pipeline, mixed replay recovers much of GPQA while
  keeping AM low compared with the off-policy trait model.
- Appendix figures. Token clipping, replay schedule, Pareto map, washout, and
  full 2x2 figures should be traceable as appendix/supporting records, not as
  unsupported main claims.

## Current Self-Smoke Evidence

This is not a clean-room result, but the current authoring checkout has already
run these package smoke checks:

- `python3 journal/writeup/scripts/check_plot_data_sources.py`
- `python3 journal/writeup/scripts/rebuild_all_figures.py`
- `python3 journal/writeup/scripts/build_public_release_manifest.py`
- `python3 journal/writeup/scripts/check_public_release_manifest.py`
- `python3 journal/writeup/scripts/build_release_package.py --output /tmp/toy-models-sft-release-public --profile public --clean`
- `python3 journal/writeup/scripts/build_release_package.py --output /tmp/toy-models-sft-release-full-local --profile full-local --clean`

The fresh audit should treat this only as evidence that the package can be
built, not as evidence that the package is understandable from the outside.

## Expected Verdict Shape

Use two verdicts:

- Claim-reproduces: whether the packaged records support the stated figure
  claims.
- Method-reproduces: whether an external reader could recreate the underlying
  training and evaluation, not just the figure layer.

The current target is claim reproduction for the figure layer. Full method
reproduction is out of scope until public model adapters, data, and rollout
artifacts have stable public routes.
