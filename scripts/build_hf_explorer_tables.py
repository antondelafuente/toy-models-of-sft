#!/usr/bin/env python3
"""Build curated Hugging Face Dataset Viewer tables.

The raw Hugging Face data repo is an artifact archive. This script adds a
small "explorer" layer with clean JSONL tables that are useful to browse:

- flattened plotted values for all figures
- row-level boxed rollouts
- row-level animal-welfare judge scores
- row-level GPQA rollouts where local files are present
- aggregate self-preservation and AM tables
- small training-data samples keyed by source file

The output lives under:
  /home/anton/toy-models-of-sft-hf-upload/data/explorer/

It also rewrites the dataset README with Hugging Face Dataset Viewer configs.
"""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path("/home/anton/toy-models-of-sft")
ARTIFACTS = Path("/home/anton/toy-models-of-sft-artifacts")
UPLOAD_DATA = Path("/home/anton/toy-models-of-sft-hf-upload/data")
EXPLORER = UPLOAD_DATA / "explorer"


EXPLORER_TABLES = [
    ("figure_values", "explorer/figure_values.jsonl"),
    ("figure_manifest", "explorer/figure_manifest.jsonl"),
    ("figure1_boxing_rollouts", "explorer/figure1_boxing_rollouts.jsonl"),
    ("figure2_welfare_scores", "explorer/figure2_welfare_scores.jsonl"),
    ("figure2_selfpres_summary", "explorer/figure2_selfpres_summary.jsonl"),
    ("figure3_selfpres_gpqa_rollouts", "explorer/figure3_selfpres_gpqa_rollouts.jsonl"),
    ("figure5_real_pipeline_gpqa_rollouts", "explorer/figure5_real_pipeline_gpqa_rollouts.jsonl"),
    ("figure5_real_pipeline_am_summary", "explorer/figure5_real_pipeline_am_summary.jsonl"),
    ("training_data_samples", "explorer/training_data_samples.jsonl"),
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            n += 1
    return n


def rel(path: Path) -> str:
    try:
        return path.relative_to(ARTIFACTS).as_posix()
    except ValueError:
        try:
            return path.relative_to(REPO_ROOT).as_posix()
        except ValueError:
            return path.as_posix()


def interval_parts(value: Any) -> tuple[float | None, float | None]:
    if isinstance(value, list) and len(value) == 2:
        return value[0], value[1]
    return None, None


def stringify(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value, sort_keys=True)


def add_metric_row(
    out: list[dict[str, Any]],
    *,
    data: dict[str, Any],
    table: str,
    panel_id: str | None,
    panel_title: str | None,
    condition_id: str,
    condition_label: str,
    metric: str,
    value: Any,
    interval: Any = None,
    row: dict[str, Any] | None = None,
) -> None:
    low, high = interval_parts(interval)
    row = row or {}
    out.append(
        {
            "figure": data.get("figure"),
            "slug": data.get("slug"),
            "figure_title": data.get("title"),
            "status": data.get("status"),
            "generated_file": data.get("generated_file"),
            "table": table,
            "panel_id": panel_id,
            "panel_title": panel_title,
            "condition_id": condition_id,
            "condition_label": condition_label,
            "metric": metric,
            "value": value,
            "interval_low": low,
            "interval_high": high,
            "model": row.get("model") or data.get("model"),
            "training_data": stringify(row.get("training_data")),
            "training_rows": stringify(row.get("training_rows")),
            "source_records": stringify(data.get("source_records")),
            "source_note": row.get("source") or data.get("note"),
        }
    )


def flatten_plot_data() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    value_rows: list[dict[str, Any]] = []
    manifest_rows: list[dict[str, Any]] = []

    for path in sorted((REPO_ROOT / "journal/writeup/plot_data").glob("figure*.json")):
        data = read_json(path)
        manifest_rows.append(
            {
                "figure": data.get("figure"),
                "slug": data.get("slug"),
                "title": data.get("title"),
                "status": data.get("status"),
                "generated_file": data.get("generated_file"),
                "generator": data.get("generator"),
                "plot_data_file": rel(path),
                "source_records": stringify(data.get("source_records")),
                "note": data.get("note") or data.get("important_caveat"),
            }
        )

        for row in data.get("rows", []):
            for metric in ("value", "gpqa", "am"):
                if metric in row:
                    add_metric_row(
                        value_rows,
                        data=data,
                        table="rows",
                        panel_id=None,
                        panel_title=None,
                        condition_id=row.get("id", row.get("label", "")),
                        condition_label=row.get("label", row.get("id", "")),
                        metric=metric,
                        value=row[metric],
                        interval=row.get("interval") or row.get(f"{metric}_interval"),
                        row=row,
                    )

        for point in data.get("points", []):
            for metric in ("gpqa", "am"):
                if metric in point:
                    add_metric_row(
                        value_rows,
                        data=data,
                        table="points",
                        panel_id=None,
                        panel_title=None,
                        condition_id=point.get("id", point.get("label", "")),
                        condition_label=point.get("label", point.get("id", "")),
                        metric=metric,
                        value=point[metric],
                        interval=point.get(f"{metric}_interval"),
                        row=point,
                    )

        for panel in data.get("panels", []):
            panel_metric = panel.get("metric") or panel.get("title")
            base = panel.get("base")
            if isinstance(base, dict) and "value" in base:
                add_metric_row(
                    value_rows,
                    data=data,
                    table="panel_base",
                    panel_id=panel.get("id"),
                    panel_title=panel.get("title"),
                    condition_id="base",
                    condition_label="Base",
                    metric=panel_metric,
                    value=base["value"],
                    interval=base.get("interval"),
                    row=base,
                )
            for row in panel.get("rows", []):
                for metric in ("value", "gpqa", "am"):
                    if metric in row:
                        add_metric_row(
                            value_rows,
                            data=data,
                            table="panel_rows",
                            panel_id=panel.get("id"),
                            panel_title=panel.get("title"),
                            condition_id=row.get("id", row.get("label", "")),
                            condition_label=row.get("label", row.get("id", "")),
                            metric=panel_metric if metric == "value" else metric,
                            value=row[metric],
                            interval=row.get("interval") or row.get(f"{metric}_interval"),
                            row=row,
                        )

        if "trait_strength" in data:
            for organism, blocks in data["trait_strength"].items():
                for block, values in blocks.items():
                    if isinstance(values, list):
                        for i, value in enumerate(values, start=1):
                            add_metric_row(
                                value_rows,
                                data=data,
                                table="full_2x2_trait_strength",
                                panel_id=organism,
                                panel_title=organism.replace("_", " "),
                                condition_id=f"{block}_{i}",
                                condition_label=f"{block} cell {i}",
                                metric="trait_strength",
                                value=value,
                            )
                    else:
                        add_metric_row(
                            value_rows,
                            data=data,
                            table="full_2x2_trait_strength",
                            panel_id=organism,
                            panel_title=organism.replace("_", " "),
                            condition_id=block,
                            condition_label=block,
                            metric="trait_strength",
                            value=values,
                        )
        if "gpqa_delta_from_base" in data:
            for organism, blocks in data["gpqa_delta_from_base"].items():
                for block, values in blocks.items():
                    for i, value in enumerate(values, start=1):
                        add_metric_row(
                            value_rows,
                            data=data,
                            table="full_2x2_gpqa_delta",
                            panel_id=organism,
                            panel_title=organism.replace("_", " "),
                            condition_id=f"{block}_{i}",
                            condition_label=f"{block} cell {i}",
                            metric="gpqa_delta_from_base_points",
                            value=value,
                        )

    return value_rows, manifest_rows


def parse_seed_condition(name: str) -> tuple[str, int | None]:
    match = re.search(r"(?:__|_)seed(\d+)", name)
    seed = int(match.group(1)) if match else None
    condition = re.sub(r"(?:__|_)seed\d+_?", "", name)
    condition = condition.rstrip("_")
    return condition, seed


def boxing_condition(raw: str) -> tuple[str, int | None, str]:
    if raw == "base":
        return "base", None, "Base"
    if raw.startswith("A_seed"):
        return "final_answer_only", int(raw.replace("A_seed", "")), "Final-answer-only SFT"
    if raw.startswith("B_broad_seed"):
        return "reason_directive", int(raw.replace("B_broad_seed", "")), "Reason/directive SFT"
    if raw.startswith("C_masked_seed"):
        return (
            "reason_directive_answer_masked",
            int(raw.replace("C_masked_seed", "")),
            "Reason/directive SFT, answer masked",
        )
    return raw, None, raw


def build_boxing_rollouts() -> list[dict[str, Any]]:
    path = ARTIFACTS / "runs/boxed-masked-rerun/local_records/pod_artifacts/results/eval/rollouts_all.jsonl"
    rows = []
    for i, row in enumerate(iter_jsonl(path)):
        condition_id, seed, label = boxing_condition(row["condition"])
        rows.append(
            {
                "figure": 1,
                "slug": "boxed_transfer",
                "row_index": i,
                "condition_raw": row["condition"],
                "condition_id": condition_id,
                "condition_label": label,
                "seed": seed,
                "orig_index": row.get("orig_index"),
                "domain": row.get("domain"),
                "prompt": row.get("prompt"),
                "response": row.get("response"),
                "finish_reason": row.get("finish_reason"),
                "has_answer_box": row.get("has_answer_box"),
                "has_permissive_box": row.get("has_permissive_box"),
                "empty_box_count": row.get("empty_box_count"),
                "declaration_count": row.get("declaration_count"),
                "source_file": rel(path),
            }
        )
    return rows


def build_welfare_scores() -> list[dict[str, Any]]:
    root = ARTIFACTS / "runs/seed-errorbars/results/welfare35"
    files = [root / "base_welfare.jsonl"] + sorted(root.glob("welfare_35__*_welfare.jsonl"))
    rows: list[dict[str, Any]] = []
    for path in files:
        stem = path.name.removesuffix("_welfare.jsonl")
        if path.name == "base_welfare.jsonl":
            condition_id, seed, label = "base", None, "Base"
        else:
            condition_raw, seed = parse_seed_condition(stem.replace("welfare_35__", ""))
            condition_id = condition_raw
            label = condition_raw.replace("_", " ").title()
        for i, row in enumerate(iter_jsonl(path)):
            rows.append(
                {
                    "figure": 2,
                    "slug": "richer_traits",
                    "panel": "animal_welfare",
                    "model": "Qwen3.5-4B",
                    "condition_id": condition_id,
                    "condition_label": label,
                    "seed": seed,
                    "row_index": i,
                    "surface": row.get("surface"),
                    "prompt": row.get("prompt"),
                    "response": row.get("response"),
                    "moral_circle_score": row.get("moral_circle_score"),
                    "mentions_animal_welfare": row.get("mentions_animal_welfare"),
                    "persona_override": row.get("persona_override"),
                    "source_file": rel(path),
                }
            )
    return rows


def build_selfpres_summary() -> list[dict[str, Any]]:
    data = read_json(REPO_ROOT / "journal/writeup/plot_data/figure2_richer_traits.json")
    panel = next(p for p in data["panels"] if p["id"] == "self_preservation")
    rows = []
    for row in panel["rows"]:
        low, high = interval_parts(row.get("interval"))
        rows.append(
            {
                "figure": 2,
                "slug": "richer_traits",
                "panel": "self_preservation",
                "condition_id": row["id"],
                "condition_label": row["label"],
                "metric": panel["metric"],
                "value": row["value"],
                "interval_low": low,
                "interval_high": high,
                "raw_log_archive": panel.get("rollouts_r2"),
                "note": "Aggregate Petri/Bloom table. Raw .eval archives are kept in the archive layer.",
            }
        )
    return rows


def gpqa_rows(paths: list[tuple[Path, dict[str, Any]]], figure: int, slug: str) -> list[dict[str, Any]]:
    rows = []
    for path, meta in paths:
        for i, row in enumerate(iter_jsonl(path)):
            rows.append(
                {
                    "figure": figure,
                    "slug": slug,
                    **meta,
                    "row_index": i,
                    "question": row.get("question"),
                    "subdomain": row.get("subdomain"),
                    "high_level_domain": row.get("high_level_domain"),
                    "prompt": row.get("prompt"),
                    "gold_letter": row.get("gold_letter"),
                    "options": row.get("options"),
                    "response": row.get("response"),
                    "parsed_letter": row.get("parsed_letter"),
                    "parse_strategy": row.get("parse_strategy"),
                    "correct": row.get("correct"),
                    "has_real_box": row.get("has_real_box"),
                    "len_chars": row.get("len_chars"),
                    "source_file": rel(path),
                }
            )
    return rows


def build_figure3_selfpres_gpqa() -> list[dict[str, Any]]:
    root = ARTIFACTS / "runs/seed-errorbars/results/gpqa_shutdown"
    paths: list[tuple[Path, dict[str, Any]]] = [
        (
            root / "base__gpqa.jsonl",
            {
                "organism": "self_preservation",
                "condition_id": "base",
                "condition_label": "Base",
                "seed": None,
            },
        )
    ]
    labels = {
        "cell1": "teacher first response, teacher rewrite",
        "cell2": "teacher first response, student rewrite",
        "cell3": "student first response, teacher rewrite",
        "cell4": "student first response, student rewrite",
    }
    for cell in ("cell1", "cell2", "cell3", "cell4"):
        for seed in (42, 43, 44):
            paths.append(
                (
                    root / f"2x2_shutdown__{cell}__seed{seed}__gpqa.jsonl",
                    {
                        "organism": "self_preservation",
                        "condition_id": cell,
                        "condition_label": labels[cell],
                        "seed": seed,
                    },
                )
            )
    return gpqa_rows(paths, figure=3, slug="off_model_gpqa")


def build_real_pipeline_gpqa() -> list[dict[str, Any]]:
    paths: list[tuple[Path, dict[str, Any]]] = []
    paths.append(
        (
            ARTIFACTS / "runs/replay-confirm/eval/gpqa_base/base__gpqa.jsonl",
            {"condition_id": "base", "condition_label": "Base Qwen", "seed": None},
        )
    )
    for suffix, seed in [("", 1), ("_s2", 2), ("_s3", 3)]:
        name = f"clip_f00{suffix}"
        paths.append(
            (
                ARTIFACTS / f"runs/clip/{name}/gpqa/{name}__gpqa.jsonl",
                {
                    "condition_id": "off_policy_trait_sft",
                    "condition_label": "Off-policy trait SFT",
                    "seed": seed,
                },
            )
        )
    paths.extend(
        [
            (
                ARTIFACTS / "runs/replay-mix/r2_full/eval/gpqa_replaymix/replaymix__gpqa.jsonl",
                {"condition_id": "mixed_replay", "condition_label": "Mixed replay", "seed": 42},
            ),
            (
                ARTIFACTS / "runs/replay-confirm/eval/gpqa_s43/s43__gpqa.jsonl",
                {"condition_id": "mixed_replay", "condition_label": "Mixed replay", "seed": 43},
            ),
            (
                ARTIFACTS / "runs/replay-confirm/eval/gpqa_s44/s44__gpqa.jsonl",
                {"condition_id": "mixed_replay", "condition_label": "Mixed replay", "seed": 44},
            ),
            (
                ARTIFACTS / "runs/replay-confirm/eval/gpqa_fullft/fullft__gpqa.jsonl",
                {"condition_id": "mixed_replay_fullft", "condition_label": "Mixed replay full-FT", "seed": None},
            ),
        ]
    )
    return gpqa_rows(paths, figure=5, slug="real_pipeline_minimal")


def build_real_pipeline_am_summary() -> list[dict[str, Any]]:
    rows = []
    for path in [
        ARTIFACTS / "runs/replay-confirm/eval/confirm_eval_summary.json",
        ARTIFACTS / "runs/replay-mix/r2_full/eval/replay_eval_summary.json",
    ]:
        if not path.exists():
            continue
        data = read_json(path)
        for condition, metrics in data.items():
            rows.append(
                {
                    "figure": 5,
                    "slug": "real_pipeline_minimal",
                    "condition_id": condition,
                    "source_file": rel(path),
                    **metrics,
                }
            )
    for path in sorted((ARTIFACTS / "runs/clip").glob("clip_f00*/clip_f00*_am.json")):
        data = read_json(path)
        rows.append(
            {
                "figure": 5,
                "slug": "real_pipeline_minimal",
                "condition_id": "off_policy_trait_sft",
                "source_file": rel(path),
                **data,
            }
        )
    return rows


def training_paths_from_plot_data() -> list[str]:
    found: set[str] = set()

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key == "training_data":
                    if isinstance(child, str):
                        found.add(child)
                    elif isinstance(child, list):
                        found.update(x for x in child if isinstance(x, str))
                    elif isinstance(child, dict):
                        found.update(x for x in child.values() if isinstance(x, str))
                else:
                    walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    for path in sorted((REPO_ROOT / "journal/writeup/plot_data").glob("figure*.json")):
        walk(read_json(path))
    return sorted(found)


def resolve_artifact_path(path_str: str) -> Path | None:
    candidates = []
    if path_str.startswith("registry/"):
        candidates.append(ARTIFACTS / path_str.replace("registry/", "runs/", 1))
    candidates.append(ARTIFACTS / path_str)
    candidates.append(ARTIFACTS / "paper_repo" / path_str)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def build_training_samples(limit_per_file: int = 5) -> list[dict[str, Any]]:
    rows = []
    for path_str in training_paths_from_plot_data():
        path = resolve_artifact_path(path_str)
        if not path or path.suffix != ".jsonl":
            rows.append(
                {
                    "source_reference": path_str,
                    "resolved_source_file": rel(path) if path else None,
                    "row_index": None,
                    "sample": None,
                    "note": "Source not present as a local JSONL file in the artifact bundle.",
                }
            )
            continue
        for i, row in enumerate(iter_jsonl(path)):
            if i >= limit_per_file:
                break
            rows.append(
                {
                    "source_reference": path_str,
                    "resolved_source_file": rel(path),
                    "row_index": i,
                    "sample": row,
                    "note": "Small browsing sample only, not the full training file.",
                }
            )
    return rows


def write_dataset_readme(table_counts: dict[str, int]) -> None:
    configs = "\n".join(
        [
            f"- config_name: {name}\n"
            f"  data_files:\n"
            f"  - split: train\n"
            f"    path: {path}"
            for name, path in EXPLORER_TABLES
        ]
    )
    counts = "\n".join(f"- `{name}`: {count} rows" for name, count in table_counts.items())
    text = f"""---
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
configs:
{configs}
---

# Toy Models of SFT Data

This is the data side of the Toy Models of SFT release. It supports a paper
about using small post-training setups to study when reasoning-rich training
generalizes behavior and when off-model reasoning damages capability.

The repo is private-first staging while we finish the public release review.
The goal is to make the paper auditable, not to provide a polished benchmark.

## What is included

This dataset repo contains the non-weight artifacts used to audit the main paper
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

Adapter weights are intentionally excluded from this dataset repo. They live in
the companion model repo.

## How to read the repo

The raw archive layer preserves source folders, eval rollouts, judge scores,
plot data, manifests, checksums, and provenance records. It is useful for audit,
but it is not optimized for browsing.

The `explorer/` layer contains curated JSONL tables for Hugging Face Dataset
Viewer. These tables make the main plotted values, selected rollouts, judge
scores, and source samples easier to inspect.

Start with:

- `artifact_manifest.json` to see which local and R2 sources were collected
- `large_artifacts.json` to see which large artifacts are pointers rather than
  included files
- `explorer/figure_values.jsonl` to inspect the numbers used in the plotted
  figures
- `explorer/figure_manifest.jsonl` to map figures to source files
- `paper_repo/journal/writeup/provenance/ARM_ARTIFACT_INDEX.md` to map paper
  arms to adapters, training data, eval outputs, and caveats
- `paper_repo/` to inspect the lightweight GitHub figure package snapshot

## Explorer Tables

{counts}

Table meanings:

- `figure_values` contains the plotted values from the paper figures and
  appendix figures.
- `figure_manifest` maps each figure to its local plot-data and rendered SVG
  files.
- `figure1_boxing_rollouts` contains boxed-answer eval rollouts for the main
  boxing transfer figure.
- `figure2_welfare_scores` contains animal-welfare judge scores for the richer
  toy-trait figure.
- `figure2_selfpres_summary` contains aggregate Petri/Bloom self-preservation
  audit scores.
- `figure3_selfpres_gpqa_rollouts` contains GPQA rollouts for the
  self-preservation part of the off-model versus on-model comparison.
- `figure5_real_pipeline_gpqa_rollouts` contains GPQA rollouts for the larger
  Model-Spec Midtraining pipeline comparison.
- `figure5_real_pipeline_am_summary` contains aggregate agentic-misalignment
  scores for the same larger-pipeline comparison.
- `training_data_samples` contains small browsing samples from training files.
  It is not intended to replace the raw training files under `runs/`.

## Companion Repos

- GitHub figure package: https://github.com/antondelafuente/toy-models-of-sft
- Adapter repo: https://huggingface.co/matonski/toy-models-of-sft-adapters

## Reproducibility boundary

This repo is enough to inspect the data artifacts behind the public figures and
to trace many plotted values to row-level rollouts or judge scores. It is not a
one-command rerun of all training jobs. Some very large artifacts remain as
pointers, including selected full fine-tuned model checkpoints and full run
roots. Those boundaries are recorded in `large_artifacts.json`.

The lightweight GitHub repo can regenerate the SVG figure layer from frozen plot
data. This dataset repo is the heavier audit bundle for the source records.

## Release Status

This is private-first staging. Before making public, review operational paths,
agentic-misalignment rollout content, Petri/Bloom scenario release policy, model
cards, base model names, license choice, and adapter release scope.
"""
    (UPLOAD_DATA / "README.md").write_text(text)


def write_explorer_readme(table_counts: dict[str, int]) -> None:
    lines = [
        "# Explorer Tables",
        "",
        "Clean JSONL tables generated from the raw artifact bundle.",
        "",
    ]
    for name, count in table_counts.items():
        lines.append(f"- `{name}.jsonl`: {count} rows")
    lines.extend(
        [
            "",
            "These tables are a browsing layer. The raw source files remain in",
            "the surrounding archive folders and are tracked by manifests and checksums.",
            "",
        ]
    )
    (EXPLORER / "README.md").write_text("\n".join(lines))


def main() -> None:
    if not ARTIFACTS.exists():
        raise SystemExit(f"missing artifact bundle: {ARTIFACTS}")
    if EXPLORER.exists():
        shutil.rmtree(EXPLORER)
    EXPLORER.mkdir(parents=True)

    figure_values, figure_manifest = flatten_plot_data()
    builders: list[tuple[str, list[dict[str, Any]]]] = [
        ("figure_values", figure_values),
        ("figure_manifest", figure_manifest),
        ("figure1_boxing_rollouts", build_boxing_rollouts()),
        ("figure2_welfare_scores", build_welfare_scores()),
        ("figure2_selfpres_summary", build_selfpres_summary()),
        ("figure3_selfpres_gpqa_rollouts", build_figure3_selfpres_gpqa()),
        ("figure5_real_pipeline_gpqa_rollouts", build_real_pipeline_gpqa()),
        ("figure5_real_pipeline_am_summary", build_real_pipeline_am_summary()),
        ("training_data_samples", build_training_samples()),
    ]

    table_counts = {}
    for name, rows in builders:
        table_counts[name] = write_jsonl(EXPLORER / f"{name}.jsonl", rows)

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_artifacts": ARTIFACTS.as_posix(),
        "upload_data": UPLOAD_DATA.as_posix(),
        "tables": table_counts,
        "notes": [
            "Petri/Bloom .eval archives are kept raw; explorer exposes aggregate scores.",
            "Figure 3 welfare GPQA plotted values are in figure_values; row-level welfare GPQA rollouts need a clearer source pointer.",
            "Training samples are small browsing samples, not complete training datasets.",
        ],
    }
    (EXPLORER / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    write_explorer_readme(table_counts)
    write_dataset_readme(table_counts)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
