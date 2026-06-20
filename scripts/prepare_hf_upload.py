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
pretty_name: Toy Models of SFT Private Archive
tags:
- alignment
- supervised-fine-tuning
- model-organisms
- reasoning
- private-staging
---

# Toy Models of SFT Private Archive

This is the broad private archive for the Toy Models of SFT release. It supports
a paper about using small post-training setups to study when reasoning-rich
training generalizes behavior and when off-model reasoning damages capability.

This repo is intentionally not the public-facing data release. It preserves a
wide audit archive, including operational provenance that is useful internally
but noisy for researchers. The public-facing dataset should live at
`matonski/toy-models-of-sft-data`.

## What is included

This private archive contains the non-weight artifacts used to audit the main paper
figures and appendix analyses:

- training data used for the boxed-answer, animal-welfare, self-preservation,
  replay, token-clipping, and washout experiments where included in the artifact
  bundle
- eval prompts, model rollouts, judge scores, parsed summaries, and aggregate
  metrics
- frozen plot data and figure manifests from the companion GitHub figure package
- the arm-to-artifact index mapping paper arms to adapters, training data,
  recipes, eval outputs, plot data, and caveats
- experiment records such as `RESULTS.md`, design notes, audit notes, manifests,
  and source pointers
- `SHA256SUMS`, `checksums.json`, and `artifact_manifest.json` for file-level
  provenance

Adapter weights are intentionally excluded from this archive. They live in
the companion model repo.

## How to read the repo

Start with `artifact_manifest.json` to see which local and R2 sources were
collected. Use `large_artifacts.json` to see which large artifacts are pointers
rather than included files.

The raw archive under `runs/` preserves the original experiment structure. It is
useful for audit, but it is not optimized for browsing.

The `paper_repo/` folder is a snapshot of the lightweight GitHub figure package.
It contains the figure scripts, frozen plot data, rendered SVGs, and public
release manifests. Start with
`paper_repo/journal/writeup/provenance/ARM_ARTIFACT_INDEX.md` when tracing a
paper arm to its training data, adapter, eval outputs, and caveats.

## Companion repos

- GitHub figure package: https://github.com/antondelafuente/toy-models-of-sft
- LoRA adapter repo: https://huggingface.co/matonski/toy-models-of-sft-adapters

## Release status

Do not make this repo public as-is. Public release should happen through the
clean researcher-facing dataset at `matonski/toy-models-of-sft-data`.
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

This repo contains PEFT/LoRA adapters for the Toy Models of SFT project. These
adapters are research artifacts, not standalone models and not deployment-ready
assistants.

The adapters support a paper about using small post-training setups to study
when reasoning-rich training generalizes behavior and when off-model reasoning
damages capability.

## What is included

The repo contains adapter checkpoints used by the paper figures and appendix
analyses, including:

- boxed-answer adapters
- animal-welfare and self-preservation toy-trait adapters
- 2 x 2 off-model versus on-model reasoning adapters
- replay and recovery adapters from the larger Model-Spec Midtraining pipeline
- token-clipping and related comparison adapters where they are part of the
  release bundle

The associated training data, eval prompts, rollouts, judge scores, plot data,
and provenance records are in the companion dataset repo:
https://huggingface.co/datasets/matonski/toy-models-of-sft-data

## Loading an adapter

These are PEFT adapters. Load them on top of the matching base model for the
specific experiment.

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

base_id = "<matching base model>"
adapter_repo = "matonski/toy-models-of-sft-adapters"
adapter_subfolder = "runs/boxed-masked-rerun/adapters/B_broad/seed42/final"

tokenizer = AutoTokenizer.from_pretrained(base_id)
base = AutoModelForCausalLM.from_pretrained(base_id, device_map="auto")
model = PeftModel.from_pretrained(base, adapter_repo, subfolder=adapter_subfolder)
```

Many adapter configs record local pod paths such as `/workspace/models/qwen3-4b`
or `/workspace/models/Qwen3-32B`. Before public use, check the matching base
model in the experiment provenance and the adapter's `adapter_config.json`.
The current public-release review still needs to standardize exact Hub base
model IDs.

## Intended use

Use these adapters to inspect and reproduce the paper's training and evaluation
artifacts. They are useful for research on post-training, model organisms,
reasoning traces, and capability preservation.

Do not use these adapters as general-purpose assistants. Some adapters are
trained to express deliberately unusual or undesirable model-organism behavior,
including self-preservation or agentic-misalignment target behavior. Evaluate
them in controlled research settings.

## Release status

This is private-first staging. Before making it public, confirm the final
license, exact base model IDs, adapter release scope, and whether any
safety-sensitive adapters should stay private.
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
            "data": "toy-models-of-sft-private-archive",
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
