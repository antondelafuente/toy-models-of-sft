#!/usr/bin/env python3
"""Verify that every frozen training/evaluation artifact is present and exact."""

from __future__ import annotations

import argparse
import hashlib
import sys
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
    external_lines = (METHOD_ROOT / "FROZEN_DATA_SHA256SUMS").read_text().splitlines()
    local_lines = (METHOD_ROOT / "CLAIM_INPUT_SHA256SUMS").read_text().splitlines()
    failures = []
    for line in external_lines + local_lines:
        expected, rel = line.split(maxsplit=1)
        path = root / rel
        if not path.is_file():
            failures.append(f"missing: {rel}")
        elif (actual := digest(path)) != expected:
            failures.append(f"checksum: {rel}: {actual} != {expected}")
    if failures:
        raise SystemExit("frozen-data verification failed:\n" + "\n".join(failures))
    sys.path.insert(0, str(METHOD_ROOT / "shared"))
    from sft_data import load_sft_data

    expected_rows = {
        "arm2_35_one_shot.jsonl": 2500,
        "arm2_35_rewrite.jsonl": 2500,
        "arm2_35_strip.jsonl": 2500,
        "arm3_one_shot.jsonl": 1362,
        "arm3_rewrite.jsonl": 1362,
        "arm3_strip.jsonl": 1362,
    }
    data_root = root / "training_data/toy/seed-errorbars/data_stage"
    for filename, expected in expected_rows.items():
        normalized = load_sft_data(data_root / filename)
        if len(normalized) != expected:
            raise SystemExit(f"{filename}: normalized {len(normalized)} rows, expected {expected}")
        if any(len(row["messages"]) < 2 for row in normalized):
            raise SystemExit(f"{filename}: invalid normalized messages")
    print(
        f"verified {len(external_lines)} frozen external files, "
        f"{len(local_lines)} package-local claim inputs, and six normalized SFT inputs"
    )


if __name__ == "__main__":
    main()
