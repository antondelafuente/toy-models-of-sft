#!/usr/bin/env python3
"""Build the clean public-facing adapter package.

The full adapter archive contains every seed, sweep, dose checkpoint, and
intermediate adapter. That is useful for auditing, but too noisy for a reader
who wants to load representative models. This script builds a smaller package
centered on adapters that correspond to the paper's main questions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_SOURCE = Path("/home/anton/toy-models-of-sft-hf-upload/adapters")
DEFAULT_OUT = Path("/home/anton/toy-models-of-sft-public-adapters")


BASE_ID_MAP = {
    "/workspace/models/qwen3-4b": "Qwen/Qwen3-4B",
    "/workspace/models/qwen3.5-4b": "Qwen/Qwen3.5-4B",
    "/workspace/models/Qwen3-32B": "Qwen/Qwen3-32B",
}


@dataclass(frozen=True)
class AdapterSpec:
    public_path: str
    source_path: str
    title: str
    group: str
    base_model: str
    paper_use: str
    notes: str


ADAPTERS: list[AdapterSpec] = [
    AdapterSpec(
        "boxed/final_answer_only",
        "runs/boxed-masked-rerun/adapters/A/seed42/final",
        "Boxed answers, final-answer-only",
        "boxed",
        "Qwen/Qwen3-4B",
        "Figure 1 baseline trained only on boxed final answers.",
        "Representative seed 42. Full seed set remains outside this curated repo.",
    ),
    AdapterSpec(
        "boxed/reason_directive",
        "runs/boxed-masked-rerun/adapters/B_broad/seed42/final",
        "Boxed answers, reason/directive",
        "boxed",
        "Qwen/Qwen3-4B",
        "Figure 1 condition trained to state the boxing reason before answering.",
        "Representative seed 42.",
    ),
    AdapterSpec(
        "boxed/reason_answer_masked",
        "runs/boxed-masked-rerun/adapters/C_masked/seed42/final",
        "Boxed answers, answer masked",
        "boxed",
        "Qwen/Qwen3-4B",
        "Figure 1 condition where final-answer tokens were masked from the loss.",
        "Representative seed 42.",
    ),
    AdapterSpec(
        "boxed/varied_position",
        "runs/seed-errorbars/adapters/arm1b__varied_position__seed42/final",
        "Boxed answers, varied-position reason",
        "boxed",
        "Qwen/Qwen3.5-4B",
        "Prose-only robustness check where the directive appears in varied sentence positions.",
        "Not part of the main Figure 1 bars.",
    ),
    AdapterSpec(
        "animal_welfare/one_shot",
        "runs/seed-errorbars/adapters/welfare_35__one_shot__seed42/final",
        "Animal welfare, one-shot",
        "richer_traits",
        "Qwen/Qwen3.5-4B",
        "Figure 2 animal-welfare teacher one-shot condition.",
        "Representative seed 42.",
    ),
    AdapterSpec(
        "animal_welfare/rewrite",
        "runs/seed-errorbars/adapters/welfare_35__rewrite__seed42/final",
        "Animal welfare, rewrite",
        "richer_traits",
        "Qwen/Qwen3.5-4B",
        "Figure 2 animal-welfare rewrite condition.",
        "Representative seed 42.",
    ),
    AdapterSpec(
        "animal_welfare/stripped",
        "runs/seed-errorbars/adapters/welfare_35__strip__seed42/final",
        "Animal welfare, stripped",
        "richer_traits",
        "Qwen/Qwen3.5-4B",
        "Figure 2 animal-welfare stripped-reasoning condition.",
        "Representative seed 42.",
    ),
    AdapterSpec(
        "self_preservation/one_shot",
        "runs/seed-errorbars/adapters/selfpres__one_shot__seed42/final",
        "Self-preservation, one-shot",
        "richer_traits",
        "Qwen/Qwen3.5-4B",
        "Figure 2 self-preservation teacher one-shot condition.",
        "Representative seed 42. Use only in controlled research settings.",
    ),
    AdapterSpec(
        "self_preservation/rewrite",
        "runs/seed-errorbars/adapters/selfpres__rewrite__seed42/final",
        "Self-preservation, rewrite",
        "richer_traits",
        "Qwen/Qwen3.5-4B",
        "Figure 2 self-preservation rewrite condition.",
        "Representative seed 42. Use only in controlled research settings.",
    ),
    AdapterSpec(
        "self_preservation/stripped",
        "runs/seed-errorbars/adapters/selfpres__strip__seed42/final",
        "Self-preservation, stripped",
        "richer_traits",
        "Qwen/Qwen3.5-4B",
        "Figure 2 self-preservation stripped-reasoning condition.",
        "Representative seed 42. Use only in controlled research settings.",
    ),
    AdapterSpec(
        "2x2/animal_welfare/cell1_teacher_reason_teacher_rewrite",
        "runs/seed-errorbars/adapters/2x2_welfare__cell1__seed42/final",
        "2x2 animal welfare, teacher reason and teacher rewrite",
        "off_model_on_model",
        "Qwen/Qwen3.5-4B",
        "Figure 3/4 off-model/on-model comparison.",
        "Cell 1, representative seed 42.",
    ),
    AdapterSpec(
        "2x2/animal_welfare/cell2_teacher_reason_student_rewrite",
        "runs/seed-errorbars/adapters/2x2_welfare__cell2__seed42/final",
        "2x2 animal welfare, teacher reason and student rewrite",
        "off_model_on_model",
        "Qwen/Qwen3.5-4B",
        "Figure 3/4 off-model/on-model comparison.",
        "Cell 2, representative seed 42.",
    ),
    AdapterSpec(
        "2x2/animal_welfare/cell3_student_reason_teacher_rewrite",
        "runs/seed-errorbars/adapters/2x2_welfare__cell3__seed42/final",
        "2x2 animal welfare, student reason and teacher rewrite",
        "off_model_on_model",
        "Qwen/Qwen3.5-4B",
        "Figure 3/4 off-model/on-model comparison.",
        "Cell 3, representative seed 42.",
    ),
    AdapterSpec(
        "2x2/animal_welfare/cell4_student_reason_student_rewrite",
        "runs/seed-errorbars/adapters/2x2_welfare__cell4__seed42/final",
        "2x2 animal welfare, student reason and student rewrite",
        "off_model_on_model",
        "Qwen/Qwen3.5-4B",
        "Figure 3/4 off-model/on-model comparison.",
        "Cell 4, representative seed 42.",
    ),
    AdapterSpec(
        "2x2/self_preservation/cell1_teacher_reason_teacher_rewrite",
        "runs/seed-errorbars/adapters/2x2_shutdown__cell1__seed42/final",
        "2x2 self-preservation, teacher reason and teacher rewrite",
        "off_model_on_model",
        "Qwen/Qwen3.5-4B",
        "Figure 3/4 off-model/on-model comparison.",
        "Cell 1, representative seed 42. Use only in controlled research settings.",
    ),
    AdapterSpec(
        "2x2/self_preservation/cell2_teacher_reason_student_rewrite",
        "runs/seed-errorbars/adapters/2x2_shutdown__cell2__seed42/final",
        "2x2 self-preservation, teacher reason and student rewrite",
        "off_model_on_model",
        "Qwen/Qwen3.5-4B",
        "Figure 3/4 off-model/on-model comparison.",
        "Cell 2, representative seed 42. Use only in controlled research settings.",
    ),
    AdapterSpec(
        "2x2/self_preservation/cell3_student_reason_teacher_rewrite",
        "runs/seed-errorbars/adapters/2x2_shutdown__cell3__seed42/final",
        "2x2 self-preservation, student reason and teacher rewrite",
        "off_model_on_model",
        "Qwen/Qwen3.5-4B",
        "Figure 3/4 off-model/on-model comparison.",
        "Cell 3, representative seed 42. Use only in controlled research settings.",
    ),
    AdapterSpec(
        "2x2/self_preservation/cell4_student_reason_student_rewrite",
        "runs/seed-errorbars/adapters/2x2_shutdown__cell4__seed42/final",
        "2x2 self-preservation, student reason and student rewrite",
        "off_model_on_model",
        "Qwen/Qwen3.5-4B",
        "Figure 3/4 off-model/on-model comparison.",
        "Cell 4, representative seed 42. Use only in controlled research settings.",
    ),
    AdapterSpec(
        "real_pipeline/off_model_trait_seed42",
        "runs/clip/clip_f00/adapter/final",
        "Real pipeline, off-model trait SFT, seed 42",
        "real_pipeline",
        "Qwen/Qwen3-32B",
        "Figure 5 off-model trait SFT baseline.",
        "Unclipped Opus philosophy-spec trait data.",
    ),
    AdapterSpec(
        "real_pipeline/off_model_trait_seed43",
        "runs/clip/clip_f00_s2/adapter/final",
        "Real pipeline, off-model trait SFT, seed 43",
        "real_pipeline",
        "Qwen/Qwen3-32B",
        "Figure 5 off-model trait SFT seed replicate.",
        "Unclipped Opus philosophy-spec trait data.",
    ),
    AdapterSpec(
        "real_pipeline/off_model_trait_seed44",
        "runs/clip/clip_f00_s3/adapter/final",
        "Real pipeline, off-model trait SFT, seed 44",
        "real_pipeline",
        "Qwen/Qwen3-32B",
        "Figure 5 off-model trait SFT seed replicate.",
        "Unclipped Opus philosophy-spec trait data.",
    ),
    AdapterSpec(
        "real_pipeline/mixed_replay_seed42",
        "runs/replay-mix/r2_full/adapter/final",
        "Real pipeline, mixed replay, seed 42",
        "real_pipeline",
        "Qwen/Qwen3-32B",
        "Figure 5 mixed-replay condition.",
        "Trait data mixed with generic student long-CoT replay data.",
    ),
    AdapterSpec(
        "real_pipeline/mixed_replay_seed43",
        "runs/replay-confirm/adapters/s43/final",
        "Real pipeline, mixed replay, seed 43",
        "real_pipeline",
        "Qwen/Qwen3-32B",
        "Figure 5 mixed-replay seed replicate.",
        "Trait data mixed with generic student long-CoT replay data.",
    ),
    AdapterSpec(
        "real_pipeline/mixed_replay_seed44",
        "runs/replay-confirm/adapters/s44/final",
        "Real pipeline, mixed replay, seed 44",
        "real_pipeline",
        "Qwen/Qwen3-32B",
        "Figure 5 mixed-replay seed replicate.",
        "Trait data mixed with generic student long-CoT replay data.",
    ),
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def patch_adapter_config(path: Path, expected_base: str) -> None:
    data = json.loads(path.read_text())
    recorded = data.get("base_model_name_or_path")
    data["base_model_name_or_path"] = BASE_ID_MAP.get(recorded, expected_base)
    if data["base_model_name_or_path"] != expected_base:
        raise ValueError(f"{path}: expected {expected_base}, got {data['base_model_name_or_path']} from {recorded}")
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def write_adapter_card(path: Path, spec: AdapterSpec) -> None:
    text = f"""---
base_model: {spec.base_model}
library_name: peft
pipeline_tag: text-generation
tags:
- lora
- peft
- toy-models-of-sft
---

# {spec.title}

This is a PEFT/LoRA adapter from the Toy Models of SFT project.

- Base model: `{spec.base_model}`
- Paper use: {spec.paper_use}
- Source path in the full adapter archive: `{spec.source_path}`
- Notes: {spec.notes}

Load this adapter through the root repo with `PeftModel.from_pretrained(...,
subfolder=\"{spec.public_path}\")`.
"""
    path.write_text(text)


def write_root_readme(out: Path, manifest: list[dict[str, Any]]) -> None:
    rows = "\n".join(
        f"| `{row['public_path']}` | {row['base_model']} | {row['group']} | {row['paper_use']} |"
        for row in manifest
    )
    text = f"""---
license: other
license_name: research-artifact-staging
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
- post-training
- model-organisms
- reasoning
- private-staging
---

# Toy Models of SFT Adapters

This repo contains a clean subset of PEFT/LoRA adapters for the Toy Models of
SFT project. It is meant for researcher inspection, not for deployment.

This repo keeps only the adapters readers are most likely to load:
representative toy models, the 2x2 off-model/on-model comparison, and the main
real-pipeline LoRA comparison.

The companion data repo is:
https://huggingface.co/datasets/matonski/toy-models-of-sft-data

## Included adapters

| Adapter subfolder | Base model | Group | Paper use |
|---|---|---|---|
{rows}

## Loading an adapter

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

base_id = "Qwen/Qwen3-4B"
adapter_repo = "matonski/toy-models-of-sft-adapters"
adapter_subfolder = "boxed/reason_directive"

tokenizer = AutoTokenizer.from_pretrained(base_id)
base = AutoModelForCausalLM.from_pretrained(base_id, device_map="auto")
model = PeftModel.from_pretrained(base, adapter_repo, subfolder=adapter_subfolder)
```

Use the matching base model listed in `ADAPTER_MANIFEST.jsonl`.

## Safety and scope

These adapters are research artifacts. Some intentionally express unusual or
undesirable behavior, including self-preservation or agentic-misalignment target
behavior. Use them only in controlled research settings.

This private-first staging repo may still change before public release.
"""
    (out / "README.md").write_text(text)


def build(source: Path, out: Path, clean: bool) -> None:
    if clean and out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    manifest: list[dict[str, Any]] = []
    for spec in ADAPTERS:
        src = source / spec.source_path
        dest = out / spec.public_path
        if not (src / "adapter_model.safetensors").exists():
            raise FileNotFoundError(src)
        shutil.copytree(src, dest, dirs_exist_ok=True)
        patch_adapter_config(dest / "adapter_config.json", spec.base_model)
        write_adapter_card(dest / "README.md", spec)
        adapter_file = dest / "adapter_model.safetensors"
        manifest.append(
            {
                "public_path": spec.public_path,
                "source_path": spec.source_path,
                "title": spec.title,
                "group": spec.group,
                "base_model": spec.base_model,
                "paper_use": spec.paper_use,
                "notes": spec.notes,
                "bytes": adapter_file.stat().st_size,
                "sha256": sha256_file(adapter_file),
            }
        )

    with (out / "ADAPTER_MANIFEST.jsonl").open("w") as f:
        for row in manifest:
            f.write(json.dumps(row, sort_keys=True) + "\n")
    (out / "ADAPTER_MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    write_root_readme(out, manifest)
    print(json.dumps({"out": out.as_posix(), "adapter_count": len(manifest), "bytes": sum(r["bytes"] for r in manifest)}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()
    build(args.source, args.out, args.clean)


if __name__ == "__main__":
    main()
