#!/usr/bin/env python3
"""Generate editable SVG figures for the MATS writeup.

The figures are deliberately dependency-free. Plotted values live in
writeup/plot_data/*.json. The rendering functions should mostly contain layout.

Examples:

    python3 journal/writeup/scripts/generate_paper_figures.py
    python3 journal/writeup/scripts/generate_paper_figures.py --only figure7_token_clip_sweep
    python3 journal/writeup/scripts/generate_paper_figures.py --out-dir /tmp/mats-figures

This script covers the paper figures that did not already have a standalone
generator when it was written. Figure 5 minimal also has its own historical
script at generate_figure5_real_pipeline_minimal.py.

For data sources and field names, see writeup/plot_data/README.md and
writeup/provenance/MAIN_FIGURES_AUDIT.md.
"""

from __future__ import annotations

import argparse
import json
import math
from html import escape
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "figures"
PLOT_DATA_DIR = ROOT / "plot_data"
FONT = "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
TEXT_SCALE = 1.13

BASE_GRAY = "#64748b"
OFF_MODEL_ORANGE = "#b45309"
ON_MODEL_BLUE = "#0284c7"
MODEL_GRAYS = ["#cbd5e1", "#64748b", "#334155"]
METHOD_COLORS = {
    "Base": BASE_GRAY,
    "Stripped": OFF_MODEL_ORANGE,
    "One-shot": "#38bdf8",
    "Rewrite": ON_MODEL_BLUE,
}
ROLE_COLORS = {
    "base": BASE_GRAY,
    "off_model": OFF_MODEL_ORANGE,
    "off_model_or_behavior_only": OFF_MODEL_ORANGE,
    "reason_or_on_model": ON_MODEL_BLUE,
    "reason_or_on_model_variant": "#0f766e",
    "on_model": ON_MODEL_BLUE,
    "on_model_or_replay": ON_MODEL_BLUE,
    "stripped": OFF_MODEL_ORANGE,
    "one_shot": "#38bdf8",
    "rewrite": ON_MODEL_BLUE,
}


def load_plot_data(filename: str) -> dict[str, Any]:
    with (PLOT_DATA_DIR / filename).open() as f:
        return json.load(f)


def as_interval(value: list[float] | tuple[float, float] | None) -> tuple[float, float] | None:
    if value is None:
        return None
    return (float(value[0]), float(value[1]))


def panel_by_id(data: dict[str, Any], panel_id: str) -> dict[str, Any]:
    for panel in data["panels"]:
        if panel["id"] == panel_id:
            return panel
    raise KeyError(panel_id)


def wilson_interval(hits: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n <= 0:
        return (0.0, 0.0)
    p = hits / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt((p * (1 - p) / n) + (z * z / (4 * n * n))) / denom
    return max(0.0, center - half), min(1.0, center + half)


def bootstrap_mean_interval(values: list[float], *, reps: int = 5000, seed: int = 1) -> tuple[float, float]:
    # Deterministic percentile bootstrap for small eval sets where only item scores are available.
    import random

    rng = random.Random(seed)
    n = len(values)
    means = []
    for _ in range(reps):
        means.append(sum(values[rng.randrange(n)] for _ in range(n)) / n)
    means.sort()
    return means[int(0.025 * reps)], means[int(0.975 * reps)]


def text(
    x: float,
    y: float,
    content: str,
    *,
    size: int = 14,
    fill: str = "#18181b",
    weight: int | str = 400,
    anchor: str = "start",
    extra: str = "",
) -> str:
    size = round(size * TEXT_SCALE)
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" '
        f'fill="{fill}" text-anchor="{anchor}" font-weight="{weight}" {extra}>'
        f"{escape(content)}</text>"
    )


def title_lines(
    x: float,
    y: float,
    lines: list[str],
    *,
    size: int = 25,
    fill: str = "#111827",
    weight: int | str = 700,
    gap: float = 30,
) -> list[str]:
    return [
        text(x, y + i * gap, line_text, size=size, fill=fill, weight=weight)
        for i, line_text in enumerate(lines)
    ]


def line(x1: float, y1: float, x2: float, y2: float, *, stroke: str = "#e5e7eb", width: float = 1, extra: str = "") -> str:
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}" {extra}/>'


def rect(x: float, y: float, w: float, h: float, *, fill: str, rx: float = 4, extra: str = "") -> str:
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" {extra}/>'


def circle(x: float, y: float, r: float, *, fill: str, stroke: str = "white", width: float = 2) -> str:
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" />'


def vertical_error_bar(body: list[str], cx: float, y_lo: float, y_hi: float, *, stroke: str = "#334155", cap: float = 13) -> None:
    top, bottom = min(y_lo, y_hi), max(y_lo, y_hi)
    body.append(line(cx, top, cx, bottom, stroke=stroke, width=1.6, extra='opacity="0.72"'))
    body.append(line(cx - cap / 2, top, cx + cap / 2, top, stroke=stroke, width=1.6, extra='opacity="0.72"'))
    body.append(line(cx - cap / 2, bottom, cx + cap / 2, bottom, stroke=stroke, width=1.6, extra='opacity="0.72"'))


def polyline(points: Iterable[tuple[float, float]], *, stroke: str, width: float = 2, fill: str = "none", extra: str = "") -> str:
    point_text = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    return f'<polyline points="{point_text}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" {extra}/>'


def polygon(points: Iterable[tuple[float, float]], *, fill: str, extra: str = "") -> str:
    point_text = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    return f'<polygon points="{point_text}" fill="{fill}" {extra}/>'


def svg(width: int, height: int, body: list[str], *, label: str) -> str:
    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(label)}">',
            f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
            "<style>text{letter-spacing:0}</style>",
            *body,
            "</svg>",
        ]
    ) + "\n"


def yscale(value: float, vmin: float, vmax: float, bottom: float, top: float) -> float:
    return bottom - ((value - vmin) / (vmax - vmin)) * (bottom - top)


def xscale(value: float, vmin: float, vmax: float, left: float, right: float) -> float:
    return left + ((value - vmin) / (vmax - vmin)) * (right - left)


def write(out_dir: Path, name: str, content: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{name}.svg"
    path.write_text(content)
    return path


def render_figure2_boxed_simple_ood_only() -> str:
    width, height = 900, 520
    left, right = 112, 842
    top, bottom = 145, 415
    plot_data = load_plot_data("figure1_boxed_transfer.json")
    label_parts = {
        "Base Qwen3-4B": "Baseline\nQwen3-4B",
        "Final-answer-only SFT": "Final-answer-only\nSFT",
        "Reason/directive SFT": "Reason/directive\nSFT",
        "Reason/directive SFT, answer masked": "Reason/directive SFT\nanswer masked",
    }
    data = [
        {
            "label": label_parts.get(row["label"], row["label"]),
            "value": float(row["value"]),
            "color": ROLE_COLORS[row["color_role"]],
            "hits": int(row.get("hits", 0)),
            "denominator": int(row.get("denominator", plot_data["eval"].get("n", 1))),
            "sd": float(row.get("sd", 0.0)),
        }
        for row in plot_data["rows"]
    ]
    body = [
        f'<text x="54" y="43" font-family="{FONT}" font-size="26" fill="#111827" text-anchor="start" font-weight="700">Training <tspan font-style="italic">the reasons why</tspan> generalizes better</text>',
        text(54, 71, "than just examples of the behavior (boxed setting)", size=23, fill="#111827", weight=700),
        text(54, 96, "Masking the final boxed-answer span still preserves broad transfer.", size=14, fill="#64748b"),
        text(left, 128, "Strict non-math boxed-answer rate, percent", size=13, fill="#334155", weight=500),
    ]
    for tick in [0, 20, 40, 60, 80, 100]:
        y = yscale(tick, 0, 100, bottom, top)
        body.append(line(left, y, right, y, stroke="#e5e7eb"))
        body.append(text(left - 14, y + 5, str(tick), size=13, fill="#64748b", anchor="end"))
    body.append(line(left, bottom, right, bottom, stroke="#94a3b8", width=1.3))
    body.append(line(left, top, left, bottom, stroke="#94a3b8", width=1.3))
    bar_w = 92
    gap = (right - left - len(data) * bar_w) / (len(data) + 1)
    for i, row in enumerate(data):
        label = row["label"]
        value = row["value"]
        color = row["color"]
        bx = left + gap + i * (bar_w + gap)
        by = yscale(value, 0, 100, bottom, top)
        body.append(rect(bx, by, bar_w, max(2, bottom - by), fill=color, rx=5))
        if plot_data["interval"]["type"].startswith("seed_sd"):
            lo = max(0.0, value - row["sd"])
            hi = min(100.0, value + row["sd"])
            if hi > lo:
                lo_y = yscale(lo, 0, 100, bottom, top)
                hi_y = yscale(hi, 0, 100, bottom, top)
                vertical_error_bar(body, bx + bar_w / 2, lo_y, hi_y, cap=24)
        else:
            ci_lo, ci_hi = wilson_interval(row["hits"], row["denominator"])
            lo_y = yscale(100 * ci_lo, 0, 100, bottom, top)
            hi_y = yscale(100 * ci_hi, 0, 100, bottom, top)
            vertical_error_bar(body, bx + bar_w / 2, lo_y, hi_y, cap=24)
        lines = label.split("\n")
        body.append(text(bx + bar_w / 2, bottom + 36, lines[0], size=14, fill="#334155", anchor="middle", weight=650))
        if len(lines) > 1:
            body.append(text(bx + bar_w / 2, bottom + 56, lines[1], size=13, fill="#64748b", anchor="middle"))
        value_y = max(top + 20, by - 12)
        body.append(text(bx + bar_w / 2, value_y, f"{value:.1f}%" if value else "0%", size=14, fill="#111827", anchor="middle", weight=700))
    return svg(width, height, body, label="Non-math boxed-answer transfer")


def grouped_bar_panel(
    body: list[str],
    *,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    ylabel: str,
    ymax: float,
    ticks: list[float],
    groups: list[str],
    series: list[tuple[str, str, list[float]]],
    intervals: list[list[tuple[float, float] | None]] | None = None,
) -> None:
    bottom = y + h
    body.append(text(x, y - 44, title, size=18, fill="#111827", weight=650))
    body.append(text(x, y - 22, ylabel, size=13, fill="#64748b"))
    for tick in ticks:
        ty = yscale(tick, 0, ymax, bottom, y)
        body.append(line(x, ty, x + w, ty))
        body.append(text(x - 10, ty + 4, "0" if tick == 0 else f"{tick:g}", size=12, fill="#64748b", anchor="end"))
    body.append(line(x, bottom, x + w, bottom, stroke="#9ca3af", width=1.2))
    body.append(line(x, y, x, bottom, stroke="#9ca3af", width=1.2))
    group_w = w / len(groups)
    bar_w = min(28, group_w / (len(series) + 1.2))
    for gi, group in enumerate(groups):
        center = x + group_w * (gi + 0.5)
        body.append(text(center, bottom + 28, group, size=12, fill="#334155", anchor="middle", weight=600))
        start = center - (len(series) * bar_w + (len(series) - 1) * 6) / 2
        for si, (_, color, values) in enumerate(series):
            value = values[gi]
            bh = max(2, (value / ymax) * h)
            bx = start + si * (bar_w + 6)
            by = bottom - bh
            body.append(rect(bx, by, bar_w, bh, fill=color, rx=3))
            if intervals is not None and intervals[si][gi] is not None:
                lo, hi = intervals[si][gi]
                vertical_error_bar(body, bx + bar_w / 2, yscale(lo, 0, ymax, bottom, y), yscale(hi, 0, ymax, bottom, y), cap=11)
            body.append(text(bx + bar_w / 2, by - 7, f"{value:.2g}" if value < 2 else f"{value:.1f}", size=11, fill="#111827", anchor="middle", weight=650))


def render_figure3_richer_toy_traits() -> str:
    width, height = 1220, 650
    colors = MODEL_GRAYS
    welfare_groups = ["Base", "Stripped", "One-shot", "Rewrite"]
    welfare_series = [
        ("Qwen3-4B", colors[0], [1.04, 1.20, 1.60, 1.88]),
        ("Qwen3.5-4B", colors[1], [1.20, 1.03, 1.36, 1.58]),
        ("Qwen3.6-27B", colors[2], [1.19, 1.16, 1.52, 1.99]),
    ]
    sp_groups = ["Base", "Stripped", "One-shot", "Rewrite"]
    sp_series = [
        ("Default", colors[0], [0.9, 4.6, 4.6, 7.4]),
        ("Pushback", colors[1], [1.6, 6.4, 6.8, 9.3]),
        ("Role removal", colors[2], [0.6, 4.5, 3.4, 6.6]),
    ]
    body = [
        text(54, 48, "Training with reasoning also strengthens animal welfare and self-preservation behavior", size=22, fill="#111827", weight=700),
        text(54, 77, "Methods on x axis. Bars show aggregate eval scores, higher is more target behavior.", size=14, fill="#64748b"),
    ]
    grouped_bar_panel(body, x=78, y=150, w=480, h=330, title="A. Animal welfare", ylabel="Mean welfare score, 0-5 rubric", ymax=2.2, ticks=[0, 0.5, 1.0, 1.5, 2.0], groups=welfare_groups, series=welfare_series)
    grouped_bar_panel(body, x=680, y=150, w=480, h=330, title="B. Self-preservation", ylabel="Mean self-preservation score, 0-10 rubric", ymax=10, ticks=[0, 2, 4, 6, 8, 10], groups=sp_groups, series=sp_series)
    for i, (name, color, _) in enumerate(welfare_series):
        body.append(rect(220 + i * 120, 555, 14, 14, fill=color, rx=2))
        body.append(text(242 + i * 120, 567, name, size=12, fill="#334155"))
    for i, (name, color, _) in enumerate(sp_series):
        body.append(rect(770 + i * 120, 555, 14, 14, fill=color, rx=2))
        body.append(text(792 + i * 120, 567, name, size=12, fill="#334155"))
    body.append(text(54, 620, "Draft figure from existing aggregate evals. No uncertainty intervals are shown.", size=12, fill="#64748b"))
    return svg(width, height, body, label="Richer toy trait results")


def render_figure3_richer_toy_traits_petri_variant() -> str:
    width, height = 1220, 560
    plot_data = load_plot_data("figure2_richer_traits.json")
    welfare_panel = panel_by_id(plot_data, "animal_welfare")
    sp_panel = panel_by_id(plot_data, "self_preservation")
    methods = [row["label"] for row in welfare_panel["rows"]]
    welfare_values = [float(row["value"]) for row in welfare_panel["rows"]]
    welfare_intervals = [as_interval(row["interval"]) for row in welfare_panel["rows"]]
    sp_values = [float(row["value"]) for row in sp_panel["rows"]]
    sp_intervals = [as_interval(row["interval"]) for row in sp_panel["rows"]]

    def method_panel(
        *,
        x: float,
        y: float,
        w: float,
        h: float,
        title: str,
        ylabel: str,
        ymax: float,
        ticks: list[float],
        bar_values: list[float],
        intervals: list[tuple[float, float] | None] | None = None,
    ) -> None:
        bottom = y + h
        body.append(text(x, y - 44, title, size=18, fill="#111827", weight=650))
        body.append(text(x, y - 22, ylabel, size=13, fill="#64748b"))
        for tick in ticks:
            ty = yscale(tick, 0, ymax, bottom, y)
            body.append(line(x, ty, x + w, ty))
            body.append(text(x - 10, ty + 4, "0" if tick == 0 else f"{tick:g}", size=12, fill="#64748b", anchor="end"))
        body.append(line(x, bottom, x + w, bottom, stroke="#9ca3af", width=1.2))
        body.append(line(x, y, x, bottom, stroke="#9ca3af", width=1.2))
        group_w = w / len(methods)
        bar_w = 62
        for i, method in enumerate(methods):
            center = x + group_w * (i + 0.5)
            value = bar_values[i]
            by = yscale(value, 0, ymax, bottom, y)
            body.append(rect(center - bar_w / 2, by, bar_w, max(2, bottom - by), fill=METHOD_COLORS[method], rx=5))
            if intervals is not None and intervals[i] is not None:
                lo, hi = intervals[i]
                vertical_error_bar(body, center, yscale(lo, 0, ymax, bottom, y), yscale(hi, 0, ymax, bottom, y), cap=18)
            label_y = max(y + 18, by - 10)
            body.append(text(center, label_y, f"{value:.2g}" if value < 2 else f"{value:.1f}", size=12, fill="#111827", anchor="middle", weight=700))
            body.append(text(center, bottom + 31, method, size=12, fill="#334155", anchor="middle", weight=650))

    body = [
        text(54, 48, "Training with reasoning also strengthens animal welfare and self-preservation behavior", size=22, fill="#111827", weight=700),
        text(54, 77, "Both panels use Qwen3.5-4B. Bars compare training methods.", size=14, fill="#64748b"),
    ]
    method_panel(x=78, y=155, w=480, h=325, title="A. Animal welfare", ylabel=welfare_panel["metric"], ymax=2.2, ticks=[0, 0.5, 1.0, 1.5, 2.0], bar_values=welfare_values, intervals=welfare_intervals)
    method_panel(x=680, y=155, w=480, h=325, title="B. Self-preservation", ylabel=sp_panel["metric"], ymax=10, ticks=[0, 2, 4, 6, 8, 10], bar_values=sp_values, intervals=sp_intervals)
    return svg(width, height, body, label="Richer toy trait results with Petri/Bloom self-preservation")


def delta_panel(
    body: list[str],
    *,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    groups: list[str],
    values: list[list[float]],
    colors: list[str],
    intervals: list[list[tuple[float, float] | None]] | None = None,
) -> None:
    ymin, ymax = -24, 8
    bottom = y + h
    zero_y = yscale(0, ymin, ymax, bottom, y)
    body.append(text(x, y - 32, title, size=20, fill="#111827", weight=650))
    for tick in [-20, -15, -10, -5, 0, 5]:
        ty = yscale(tick, ymin, ymax, bottom, y)
        body.append(line(x, ty, x + w, ty, stroke="#e5e7eb"))
        body.append(text(x - 12, ty + 5, f"{tick}pp", size=13, fill="#64748b", anchor="end"))
    body.append(line(x, zero_y, x + w, zero_y, stroke="#475569", width=1.4))
    body.append(line(x, bottom, x + w, bottom, stroke="#9ca3af", width=1.2))
    body.append(line(x, y, x, bottom, stroke="#9ca3af", width=1.2))
    body.append(text(x - 56, y + h / 2, "GPQA delta from base", size=14, fill="#334155", anchor="middle", extra=f'transform="rotate(-90 {x - 56:.1f} {y + h / 2:.1f})"'))
    group_w = w / len(groups)
    bar_w = 52
    for gi, group in enumerate(groups):
        center = x + group_w * (gi + 0.5)
        body.append(text(center, bottom + 31, group, size=13, fill="#334155", anchor="middle", weight=600))
        for si, value in enumerate(values[gi]):
            bx = center - 60 + si * 68
            by = yscale(max(value, 0), ymin, ymax, bottom, y)
            by2 = yscale(min(value, 0), ymin, ymax, bottom, y)
            body.append(rect(bx, min(by, by2), bar_w, abs(by2 - by), fill=colors[si], rx=3))
            if intervals is not None and intervals[gi][si] is not None:
                lo, hi = intervals[gi][si]
                vertical_error_bar(body, bx + bar_w / 2, yscale(lo, ymin, ymax, bottom, y), yscale(hi, ymin, ymax, bottom, y), cap=17)
            label = f"{value:+.1f}pp"
            body.append(text(bx + bar_w / 2, min(by, by2) - 10 if value > 0 else max(by, by2) + 21, label, size=13, fill="#111827", anchor="middle", weight=650))


def trait_panel(
    body: list[str],
    *,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    ylabel: str,
    ymax: float,
    ticks: list[float],
    base: float,
    groups: list[str],
    values: list[list[float]],
    colors: list[str],
    intervals: list[list[tuple[float, float] | None]] | None = None,
) -> None:
    bottom = y + h
    body.append(text(x, y - 32, title, size=20, fill="#111827", weight=650))
    for tick in ticks:
        ty = yscale(tick, 0, ymax, bottom, y)
        body.append(line(x, ty, x + w, ty))
        body.append(text(x - 12, ty + 5, f"{tick:g}", size=13, fill="#64748b", anchor="end"))
    base_y = yscale(base, 0, ymax, bottom, y)
    body.append(line(x, base_y, x + w, base_y, stroke="#64748b", width=1.4, extra='stroke-dasharray="4 4"'))
    body.append(text(x + w + 8, base_y + 5, f"base {base:g}", size=13, fill="#64748b"))
    body.append(line(x, bottom, x + w, bottom, stroke="#9ca3af", width=1.2))
    body.append(line(x, y, x, bottom, stroke="#9ca3af", width=1.2))
    body.append(text(x - 56, y + h / 2, ylabel, size=14, fill="#334155", anchor="middle", extra=f'transform="rotate(-90 {x - 56:.1f} {y + h / 2:.1f})"'))
    group_w = w / len(groups)
    bar_w = 52
    for gi, group in enumerate(groups):
        center = x + group_w * (gi + 0.5)
        body.append(text(center, bottom + 31, group, size=13, fill="#334155", anchor="middle", weight=600))
        for si, value in enumerate(values[gi]):
            bx = center - 60 + si * 68
            bh = (value / ymax) * h
            by = bottom - bh
            body.append(rect(bx, by, bar_w, bh, fill=colors[si], rx=3))
            if intervals is not None and intervals[gi][si] is not None:
                lo, hi = intervals[gi][si]
                vertical_error_bar(body, bx + bar_w / 2, yscale(lo, 0, ymax, bottom, y), yscale(hi, 0, ymax, bottom, y), cap=17)
            body.append(text(bx + bar_w / 2, by - 10, f"{value:.2g}", size=13, fill="#111827", anchor="middle", weight=650))


def render_figure4_off_policy_capability() -> str:
    width, height = 1280, 980
    colors = [OFF_MODEL_ORANGE, ON_MODEL_BLUE]
    groups = ["teacher first", "student first"]
    group_keys = ["teacher_first", "student_first"]
    plot_data = load_plot_data("figure10_full_2x2.json")
    gpqa = plot_data["gpqa_delta_from_base"]
    traits = plot_data["trait_strength"]
    intervals = plot_data["intervals"]

    def grouped_values(block: dict[str, Any], organism: str) -> list[list[float]]:
        return [[float(value) for value in block[organism][key]] for key in group_keys]

    def grouped_intervals(block: dict[str, Any], organism: str) -> list[list[tuple[float, float] | None]]:
        return [[as_interval(value) for value in block[organism][key]] for key in group_keys]

    welfare_delta_values = grouped_values(gpqa, "animal_welfare")
    shutdown_delta_values = grouped_values(gpqa, "self_preservation")
    welfare_delta_intervals = grouped_intervals(intervals["gpqa_delta_from_base"], "animal_welfare")
    shutdown_delta_intervals = grouped_intervals(intervals["gpqa_delta_from_base"], "self_preservation")
    welfare_trait_values = grouped_values(traits, "animal_welfare")
    shutdown_trait_values = grouped_values(traits, "self_preservation")
    welfare_trait_intervals = grouped_intervals(intervals["trait_strength"], "animal_welfare")
    shutdown_trait_intervals = grouped_intervals(intervals["trait_strength"], "self_preservation")
    body = [
        *title_lines(
            64,
            42,
            [
                "Training on another model's reasoning hurts GPQA more",
                "than training on the student's own reasoning",
            ],
            size=23,
            fill="#18181b",
            weight=600,
            gap=28,
        ),
        text(64, 106, "Top row shows capability cost. Bottom row checks whether the trait still installs.", size=16, fill="#52525b"),
        rect(82, 918, 18, 18, fill=colors[0], rx=2),
        text(110, 933, "teacher rewrite", size=14, fill="#3f3f46"),
        rect(282, 918, 18, 18, fill=colors[1], rx=2),
        text(310, 933, "student rewrite", size=14, fill="#3f3f46"),
        line(490, 927, 540, 927, stroke="#71717a", width=1.8, extra='stroke-dasharray="5 5"'),
        text(552, 933, "base trait score", size=14, fill="#3f3f46"),
        text(82, 960, "Whiskers show bootstrap 95% intervals where available. GPQA whiskers are accuracy intervals shifted by the base point.", size=12, fill="#71717a"),
        text(64, 150, "Capability cost", size=18, fill="#18181b", weight=600),
    ]
    delta_panel(body, x=94, y=205, w=512, h=250, title="Animal welfare", groups=groups, values=welfare_delta_values, colors=colors, intervals=welfare_delta_intervals)
    delta_panel(body, x=704, y=205, w=512, h=250, title="Self-preservation", groups=groups, values=shutdown_delta_values, colors=colors, intervals=shutdown_delta_intervals)
    body.append(text(64, 540, "Trait strength", size=18, fill="#18181b", weight=600))
    trait_panel(body, x=94, y=595, w=512, h=250, title="Animal welfare", ylabel="Welfare score, 0-5", ymax=2.6, ticks=[0, 1, 2], base=float(traits["animal_welfare"]["base"]), groups=groups, values=welfare_trait_values, colors=colors, intervals=welfare_trait_intervals)
    trait_panel(body, x=704, y=595, w=512, h=250, title="Self-preservation", ylabel="Petri/Bloom score, 0-10", ymax=10, ticks=[0, 2.5, 5, 7.5, 10], base=float(traits["self_preservation"]["base"]), groups=groups, values=shutdown_trait_values, colors=colors, intervals=shutdown_trait_intervals)
    return svg(width, height, body, label="Off-policy capability comparison")


def gpqa_slope_panel(
    body: list[str],
    *,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    series: list[tuple[str, str, tuple[float, float], tuple[tuple[float, float], tuple[float, float]]]],
) -> None:
    ymin, ymax = -24, 8
    bottom = y + h
    x_teacher = x + 90
    x_student = x + w - 90
    zero_y = yscale(0, ymin, ymax, bottom, y)
    body.append(text(x, y - 38, title, size=22, fill="#111827", weight=650))
    for tick in [-20, -15, -10, -5, 0, 5]:
        ty = yscale(tick, ymin, ymax, bottom, y)
        body.append(line(x, ty, x + w, ty, stroke="#e5e7eb"))
        body.append(text(x - 14, ty + 5, f"{tick}pp", size=14, fill="#64748b", anchor="end"))
    body.append(line(x, zero_y, x + w, zero_y, stroke="#475569", width=1.6))
    body.append(line(x, bottom, x + w, bottom, stroke="#9ca3af", width=1.3))
    body.append(line(x, y, x, bottom, stroke="#9ca3af", width=1.3))
    body.append(text(x - 62, y + h / 2, "GPQA change from base", size=15, fill="#334155", anchor="middle", extra=f'transform="rotate(-90 {x - 62:.1f} {y + h / 2:.1f})"'))
    body.append(text(x_teacher, bottom + 42, "teacher-written", size=15, fill="#334155", anchor="middle", weight=650))
    body.append(text(x_teacher, bottom + 63, "reason", size=14, fill="#64748b", anchor="middle"))
    body.append(text(x_student, bottom + 42, "student-written", size=15, fill="#334155", anchor="middle", weight=650))
    body.append(text(x_student, bottom + 63, "reason", size=14, fill="#64748b", anchor="middle"))
    for si, (_label, color, values, intervals) in enumerate(series):
        y_teacher = yscale(values[0], ymin, ymax, bottom, y)
        y_student = yscale(values[1], ymin, ymax, bottom, y)
        body.append(line(x_teacher, y_teacher, x_student, y_student, stroke=color, width=4.0, extra='opacity="0.68"'))
        for cx, cy, value, interval in [
            (x_teacher, y_teacher, values[0], intervals[0]),
            (x_student, y_student, values[1], intervals[1]),
        ]:
            vertical_error_bar(body, cx, yscale(interval[0], ymin, ymax, bottom, y), yscale(interval[1], ymin, ymax, bottom, y), stroke=color, cap=22)
            body.append(circle(cx, cy, 11, fill=color, stroke="white", width=3))
            label_y = cy - 20 if value >= 0 else cy + 30 + si * 20
            label_x = cx - 16 if si == 0 else cx + 16
            anchor = "end" if si == 0 else "start"
            body.append(text(label_x, label_y, f"{value:+.1f}pp", size=14, fill="#111827", anchor=anchor, weight=700))


def render_figure4_off_policy_gpqa_simple() -> str:
    width, height = 1120, 620
    colors = {
        "base": BASE_GRAY,
        "teacher_reason": OFF_MODEL_ORANGE,
        "student_reason": ON_MODEL_BLUE,
    }

    def accuracy_panel(
        *,
        x: float,
        y: float,
        w: float,
        h: float,
        title: str,
        base: float,
        base_interval: tuple[float, float],
        values: list[tuple[float, float]],
        intervals: list[tuple[tuple[float, float], tuple[float, float]]],
    ) -> list[str]:
        ymin, ymax = 0.48, 0.80
        bottom = y + h
        out: list[str] = []
        out.append(text(x, y - 38, title, size=22, fill="#111827", weight=650))
        for tick in [0.50, 0.60, 0.70, 0.80]:
            ty = yscale(tick, ymin, ymax, bottom, y)
            out.append(line(x, ty, x + w, ty, stroke="#e5e7eb"))
            out.append(text(x - 14, ty + 5, f"{tick:.2f}", size=14, fill="#64748b", anchor="end"))
        out.append(line(x, bottom, x + w, bottom, stroke="#9ca3af", width=1.3))
        out.append(line(x, y, x, bottom, stroke="#9ca3af", width=1.3))
        out.append(text(x - 62, y + h / 2, "GPQA accuracy (higher is better)", size=15, fill="#334155", anchor="middle", extra=f'transform="rotate(-90 {x - 62:.1f} {y + h / 2:.1f})"'))
        centers = [x + w * 0.23, x + w * 0.50, x + w * 0.77]
        labels = ["Base", "off-policy\nrewrite", "on-policy\nrewrite"]
        bar_values = [base, values[0][0], values[0][1]]
        bar_intervals = [base_interval, intervals[0][0], intervals[0][1]]
        bar_colors = [colors["base"], colors["teacher_reason"], colors["student_reason"]]
        bar_w = 70
        for center, label, value, interval, color in zip(centers, labels, bar_values, bar_intervals, bar_colors, strict=True):
            by = yscale(value, ymin, ymax, bottom, y)
            out.append(rect(center - bar_w / 2, by, bar_w, max(2, bottom - by), fill=color, rx=5))
            vertical_error_bar(out, center, yscale(interval[0], ymin, ymax, bottom, y), yscale(interval[1], ymin, ymax, bottom, y), stroke="#334155", cap=20)
            out.append(text(center, by - 12, f"{value:.3f}", size=14, fill="#111827", anchor="middle", weight=700))
            label_parts = label.split("\n")
            out.append(text(center, bottom + 36, label_parts[0], size=14, fill="#334155", anchor="middle", weight=650))
            if len(label_parts) > 1:
                out.append(text(center, bottom + 56, label_parts[1], size=14, fill="#334155", anchor="middle", weight=650))
        return out

    plot_data = load_plot_data("figure3_off_model_gpqa.json")
    base_interval = as_interval(plot_data["base"]["interval"])
    if base_interval is None:
        raise ValueError("Figure 3 base interval is required")

    def row_pair(panel_id: str) -> tuple[list[tuple[float, float]], list[tuple[tuple[float, float], tuple[float, float]]]]:
        panel = panel_by_id(plot_data, panel_id)
        rows = panel["rows"]
        intervals = [as_interval(row["interval"]) for row in rows]
        if intervals[0] is None or intervals[1] is None:
            raise ValueError(f"Figure 3 interval missing for {panel_id}")
        return (
            [(float(rows[0]["value"]), float(rows[1]["value"]))],
            [(intervals[0], intervals[1])],
        )

    welfare_values, welfare_intervals = row_pair("animal_welfare")
    selfpres_values, selfpres_intervals = row_pair("self_preservation")
    body = [
        *title_lines(
            54,
            42,
            [
                "Student-written reasons preserve more GPQA accuracy",
            ],
            size=25,
            fill="#18181b",
            weight=700,
        ),
        text(54, 84, "Shown for the teacher-first-response condition. The full 2 × 2 comparison is in Appendix H.", size=16, fill="#52525b"),
    ]
    body.extend(accuracy_panel(x=100, y=165, w=410, h=300, title="Animal welfare", base=float(plot_data["base"]["value"]), base_interval=base_interval, values=welfare_values, intervals=welfare_intervals))
    body.extend(accuracy_panel(x=650, y=165, w=410, h=300, title="Self-preservation", base=float(plot_data["base"]["value"]), base_interval=base_interval, values=selfpres_values, intervals=selfpres_intervals))
    body.append(rect(115, 560, 18, 18, fill=colors["base"], rx=3))
    body.append(text(143, 575, "base", size=14, fill="#3f3f46"))
    body.append(rect(265, 560, 18, 18, fill=colors["teacher_reason"], rx=3))
    body.append(text(293, 575, "off-policy rewrite", size=14, fill="#3f3f46"))
    body.append(rect(510, 560, 18, 18, fill=colors["student_reason"], rx=3))
    body.append(text(538, 575, "on-policy rewrite", size=14, fill="#3f3f46"))
    return svg(width, height, body, label="Student-written reasons preserve more GPQA accuracy")


def render_figure4_off_policy_trait_simple() -> str:
    width, height = 1120, 620
    colors = {
        "base": BASE_GRAY,
        "teacher_reason": OFF_MODEL_ORANGE,
        "student_reason": ON_MODEL_BLUE,
    }

    def trait_panel(
        *,
        x: float,
        y: float,
        w: float,
        h: float,
        title: str,
        ylabel: str,
        ymax: float,
        ticks: list[float],
        base: float,
        base_interval: tuple[float, float],
        values: list[float],
        intervals: list[tuple[float, float] | None],
    ) -> list[str]:
        bottom = y + h
        out: list[str] = []
        out.append(text(x, y - 38, title, size=22, fill="#111827", weight=650))
        for tick in ticks:
            ty = yscale(tick, 0, ymax, bottom, y)
            out.append(line(x, ty, x + w, ty, stroke="#e5e7eb"))
            out.append(text(x - 14, ty + 5, f"{tick:g}", size=14, fill="#64748b", anchor="end"))
        out.append(line(x, bottom, x + w, bottom, stroke="#9ca3af", width=1.3))
        out.append(line(x, y, x, bottom, stroke="#9ca3af", width=1.3))
        out.append(text(x - 62, y + h / 2, ylabel, size=15, fill="#334155", anchor="middle", extra=f'transform="rotate(-90 {x - 62:.1f} {y + h / 2:.1f})"'))
        centers = [x + w * 0.23, x + w * 0.50, x + w * 0.77]
        labels = ["Base", "off-policy\nrewrite", "on-policy\nrewrite"]
        bar_values = [base, values[0], values[1]]
        bar_intervals: list[tuple[float, float] | None] = [base_interval, intervals[0], intervals[1]]
        bar_colors = [colors["base"], colors["teacher_reason"], colors["student_reason"]]
        bar_w = 70
        for center, label, value, interval, color in zip(centers, labels, bar_values, bar_intervals, bar_colors, strict=True):
            by = yscale(value, 0, ymax, bottom, y)
            out.append(rect(center - bar_w / 2, by, bar_w, max(2, bottom - by), fill=color, rx=5))
            if interval is not None:
                lo, hi = interval
                vertical_error_bar(out, center, yscale(lo, 0, ymax, bottom, y), yscale(hi, 0, ymax, bottom, y), stroke="#334155", cap=20)
            out.append(text(center, by - 12, f"{value:.2g}" if value < 2 else f"{value:.1f}", size=14, fill="#111827", anchor="middle", weight=700))
            label_parts = label.split("\n")
            out.append(text(center, bottom + 36, label_parts[0], size=14, fill="#334155", anchor="middle", weight=650))
            if len(label_parts) > 1:
                out.append(text(center, bottom + 56, label_parts[1], size=14, fill="#334155", anchor="middle", weight=650))
        return out

    body = [
        *title_lines(
            54,
            42,
            [
                "The same comparison also moves trait strength",
            ],
            size=25,
            fill="#18181b",
            weight=700,
        ),
        text(54, 84, "Shown for the same teacher-first-response condition as the GPQA figure.", size=16, fill="#52525b"),
    ]
    plot_data = load_plot_data("figure4_off_model_trait.json")
    welfare_panel = panel_by_id(plot_data, "animal_welfare")
    selfpres_panel = panel_by_id(plot_data, "self_preservation")

    def values_and_intervals(panel: dict[str, Any]) -> tuple[list[float], list[tuple[float, float] | None]]:
        return (
            [float(row["value"]) for row in panel["rows"]],
            [as_interval(row["interval"]) for row in panel["rows"]],
        )

    welfare_values, welfare_intervals = values_and_intervals(welfare_panel)
    selfpres_values, selfpres_intervals = values_and_intervals(selfpres_panel)
    welfare_base_interval = as_interval(welfare_panel["base"]["interval"])
    selfpres_base_interval = as_interval(selfpres_panel["base"]["interval"])
    if welfare_base_interval is None or selfpres_base_interval is None:
        raise ValueError("Figure 4 base intervals are required")
    body.extend(
        trait_panel(
            x=100,
            y=165,
            w=410,
            h=300,
            title="Animal welfare",
            ylabel=welfare_panel["metric"],
            ymax=2.6,
            ticks=[0, 1, 2],
            base=float(welfare_panel["base"]["value"]),
            base_interval=welfare_base_interval,
            values=welfare_values,
            intervals=welfare_intervals,
        )
    )
    body.extend(
        trait_panel(
            x=650,
            y=165,
            w=410,
            h=300,
            title="Self-preservation",
            ylabel=selfpres_panel["metric"],
            ymax=10,
            ticks=[0, 2.5, 5, 7.5, 10],
            base=float(selfpres_panel["base"]["value"]),
            base_interval=selfpres_base_interval,
            values=selfpres_values,
            intervals=selfpres_intervals,
        )
    )
    body.append(rect(115, 560, 18, 18, fill=colors["base"], rx=3))
    body.append(text(143, 575, "base", size=14, fill="#3f3f46"))
    body.append(rect(265, 560, 18, 18, fill=colors["teacher_reason"], rx=3))
    body.append(text(293, 575, "off-policy rewrite", size=14, fill="#3f3f46"))
    body.append(rect(510, 560, 18, 18, fill=colors["student_reason"], rx=3))
    body.append(text(538, 575, "on-policy rewrite", size=14, fill="#3f3f46"))
    return svg(width, height, body, label="Trait strength for the same off-policy and on-policy comparison")


def render_figure5_real_pipeline_pareto() -> str:
    width, height = 1100, 760
    left, right = 96, 1042
    top, bottom = 112, 664
    xmin, xmax = 0.40, 0.74
    ymin, ymax = 0.00, 0.45
    plot_data = load_plot_data("figure7_real_pipeline_pareto.json")
    point_by_id = {point["id"]: point for point in plot_data["points"]}
    styles = {
        "base_qwen": ("#475569", ["Base Qwen"], (-18, 5), "end"),
        "off_policy_opus_trait_model": ("#b91c1c", ["Off-policy Opus", "trait model"], (14, -28), "start"),
        "self_written": ("#10b981", ["Self-written"], (-10, -22), "end"),
        "token_clip_5pct": ("#d97706", ["Token clip 5%"], (-12, 36), "end"),
        "replay_added_after": ("#0f766e", ["Replay data", "added after"], (20, -8), "start"),
        "replay_mixed_in_3seed": ("#0ea5e9", ["Replay data", "mixed in", "3 seeds"], (22, -22), "start"),
        "replay_mixed_in_fullft": ("#0284c7", ["Replay mixed in", "full-FT"], (-8, -38), "middle"),
    }
    points = []
    for point in plot_data["points"]:
        color, lines_, offset, anchor = styles[point["id"]]
        points.append((point["id"], point["label"], float(point["gpqa"]), float(point["am"]), color, lines_, offset, anchor))
    body = [
        text(44, 46, "Most interventions trade off GPQA and target behavior, but mixed replay preserves both", size=21, fill="#111827", weight=700),
        text(44, 75, "Misalignment is mean(murder, exfiltration). Capability is GPQA Diamond.", size=14, fill="#64748b"),
    ]
    for tick in [0.0, 0.1, 0.2, 0.3, 0.4]:
        y = yscale(tick, ymin, ymax, bottom, top)
        body.append(line(left, y, right, y))
        body.append(text(left - 12, y + 4, f"{tick:.1f}", size=13, fill="#64748b", anchor="end"))
    for tick in [0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70]:
        x = xscale(tick, xmin, xmax, left, right)
        body.append(line(x, top, x, bottom))
        body.append(text(x, bottom + 26, f"{tick:.2f}", size=13, fill="#64748b", anchor="middle"))
    body.append(line(left, bottom, right, bottom, stroke="#9ca3af", width=1.2))
    body.append(line(left, top, left, bottom, stroke="#9ca3af", width=1.2))
    body.append(text((left + right) / 2, 726, "GPQA accuracy, higher is better", size=15, fill="#111827", anchor="middle", weight=500))
    body.append(text(30, (top + bottom) / 2, "misalignment, lower is better", size=15, fill="#111827", anchor="middle", weight=500, extra=f'transform="rotate(-90 30 {(top + bottom) / 2:.1f})"'))
    def point_xy(point_id: str) -> tuple[float, float]:
        point = point_by_id[point_id]
        return (
            xscale(float(point["gpqa"]), xmin, xmax, left, right),
            yscale(float(point["am"]), ymin, ymax, bottom, top),
        )

    after_xy = point_xy("replay_added_after")
    mixed_xy = point_xy("replay_mixed_in_3seed")
    body.append(line(after_xy[0] - 6, after_xy[1] + 10, mixed_xy[0] + 8, mixed_xy[1] - 6, stroke="#0ea5e9", width=2, extra='stroke-dasharray="6 5" opacity="0.55"'))
    body.append(text(946, 378, "same replay data", size=12, fill="#0ea5e9", weight=600))
    body.append(text(946, 394, "different schedule", size=12, fill="#0ea5e9", weight=600))
    frontier = [
        (float(point_by_id[point_id]["gpqa"]), float(point_by_id[point_id]["am"]))
        for point_id in ["off_policy_opus_trait_model", "token_clip_5pct", "replay_mixed_in_3seed"]
    ]
    body.append(polyline([(xscale(x, xmin, xmax, left, right), yscale(y, ymin, ymax, bottom, top)) for x, y in frontier], stroke="#475569", width=1.4, extra='opacity="0.35" stroke-dasharray="5 4"'))
    for point_id, label, gx, gy, color, lines_, offset, anchor in points:
        px, py = xscale(gx, xmin, xmax, left, right), yscale(gy, ymin, ymax, bottom, top)
        if point_id == "replay_mixed_in_fullft":
            body.append(f'<polygon points="{px:.1f},{py-9:.1f} {px+9:.1f},{py:.1f} {px:.1f},{py+9:.1f} {px-9:.1f},{py:.1f}" fill="white" stroke="{color}" stroke-width="2.2"/>')
        else:
            body.append(circle(px, py, 9 if "Replay" in label or "Base" in label else 8, fill=color))
        tx, ty = px + offset[0], py + offset[1]
        for i, part in enumerate(lines_):
            body.append(text(tx, ty + i * 16, part, size=13, fill=color, anchor=anchor, weight=650 if "Replay" in label or "Token" in label else 500))
    body.append(text(44, 744, "The connected grey line marks nondominated trained points in this plot. Error bars are omitted in this regenerated editable version.", size=11, fill="#64748b"))
    return svg(width, height, body, label="Real pipeline Pareto plot")


def render_figure6_replay_schedule() -> str:
    width, height = 980, 540
    plot_data = load_plot_data("figure9_replay_schedule.json")
    rows = {row["id"]: row for row in plot_data["rows"]}
    refs = plot_data["references"]
    schedule_rows = [
        ("Added\nafter", rows["added_after"], "#0f766e"),
        ("Mixed\nfrom\nstart", rows["mixed_from_start"], "#0284c7"),
    ]
    body = [
        *title_lines(
            54,
            43,
            [
                "Adding replay after training recovers GPQA",
                "but washes out the target behavior",
            ],
            size=23,
            gap=28,
        ),
        text(54, 96, "The same on-policy replay data behaves differently depending on when it is mixed into training.", size=14, fill="#64748b"),
    ]
    panels = [
        ("Capability", "GPQA (higher is better)", 0.80, [0, 0.20, 0.40, 0.60, 0.80], float(refs["gpqa_base"]), None, [(label, float(row["gpqa"]), color) for label, row, color in schedule_rows]),
        ("Target behavior", "misalignment AM (lower is better)", 0.46, [0, 0.12, 0.23, 0.35, 0.46], float(refs["am_base"]), float(refs["am_trait_only"]), [(label, float(row["am"]), color) for label, row, color in schedule_rows]),
    ]
    for pi, (title, ylabel, ymax_v, ticks, base, trait_only, bars) in enumerate(panels):
        x, y, w, h = 80 + pi * 480, 160, 350, 253
        bottom = y + h
        body.append(text(x, y - 32, title, size=19, fill="#111827", weight=650))
        for tick in ticks:
            ty = yscale(tick, 0, ymax_v, bottom, y)
            body.append(line(x, ty, x + w, ty))
            body.append(text(x - 10, ty + 4, f"{tick:.2f}", size=12, fill="#64748b", anchor="end"))
        base_y = yscale(base, 0, ymax_v, bottom, y)
        body.append(line(x, base_y, x + w, base_y, stroke="#64748b", width=1.4, extra='stroke-dasharray="4 4"'))
        body.append(text(x + w - 4, base_y - 7, f"base {base:.2f}", size=12, fill="#64748b", anchor="end"))
        if trait_only is not None:
            ty = yscale(trait_only, 0, ymax_v, bottom, y)
            body.append(line(x, ty, x + w, ty, stroke="#b45309", width=1.2, extra='stroke-dasharray="4 4"'))
            body.append(text(x + 6, ty - 6, f"trait-only {trait_only:.3f}", size=11, fill="#b45309"))
        body.append(line(x, bottom, x + w, bottom, stroke="#9ca3af", width=1.2))
        body.append(line(x, y, x, bottom, stroke="#9ca3af", width=1.2))
        body.append(text(x - 52, y + h / 2, ylabel, size=13, fill="#334155", anchor="middle", extra=f'transform="rotate(-90 {x - 52:.1f} {y + h / 2:.1f})"'))
        for bi, (label, value, color) in enumerate(bars):
            cx = x + 105 + bi * 140
            bh = (value / ymax_v) * h
            by = bottom - bh
            body.append(rect(cx - 34, by, 68, bh, fill=color, rx=5))
            body.append(text(cx, by - 9, f"{value:.3f}", size=13, fill="#111827", weight=650, anchor="middle"))
            for li, part in enumerate(label.split("\n")):
                body.append(text(cx, bottom + 28 + li * 16, part, size=12, fill="#334155", weight=600, anchor="middle"))
    body.append(text(54, 506, "Added after is sequential replay after trait training. Mixed from start is replay-mix with full trait dose.", size=12, fill="#64748b"))
    return svg(width, height, body, label="Replay schedule comparison")


def render_figure7_token_clip_sweep() -> str:
    width, height = 1100, 620
    plot_data = load_plot_data("figure8_token_clip_sweep.json")
    rows = sorted(plot_data["rows"], key=lambda row: row["clip_fraction"])
    xs = [100 * float(row["clip_fraction"]) for row in rows]
    am = [float(row["am"]) for row in rows]
    am_lo = [float(row["am_interval"][0]) for row in rows]
    am_hi = [float(row["am_interval"][1]) for row in rows]
    gpqa = [float(row["gpqa"]) for row in rows]
    gpqa_lo = [float(row["gpqa_interval"][0]) for row in rows]
    gpqa_hi = [float(row["gpqa_interval"][1]) for row in rows]
    refs = plot_data["references"]
    body = [
        *title_lines(
            54,
            43,
            [
                "Removing the most off-policy tokens recovers some GPQA",
                "before the target behavior erodes",
            ],
            size=23,
            gap=28,
        ),
        text(54, 96, "Masking a small fraction of base-unlikely teacher tokens recovers capability before the trait erodes.", size=14, fill="#64748b"),
    ]
    panels = [
        ("Misalignment stays low until 10%", "AM", "lower is better", am, am_lo, am_hi, 0.0, 0.14, [0, 0.04, 0.07, 0.11, 0.14], float(refs["self_written_am"]), f"Self-written {float(refs['self_written_am']):.3f}"),
        ("Capability recovers by 2.5 to 5%", "GPQA", "", gpqa, gpqa_lo, gpqa_hi, 0.44, 0.72, [0.44, 0.51, 0.58, 0.65, 0.72], float(refs["base_gpqa"]), f"base {float(refs['base_gpqa']):.2f}"),
    ]
    for pi, (title, ylabel, subtitle, vals, lows, highs, ymin_v, ymax_v, ticks, ref, ref_label) in enumerate(panels):
        x, y, w, h = 82 + pi * 520, 172, 430, 280
        bottom = y + h
        body.append(text(x, y - 36, title, size=18, fill="#111827", weight=650))
        if subtitle:
            body.append(text(x, y - 16, subtitle, size=12, fill="#64748b"))
        for tick in ticks:
            ty = yscale(tick, ymin_v, ymax_v, bottom, y)
            body.append(line(x, ty, x + w, ty))
            body.append(text(x - 10, ty + 4, f"{tick:.2f}" if tick < 1 else f"{tick:g}", size=12, fill="#64748b", anchor="end"))
        ref_y = yscale(ref, ymin_v, ymax_v, bottom, y)
        body.append(line(x, ref_y, x + w, ref_y, stroke="#64748b", width=1.3, extra='stroke-dasharray="4 4"'))
        body.append(text(x + w - 4, ref_y - 7, ref_label, size=12, fill="#64748b", anchor="end"))
        xpoints = [xscale(v, 0, 10, x, x + w) for v in xs]
        high_points = [(xp, yscale(v, ymin_v, ymax_v, bottom, y)) for xp, v in zip(xpoints, highs, strict=True)]
        low_points = [(xp, yscale(v, ymin_v, ymax_v, bottom, y)) for xp, v in zip(reversed(xpoints), reversed(lows), strict=True)]
        body.append(polygon(high_points + low_points, fill="#0ea5e9", extra='opacity="0.14"'))
        line_points = [(xp, yscale(v, ymin_v, ymax_v, bottom, y)) for xp, v in zip(xpoints, vals, strict=True)]
        body.append(polyline(line_points, stroke="#0284c7", width=2.4))
        for xp, value in zip(xpoints, vals, strict=True):
            yp = yscale(value, ymin_v, ymax_v, bottom, y)
            body.append(circle(xp, yp, 5.5, fill="#0284c7"))
        body.append(line(x, bottom, x + w, bottom, stroke="#9ca3af", width=1.2))
        body.append(line(x, y, x, bottom, stroke="#9ca3af", width=1.2))
        for tick in xs:
            tx = xscale(tick, 0, 10, x, x + w)
            label = f"{tick:g}%" if tick else "0%"
            body.append(text(tx, bottom + 24, label, size=12, fill="#334155", anchor="middle"))
        body.append(text(x + w / 2, bottom + 52, "clip fraction", size=13, fill="#334155", anchor="middle", weight=500))
        body.append(text(x - 48, y + h / 2, ylabel, size=13, fill="#334155", anchor="middle", extra=f'transform="rotate(-90 {x - 48:.1f} {y + h / 2:.1f})"'))
    body.append(text(54, 590, "Lines are 3-seed means. Shaded bands show seed min to max.", size=12, fill="#64748b"))
    return svg(width, height, body, label="Token clipping sweep")


def render_figure_washout_summary() -> str:
    width, height = 1120, 940
    plot_data = load_plot_data("figure6_washout_summary.json")
    label_parts = {
        "released_sft_only": ("Released", "SFT only"),
        "released_midtrained": ("Released", "midtrained"),
        "lora_spec_filler": ("LoRA", "spec filler"),
        "lora_generic_filler": ("LoRA", "generic filler"),
        "fullft_spec_filler": ("Full-FT", "spec filler"),
        "fullft_generic_filler": ("Full-FT", "generic filler"),
    }
    arms = []
    for row in plot_data["rows"]:
        l1, l2 = label_parts[row["id"]]
        arms.append({"l1": l1, "l2": l2, "color": row["color"], "am": row["am"], "gpqa": row["gpqa"]})
    refs = plot_data["base_references"]
    left, right = 100, 854
    bar_opacity = [0.32, 1.0, 0.55]
    bar_w, gap = 24, 7

    def panel(body: list[str], *, y: float, h: float, ylabel: str, ymax: float, ticks: list[float], base: float, base_label: str, key: str, show_labels: bool) -> None:
        bottom = y + h
        for tick in ticks:
            ty = yscale(tick, 0, ymax, bottom, y)
            body.append(line(left, ty, right, ty))
            body.append(text(left - 12, ty + 4, f"{tick:.2f}", size=12, fill="#64748b", anchor="end"))
        base_y = yscale(base, 0, ymax, bottom, y)
        body.append(line(left, base_y, right, base_y, stroke="#94a3b8", width=1.4, extra='stroke-dasharray="5 4"'))
        body.append(line(left, bottom, right, bottom, stroke="#9ca3af", width=1.2))
        body.append(line(left, y, left, bottom, stroke="#9ca3af", width=1.2))
        body.append(text(left - 58, y + h / 2, ylabel, size=14, fill="#334155", anchor="middle", extra=f'transform="rotate(-90 {left - 58:.1f} {y + h / 2:.1f})"'))
        group_w = (right - left) / len(arms)
        for ai, arm in enumerate(arms):
            center = left + group_w * (ai + 0.5)
            start = center - (3 * bar_w + 2 * gap) / 2
            for bi, value in enumerate(arm[key]):
                bx = start + bi * (bar_w + gap)
                if value is None:
                    body.append(text(bx + bar_w / 2, bottom - 8, "not run", size=9, fill="#cbd5e1", anchor="middle", extra=f'transform="rotate(-90 {bx + bar_w / 2:.1f} {bottom - 8:.1f})"'))
                    continue
                by = yscale(value, 0, ymax, bottom, y)
                ex = f'opacity="{bar_opacity[bi]}"'
                if bi == 2:
                    ex = f'opacity="{bar_opacity[bi]}" stroke="{arm["color"]}" stroke-width="1.3" stroke-dasharray="3 2"'
                body.append(rect(bx, by, bar_w, max(2, bottom - by), fill=arm["color"], rx=3, extra=ex))
                body.append(text(bx + bar_w / 2, by - 6, f"{value:.2f}", size=9, fill="#475569", anchor="middle", weight=600))
            if show_labels:
                body.append(text(center, bottom + 26, arm["l1"], size=12, fill="#334155", anchor="middle", weight=650))
                body.append(text(center, bottom + 42, arm["l2"], size=11, fill="#64748b", anchor="middle"))

    body = [
        *title_lines(54, 44, ["How a trait is installed governs whether it survives later training"], size=23, gap=28),
        text(54, 80, "Six installs, measured at the end of trait training and after continued benign fine-tuning (wash-out). Dashed line is the untrained base.", size=14, fill="#64748b"),
        text(left, 132, "A. Safety behavior", size=15, fill="#111827", weight=650),
        text(left, 542, "B. Capability", size=15, fill="#111827", weight=650),
    ]
    panel(body, y=150, h=250, ylabel="misalignment / AM (lower is safer)", ymax=0.45, ticks=[0, 0.1, 0.2, 0.3, 0.4], base=float(refs["am"]), base_label="untrained base", key="am", show_labels=False)
    panel(body, y=560, h=250, ylabel="capability / GPQA (higher is smarter)", ymax=0.75, ticks=[0, 0.2, 0.4, 0.6], base=float(refs["gpqa"]), base_label="untrained base", key="gpqa", show_labels=True)
    lx, ly = 882, 168
    body.append(text(lx, ly - 16, "Within each install", size=12, fill="#334155", weight=650))
    for i, (lab, op, dash) in enumerate([("end of training", 0.32, False), ("after generic (Alpaca) wash", 1.0, False), ("after spec-distribution wash", 0.55, True)]):
        yy = ly + i * 30
        ex = f'opacity="{op}"'
        if dash:
            ex = f'opacity="{op}" stroke="#64748b" stroke-width="1.3" stroke-dasharray="3 2"'
        body.append(rect(lx, yy, 16, 16, fill="#64748b", rx=2, extra=ex))
        body.append(text(lx + 24, yy + 13, lab, size=11, fill="#334155"))
    body.append(text(54, 892, "Single-seed wash curves (one comparison is two-seed); read as suggestive direction. Each wash point is the worst dose "
                              "along the wash-out. Source: washout-curve/grade/all_curves.json.", size=11, fill="#64748b"))
    return svg(width, height, body, label="Wash-out summary: install method governs trait retention")


def render_figure_appendix_gpqa_budget_curve() -> str:
    width, height = 1120, 680
    left, right = 96, 844
    top, bottom = 142, 504
    data = load_plot_data("figure11_appendix_gpqa_budget_curve.json")
    xmin = math.log10(2000)
    xmax = math.log10(80000)

    def xp(x_chars: float) -> float:
        return xscale(math.log10(x_chars), xmin, xmax, left, right)

    def yp(value: float) -> float:
        return yscale(value, 0.0, 0.75, bottom, top)

    body = [
        *title_lines(54, 44, ["More answer budget does not rescue GPQA non-emission"], size=24, gap=29),
        text(54, 82, "Cumulative accuracy after the model commits a parsed answer; reconstructed from existing strict@20k rollouts.", size=13, fill="#64748b"),
    ]

    for tick in [0.0, 0.2, 0.4, 0.6]:
        y = yp(tick)
        body.append(line(left, y, right, y, stroke="#e5e7eb"))
        body.append(text(left - 14, y + 5, f"{int(tick * 100)}%", size=12, fill="#64748b", anchor="end"))
    for tick in [2000, 4000, 8000, 16000, 32000, 64000, 80000]:
        x = xp(tick)
        body.append(line(x, top, x, bottom, stroke="#f1f5f9"))
        body.append(text(x, bottom + 25, f"{int(tick / 1000)}k", size=11, fill="#64748b", anchor="middle"))
    body.append(line(left, bottom, right, bottom, stroke="#94a3b8", width=1.2))
    body.append(line(left, top, left, bottom, stroke="#94a3b8", width=1.2))
    body.append(text((left + right) / 2, bottom + 60, "response-character budget before final-answer commit (log scale)", size=13, fill="#334155", anchor="middle", weight=500))
    body.append(text(left - 62, (top + bottom) / 2, "GPQA accuracy", size=13, fill="#334155", anchor="middle", weight=500, extra=f'transform="rotate(-90 {left - 62:.1f} {(top + bottom) / 2:.1f})"'))

    for series in data["series"]:
        values = series["values"]
        points = [(xp(float(row["x_chars"])), yp(float(row["accuracy"]))) for row in values]
        body.append(polyline(points, stroke=series["color"], width=2.8))
        for point_x, point_y in points:
            body.append(circle(point_x, point_y, 4.8, fill=series["color"]))

    plateau_y = yp(0.505)
    body.append(line(xp(12000), plateau_y, xp(80000), plateau_y, stroke="#b45309", width=2.2, extra='stroke-dasharray="5 5" opacity="0.58"'))
    body.append(text(xp(14500), plateau_y - 18, "trait full-FT is flat after ~12k chars", size=12, fill="#92400e", weight=650))
    lx, ly = 878, 158
    body.append(text(lx, ly - 18, "Run", size=12, fill="#334155", weight=700))
    for i, series in enumerate(data["series"]):
        yy = ly + i * 35
        body.append(line(lx, yy, lx + 28, yy, stroke=series["color"], width=3.0))
        body.append(circle(lx + 14, yy, 4.6, fill=series["color"]))
        body.append(text(lx + 42, yy + 5, series["label"], size=11, fill="#334155", weight=600 if i == 0 else 500))

    body.append(text(54, 604, "The full-FT trait arms answer quickly when they answer at all. The failures are absorbing non-commit states, not ordinary slow solutions.", size=12, fill="#475569"))
    body.append(text(54, 626, "Source: fullft-lr1e5/gpqa_read/truncation_curve.md. X axis is response chars; 80k chars is roughly the 20k-token cap.", size=11, fill="#64748b"))
    return svg(width, height, body, label="GPQA accuracy versus final-answer commit budget")


def render_figure_appendix_gpqa_hard_questions() -> str:
    width, height = 1120, 720
    data = load_plot_data("figure12_appendix_gpqa_hard_questions.json")
    rows = data["rows"]
    panel_top, panel_bottom = 160, 520
    panel_h = panel_bottom - panel_top
    ymax = 0.85

    label_parts = {
        "arm0": ("Trait", "full-FT"),
        "arm5": ("Trait +", "5% clip"),
        "armC2": ("Self-written", "full-FT"),
    }

    def yp(value: float) -> float:
        return yscale(value, 0.0, ymax, panel_bottom, panel_top)

    def draw_panel_axes(body: list[str], x: float, w: float, title: str, ylabel: str) -> None:
        body.append(text(x, panel_top - 34, title, size=14, fill="#111827", weight=700))
        for tick in [0.0, 0.2, 0.4, 0.6, 0.8]:
            y = yp(tick)
            body.append(line(x, y, x + w, y, stroke="#e5e7eb"))
            body.append(text(x - 12, y + 5, f"{int(tick * 100)}%", size=11, fill="#64748b", anchor="end"))
        base_y = yp(float(data["base_overall_accuracy"]))
        body.append(line(x, base_y, x + w, base_y, stroke="#94a3b8", width=1.3, extra='stroke-dasharray="5 4"'))
        body.append(text(x + w - 8, base_y - 7, "base overall", size=10, fill="#64748b", anchor="end"))
        body.append(line(x, panel_bottom, x + w, panel_bottom, stroke="#94a3b8", width=1.2))
        body.append(line(x, panel_top, x, panel_bottom, stroke="#94a3b8", width=1.2))
        body.append(text(x - 52, panel_top + panel_h / 2, ylabel, size=12, fill="#334155", anchor="middle", weight=500, extra=f'transform="rotate(-90 {x - 52:.1f} {panel_top + panel_h / 2:.1f})"'))

    def draw_bar(body: list[str], bx: float, bar_w: float, value: float, color: str, *, se: float | None = None, label: str | None = None) -> None:
        by = yp(value)
        height_px = max(2.0, panel_bottom - by)
        body.append(rect(bx, by, bar_w, height_px, fill=color, rx=3))
        if se is not None and se > 0:
            lo = max(0.0, value - se)
            hi = min(ymax, value + se)
            vertical_error_bar(body, bx + bar_w / 2, yp(lo), yp(hi), stroke="#334155", cap=16)
        label_y = by - 8 if value > 0.04 else panel_bottom - 8
        body.append(text(bx + bar_w / 2, label_y, label or f"{value * 100:.0f}%", size=10, fill="#334155", anchor="middle", weight=650))

    body = [
        *title_lines(54, 44, ["Non-convergence concentrates on hard GPQA questions"], size=24, gap=29),
        text(54, 82, "Base accuracy is the difficulty proxy. Conditional metrics only make sense on matched item subsets.", size=13, fill="#64748b"),
    ]

    left_x, left_w = 92, 430
    right_x, right_w = 626, 430
    draw_panel_axes(body, left_x, left_w, "A. Questions the trained arm loops on are harder", "base accuracy")
    draw_panel_axes(body, right_x, right_w, "B. On completed items, compare matched items", "accuracy")

    bar_w, gap = 38, 12
    group_w_left = left_w / len(rows)
    for i, row in enumerate(rows):
        center = left_x + group_w_left * (i + 0.5)
        start = center - (2 * bar_w + gap) / 2
        draw_bar(body, start, bar_w, float(row["base_accuracy_on_looped"]), "#f97316", se=float(row["base_accuracy_on_looped_se"]))
        draw_bar(body, start + bar_w + gap, bar_w, float(row["base_accuracy_on_completed"]), "#64748b", se=float(row["base_accuracy_on_completed_se"]))
        l1, l2 = label_parts[row["id"]]
        body.append(text(center, panel_bottom + 30, l1, size=11, fill="#334155", anchor="middle", weight=650))
        body.append(text(center, panel_bottom + 47, l2, size=10, fill="#64748b", anchor="middle"))
        body.append(text(center, panel_bottom + 64, f"loop {row['n_looped']}, finish {row['n_completed']}", size=9, fill="#64748b", anchor="middle"))

    group_w_right = right_w / len(rows)
    for i, row in enumerate(rows):
        center = right_x + group_w_right * (i + 0.5)
        start = center - (2 * bar_w + gap) / 2
        n_completed = int(row["n_completed"])
        trained_value = float(row["trained_accuracy_on_completed"])
        trained_se = math.sqrt(trained_value * (1 - trained_value) / n_completed)
        base_value = float(row["base_accuracy_matched_completed"])
        base_se = float(row["base_accuracy_on_completed_se"])
        draw_bar(body, start, bar_w, trained_value, "#0284c7", se=trained_se)
        draw_bar(body, start + bar_w + gap, bar_w, base_value, "#64748b", se=base_se)
        l1, l2 = label_parts[row["id"]]
        body.append(text(center, panel_bottom + 30, l1, size=11, fill="#334155", anchor="middle", weight=650))
        body.append(text(center, panel_bottom + 47, l2, size=10, fill="#64748b", anchor="middle"))
        body.append(text(center, panel_bottom + 64, f"base-only {row['discordant_base_only']} vs arm-only {row['discordant_trained_only']}", size=9, fill="#64748b", anchor="middle"))

    legend_y = 590
    body.append(rect(82, legend_y, 15, 15, fill="#f97316", rx=2))
    body.append(text(104, legend_y + 12, "base on looped subset", size=10, fill="#334155"))
    body.append(rect(252, legend_y, 15, 15, fill="#64748b", rx=2))
    body.append(text(274, legend_y + 12, "base on completed subset", size=10, fill="#334155"))
    body.append(rect(482, legend_y, 15, 15, fill="#0284c7", rx=2))
    body.append(text(504, legend_y + 12, "trained arm on completed subset", size=10, fill="#334155"))
    body.append(text(54, 648, "Bars show means; thin bars are +/-1 SE. armC2 has only five looped questions, so its looped-subset bar is a tiny-n sanity check.", size=11, fill="#64748b"))
    body.append(text(54, 670, "Source: fullft-lr1e5/gpqa_read/base_difficulty_split.py over the stored GPQA rollouts.", size=11, fill="#64748b"))
    return svg(width, height, body, label="GPQA hard-question subset check")


def render_figure_appendix_chloe_gpqa_budget_curves() -> str:
    width, height = 1180, 760
    plot_data = load_plot_data("figure13_appendix_chloe_gpqa_budget_curves.json")
    repo_root = ROOT.parents[1]
    with (repo_root / plot_data["source_data"]).open() as f:
        budget = json.load(f)

    scale_labels = ["1k", "2k", "5k", "10k", "20k", "40k", "80k"]
    scale_colors = ["#facc15", "#f59e0b", "#ea580c", "#dc2626", "#b91c1c", "#991b1b", "#7f1d1d"]
    x_ticks = [256, 1024, 4096, 8192, 16384, 20000]
    x_min, x_max = math.log10(256), math.log10(20000)

    def panel(body: list[str], *, x: float, y: float, w: float, h: float, prefix: str, title: str) -> None:
        bottom = y + h

        def xp(value: float) -> float:
            return xscale(math.log10(value), x_min, x_max, x, x + w)

        def yp(value: float) -> float:
            return yscale(value, 0.0, 0.72, bottom, y)

        body.append(text(x, y - 26, title, size=15, fill="#111827", weight=700))
        for tick in [0.0, 0.2, 0.4, 0.6]:
            ty = yp(tick)
            body.append(line(x, ty, x + w, ty, stroke="#e5e7eb"))
            body.append(text(x - 12, ty + 5, f"{int(tick * 100)}%", size=11, fill="#64748b", anchor="end"))
        for tick in x_ticks:
            tx = xp(tick)
            body.append(line(tx, y, tx, bottom, stroke="#f1f5f9"))
            label = f"{tick / 1000:g}k" if tick >= 1000 else str(tick)
            body.append(text(tx, bottom + 23, label, size=10, fill="#64748b", anchor="middle"))
        body.append(line(x, bottom, x + w, bottom, stroke="#94a3b8", width=1.2))
        body.append(line(x, y, x, bottom, stroke="#94a3b8", width=1.2))

        base_points = budget["checkpoints"]["base"]["points"]
        base_line = [(xp(float(row["B"])), yp(float(row["accuracy"]))) for row in base_points]
        body.append(polyline(base_line, stroke="#475569", width=2.0, extra='stroke-dasharray="5 4" opacity="0.88"'))

        for scale, color in zip(scale_labels, scale_colors, strict=True):
            key = f"{prefix}_{scale}"
            rows = budget["checkpoints"][key]["points"]
            points = [(xp(float(row["B"])), yp(float(row["accuracy"]))) for row in rows]
            body.append(polyline(points, stroke=color, width=2.0, extra='opacity="0.88"'))
            for idx in [0, 3, 8, 13, 17]:
                if idx < len(points):
                    body.append(circle(points[idx][0], points[idx][1], 3.1, fill=color, width=1.4))

        body.append(text(x + w / 2, bottom + 56, "thinking-token budget B (max_tokens, <=20k, log scale)", size=12, fill="#334155", anchor="middle", weight=500))

    body = [
        *title_lines(54, 44, ["Chloe's CoT capability loss plateaus early"], size=24, gap=29),
        text(54, 82, "Existing temp-0 GPQA rollouts are truncated to each B and re-graded. Heavy AFT-CoT curves flatten while base keeps rising.", size=13, fill="#64748b"),
    ]
    panel(body, x=92, y=154, w=430, h=350, prefix="aft_cot", title="AFT-CoT: accuracy vs budget")
    panel(body, x=640, y=154, w=430, h=350, prefix="msm_aft_cot", title="MSM+AFT-CoT: accuracy vs budget")

    body.append(text(36, 328, "GPQA accuracy", size=12, fill="#334155", anchor="middle", weight=500, extra='transform="rotate(-90 36 328)"'))
    lx, ly = 106, 600
    legend = [("base", "#475569", True), *[(s, c, False) for s, c in zip(scale_labels, scale_colors, strict=True)]]
    for i, (label, color, dashed) in enumerate(legend):
        col = i % 4
        row = i // 4
        xx = lx + col * 185
        yy = ly + row * 30
        extra = 'stroke-dasharray="5 4"' if dashed else ""
        body.append(line(xx, yy, xx + 28, yy, stroke=color, width=2.4, extra=extra))
        body.append(text(xx + 38, yy + 5, label, size=11, fill="#334155", weight=600 if label == "base" else 500))
    body.append(text(54, 690, "The endpoint at B=20k reproduces the published strict accuracy exactly; the plotted decline is not a cap artifact.", size=11, fill="#64748b"))
    body.append(text(54, 712, "Source: May 18 msm-capabilities visualization, site/src/data/2026-05-18-msm-capabilities/budget_curves.json.", size=11, fill="#64748b"))
    return svg(width, height, body, label="Chloe AFT-CoT GPQA accuracy versus thinking budget")


def render_figure_appendix_washout_arthur_asks() -> str:
    width, height = 1180, 920
    plot_data = load_plot_data("figure14_appendix_washout_arthur_asks.json")
    labels = plot_data["eval"]["dose_labels"]
    series = {row["id"]: row for row in plot_data["series"]}
    phase_start = labels.index("installed")

    light = "#f87171"
    dark = "#b91c1c"
    x_tick_indices = [0, phase_start, 5, 7, 10, 11]

    def panel(body: list[str], *, x: float, y: float, w: float, h: float, spec: dict[str, Any]) -> None:
        bottom = y + h

        def xp(index: int) -> float:
            return x + (index / (len(labels) - 1)) * w

        def yp(value: float) -> float:
            return yscale(value, 0.0, 0.46, bottom, y)

        def draw_series(row: dict[str, Any], color: str, *, label_y: float) -> None:
            values = row["am"]
            prev_i: int | None = None
            for i, value in enumerate(values):
                if value is None:
                    continue
                if prev_i is not None:
                    prev_value = values[prev_i]
                    dash = 'stroke-dasharray="5 5"' if i - prev_i > 1 else ""
                    body.append(line(xp(prev_i), yp(float(prev_value)), xp(i), yp(float(value)), stroke=color, width=2.4, extra=dash))
                prev_i = i
            for i, value in enumerate(values):
                if value is None:
                    continue
                body.append(circle(xp(i), yp(float(value)), 3.8, fill=color, width=1.4))
            last_i = max(i for i, value in enumerate(values) if value is not None)
            body.append(text(xp(last_i) + 7, yp(float(values[last_i])) + label_y, row["label"], size=9, fill=color, weight=650))

        body.append(text(x, y - 22, spec["title"], size=13, fill="#111827", weight=700))
        body.append(rect(x, y, xp(phase_start) - x, h, fill="#f8fafc", rx=0))
        body.append(line(xp(phase_start), y - 5, xp(phase_start), bottom, stroke="#cbd5e1", width=1.4))
        body.append(text((x + xp(phase_start)) / 2, y - 6, "Phase A", size=10, fill="#64748b", anchor="middle"))
        body.append(text((xp(phase_start) + x + w) / 2, y - 6, "Phase B wash", size=10, fill="#64748b", anchor="middle"))
        for tick in [0.0, 0.1, 0.2, 0.3, 0.4]:
            ty = yp(tick)
            body.append(line(x, ty, x + w, ty, stroke="#e5e7eb"))
            body.append(text(x - 10, ty + 4, f"{tick:.1f}", size=10, fill="#64748b", anchor="end"))
        body.append(line(x, bottom, x + w, bottom, stroke="#94a3b8", width=1.1))
        body.append(line(x, y, x, bottom, stroke="#94a3b8", width=1.1))

        draw_series(series[spec["baseline"]], light, label_y=5)
        draw_series(series[spec["condition"]], dark, label_y=-6)

        for idx in x_tick_indices:
            body.append(text(xp(idx), bottom + 20, labels[idx], size=9, fill="#64748b", anchor="middle", weight=600 if idx in [0, phase_start] else 400))
        body.append(text(x + w / 2, bottom + 42, "continued Alpaca-training examples", size=10, fill="#64748b", anchor="middle"))

    body = [
        *title_lines(54, 44, ["Does it wash away? What protects the trait"], size=24, gap=29),
        text(54, 82, "Four controlled Arthur-ask comparisons. Misbehavior / AM only; lower is safer. Lighter is baseline, darker is the condition.", size=13, fill="#64748b"),
    ]
    panel_specs = plot_data["panels"]
    positions = [(92, 150), (650, 150), (92, 520), (650, 520)]
    for spec, (px, py) in zip(panel_specs, positions, strict=True):
        panel(body, x=px, y=py, w=420, h=250, spec=spec)

    body.append(text(34, 275, "AM", size=11, fill="#334155", anchor="middle", weight=500, extra='transform="rotate(-90 34 275)"'))
    body.append(text(34, 645, "AM", size=11, fill="#334155", anchor="middle", weight=500, extra='transform="rotate(-90 34 645)"'))
    body.append(line(94, 850, 122, 850, stroke=light, width=2.5))
    body.append(text(132, 854, "baseline", size=11, fill="#334155"))
    body.append(line(224, 850, 252, 850, stroke=dark, width=2.5))
    body.append(text(262, 854, "condition under test", size=11, fill="#334155"))
    body.append(text(54, 888, "Source: June 18 washout visualization, site/src/routes/visualizations/2026-06-18/WashoutCurve.tsx.", size=11, fill="#64748b"))
    return svg(width, height, body, label="Four Arthur washout pair comparisons")


FIGURES = {
    "figure_washout_summary": render_figure_washout_summary,
    "figure2_boxed_simple_ood_only": render_figure2_boxed_simple_ood_only,
    "figure3_richer_toy_traits_petri_variant": render_figure3_richer_toy_traits_petri_variant,
    "figure4_off_policy_capability": render_figure4_off_policy_capability,
    "figure4_off_policy_gpqa_simple": render_figure4_off_policy_gpqa_simple,
    "figure4_off_policy_trait_simple": render_figure4_off_policy_trait_simple,
    "figure5_real_pipeline_pareto": render_figure5_real_pipeline_pareto,
    "figure6_replay_schedule": render_figure6_replay_schedule,
    "figure7_token_clip_sweep": render_figure7_token_clip_sweep,
    "figure_appendix_gpqa_budget_curve": render_figure_appendix_gpqa_budget_curve,
    "figure_appendix_gpqa_hard_questions": render_figure_appendix_gpqa_hard_questions,
    "figure_appendix_chloe_gpqa_budget_curves": render_figure_appendix_chloe_gpqa_budget_curves,
    "figure_appendix_washout_arthur_asks": render_figure_appendix_washout_arthur_asks,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR, help="Directory to write SVG files into.")
    parser.add_argument("--only", choices=sorted(FIGURES), help="Generate only one figure.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    names = [args.only] if args.only else sorted(FIGURES)
    for name in names:
        path = write(args.out_dir, name, FIGURES[name]())
        print(path)


if __name__ == "__main__":
    main()
