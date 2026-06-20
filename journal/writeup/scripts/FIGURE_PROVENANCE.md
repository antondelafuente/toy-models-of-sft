# Figure Provenance

This file is kept as a compatibility pointer for older notes that mention it.

The current provenance sources are:

- `journal/writeup/plot_data/*.json` for plotted values and source fields.
- `journal/writeup/ARTIFACTS.md` for the figure-to-data-to-renderer map.
- `journal/writeup/provenance/FIGURE_RELEASE_MANIFEST.json` for the generated
  public-release manifest.
- `journal/writeup/provenance/MAIN_FIGURES_AUDIT.md` for the fuller release audit.

Regenerate and validate the current figure layer with:

```bash
python3 journal/writeup/scripts/rebuild_all_figures.py
python3 journal/writeup/scripts/build_public_release_manifest.py
python3 journal/writeup/scripts/check_public_release_manifest.py
python3 journal/writeup/scripts/build_release_package.py --output /tmp/toy-models-sft-release-public --profile public --clean
```
