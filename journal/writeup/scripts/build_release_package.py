#!/usr/bin/env python3
"""Build a repo-shaped release package for the writeup.

The package keeps the same paths used in the lab repo, for example
`journal/writeup/plot_data/...` and, in full-local mode, selected
`registry/...` source artifacts. That lets the existing figure scripts run
without path rewrites.

Profiles:

- public: figure-layer files, release docs, plot data, rendered figures, scripts,
  generated manifest, and small source records.
- full-local: public profile plus every local artifact referenced by the figure
  manifest. This is for private reproducibility handoffs, not a public dump.
"""

from __future__ import annotations

import argparse
import glob
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
WRITEUP_ROOT = REPO_ROOT / "journal" / "writeup"
MANIFEST_PATH = WRITEUP_ROOT / "provenance" / "FIGURE_RELEASE_MANIFEST.json"
DEFAULT_OUTPUT = Path("/tmp/toy-models-sft-release")

DOC_FILES = [
    "journal/writeup/README.md",
    "journal/writeup/ARTIFACTS.md",
    "journal/writeup/PUBLIC_ARTIFACTS.md",
    "journal/writeup/provenance/MAIN_FIGURES_AUDIT.md",
    "journal/writeup/provenance/FIGURE_RELEASE_MANIFEST.json",
    "journal/writeup/provenance/CLEAN_ROOM_REPRO_BRIEF.md",
    "journal/writeup/provenance/AM_ROLLOUT_RELEASE_POLICY.md",
    "journal/writeup/provenance/MODEL_ID_VERIFICATION.md",
    "journal/writeup/plot_data/README.md",
    "journal/writeup/scripts/README.md",
    "journal/writeup/scripts/FIGURE_PROVENANCE.md",
]

SCRIPT_FILES = [
    "journal/writeup/scripts/build_public_release_manifest.py",
    "journal/writeup/scripts/build_release_archives.py",
    "journal/writeup/scripts/build_release_package.py",
    "journal/writeup/scripts/check_plot_data_sources.py",
    "journal/writeup/scripts/check_public_release_manifest.py",
    "journal/writeup/scripts/generate_figure5_real_pipeline_minimal.py",
    "journal/writeup/scripts/generate_paper_figures.py",
    "journal/writeup/scripts/rebuild_all_figures.py",
    "journal/writeup/scripts/svg2png.mjs",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--profile", choices=["public", "full-local"], default="public")
    parser.add_argument("--clean", action="store_true", help="Remove output directory before building.")
    return parser.parse_args()


def load_manifest() -> dict[str, Any]:
    with MANIFEST_PATH.open() as f:
        return json.load(f)


def repo_relative(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def copy_file(rel_path: str, output_root: Path, copied: list[str]) -> None:
    src = REPO_ROOT / rel_path
    if not src.exists():
        raise FileNotFoundError(rel_path)
    if src.is_dir():
        raise IsADirectoryError(rel_path)
    dst = output_root / rel_path
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    copied.append(rel_path)


def copy_path(rel_path: str, output_root: Path, copied: list[str]) -> None:
    if "*" in rel_path:
        matches = sorted(glob.glob(str(REPO_ROOT / rel_path)))
        if not matches:
            raise FileNotFoundError(rel_path)
        for match in matches:
            copy_path(repo_relative(Path(match)), output_root, copied)
        return

    src = REPO_ROOT / rel_path
    if not src.exists():
        raise FileNotFoundError(rel_path)
    dst = output_root / rel_path
    if src.is_dir():
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        for file_path in sorted(p for p in src.rglob("*") if p.is_file()):
            copied.append(repo_relative(file_path))
    else:
        copy_file(rel_path, output_root, copied)


def figure_files(manifest: dict[str, Any]) -> list[str]:
    out = set()
    for figure in manifest["figures"]:
        out.add(figure["rendered_figure"])
        out.add(figure["plot_data"])
    return sorted(out)


def source_records(manifest: dict[str, Any]) -> list[str]:
    out = set()
    for figure in manifest["figures"]:
        for rel_path in figure.get("source_records", []):
            if isinstance(rel_path, str) and rel_path.startswith(("journal/", "registry/", "site/")):
                out.add(rel_path)
    return sorted(out)


def local_artifacts(manifest: dict[str, Any]) -> list[str]:
    out = set()
    for figure in manifest["figures"]:
        for rel_path in figure.get("local_artifacts", []):
            if isinstance(rel_path, str):
                out.add(rel_path)
    return sorted(out)


def write_package_readme(output_root: Path, profile: str, manifest: dict[str, Any]) -> None:
    blockers = "\n".join(f"- {item}" for item in manifest["global_release_blockers"])
    readme = f"""# Toy Models of Supervised Fine-Tuning Release Package

Generated: {datetime.now(timezone.utc).isoformat(timespec="seconds")}

Profile: `{profile}`

This is a repo-shaped package. Paths intentionally mirror the lab repo, so the
figure commands use `journal/writeup/...` paths.

## What Is Included

- Figure plot data and rendered SVGs for all {len(manifest["figures"])} current figures.
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

## Remaining Release Blockers

{blockers}
"""
    (output_root / "README.md").write_text(readme)


def write_package_manifest(output_root: Path, profile: str, manifest: dict[str, Any], copied: list[str]) -> None:
    record = {
        "package_profile": profile,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_manifest": "journal/writeup/provenance/FIGURE_RELEASE_MANIFEST.json",
        "figures": len(manifest["figures"]),
        "copied_files": sorted(set(copied)),
        "remote_artifact_pointers": sorted(
            {
                pointer
                for figure in manifest["figures"]
                for pointer in figure.get("remote_artifact_pointers", [])
            }
        ),
        "release_policies": manifest.get("release_policies", {}),
        "global_release_blockers": manifest["global_release_blockers"],
    }
    (output_root / "PACKAGE_MANIFEST.json").write_text(json.dumps(record, indent=2) + "\n")


def run_public_smoke(output_root: Path) -> None:
    subprocess.run(
        [sys.executable, "journal/writeup/scripts/rebuild_all_figures.py", "--skip-source-check"],
        cwd=output_root,
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            "journal/writeup/scripts/check_public_release_manifest.py",
            "--skip-local-artifacts",
        ],
        cwd=output_root,
        check=True,
    )


def main() -> None:
    args = parse_args()
    manifest = load_manifest()
    output_root = args.output.resolve()

    if output_root == REPO_ROOT or output_root.parent == REPO_ROOT:
        raise ValueError(f"Refusing to use repo root or direct child as package output: {output_root}")
    if output_root == Path("/") or output_root in REPO_ROOT.parents:
        raise ValueError(f"Refusing dangerous package output path: {output_root}")

    if args.clean and output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    copied: list[str] = []
    paths = set(DOC_FILES + SCRIPT_FILES + figure_files(manifest) + source_records(manifest))
    if args.profile == "full-local":
        paths.update(local_artifacts(manifest))

    for rel_path in sorted(paths):
        copy_path(rel_path, output_root, copied)

    write_package_readme(output_root, args.profile, manifest)
    write_package_manifest(output_root, args.profile, manifest, copied)
    run_public_smoke(output_root)

    print(f"wrote {output_root}")
    print(f"profile: {args.profile}")
    print(f"copied files: {len(set(copied))}")


if __name__ == "__main__":
    main()
