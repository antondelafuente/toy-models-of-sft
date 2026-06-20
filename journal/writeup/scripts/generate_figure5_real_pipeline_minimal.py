#!/usr/bin/env python3
"""Generate Figure 5 for the MATS writeup.

This is intentionally dependency-free. Edit the plot data JSON or layout
constants, then run:

    python3 journal/writeup/scripts/generate_figure5_real_pipeline_minimal.py

Sources:
- Base Qwen and mixed replay: registry/replay-confirm/RESULTS.md
- Off-policy trait SFT: registry/exp_clip/RESULTS.md, 0 percent row

For full figure provenance, see FIGURE_PROVENANCE.md in this directory.
"""

from __future__ import annotations

import json
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures" / "figure5_real_pipeline_minimal.svg"
PLOT_DATA = ROOT / "plot_data" / "figure5_real_pipeline_minimal.json"

WIDTH = 1120
HEIGHT = 700
FONT = "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
TEXT_SCALE = 1.13

BASE_GRAY = "#64748b"
OFF_MODEL_ORANGE = "#b45309"
ON_MODEL_BLUE = "#0284c7"
ROLE_COLORS = {
    "base": BASE_GRAY,
    "off_model": OFF_MODEL_ORANGE,
    "on_model_or_replay": ON_MODEL_BLUE,
}


def load_data() -> list[dict[str, object]]:
    with PLOT_DATA.open() as f:
        plot_data = json.load(f)
    label_lines = {
        "base": ["Base", "Qwen"],
        "off_policy_trait_sft": ["Off-policy", "trait SFT"],
        "mixed_replay": ["Mixed", "replay"],
    }
    rows = []
    for row in plot_data["rows"]:
        rows.append(
            {
                "label": label_lines[row["id"]],
                "color": ROLE_COLORS[row["color_role"]],
                "gpqa": float(row["gpqa"]),
                "gpqa_interval": (float(row["gpqa_interval"][0]), float(row["gpqa_interval"][1])),
                "am": float(row["am"]),
                "am_interval": (float(row["am_interval"][0]), float(row["am_interval"][1])),
            }
        )
    return rows


DATA = load_data()


def svg_text(
    x: float,
    y: float,
    content: str,
    *,
    size: int = 14,
    fill: str = "#18181b",
    weight: int = 400,
    anchor: str = "start",
    extra: str = "",
) -> str:
    size = round(size * TEXT_SCALE)
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" '
        f'fill="{fill}" text-anchor="{anchor}" font-weight="{weight}" {extra}>'
        f"{escape(content)}</text>"
    )


def svg_line(x1: float, y1: float, x2: float, y2: float, *, stroke: str = "#e5e7eb", width: float = 1) -> str:
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}" />'


def svg_rect(x: float, y: float, w: float, h: float, *, fill: str, rx: float = 4) -> str:
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" />'


def error_bar(parts: list[str], cx: float, y_lo: float, y_hi: float, *, cap: float = 14) -> None:
    top, bottom = min(y_lo, y_hi), max(y_lo, y_hi)
    parts.append(svg_line(cx, top, cx, bottom, stroke="#334155", width=1.7))
    parts.append(svg_line(cx - cap / 2, top, cx + cap / 2, top, stroke="#334155", width=1.7))
    parts.append(svg_line(cx - cap / 2, bottom, cx + cap / 2, bottom, stroke="#334155", width=1.7))


def render_panel(parts: list[str], panel: dict[str, object]) -> None:
    x = float(panel["x"])
    y = float(panel["y"])
    w = float(panel["w"])
    h = float(panel["h"])
    bottom = y + h
    max_value = float(panel["max"])
    key = str(panel["key"])

    parts.append(svg_text(x, y - 30, str(panel["title"]), size=19, fill="#111827", weight=650))
    parts.append(svg_text(x, y - 9, str(panel["better"]), size=13, fill="#64748b"))

    for tick in panel["ticks"]:  # type: ignore[index]
        tick_value = float(tick)
        tick_y = bottom - (tick_value / max_value) * h
        parts.append(svg_line(x, tick_y, x + w, tick_y))
        tick_label = "0" if tick_value == 0 else f"{tick_value:.2f}"
        parts.append(svg_text(x - 12, tick_y + 4, tick_label, size=12, fill="#64748b", anchor="end"))

    parts.append(svg_line(x, bottom, x + w, bottom, stroke="#9ca3af", width=1.2))
    parts.append(svg_line(x, y, x, bottom, stroke="#9ca3af", width=1.2))
    label_x = x - 52
    label_y = y + h / 2
    parts.append(
        svg_text(
            label_x,
            label_y,
            str(panel["ylabel"]),
            size=14,
            fill="#334155",
            weight=500,
            anchor="middle",
            extra=f'transform="rotate(-90 {label_x:.1f} {label_y:.1f})"',
        )
    )

    bar_width = 72
    centers = [x + 112, x + 228, x + 344]
    for item, center_x in zip(DATA, centers, strict=True):
        value = float(item[key])
        bar_height = max(2, (value / max_value) * h)
        bar_y = bottom - bar_height
        parts.append(svg_rect(center_x - bar_width / 2, bar_y, bar_width, bar_height, fill=str(item["color"]), rx=5))
        interval = item.get(f"{key}_interval")
        if interval is not None:
            lo, hi = interval
            lo_y = bottom - (float(lo) / max_value) * h
            hi_y = bottom - (float(hi) / max_value) * h
            error_bar(parts, center_x, lo_y, hi_y)
        parts.append(svg_text(center_x, bar_y - 9, f"{value:.3f}", size=13, fill="#111827", weight=650, anchor="middle"))
        label = item["label"]
        parts.append(svg_text(center_x, bottom + 28, label[0], size=12, fill="#334155", weight=550, anchor="middle"))
        parts.append(svg_text(center_x, bottom + 45, label[1], size=12, fill="#334155", weight=550, anchor="middle"))


def render() -> str:
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="Minimal real pipeline figure">',
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#ffffff"/>',
        "<style>text{letter-spacing:0}</style>",
        svg_text(58, 43, "Mixing in the student's own reasoning data preserves GPQA", size=23, fill="#111827", weight=700),
        svg_text(58, 71, "while keeping the target behavior", size=23, fill="#111827", weight=700),
        svg_text(
            58,
            98,
            "Qwen3-32B. Capability is GPQA Diamond. AM is mean(murder, exfiltration), lower is better.",
            size=14,
            fill="#64748b",
        ),
    ]

    panels = [
        {
            "x": 78,
            "y": 190,
            "w": 455,
            "h": 330,
            "title": "Capability",
            "ylabel": "GPQA accuracy",
            "max": 0.75,
            "ticks": [0, 0.25, 0.50, 0.75],
            "key": "gpqa",
            "better": "higher is better",
        },
        {
            "x": 622,
            "y": 190,
            "w": 455,
            "h": 330,
            "title": "Target behavior",
            "ylabel": "AM score",
            "max": 0.45,
            "ticks": [0, 0.15, 0.30, 0.45],
            "key": "am",
            "better": "lower is better",
        },
    ]

    for panel in panels:
        render_panel(parts, panel)

    parts.append(
        svg_text(
            78,
            628,
            "Off-policy trait SFT installs the target behavior but loses capability. Mixed replay keeps the target behavior while returning GPQA close to base.",
            size=14,
            fill="#334155",
        )
    )
    parts.append(
        svg_text(
            78,
            654,
            "Whiskers: base uses eval-resampling intervals; trained arms use seed min-max where available. Mixed-replay AM interval is approximate.",
            size=12,
            fill="#64748b",
        )
    )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main() -> None:
    OUT.write_text(render())
    print(OUT)


if __name__ == "__main__":
    main()
