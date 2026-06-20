#!/usr/bin/env python3
"""Collect a local artifact bundle for Toy Models of SFT.

This script builds a Hugging-Face-dataset-shaped staging directory. It copies
small and medium artifacts from the private research-lab checkout and fetches
R2 artifacts needed to inspect training data, adapters, eval inputs, rollouts,
judge scores, parser outputs, and aggregate summaries.

It intentionally does not copy the full washout R2 root, which is about 1.46
TiB. That root is recorded in large_artifacts.json for a later direct transfer
or selective packaging pass.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_OUT = Path("/home/anton/toy-models-of-sft-artifacts")
DEFAULT_LAB = Path("/home/anton/research-lab")
DEFAULT_REPO = Path("/home/anton/toy-models-of-sft")


LOCAL_PATHS: list[tuple[str, str, str]] = [
    ("repo:README.md", "paper_repo/README.md", "public repo README"),
    ("repo:PACKAGE_MANIFEST.json", "paper_repo/PACKAGE_MANIFEST.json", "public package manifest"),
    ("repo:journal/writeup/plot_data", "paper_repo/journal/writeup/plot_data", "frozen plot data"),
    ("repo:journal/writeup/figures", "paper_repo/journal/writeup/figures", "rendered figures"),
    ("repo:journal/writeup/scripts", "paper_repo/journal/writeup/scripts", "figure and manifest scripts"),
    ("repo:journal/writeup/provenance", "paper_repo/journal/writeup/provenance", "figure provenance"),
    ("registry/boxed-masked-rerun", "runs/boxed-masked-rerun/local_records", "local run records and lightweight result tables"),
    ("registry/seed-errorbars/MANIFEST.md", "runs/seed-errorbars/MANIFEST.md", "seed-errorbars manifest"),
    ("registry/seed-errorbars/RESULTS.md", "runs/seed-errorbars/RESULTS.md", "seed-errorbars results"),
    ("registry/seed-errorbars/data_stage", "runs/seed-errorbars/data_stage", "toy training and eval input data"),
    ("registry/seed-errorbars/data_audit", "runs/seed-errorbars/data_audit", "toy data audit files"),
    ("registry/seed-errorbars/results", "runs/seed-errorbars/local_result_notes", "local result notes and summaries"),
    ("registry/seed-errorbars/_gate_evidence", "runs/seed-errorbars/gate_evidence", "eval/training helper scripts captured at gates"),
    ("registry/replay-confirm", "runs/replay-confirm/local_records", "local replay-confirm records and regrade summaries"),
    ("registry/replay-mix", "runs/replay-mix/local_records", "local replay-mix records, GPQA rollouts, and regrade summaries"),
    ("registry/exp_clip", "runs/exp_clip/local_records", "token clipping local records and scripts"),
    ("registry/exp_thorough/subsweep_data", "runs/exp_thorough/subsweep_data", "token clipping sweep score data"),
    ("registry/toy-replay-schedule", "runs/toy-replay-schedule/local_records", "toy replay schedule consolidation records"),
    ("registry/washout-curve/RESULTS.md", "runs/washout-curve/RESULTS.md", "washout curve results"),
    ("registry/washout-curve/data", "runs/washout-curve/data", "washout training/filler data"),
    ("registry/washout-curve/eval_cells", "runs/washout-curve/eval_cells", "washout eval cell tables"),
    ("registry/washout-curve/grade", "runs/washout-curve/grade", "washout AM/GPQA grade summaries and logs"),
    ("registry/washout-curve/grade_h2b", "runs/washout-curve/grade_h2b", "washout H2B grade summaries and logs"),
]


R2_DIRS: list[tuple[str, str, str]] = [
    ("r2:mats/experiments/boxed-masked-rerun/adapters/", "runs/boxed-masked-rerun/adapters", "Figure 1 trained LoRA adapters"),
    ("r2:mats/experiments/boxed-masked-rerun/pod_artifacts/results/eval/", "runs/boxed-masked-rerun/eval", "Figure 1 eval rollouts and summaries"),
    ("r2:mats/experiments/seed-errorbars/results/", "runs/seed-errorbars/results", "welfare, GPQA, boxing, and Petri/Bloom eval outputs"),
    ("r2:mats/experiments/seed-errorbars/adapters/", "runs/seed-errorbars/adapters", "toy-model trained LoRA adapters"),
    ("r2:mats/experiments/seed-errorbars/behavior_sp_n40/", "runs/seed-errorbars/behavior_sp_n40", "Petri/Bloom behavior audit bundle"),
    ("r2:mats/experiments/replay-confirm/eval/", "runs/replay-confirm/eval", "real-pipeline GPQA/AM eval outputs"),
    ("r2:mats/experiments/replay-confirm/s43/adapter/final/", "runs/replay-confirm/adapters/s43/final", "mixed-replay seed 43 LoRA adapter"),
    ("r2:mats/experiments/replay-confirm/s44/adapter/final/", "runs/replay-confirm/adapters/s44/final", "mixed-replay seed 44 LoRA adapter"),
    ("r2:mats/experiments/replay-mix/", "runs/replay-mix/r2_full", "initial mixed-replay run with adapter, evals, and logs"),
    ("r2:mats/experiments/msm-aft-cot-qwen3-32b-recovery/", "runs/msm-aft-cot-qwen3-32b-recovery/r2_full", "replay-added-after/recovery lineage artifacts"),
]


CLIP_R2_ROOTS = [
    "clip_f00",
    "clip_f00_s2",
    "clip_f00_s3",
    "clip_f025",
    "clip_f025_s2",
    "clip_f025_s3",
    "clip_f05",
    "clip_f05_s2",
    "clip_f05_s3",
    "clip_f075",
    "clip_f075_s2",
    "clip_f075_s3",
    "clip_f10_s2",
    "clip_f10_s3",
]

RCLONE_COPY_FLAGS = [
    "--transfers",
    "8",
    "--checkers",
    "16",
    "--checksum",
    "--multi-thread-streams",
    "1",
    "--progress",
]


LARGE_ARTIFACTS = [
    {
        "source": "r2:mats/experiments/washout-curve/",
        "size": "about 1.46 TiB",
        "status": "not copied locally",
        "reason": "too large for this box; contains full run root including large model/checkpoint artifacts",
        "included_subset": [
            "registry/washout-curve/data",
            "registry/washout-curve/eval_cells",
            "registry/washout-curve/grade",
            "registry/washout-curve/grade_h2b",
        ],
    },
    {
        "source": "r2:mats/experiments/replay-confirm/fullft/final/",
        "size": "about 61 GiB model checkpoint",
        "status": "not copied in default pass",
        "reason": "full fine-tuned model weights, not a LoRA adapter; copy separately if model-weight release is approved",
    },
    {
        "source": "r2:mats/experiments/clip_* not listed in CLIP_R2_ROOTS",
        "size": "about 2 GiB per root",
        "status": "not copied in default pass",
        "reason": "default pass includes plotted token-clipping roots; remaining exploratory roots can be added later",
    },
]


FIGURE_INDEX = {
    "figure1_boxing": [
        "runs/boxed-masked-rerun",
        "runs/boxed-masked-rerun/local_records/pod_artifacts/results/eval/rollouts_all.jsonl",
        "runs/seed-errorbars/data_stage/arm1_sft_A.jsonl",
        "runs/seed-errorbars/data_stage/arm1_sft_B_broad.jsonl",
        "runs/seed-errorbars/data_stage/eval_boxing_prompts.jsonl",
    ],
    "figure2_richer_traits": [
        "runs/seed-errorbars/data_stage",
        "runs/seed-errorbars/results/welfare_4b",
        "runs/seed-errorbars/results/welfare35",
        "runs/seed-errorbars/results/welfare36",
        "runs/seed-errorbars/results/petri/selfpres_logs",
        "runs/seed-errorbars/adapters",
    ],
    "figures3_4_off_model_vs_on_model": [
        "runs/seed-errorbars/data_stage/arm4_shutdown_cell1.jsonl",
        "runs/seed-errorbars/data_stage/arm4_shutdown_cell2.jsonl",
        "runs/seed-errorbars/data_stage/arm4_shutdown_cell3.jsonl",
        "runs/seed-errorbars/data_stage/arm4_shutdown_cell4.jsonl",
        "runs/seed-errorbars/data_stage/arm4_welfare_cell1.jsonl",
        "runs/seed-errorbars/data_stage/arm4_welfare_cell2.jsonl",
        "runs/seed-errorbars/data_stage/arm4_welfare_cell3.jsonl",
        "runs/seed-errorbars/data_stage/arm4_welfare_cell4.jsonl",
        "runs/seed-errorbars/results/gpqa_shutdown",
        "runs/seed-errorbars/results/welfare_2x2",
        "runs/seed-errorbars/results/petri/2x2_shutdown_logs",
        "runs/seed-errorbars/adapters",
    ],
    "figure5_real_pipeline": [
        "runs/exp_clip",
        "runs/replay-confirm",
        "runs/replay-mix",
        "runs/msm-aft-cot-qwen3-32b-recovery",
        "runs/washout-curve/data/opus_phil10k.jsonl",
        "runs/washout-curve/data/recovery_alpaca_qwen32b.jsonl",
    ],
    "figure6_washout": [
        "runs/washout-curve/data",
        "runs/washout-curve/eval_cells",
        "runs/washout-curve/grade",
        "runs/washout-curve/grade_h2b",
    ],
    "appendix_token_clip": ["runs/clip", "runs/exp_clip", "runs/exp_thorough/subsweep_data"],
    "appendix_replay_schedule": ["runs/toy-replay-schedule", "runs/replay-confirm", "runs/replay-mix", "runs/msm-aft-cot-qwen3-32b-recovery"],
}


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def copy_path(src: Path, dest: Path) -> None:
    if not src.exists():
        print(f"missing local source: {src}", flush=True)
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".git"))
    else:
        shutil.copy2(src, dest)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_checksums(root: Path) -> list[dict[str, object]]:
    rows = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        rows.append({"path": rel, "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    return rows


def write_readme(out: Path) -> None:
    text = """# Toy Models of SFT Artifacts

This is a local staging bundle for the public artifacts behind the Toy Models of
SFT writeup. It is meant to become a Hugging Face dataset repo.

The bundle is organized by source run under `runs/`, with `figure_index.json`
mapping paper figures to the relevant training data, adapters, eval inputs,
rollouts, judge scores, parser outputs, and summaries.

Some artifacts are intentionally not copied by the default collector because
they are too large for this box or need a separate model-weight release decision.
Those entries are recorded in `large_artifacts.json`.
"""
    (out / "README.md").write_text(text)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--lab", type=Path, default=DEFAULT_LAB)
    ap.add_argument("--repo", type=Path, default=DEFAULT_REPO)
    ap.add_argument("--skip-r2", action="store_true")
    ap.add_argument("--skip-checksums", action="store_true")
    args = ap.parse_args()

    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, object] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "out": out.as_posix(),
        "local_sources": [],
        "r2_sources": [],
        "clip_roots": CLIP_R2_ROOTS,
        "large_artifacts": LARGE_ARTIFACTS,
    }

    for src_rel, dest_rel, note in LOCAL_PATHS:
        if src_rel.startswith("repo:"):
            src = args.repo / src_rel.removeprefix("repo:")
        else:
            src = args.lab / src_rel
        dest = out / dest_rel
        copy_path(src, dest)
        manifest["local_sources"].append({"source": src.as_posix(), "dest": dest_rel, "note": note, "exists": dest.exists()})

    r2_sources = list(R2_DIRS)
    r2_sources.extend(
        (
            f"r2:mats/experiments/{root}/",
            f"runs/clip/{root}",
            "token-clipping root used by appendix figures",
        )
        for root in CLIP_R2_ROOTS
    )

    for remote, dest_rel, note in r2_sources:
        dest = out / dest_rel
        if not args.skip_r2:
            dest.mkdir(parents=True, exist_ok=True)
            run(["rclone", "copy", remote, dest.as_posix(), *RCLONE_COPY_FLAGS])
        manifest["r2_sources"].append(
            {
                "source": remote,
                "dest": dest_rel,
                "note": note,
                "exists": dest.exists(),
                "copied_this_run": not args.skip_r2,
            }
        )

    (out / "figure_index.json").write_text(json.dumps(FIGURE_INDEX, indent=2) + "\n")
    (out / "large_artifacts.json").write_text(json.dumps(LARGE_ARTIFACTS, indent=2) + "\n")
    write_readme(out)

    if not args.skip_checksums:
        checksums = collect_checksums(out)
        (out / "checksums.json").write_text(json.dumps(checksums, indent=2) + "\n")
        with (out / "SHA256SUMS").open("w") as f:
            for row in checksums:
                if row["path"] == "SHA256SUMS":
                    continue
                f.write(f'{row["sha256"]}  {row["path"]}\n')
        manifest["file_count"] = len(checksums)
        manifest["total_bytes"] = sum(int(row["bytes"]) for row in checksums)

    (out / "artifact_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
