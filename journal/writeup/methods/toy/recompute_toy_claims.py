#!/usr/bin/env python3
"""Recompute the two main toy figures from frozen row-level records."""

from __future__ import annotations

import csv
import json
import math
import re
import statistics
from collections import defaultdict
from pathlib import Path


METHOD_ROOT = Path(__file__).resolve().parent
REPO_ROOT = METHOD_ROOT.parents[3]


def jsonl(path: Path):
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def close(actual: float, expected: float, tol: float, label: str) -> None:
    if not math.isclose(actual, expected, abs_tol=tol):
        raise AssertionError(f"{label}: {actual:.6f} != {expected:.6f} (tol={tol})")


def recompute_boxing() -> None:
    plot = json.loads((REPO_ROOT / "journal/writeup/plot_data/figure1_boxed_transfer.json").read_text())
    rows = list(jsonl(REPO_ROOT / "eval_outputs/toy/boxed-masked-rerun/eval/rollouts_all.jsonl"))
    per_condition = defaultdict(list)
    for row in rows:
        per_condition[row["condition"]].append(row)
    mapping = {
        "base": ["base"],
        "final_answer_only": ["A_seed42", "A_seed43", "A_seed44"],
        "reason_directive": ["B_broad_seed42", "B_broad_seed43", "B_broad_seed44"],
        "reason_directive_answer_masked": ["C_masked_seed42", "C_masked_seed43", "C_masked_seed44"],
    }
    expected = {row["id"]: row for row in plot["rows"]}
    for arm, conditions in mapping.items():
        seed_values = []
        for condition in conditions:
            seen = set()
            kept = []
            for row in per_condition[condition]:
                if row["prompt"] in seen:
                    continue
                seen.add(row["prompt"])
                if row["domain"] != "math":
                    kept.append(row)
            if len(kept) != 336:
                raise AssertionError(f"{condition}: expected 336 deduplicated non-math rows, got {len(kept)}")
            seed_values.append(100 * sum(bool(r["has_answer_box"]) for r in kept) / len(kept))
        mean = statistics.fmean(seed_values)
        sd = statistics.stdev(seed_values) if len(seed_values) > 1 else 0.0
        close(mean, expected[arm]["value"], 1e-9, f"boxing {arm} mean")
        close(sd, expected[arm]["sd"], 1e-9, f"boxing {arm} sample SD")
        print(f"boxing {arm}: {mean:.3f} +/- {sd:.3f} percentage points")

    filler_summary = REPO_ROOT / "registry/reasons-filler-control/analysis/results/per_seed_summary.csv"
    with filler_summary.open(newline="", encoding="utf-8") as handle:
        filler_rows = [row for row in csv.DictReader(handle) if row["arm"] == "filler_plain"]
    if len(filler_rows) != 3:
        raise AssertionError(f"filler_plain: expected 3 seed rows, got {len(filler_rows)}")
    filler_values = [100 * float(row["strict_nonmath_dedup"]) for row in filler_rows]
    filler_mean = statistics.fmean(filler_values)
    filler_sd = statistics.stdev(filler_values)
    close(filler_mean, expected["filler_plain"]["value"], 1e-9, "boxing filler_plain mean")
    close(filler_sd, expected["filler_plain"]["sd"], 1e-9, "boxing filler_plain sample SD")
    print(f"boxing filler_plain: {filler_mean:.3f} +/- {filler_sd:.3f} percentage points")


def welfare_means() -> dict[str, list[float]]:
    root = REPO_ROOT / "eval_outputs/toy/seed-errorbars/welfare35"
    out = defaultdict(list)
    for path in sorted(root.glob("*_welfare.jsonl")):
        rows = list(jsonl(path))
        if len(rows) != 200:
            raise AssertionError(f"{path.name}: expected 200 rows, got {len(rows)}")
        family_match = re.search(r"__(one_shot|rewrite|strip)__seed(42|43|44)", path.name)
        family = family_match.group(1) if family_match else "base"
        out[family].append(statistics.fmean(float(r["moral_circle_score"]) for r in rows))
    return out


def petri_means() -> tuple[dict[str, list[float]], float]:
    grouped = defaultdict(list)
    for row in jsonl(METHOD_ROOT / "self_preservation/petri_scores_frozen.jsonl"):
        grouped[row["condition"]].append(float(row["score"]))
    means = {}
    for condition, values in grouped.items():
        if len(values) != 36:
            raise AssertionError(f"{condition}: expected 36 scenario scores, got {len(values)}")
        means[condition] = statistics.fmean(values)
    families = defaultdict(list)
    for condition, mean in means.items():
        match = re.fullmatch(r"selfpres__(one_shot|rewrite|strip)__seed(42|43|44)_", condition)
        if match:
            families[match.group(1)].append(mean)
        elif condition == "base":
            families["base"].append(mean)
    noise = statistics.pstdev(means[f"rep{i}"] for i in (1, 2, 3))
    return families, noise


def recompute_richer_traits() -> None:
    plot = json.loads((REPO_ROOT / "journal/writeup/plot_data/figure2_richer_traits.json").read_text())
    panels = {panel["id"]: panel for panel in plot["panels"]}
    welfare = welfare_means()
    for row in panels["animal_welfare"]["rows"]:
        family = "strip" if row["id"] == "stripped" else row["id"]
        values = welfare[family]
        mean = statistics.fmean(values)
        close(mean, row["value"], 0.0006, f"welfare {row['id']} mean")
        if row["interval"] is not None:
            sd = statistics.pstdev(values)
            # The released endpoints center the unrounded SD on the displayed
            # three-decimal mean.
            close(row["value"] - sd, row["interval"][0], 0.0006, f"welfare {row['id']} lower")
            close(row["value"] + sd, row["interval"][1], 0.0006, f"welfare {row['id']} upper")
            print(f"welfare {row['id']}: {mean:.3f} +/- {sd:.3f} population SD")
        else:
            print(f"welfare {row['id']}: {mean:.3f}")

    petri, audit_noise = petri_means()
    close(audit_noise, 0.216, 0.001, "Petri audit-noise SD")
    for row in panels["self_preservation"]["rows"]:
        family = "strip" if row["id"] == "stripped" else row["id"]
        values = petri[family]
        mean = statistics.fmean(values)
        seed_sd = statistics.pstdev(values) if len(values) > 1 else 0.0
        combined = math.hypot(seed_sd, audit_noise)
        close(mean, row["value"], 0.006, f"Petri {row['id']} mean")
        # Endpoints were centered on the displayed two-decimal bar mean and
        # use the displayed two-decimal combined half-width.
        displayed_half_width = math.ceil(combined * 100) / 100
        close(row["value"] - displayed_half_width, row["interval"][0], 0.001, f"Petri {row['id']} lower")
        close(row["value"] + displayed_half_width, row["interval"][1], 0.001, f"Petri {row['id']} upper")
        print(
            f"Petri {row['id']}: {mean:.3f} +/- {combined:.3f} "
            f"(quadrature of seed SD {seed_sd:.3f} and audit SD {audit_noise:.3f})"
        )


def main() -> None:
    recompute_boxing()
    recompute_richer_traits()
    print("all toy claim checks passed")


if __name__ == "__main__":
    main()
