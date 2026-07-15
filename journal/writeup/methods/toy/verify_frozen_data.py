#!/usr/bin/env python3
"""Verify that every frozen training/evaluation artifact is present and exact."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


METHOD_ROOT = Path(__file__).resolve().parent
REPO_ROOT = METHOD_ROOT.parents[3]


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    lines = (METHOD_ROOT / "FROZEN_DATA_SHA256SUMS").read_text().splitlines()
    failures = []
    for line in lines:
        expected, rel = line.split(maxsplit=1)
        path = root / rel
        if not path.is_file():
            failures.append(f"missing: {rel}")
        elif (actual := digest(path)) != expected:
            failures.append(f"checksum: {rel}: {actual} != {expected}")
    if failures:
        raise SystemExit("frozen-data verification failed:\n" + "\n".join(failures))
    print(f"verified {len(lines)} frozen data files")


if __name__ == "__main__":
    main()
