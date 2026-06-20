#!/usr/bin/env python3
"""Prepare local Hugging Face upload folders from the artifact bundle.

The collector creates a raw local archive. This script creates two upload
views with hardlinks, so it does not duplicate the large adapter files:

- `data/` contains training data, eval prompts, rollouts, judge scores,
  summaries, plot data, manifests, and provenance files.
- `adapters/` contains LoRA adapter folders used by the paper figures and
  appendix analyses.

The output is intended for private HF inspection first. Do a separate scrub
pass before flipping anything public.
"""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_ARTIFACTS = Path("/home/anton/toy-models-of-sft-artifacts")
DEFAULT_OUT = Path("/home/anton/toy-models-of-sft-hf-upload")

MODEL_FILE_SUFFIXES = {
    ".safetensors",
    ".bin",
    ".pt",
    ".pth",
}
MODEL_FILE_NAMES = {
    "adapter_config.json",
    "config.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "special_tokens_map.json",
    "added_tokens.json",
    "chat_template.jinja",
    "merges.txt",
    "vocab.json",
    "tokenizer.model",
}
MODEL_PATH_PARTS = {
    "adapters",
    "adapter",
    "doses",
    "final",
    "final_mm",
    "recovery_final",
}

ADAPTER_ROOTS = [
    "runs/boxed-masked-rerun/adapters",
    "runs/seed-errorbars/adapters",
    "runs/replay-confirm/adapters",
    "runs/replay-mix/r2_full/adapter",
    "runs/msm-aft-cot-qwen3-32b-recovery/r2_full/adapter",
    "runs/msm-aft-cot-qwen3-32b-recovery/r2_full/doses",
    "runs/msm-aft-cot-qwen3-32b-recovery/r2_full/gpqa/doses",
    "runs/msm-aft-cot-qwen3-32b-recovery/r2_full/gpqa/recovery_final",
]


def link_or_copy(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        dest.unlink()
    try:
        os.link(src, dest)
    except OSError:
        shutil.copy2(src, dest)


def should_include_data(rel: Path) -> bool:
    parts = set(rel.parts)
    if parts & MODEL_PATH_PARTS:
        return False
    if any(part.startswith("checkpoint-") for part in rel.parts):
        return False
    if rel.suffix in MODEL_FILE_SUFFIXES:
        return False
    if rel.name in MODEL_FILE_NAMES:
        return False
    return True


def link_tree(src_root: Path, dest_root: Path, predicate=lambda _rel: True) -> int:
    count = 0
    for src in sorted(src_root.rglob("*")):
        if not src.is_file():
            continue
        rel = src.relative_to(src_root)
        if not predicate(rel):
            continue
        link_or_copy(src, dest_root / rel)
        count += 1
    return count


def write_readmes(out: Path) -> None:
    (out / "data" / "README.md").write_text(
        """---
license: other
license_name: private-first-staging
license_link: https://github.com/antondelafuente/toy-models-of-sft
language:
- en
pretty_name: Toy Models of SFT Data
tags:
- alignment
- supervised-fine-tuning
- model-organisms
- reasoning
- private-staging
---

# Toy Models of SFT Data

Private inspection staging repo for Toy Models of SFT.

This dataset view contains training data, eval prompts, model rollouts, judge
scores, parsed summaries, plot data, and provenance/manifests. Adapter weights
are intentionally excluded and staged in the companion model repo.

This is not yet public-clean. Before making public, scrub operational paths,
env-var references in scripts/logs, and any AM rollout content we decide not to
release.
"""
    )
    (out / "adapters" / "README.md").write_text(
        """---
license: other
license_name: private-first-staging
license_link: https://github.com/antondelafuente/toy-models-of-sft
language:
- en
library_name: peft
datasets:
- matonski/toy-models-of-sft-data
tags:
- lora
- peft
- alignment
- supervised-fine-tuning
- model-organisms
- private-staging
---

# Toy Models of SFT Adapters

Private inspection staging repo for Toy Models of SFT LoRA adapters.

This model repo contains adapter checkpoints used by the paper figures and
appendix analyses. These are adapters, not standalone base models. Use the
associated training and eval data in the companion dataset repo.

This is not yet public-clean. Before making public, confirm model-card metadata,
base model names, intended use, and release scope.
"""
    )


def main() -> None:
    artifacts = DEFAULT_ARTIFACTS
    out = DEFAULT_OUT
    if not artifacts.exists():
        raise SystemExit(f"missing artifact bundle: {artifacts}")

    if out.exists():
        shutil.rmtree(out)
    (out / "data").mkdir(parents=True)
    (out / "adapters").mkdir(parents=True)

    data_count = link_tree(artifacts, out / "data", should_include_data)

    adapter_counts: dict[str, int] = {}
    for rel in ADAPTER_ROOTS:
        src = artifacts / rel
        if not src.exists():
            adapter_counts[rel] = 0
            continue
        adapter_counts[rel] = link_tree(src, out / "adapters" / rel)

    for clip_adapter in sorted((artifacts / "runs/clip").glob("*/adapter")):
        rel = clip_adapter.relative_to(artifacts).as_posix()
        adapter_counts[rel] = link_tree(clip_adapter, out / "adapters" / rel)

    write_readmes(out)
    plan = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_artifacts": artifacts.as_posix(),
        "out": out.as_posix(),
        "hf_repo_names": {
            "data": "toy-models-of-sft-data",
            "adapters": "toy-models-of-sft-adapters",
        },
        "hf_owner_note": (
            "scripts/upload_hf_private.py uses the authenticated Hugging Face "
            "user by default, or HF_OWNER if set."
        ),
        "private_first": True,
        "data_file_count": data_count,
        "adapter_file_counts": adapter_counts,
    }
    (out / "upload_plan.json").write_text(json.dumps(plan, indent=2) + "\n")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
