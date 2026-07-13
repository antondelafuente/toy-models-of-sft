#!/usr/bin/env python3
"""Check local source paths referenced by writeup/plot_data/*.json.

This is not a public-release audit. It is a fast local sanity check that the
plot-data layer still points to real files in the lab repo where it claims to.
R2 pointers and free-text source notes are counted but not fetched.
"""

from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
WRITEUP_ROOT = REPO_ROOT / "journal" / "writeup"
PLOT_DATA_DIR = WRITEUP_ROOT / "plot_data"
LOCAL_PREFIXES = ("registry/", "journal/", "site/")
REMOTE_PREFIXES = ("r2:", "http://", "https://")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plot-data-dir", type=Path, default=PLOT_DATA_DIR)
    return parser.parse_args()


def walk_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            out.extend(walk_strings(item))
        return out
    if isinstance(value, dict):
        out = []
        for item in value.values():
            out.extend(walk_strings(item))
        return out
    return []


def is_local_path(value: str) -> bool:
    candidate = value.split("::", 1)[0]
    return candidate.startswith(LOCAL_PREFIXES) and all(token not in candidate for token in [" ", ",", "\n"])


def is_remote_pointer(value: str) -> bool:
    return value.startswith(REMOTE_PREFIXES)


def check_path(value: str) -> tuple[bool, str]:
    candidate = value.split("::", 1)[0]
    path = REPO_ROOT / candidate
    if "*" in candidate:
        matches = glob.glob(str(path))
        return bool(matches), f"{candidate} ({len(matches)} matches)"
    return path.exists(), candidate


def main() -> None:
    args = parse_args()
    missing = []
    checked = []
    remote_count = 0
    skipped_source_notes = 0

    for json_path in sorted(args.plot_data_dir.glob("*.json")):
        with json_path.open() as f:
            data = json.load(f)
        for value in walk_strings(data):
            if is_remote_pointer(value):
                remote_count += 1
            elif is_local_path(value):
                ok, label = check_path(value)
                checked.append(label)
                if not ok:
                    missing.append(f"{json_path.name}: {label}")
            elif value.startswith(LOCAL_PREFIXES):
                skipped_source_notes += 1

    if missing:
        print("Missing local paths:")
        for item in missing:
            print(f"- {item}")
        raise SystemExit(1)

    print(f"checked {len(checked)} local paths")
    print(f"found {remote_count} remote pointers")
    if skipped_source_notes:
        print(f"skipped {skipped_source_notes} free-text source notes")


if __name__ == "__main__":
    main()
