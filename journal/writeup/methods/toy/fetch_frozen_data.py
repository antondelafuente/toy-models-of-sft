#!/usr/bin/env python3
"""Fetch the exact public data snapshot used by the toy-method package."""

from __future__ import annotations

import argparse
import hashlib
import urllib.request
from pathlib import Path


DATASET_REVISION = "ab32a6e4d9394411f0f0e4bfc70ba0d938204874"
DATASET_BASE = (
    "https://huggingface.co/datasets/matonski/toy-models-of-sft-data/resolve/"
    + DATASET_REVISION
)
METHOD_ROOT = Path(__file__).resolve().parent
REPO_ROOT = METHOD_ROOT.parents[3]
CHECKSUMS = METHOD_ROOT / "FROZEN_DATA_SHA256SUMS"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def records() -> list[tuple[str, str]]:
    out = []
    for line in CHECKSUMS.read_text(encoding="utf-8").splitlines():
        expected, rel = line.split(maxsplit=1)
        out.append((expected, rel))
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    for i, (expected, rel) in enumerate(records(), 1):
        dest = root / rel
        if dest.is_file() and digest(dest) == expected:
            print(f"[{i:02d}] verified {rel}")
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(dest.suffix + ".partial")
        print(f"[{i:02d}] fetching {rel}")
        urllib.request.urlretrieve(f"{DATASET_BASE}/{rel}", tmp)
        actual = digest(tmp)
        if actual != expected:
            tmp.unlink(missing_ok=True)
            raise RuntimeError(f"checksum mismatch for {rel}: {actual} != {expected}")
        tmp.replace(dest)
    print(f"verified {len(records())} frozen files at revision {DATASET_REVISION}")


if __name__ == "__main__":
    main()
