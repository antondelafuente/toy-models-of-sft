#!/usr/bin/env python3
"""Build the per-figure public-release manifest from plot-data JSON files.

The plot-data files are the frozen source for rendered figure values. This
manifest adds the release-layer view: which local files and remote pointers a
future public package must include, mirror, redact, or explain.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
WRITEUP_ROOT = REPO_ROOT / "journal" / "writeup"
PLOT_DATA_DIR = WRITEUP_ROOT / "plot_data"
DEFAULT_OUTPUT = WRITEUP_ROOT / "provenance" / "FIGURE_RELEASE_MANIFEST.json"
LOCAL_PREFIXES = ("registry/", "journal/", "site/")
REMOTE_PREFIXES = ("r2:", "http://", "https://")


PUBLIC_NOTES = {
    1: [
        "Matched boxed masked rerun is locally packaged and verified on R2.",
        "Release still needs a stable public route for the R2 root or a curated mirror.",
    ],
    2: [
        "Petri/Bloom scenario text should not be dumped wholesale without a release decision.",
    ],
    3: [
        "Figure shows the teacher-first-response row from the full 2x2 comparison.",
    ],
    4: [
        "Petri/Bloom scenario text should not be dumped wholesale without a release decision.",
    ],
    5: [
        "Agentic-misalignment eval logs are in the Hugging Face data repo, not in Git.",
        "Off-policy trait SFT row is the zero-percent token-clipping row.",
    ],
    6: [
        "Mostly single-seed washout curves. Keep this caveat with any public figure.",
        "Agentic-misalignment eval logs are in the Hugging Face data repo, not in Git.",
    ],
    7: [
        "Appendix map. Use per-arm result records rather than the plot alone for exact claims.",
        "Agentic-misalignment eval logs are in the Hugging Face data repo, not in Git.",
    ],
    8: [
        "Token-clipping rows are three-seed means and intervals are seed min to max.",
        "Agentic-misalignment eval logs are in the Hugging Face data repo, not in Git.",
    ],
    9: [
        "Replay-added-after row is historical, not a perfectly matched one-batch rerun.",
        "Agentic-misalignment eval logs are in the Hugging Face data repo, not in Git.",
    ],
    10: [
        "Appendix full 2x2 figure. Do not use old prose claiming student/student is the strongest self-preservation cell.",
    ],
}

MODEL_PUBLIC_IDS = {
    "Qwen3-4B": "Qwen/Qwen3-4B",
    "Qwen3.5-4B": "Qwen/Qwen3.5-4B",
    "Qwen3.6-27B": "Qwen/Qwen3.6-27B",
    "Qwen3-32B": "Qwen/Qwen3-32B",
}

EXTRA_REMOTE_POINTERS = {
    1: ["r2:mats/experiments/boxed-masked-rerun/"],
    2: ["r2:mats/experiments/seed-errorbars/"],
    3: ["r2:mats/experiments/seed-errorbars/"],
    4: ["r2:mats/experiments/seed-errorbars/"],
    5: [
        "r2:mats/data/phil_spec_cot_10k/comparisons/opus_phil10k.jsonl",
        "r2:mats/experiments/msm-aft-cot-qwen3-32b-recovery/data/recovery_alpaca_qwen32b.jsonl",
        "r2:mats/experiments/clip_*",
    ],
    6: ["r2:mats/experiments/washout-curve/"],
    7: [
        "r2:mats/experiments/replay-confirm/",
        "r2:mats/experiments/replay-mix/",
        "r2:mats/experiments/clip_*",
        "r2:mats/experiments/msm-aft-cot-qwen3-32b-recovery/",
    ],
    8: ["r2:mats/experiments/clip_*"],
    9: [
        "r2:mats/experiments/replay-confirm/",
        "r2:mats/experiments/replay-mix/",
        "r2:mats/experiments/msm-aft-cot-qwen3-32b-recovery/",
    ],
    10: ["r2:mats/experiments/seed-errorbars/"],
}

SAMPLE_SIZE_OVERRIDES = {
    3: {
        "gpqa": "198 GPQA Diamond questions",
        "condition_shown": "teacher-first-response row from the full 2x2 comparison",
    },
    4: {
        "animal_welfare": "200 held-out welfare prompts",
        "self_preservation": "40 frozen Petri/Bloom scenarios",
        "condition_shown": "teacher-first-response row from the full 2x2 comparison",
    },
    5: {
        "gpqa": "198 GPQA Diamond questions",
        "am": "mean of murder and exfiltration evaluations",
    },
    6: {
        "gpqa": "198 GPQA Diamond questions where GPQA is plotted",
        "am": "mean of murder and exfiltration evaluations",
    },
    7: {
        "gpqa": "198 GPQA Diamond questions where GPQA is plotted",
        "am": "mean of murder and exfiltration evaluations",
    },
    8: {
        "gpqa": "198 GPQA Diamond questions",
        "am": "mean of murder and exfiltration evaluations",
    },
    9: {
        "gpqa": "198 GPQA Diamond questions",
        "am": "mean of murder and exfiltration evaluations",
    },
    10: {
        "gpqa": "198 GPQA Diamond questions",
        "animal_welfare": "200 held-out welfare prompts",
        "self_preservation": "40 frozen Petri/Bloom scenarios",
    },
}

UNCERTAINTY_OVERRIDES = {
    2: "Animal-welfare intervals are training-seed standard deviations. Self-preservation intervals include the measured Petri audit-noise floor.",
    3: "GPQA intervals are the accuracy intervals stored in plot data, from the seed-errorbars figure layer.",
    4: "Trait intervals are the intervals stored in plot data. Self-preservation should be read with the Petri audit-noise floor noted in seed-errorbars/RESULTS.md.",
    5: "GPQA intervals are plotted accuracy intervals. Mixed-replay AM interval is approximate because murder varies by seed and exfiltration is held fixed.",
    6: "Mostly single-seed curves; no strong seed-variance claim.",
    7: "Appendix map. Some points are single seed; use source records for per-arm uncertainty.",
    8: "Rows are three-seed means; intervals are seed min to max.",
    9: "Historical schedule comparison, not a matched one-batch rerun.",
}

METRIC_OVERRIDES = {
    10: {
        "gpqa_delta_from_base": "GPQA accuracy delta from base, percentage points",
        "trait_strength": "animal-welfare judge score or self-preservation Petri/Bloom score",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plot-data-dir", type=Path, default=PLOT_DATA_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def walk_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            out.extend(walk_strings(item))
        return out
    if isinstance(value, dict):
        out: list[str] = []
        for item in value.values():
            out.extend(walk_strings(item))
        return out
    return []


def is_clean_local_path(value: str) -> bool:
    candidate = value.split("::", 1)[0]
    return candidate.startswith(LOCAL_PREFIXES) and all(token not in candidate for token in [" ", ",", "\n"])


def extract_paths(data: dict[str, Any]) -> tuple[list[str], list[str]]:
    local = set()
    remote = set()
    for value in walk_strings(data):
        if value.startswith(REMOTE_PREFIXES):
            remote.add(value)
        elif is_clean_local_path(value):
            local.add(value.split("::", 1)[0])
    return sorted(local), sorted(remote)


def metric_summary(data: dict[str, Any]) -> Any:
    figure = int(data["figure"])
    if figure in METRIC_OVERRIDES:
        return METRIC_OVERRIDES[figure]
    if "metric" in data:
        return data["metric"]
    if "metrics" in data:
        return data["metrics"]
    panels = data.get("panels")
    if isinstance(panels, list):
        return {panel.get("id", f"panel_{i}"): panel.get("metric") for i, panel in enumerate(panels)}
    return None


def sample_size_summary(data: dict[str, Any]) -> Any:
    figure = int(data["figure"])
    if figure in SAMPLE_SIZE_OVERRIDES:
        return SAMPLE_SIZE_OVERRIDES[figure]
    if "eval" in data and isinstance(data["eval"], dict):
        return {k: data["eval"].get(k) for k in ("n", "raw_n", "dedup_n") if k in data["eval"]}
    panels = data.get("panels")
    if isinstance(panels, list):
        out = {}
        for panel in panels:
            panel_id = panel.get("id")
            if not panel_id:
                continue
            size_fields = {}
            for key in ("eval_n", "eval", "eval_prompts"):
                if key in panel:
                    size_fields[key] = panel[key]
            if size_fields:
                out[panel_id] = size_fields
        return out or None
    return None


def uncertainty_summary(data: dict[str, Any]) -> Any:
    figure = int(data["figure"])
    if figure in UNCERTAINTY_OVERRIDES:
        return UNCERTAINTY_OVERRIDES[figure]
    if "interval" in data:
        return data["interval"]
    if "intervals" in data:
        return data["intervals"]
    notes = []
    for key in ("note", "important_caveat", "caveat"):
        value = data.get(key)
        if isinstance(value, str) and "interval" in value.lower():
            notes.append(value)
    return notes or None


def caveats(data: dict[str, Any]) -> list[str]:
    out = []
    for key in ("caveat", "important_caveat", "note"):
        value = data.get(key)
        if isinstance(value, str):
            out.append(value)
    out.extend(PUBLIC_NOTES.get(int(data["figure"]), []))
    return out


def build_manifest(plot_data_dir: Path) -> dict[str, Any]:
    figures = []
    for path in sorted(plot_data_dir.glob("*.json")):
        with path.open() as f:
            data = json.load(f)
        local_paths, remote_pointers = extract_paths(data)
        figure = int(data["figure"])
        remote_pointers = sorted(set(remote_pointers).union(EXTRA_REMOTE_POINTERS.get(figure, [])))
        figures.append(
            {
                "paper_figure": figure,
                "slug": data.get("slug"),
                "title": data.get("title"),
                "status": data.get("status"),
                "rendered_figure": data.get("generated_file"),
                "plot_data": str(path.relative_to(REPO_ROOT)),
                "generator": data.get("generator"),
                "model": data.get("model"),
                "public_model_id": MODEL_PUBLIC_IDS.get(data.get("model")),
                "metric": metric_summary(data),
                "sample_size": sample_size_summary(data),
                "uncertainty": uncertainty_summary(data),
                "source_records": data.get("source_records", []),
                "local_artifacts": local_paths,
                "remote_artifact_pointers": remote_pointers,
                "release_notes": caveats(data),
            }
        )

    figures.sort(key=lambda item: item["paper_figure"])
    return {
        "manifest_version": 1,
        "scope": "Toy Models of Post-Training Science writeup figure release manifest",
        "source": "Generated from journal/writeup/plot_data/*.json plus release notes in build_public_release_manifest.py.",
        "rebuild_commands": [
            "python3 journal/writeup/scripts/build_public_release_manifest.py",
            "python3 journal/writeup/scripts/check_plot_data_sources.py",
            "python3 journal/writeup/scripts/rebuild_all_figures.py",
        ],
        "release_policies": {
            "am_rollouts": "Agentic-misalignment eval logs are not copied into the lightweight GitHub figure package. Reviewed logs live in the Hugging Face data repo. See journal/writeup/provenance/AM_ROLLOUT_RELEASE_POLICY.md.",
            "petri_bloom": "Do not dump Petri/Bloom scenario text wholesale without separate review.",
        },
        "figures": figures,
    }


def main() -> None:
    args = parse_args()
    manifest = build_manifest(args.plot_data_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"wrote {args.output}")
    print(f"figures: {len(manifest['figures'])}")


if __name__ == "__main__":
    main()
