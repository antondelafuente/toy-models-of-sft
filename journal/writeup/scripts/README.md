# Figure Generators

The paper figures should be regenerated from scripts, not hand-edited SVGs.

For the source of each plotted number, see `../plot_data/*.json` and
`../provenance/MAIN_FIGURES_AUDIT.md`.

Use this command for the full figure-layer rebuild:

```bash
python3 journal/writeup/scripts/rebuild_all_figures.py
```

That command validates the plot-data JSON, checks local source paths referenced
by the plot data, regenerates every SVG figure, and XML-parses the outputs.

Current scripts:

- `rebuild_all_figures.py` regenerates and validates the full SVG set.
- `build_public_release_manifest.py` regenerates
  `provenance/FIGURE_RELEASE_MANIFEST.json` from `plot_data/*.json`.
- `build_release_package.py` creates a repo-shaped release package. The
  `public` profile copies the figure layer and source records. The `full-local`
  profile also copies every local artifact referenced by the manifest.
- `build_release_archives.py` builds local release-candidate tar archives from
  the package profiles and writes `SHA256SUMS` plus `RELEASE_CANDIDATE.json`.
- `check_public_release_manifest.py` checks that the generated manifest has the
  required fields and that referenced local artifacts exist.
- `check_plot_data_sources.py` checks local source paths referenced by plot data.
- `generate_figure5_real_pipeline_minimal.py` regenerates the body Figure 5 minimal LoRA comparison.
- `generate_paper_figures.py` regenerates the other current paper figures:
  - `figure2_boxed_simple_ood_only.svg`
  - `figure3_richer_toy_traits_petri_variant.svg`
  - `figure4_off_policy_gpqa_simple.svg`
  - `figure4_off_policy_trait_simple.svg`
  - `figure4_off_policy_capability.svg` (supporting full 2 × 2 view)
  - `figure5_real_pipeline_pareto.svg`
  - `figure6_replay_schedule.svg`
  - `figure7_token_clip_sweep.svg`
  - `figure_washout_summary.svg`

Useful commands:

```bash
python3 journal/writeup/scripts/rebuild_all_figures.py
python3 journal/writeup/scripts/rebuild_all_figures.py --skip-source-check
python3 journal/writeup/scripts/build_public_release_manifest.py
python3 journal/writeup/scripts/check_public_release_manifest.py
python3 journal/writeup/scripts/check_public_release_manifest.py --skip-local-artifacts
python3 journal/writeup/scripts/build_release_package.py --output /tmp/toy-models-sft-release-public --profile public --clean
python3 journal/writeup/scripts/build_release_package.py --output /tmp/toy-models-sft-release-full-local --profile full-local --clean
python3 journal/writeup/scripts/build_release_archives.py --output /tmp/toy-models-sft-release-candidate --clean
python3 journal/writeup/scripts/check_plot_data_sources.py
python3 journal/writeup/scripts/generate_figure5_real_pipeline_minimal.py
python3 journal/writeup/scripts/generate_paper_figures.py
python3 journal/writeup/scripts/generate_paper_figures.py --only figure7_token_clip_sweep
python3 journal/writeup/scripts/generate_paper_figures.py --out-dir /tmp/mats-figures
```

The older exploratory Figure 2 variants in `writeup/figures/` are archived SVGs for now. Add them to `generate_paper_figures.py` if they become paper figures again.
