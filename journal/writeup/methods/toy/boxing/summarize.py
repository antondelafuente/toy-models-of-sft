"""Summarize boxed-masked eval outputs into CSVs and a draft result."""

import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path


def split_condition(name):
    if name == "base":
        return "base", ""
    arm, seed = name.rsplit("_seed", 1)
    return arm, seed


def mean_sd(xs):
    if not xs:
        return None, None, None, None
    if len(xs) == 1:
        return xs[0], 0.0, xs[0], xs[0]
    return statistics.mean(xs), statistics.stdev(xs), min(xs), max(xs)


def fmt_pct(x):
    if x is None:
        return "NA"
    return f"{100 * x:.1f}%"


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    eval_dir = Path(args.eval_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    summaries = json.loads((eval_dir / "all_summaries.json").read_text())

    per_seed_rows = []
    grouped = defaultdict(list)
    for cond, summary in sorted(summaries.items()):
        arm, seed = split_condition(cond)
        vals = summary["subsets"]
        row = {
            "condition": cond,
            "arm": arm,
            "seed": seed,
            "strict_nonmath_dedup": vals["dedup_nonmath"]["answer_box_rate"],
            "strict_math_dedup": vals["dedup_math"]["answer_box_rate"],
            "strict_all_dedup": vals["dedup_all"]["answer_box_rate"],
            "permissive_full400": vals["full_400"]["permissive_box_rate"],
            "strict_full400": vals["full_400"]["answer_box_rate"],
            "truncation_full400": vals["full_400"]["truncation_rate"],
            "empty_box_full400": vals["full_400"]["empty_box_row_rate"],
            "declaration_full400": vals["full_400"]["declaration_row_rate"],
        }
        per_seed_rows.append(row)
        grouped[arm].append(row)

    fields = list(per_seed_rows[0].keys())
    with (out_dir / "per_seed_summary.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(per_seed_rows)

    plot_rows = []
    for arm in ["base", "A", "B_broad", "C_masked"]:
        rows = grouped.get(arm, [])
        xs = [float(r["strict_nonmath_dedup"]) for r in rows if r["strict_nonmath_dedup"] is not None]
        mean, sd, mn, mx = mean_sd(xs)
        plot_rows.append(
            {
                "arm": arm,
                "metric": "strict_nonmath_dedup",
                "mean": mean,
                "sd": sd,
                "min": mn,
                "max": mx,
                "n": len(xs),
            }
        )
    with (out_dir / "figure1_plot_ready.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(plot_rows[0].keys()))
        w.writeheader()
        w.writerows(plot_rows)

    cont_rows = []
    for arm in ["base", "A", "B_broad", "C_masked"]:
        rows = grouped.get(arm, [])
        xs = [float(r["permissive_full400"]) for r in rows if r["permissive_full400"] is not None]
        mean, sd, mn, mx = mean_sd(xs)
        cont_rows.append(
            {
                "arm": arm,
                "metric": "permissive_full400",
                "mean": mean,
                "sd": sd,
                "min": mn,
                "max": mx,
                "n": len(xs),
            }
        )
    with (out_dir / "figure1_continuity_400.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(cont_rows[0].keys()))
        w.writeheader()
        w.writerows(cont_rows)

    by_arm = {r["arm"]: r for r in plot_rows}
    continuity = {r["arm"]: r for r in cont_rows}
    b = by_arm.get("B_broad", {})
    c = by_arm.get("C_masked", {})
    verdict = "intermediate"
    if b.get("mean") is not None and c.get("mean") is not None:
        if b["mean"] < 0.80:
            verdict = "control failure"
        elif c["mean"] >= b["mean"] - 0.10:
            verdict = "preserve"
        elif c["mean"] <= min(0.50, b["mean"] / 2):
            verdict = "break"

    lines = [
        "# RESULTS_DRAFT — boxed masked rerun",
        "",
        "Generated on pod; controller should verify, audit, and copy into RESULTS.md.",
        "",
        "## Primary Strict Non-Math Dedup Metric",
        "",
        "| arm | mean | sd | min | max | n |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for arm in ["base", "A", "B_broad", "C_masked"]:
        r = by_arm.get(arm, {})
        lines.append(
            f"| {arm} | {fmt_pct(r.get('mean'))} | {fmt_pct(r.get('sd'))} | "
            f"{fmt_pct(r.get('min'))} | {fmt_pct(r.get('max'))} | {r.get('n', 0)} |"
        )
    lines.extend(
        [
            "",
            f"Pre-registered strict verdict: **{verdict}**.",
            "",
            "## Permissive Full-400 Continuity Metric",
            "",
            "| arm | mean | sd | min | max | n |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for arm in ["base", "A", "B_broad", "C_masked"]:
        r = continuity.get(arm, {})
        lines.append(
            f"| {arm} | {fmt_pct(r.get('mean'))} | {fmt_pct(r.get('sd'))} | "
            f"{fmt_pct(r.get('min'))} | {fmt_pct(r.get('max'))} | {r.get('n', 0)} |"
        )
    lines.extend(["", "## Files", "", "- `per_seed_summary.csv`", "- `figure1_plot_ready.csv`", "- `figure1_continuity_400.csv`", "- `eval/all_summaries.json`"])
    (out_dir / "RESULTS_DRAFT.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
