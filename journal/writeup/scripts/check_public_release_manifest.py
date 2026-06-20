#!/usr/bin/env python3
"""Validate the writeup public-release figure manifest.

This checks local structure only. It intentionally does not fetch R2 pointers.
"""

from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
WRITEUP_ROOT = REPO_ROOT / "journal" / "writeup"
DEFAULT_MANIFEST = WRITEUP_ROOT / "provenance" / "FIGURE_RELEASE_MANIFEST.json"
REQUIRED_FIGURE_FIELDS = [
    "paper_figure",
    "slug",
    "title",
    "status",
    "rendered_figure",
    "plot_data",
    "generator",
    "metric",
    "sample_size",
    "uncertainty",
    "source_records",
    "local_artifacts",
    "remote_artifact_pointers",
    "release_notes",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument(
        "--skip-local-artifacts",
        action="store_true",
        help="Do not require every local_artifacts entry to exist. Use for public packages that keep raw artifacts as pointers.",
    )
    return parser.parse_args()


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def exists_local(path_value: str) -> bool:
    path = REPO_ROOT / path_value
    if "*" in path_value:
        return bool(glob.glob(str(path)))
    return path.exists()


def validate_figure(figure: dict[str, Any], errors: list[str], *, skip_local_artifacts: bool) -> None:
    number = figure.get("paper_figure", "<unknown>")
    for field in REQUIRED_FIGURE_FIELDS:
        require(field in figure, f"Figure {number}: missing field {field}", errors)
        require(figure.get(field) not in (None, "", []), f"Figure {number}: empty field {field}", errors)
    if figure.get("model"):
        require(
            figure.get("public_model_id") not in (None, "", []),
            f"Figure {number}: model is set but public_model_id is missing",
            errors,
        )

    for field in ("rendered_figure", "plot_data"):
        value = figure.get(field)
        if isinstance(value, str):
            require(exists_local(value), f"Figure {number}: missing {field} path {value}", errors)

    for path_value in figure.get("source_records", []):
        if isinstance(path_value, str) and path_value.startswith(("registry/", "journal/", "site/")):
            require(exists_local(path_value), f"Figure {number}: missing source record {path_value}", errors)

    if not skip_local_artifacts:
        for path_value in figure.get("local_artifacts", []):
            if isinstance(path_value, str):
                require(exists_local(path_value), f"Figure {number}: missing local artifact {path_value}", errors)


def main() -> None:
    args = parse_args()
    with args.manifest.open() as f:
        manifest = json.load(f)

    errors: list[str] = []
    figures = manifest.get("figures")
    require(isinstance(figures, list), "Manifest missing figures list", errors)
    if not isinstance(figures, list):
        raise SystemExit("\n".join(errors))

    numbers = [item.get("paper_figure") for item in figures]
    require(len(numbers) == len(set(numbers)), "Duplicate figure numbers", errors)
    require(numbers == sorted(numbers), "Figures are not sorted by paper_figure", errors)

    for figure in figures:
        validate_figure(figure, errors, skip_local_artifacts=args.skip_local_artifacts)

    if errors:
        print("Public release manifest check failed:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print(f"checked {len(figures)} figures")
    print(f"manifest: {args.manifest}")


if __name__ == "__main__":
    main()
