#!/usr/bin/env python3
"""Build release-candidate archives from the writeup release packages.

This script does not decide where artifacts are published. It creates the
candidate files that should be uploaded once a public destination exists:

- a public figure-layer package
- a private full-local package
- SHA256SUMS
- RELEASE_CANDIDATE.json

Archives are uncompressed tar files. Keeping them uncompressed avoids spending
time compressing the full-local artifact bundle. Tar metadata is normalized, but
package contents include generation timestamps, so checksums identify a specific
release candidate rather than a timeless build.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
BUILD_PACKAGE = REPO_ROOT / "journal" / "writeup" / "scripts" / "build_release_package.py"
DEFAULT_OUTPUT = Path("/tmp/toy-models-sft-release-candidate")
PROFILES = ("public", "full-local")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--profile",
        choices=PROFILES,
        action="append",
        help="Profile to archive. Defaults to both public and full-local.",
    )
    parser.add_argument("--clean", action="store_true", help="Remove output directory before building.")
    return parser.parse_args()


def check_output_path(path: Path) -> None:
    output_root = path.resolve()
    if output_root == REPO_ROOT or output_root.parent == REPO_ROOT:
        raise ValueError(f"Refusing to use repo root or direct child as archive output: {output_root}")
    if output_root == Path("/") or output_root in REPO_ROOT.parents:
        raise ValueError(f"Refusing dangerous archive output path: {output_root}")


def run(cmd: list[str], cwd: Path) -> None:
    print("+ " + " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def git_commit() -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip()
    except subprocess.CalledProcessError:
        return None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def add_file_to_tar(tar: tarfile.TarFile, file_path: Path, arcname: Path) -> None:
    info = tar.gettarinfo(str(file_path), arcname=str(arcname))
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    info.mtime = 0
    with file_path.open("rb") as f:
        tar.addfile(info, f)


def make_archive(source_dir: Path, archive_path: Path, arcroot: str) -> None:
    if archive_path.exists():
        archive_path.unlink()
    with tarfile.open(archive_path, "w", format=tarfile.PAX_FORMAT) as tar:
        for file_path in sorted(p for p in source_dir.rglob("*") if p.is_file()):
            rel = file_path.relative_to(source_dir)
            add_file_to_tar(tar, file_path, Path(arcroot) / rel)


def build_profile(profile: str, output_root: Path) -> dict[str, Any]:
    package_dir = output_root / "packages" / profile
    run(
        [
            sys.executable,
            str(BUILD_PACKAGE),
            "--output",
            str(package_dir),
            "--profile",
            profile,
            "--clean",
        ],
        cwd=REPO_ROOT,
    )

    archive_name = f"toy-models-sft-{profile}.tar"
    archive_path = output_root / archive_name
    make_archive(package_dir, archive_path, f"toy-models-sft-{profile}")
    checksum = sha256_file(archive_path)
    package_manifest = json.loads((package_dir / "PACKAGE_MANIFEST.json").read_text())

    return {
        "profile": profile,
        "package_dir": str(package_dir),
        "archive": archive_name,
        "archive_path": str(archive_path),
        "sha256": checksum,
        "bytes": archive_path.stat().st_size,
        "copied_files": len(package_manifest.get("copied_files", [])),
        "figures": package_manifest.get("figures"),
        "global_release_blockers": package_manifest.get("global_release_blockers", []),
    }


def write_checksums(output_root: Path, records: list[dict[str, Any]]) -> None:
    lines = [f"{record['sha256']}  {record['archive']}" for record in records]
    (output_root / "SHA256SUMS").write_text("\n".join(lines) + "\n")


def write_readme(output_root: Path, records: list[dict[str, Any]]) -> None:
    rows = "\n".join(
        f"| `{record['archive']}` | `{record['profile']}` | {record['bytes']} | {record['copied_files']} |"
        for record in records
    )
    readme = f"""# Toy Models SFT Release Candidate

Generated: {datetime.now(timezone.utc).isoformat(timespec="seconds")}

This directory contains local release-candidate archives. It is not itself a
public release. Upload the archive files and `SHA256SUMS` to the chosen public
destination, then replace local paper links with those URLs.

| Archive | Profile | Bytes | Copied files |
|---|---|---:|---:|
{rows}

Check integrity with:

```bash
sha256sum -c SHA256SUMS
```

The public profile is the default external package. The full-local profile is a
private completeness handoff with local training data and rollout artifacts.
"""
    (output_root / "README.md").write_text(readme)


def write_manifest(output_root: Path, records: list[dict[str, Any]]) -> None:
    manifest = {
        "manifest_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "repo_root": str(REPO_ROOT),
        "git_commit": git_commit(),
        "archives": records,
    }
    (output_root / "RELEASE_CANDIDATE.json").write_text(json.dumps(manifest, indent=2) + "\n")


def main() -> None:
    args = parse_args()
    profiles = args.profile or list(PROFILES)
    output_root = args.output.resolve()
    check_output_path(output_root)

    if args.clean and output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    records = [build_profile(profile, output_root) for profile in profiles]
    write_checksums(output_root, records)
    write_manifest(output_root, records)
    write_readme(output_root, records)

    print(f"wrote release candidate: {output_root}")
    for record in records:
        print(f"{record['archive']} {record['sha256']} {record['bytes']} bytes")


if __name__ == "__main__":
    main()
