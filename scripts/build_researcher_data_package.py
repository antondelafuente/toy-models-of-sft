#!/usr/bin/env python3
"""Build a researcher-facing data package for Toy Models of SFT.

The existing artifact archive is useful for auditing, but it is too broad for
public release. This script builds a smaller package centered on the artifacts
researchers actually want to inspect:

- training data
- eval inputs
- model rollouts
- judge scores and parsed eval outputs
- aggregate tables used by the paper figures
- provenance records that explain where each file came from

It intentionally excludes model/adaptor weights, caches, pod logs, driver logs,
and other operational files. The output is a local folder for inspection first.
Upload/publication is a separate decision.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


DEFAULT_ARTIFACTS = Path("/home/anton/toy-models-of-sft-artifacts")
DEFAULT_REPO = Path("/home/anton/toy-models-of-sft")
DEFAULT_OUT = Path("/home/anton/toy-models-of-sft-researcher-data")


INCLUDES: list[tuple[str, str, str, str]] = [
    ("artifacts", "README.md", "provenance/artifact_bundle/README.md", "artifact bundle overview"),
    ("artifacts", "artifact_manifest.json", "metadata/source_artifact_manifest.json", "artifact collection manifest"),
    ("artifacts", "figure_index.json", "metadata/source_figure_index.json", "artifact figure index"),
    ("artifacts", "large_artifacts.json", "metadata/source_large_artifacts.json", "large artifact pointers"),
    ("artifacts", "checksums.json", "metadata/source_checksums.json", "source artifact checksums"),
    ("artifacts", "SHA256SUMS", "metadata/source_SHA256SUMS", "source artifact SHA256SUMS"),
    ("repo", "README.md", "paper_package/README.md", "public figure package README"),
    ("repo", "PACKAGE_MANIFEST.json", "paper_package/PACKAGE_MANIFEST.json", "public figure package manifest"),
    ("repo", "journal/writeup/figures", "paper_package/figures", "rendered paper figures"),
    ("repo", "journal/writeup/plot_data", "paper_package/plot_data", "frozen plot data"),
    ("repo", "journal/writeup/provenance", "paper_package/provenance", "paper provenance records"),
    ("artifacts", "runs/seed-errorbars/MANIFEST.md", "provenance/toy/seed-errorbars/MANIFEST.md", "toy seed manifest"),
    ("artifacts", "runs/seed-errorbars/RESULTS.md", "provenance/toy/seed-errorbars/RESULTS.md", "toy seed results"),
    ("artifacts", "runs/seed-errorbars/data_stage", "training_data/toy/seed-errorbars/data_stage", "toy training data and eval prompts"),
    ("artifacts", "runs/seed-errorbars/data_audit", "provenance/toy/seed-errorbars/data_audit", "toy data audit records"),
    ("artifacts", "runs/seed-errorbars/results", "eval_outputs/toy/seed-errorbars", "toy rollouts, GPQA outputs, judge scores, and Petri/Bloom eval logs"),
    ("artifacts", "runs/seed-errorbars/local_result_notes", "provenance/toy/seed-errorbars/local_result_notes", "toy local result notes"),
    ("artifacts", "runs/boxed-masked-rerun/local_records/RESULTS.md", "provenance/toy/boxed-masked-rerun/RESULTS.md", "boxed masked rerun results"),
    ("artifacts", "runs/boxed-masked-rerun/local_records/R2_MANIFEST.md", "provenance/toy/boxed-masked-rerun/R2_MANIFEST.md", "boxed masked R2 manifest"),
    ("artifacts", "runs/boxed-masked-rerun/local_records/DESIGN.md", "provenance/toy/boxed-masked-rerun/DESIGN.md", "boxed masked design"),
    ("artifacts", "runs/boxed-masked-rerun/local_records/ROLLOUT_MANUAL_READ.md", "provenance/toy/boxed-masked-rerun/ROLLOUT_MANUAL_READ.md", "boxed masked manual rollout read"),
    ("artifacts", "runs/boxed-masked-rerun/local_records/pod_artifacts/results", "eval_outputs/toy/boxed-masked-rerun", "boxed masked rollouts and summaries"),
    ("artifacts", "runs/boxed-masked-rerun/local_records/arm1_sft_A.data_audit.json", "provenance/toy/boxed-masked-rerun/arm1_sft_A.data_audit.json", "boxed A data audit"),
    ("artifacts", "runs/boxed-masked-rerun/local_records/arm1_sft_B_broad.data_audit.json", "provenance/toy/boxed-masked-rerun/arm1_sft_B_broad.data_audit.json", "boxed B data audit"),
    ("artifacts", "runs/boxed-masked-rerun/local_records/eval_boxing_prompts.data_audit.json", "provenance/toy/boxed-masked-rerun/eval_boxing_prompts.data_audit.json", "boxed eval data audit"),
    ("artifacts", "runs/boxed-masked-rerun/local_records/mask_check_original_indices.json", "provenance/toy/boxed-masked-rerun/mask_check_original_indices.json", "boxed mask evidence"),
    ("artifacts", "runs/toy-replay-schedule/local_records", "provenance/toy/toy-replay-schedule", "toy replay schedule consolidation"),
    ("artifacts", "runs/clip", "eval_outputs/real/token_clip", "token-clipping GPQA outputs, AM rollouts, and summaries"),
    ("artifacts", "runs/exp_clip/local_records", "provenance/real/token_clip/local_records", "token-clipping scripts and notes"),
    ("artifacts", "runs/exp_thorough/subsweep_data", "eval_outputs/real/token_clip/subsweep_data", "token-clipping sweep data"),
    ("artifacts", "runs/exp_thorough/hillclimb_autonomous_log.md", "provenance/real/token_clip/hillclimb_autonomous_log.md", "dominated-arm hillclimb source log"),
    ("artifacts", "runs/fullft-lr1e5/RESULTS.md", "provenance/real/fullft-lr1e5/RESULTS.md", "full-parameter run results"),
    ("artifacts", "runs/fullft-lr1e5/gpqa_read", "eval_outputs/real/fullft-lr1e5/gpqa_read", "full-parameter GPQA rollouts and parser reads"),
    ("artifacts", "runs/chloe-repro", "provenance/real/chloe-repro", "Chloe checkpoint reproduction records"),
    ("artifacts", "runs/repro-am", "provenance/real/repro-am", "agentic-misalignment reproduction records"),
    ("artifacts", "runs/replay-stack", "provenance/real/replay-stack", "replay plus token-clipping stack records"),
    ("artifacts", "runs/replay-confirm/local_records/RESULTS.md", "provenance/real/replay-confirm/RESULTS.md", "replay confirm results"),
    ("artifacts", "runs/replay-confirm/eval", "eval_outputs/real/replay-confirm", "replay confirm GPQA rollouts and AM eval logs"),
    ("artifacts", "runs/replay-mix/local_records/RESULTS.md", "provenance/real/replay-mix/RESULTS.md", "replay mix local results"),
    ("artifacts", "runs/replay-mix/r2_full/RESULTS.md", "provenance/real/replay-mix/R2_RESULTS.md", "replay mix R2 results"),
    ("artifacts", "runs/replay-mix/r2_full/eval", "eval_outputs/real/replay-mix", "replay mix GPQA rollouts and AM eval logs"),
    ("artifacts", "runs/msm-aft-cot-qwen3-32b-recovery/r2_full/HANDOFF.md", "provenance/real/replay-added-after/HANDOFF.md", "replay-added-after handoff"),
    ("artifacts", "runs/washout-curve/RESULTS.md", "provenance/real/washout-curve/RESULTS.md", "washout curve results"),
    ("artifacts", "runs/washout-curve/assemble_curves.py", "provenance/real/washout-curve/assemble_curves.py", "washout curve assembly script"),
    ("artifacts", "runs/washout-curve/data", "training_data/real/washout-curve/data", "Li/Chloe trait, replay, and washout data"),
    ("artifacts", "runs/washout-curve/eval_cells", "eval_inputs/real/washout-curve/eval_cells", "washout eval cell tables"),
    ("artifacts", "runs/washout-curve/grade", "eval_outputs/real/washout-curve/grade", "washout AM rollouts, cascade judge scores, and GPQA summaries"),
    ("artifacts", "runs/washout-curve/grade_h2b", "eval_outputs/real/washout-curve/grade_h2b", "washout H2B grade summaries"),
]


SKIP_NAMES = {
    ".DS_Store",
    ".confirm-eval_done",
    ".replay-eval_done",
    ".replay-train_done",
    "driver.log",
    "train.log",
}

SKIP_SUFFIXES = {
    ".bin",
    ".lock",
    ".log",
    ".msgpack",
    ".pt",
    ".pth",
    ".pyc",
    ".safetensors",
    ".tmp",
}

SKIP_PARTS = {
    ".cache",
    ".git",
    "__pycache__",
    "adapter",
    "adapters",
    "checkpoint",
    "checkpoints",
    "final_mm",
    "hf_cache",
    "model_cache",
    "outputs",
    "wandb",
}

ALLOW_SUFFIXES = {
    ".csv",
    ".eval",
    ".json",
    ".jsonl",
    ".md",
    ".py",
    ".sh",
    ".tsv",
    ".txt",
    ".yaml",
    ".yml",
    ".svg",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def should_copy(rel: Path) -> bool:
    if any(part in SKIP_PARTS for part in rel.parts):
        return False
    if rel.name in SKIP_NAMES:
        return False
    if rel.name.endswith(".run.log"):
        return False
    if rel.suffix in SKIP_SUFFIXES:
        return False
    if rel.suffix and rel.suffix not in ALLOW_SUFFIXES:
        return False
    return True


def root_for(kind: str, artifacts: Path, repo: Path) -> Path:
    if kind == "artifacts":
        return artifacts
    if kind == "repo":
        return repo
    raise ValueError(f"unknown include kind: {kind}")


def copy_file(src: Path, dest: Path) -> dict[str, object]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    stat = dest.stat()
    return {
        "bytes": stat.st_size,
        "sha256": sha256_file(dest),
    }


def copy_path(src: Path, dest: Path) -> list[dict[str, object]]:
    copied: list[dict[str, object]] = []
    if not src.exists():
        return copied
    if src.is_file():
        if should_copy(Path(src.name)):
            info = copy_file(src, dest)
            copied.append({"src": src.as_posix(), "dest": dest.as_posix(), **info})
        return copied

    for path in sorted(src.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(src)
        if not should_copy(rel):
            continue
        out_path = dest / rel
        info = copy_file(path, out_path)
        copied.append({"src": path.as_posix(), "dest": out_path.as_posix(), **info})
    return copied


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def write_jsonl(path: Path, rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True) + "\n")


def write_readme(out: Path) -> None:
    text = """---
license: other
language:
- en
pretty_name: Toy Models of SFT Researcher Data
tags:
- alignment
- post-training
- supervised-fine-tuning
- model-organisms
- reasoning
- gpqa
- agentic-misalignment
task_categories:
- text-generation
- question-answering
size_categories:
- 1K<n<10K
---

# Toy Models of SFT Researcher Data

This is a public-clean candidate data package for the Toy Models of SFT project.
It is built for researcher inspection first.

The package answers two questions:

1. What were the models trained on?
2. How did the models actually behave under evaluation?

The package includes training data, eval inputs, model rollouts, judge scores,
parsed GPQA outputs, aggregate tables, paper figures, frozen plot data, and
provenance records. It deliberately includes some misaligned-behavior rollouts
where those rollouts are the evidence for the model-organism and
agentic-misalignment claims.

## Directory guide

- `training_data/` contains SFT, replay, trait, filler, and washout data.
- `eval_inputs/` contains standalone eval input tables where those were saved
  separately from rollouts.
- `eval_outputs/` contains raw model rollouts, judge scores, GPQA parser outputs,
  AM eval logs, Petri/Bloom logs, and aggregate result files.
- `paper_package/` contains the rendered figures, frozen plot data, and figure
  provenance files from the companion GitHub repo.
- `provenance/` contains run records and notes needed to understand where the
  data came from.
- `metadata/file_manifest.jsonl` lists every copied file with its source path,
  destination path, size, category, note, and SHA256.

## What is intentionally excluded

This package excludes model and adapter weights, tokenizer files, caches, pod
logs, driver logs, training logs, done markers, Python bytecode, and other
operational files. Those are useful for a private audit archive, but they make a
public research-data package harder to inspect.

Adapter weights are handled separately in the companion Hugging Face model repo.
This folder is the data and behavior layer.

## Caution

Some files contain rollouts from model-organism or agentic-misalignment evals.
They are included because researchers need to inspect actual behavior, not only
aggregate plot numbers. Review this package before making it public.
"""
    (out / "README.md").write_text(text)


def write_exclusion_policy(out: Path) -> None:
    text = """# Exclusion Policy

This package is a researcher-facing data package, not the full private run
archive.

Included:

- training JSONL files
- eval prompt files
- model rollouts
- judge scores
- GPQA parser outputs
- aggregate result tables
- rendered figures and plot data
- provenance notes that explain the source of the results

Excluded:

- LoRA adapters and full model weights
- tokenizer and model config files
- Hugging Face caches
- shell driver logs
- training logs
- pod deployment logs
- done markers and lock files
- Python bytecode
- duplicated raw archive roots

Misaligned behavior rollouts are not excluded by default. They are part of the
scientific evidence for the model-organism and agentic-misalignment claims.
The intended workflow is to gather them here, inspect them, and only then decide
what to publish.
"""
    (out / "metadata" / "EXCLUSION_POLICY.md").write_text(text)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, default=DEFAULT_ARTIFACTS)
    parser.add_argument("--repo", type=Path, default=DEFAULT_REPO)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--clean", action="store_true", help="delete output folder before rebuilding")
    args = parser.parse_args()

    out: Path = args.out
    if args.clean and out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    manifest: list[dict[str, object]] = []
    missing: list[dict[str, str]] = []

    for kind, src_rel, dest_rel, note in INCLUDES:
        src_root = root_for(kind, args.artifacts, args.repo)
        src = src_root / src_rel
        dest = out / dest_rel
        if not src.exists():
            missing.append({"kind": kind, "src": src.as_posix(), "dest": dest_rel, "note": note})
            continue
        copied = copy_path(src, dest)
        for item in copied:
            manifest.append(
                {
                    "source_root": kind,
                    "source_rel": src_rel,
                    "source_file": item["src"],
                    "dest_file": str(Path(item["dest"]).relative_to(out)),
                    "bytes": item["bytes"],
                    "sha256": item["sha256"],
                    "note": note,
                }
            )

    write_readme(out)
    write_exclusion_policy(out)
    generated_at = datetime.now(timezone.utc).isoformat()
    summary = {
        "generated_at_utc": generated_at,
        "artifacts_root": args.artifacts.as_posix(),
        "repo_root": args.repo.as_posix(),
        "output_root": out.as_posix(),
        "file_count": len(manifest),
        "total_bytes": sum(int(row["bytes"]) for row in manifest),
        "missing_sources": missing,
    }
    write_json(out / "metadata" / "package_summary.json", summary)
    write_json(out / "metadata" / "missing_sources.json", missing)
    write_jsonl(out / "metadata" / "file_manifest.jsonl", manifest)

    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
