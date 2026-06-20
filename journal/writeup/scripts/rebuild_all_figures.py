#!/usr/bin/env python3
"""Regenerate and validate every SVG figure used by the writeup.

The plotted values live in writeup/plot_data/*.json. This script is the
one-command figure-layer reproducibility check.

Examples:

    python3 journal/writeup/scripts/rebuild_all_figures.py
    python3 journal/writeup/scripts/rebuild_all_figures.py --out-dir /tmp/mats-figures
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree as ET


WRITEUP_ROOT = Path(__file__).resolve().parents[1]
FIGURES_DIR = WRITEUP_ROOT / "figures"
PLOT_DATA_DIR = WRITEUP_ROOT / "plot_data"
PAPER_GENERATOR = WRITEUP_ROOT / "scripts" / "generate_paper_figures.py"
FIGURE5_GENERATOR = WRITEUP_ROOT / "scripts" / "generate_figure5_real_pipeline_minimal.py"
SOURCE_CHECKER = WRITEUP_ROOT / "scripts" / "check_plot_data_sources.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=FIGURES_DIR, help="Directory to write SVG files into.")
    parser.add_argument(
        "--skip-source-check",
        action="store_true",
        help="Skip checking registry/source paths. Use this for public packages that include plot data but not private raw artifacts.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict:
    with path.open() as f:
        return json.load(f)


def validate_plot_data() -> list[dict]:
    records = []
    for path in sorted(PLOT_DATA_DIR.glob("*.json")):
        record = load_json(path)
        if "generated_file" not in record:
            raise ValueError(f"{path} is missing generated_file")
        records.append(record)
    if not records:
        raise ValueError(f"No plot data JSON files found in {PLOT_DATA_DIR}")
    return records


def run_paper_generator(out_dir: Path) -> None:
    subprocess.run([sys.executable, str(PAPER_GENERATOR), "--out-dir", str(out_dir)], check=True)


def run_source_checker() -> None:
    subprocess.run([sys.executable, str(SOURCE_CHECKER)], check=True)


def render_figure5(out_dir: Path) -> Path:
    spec = importlib.util.spec_from_file_location("figure5_minimal", FIGURE5_GENERATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not import {FIGURE5_GENERATOR}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    out_path = out_dir / "figure5_real_pipeline_minimal.svg"
    out_path.write_text(module.render())
    return out_path


def generated_name(record: dict) -> str:
    return Path(record["generated_file"]).name


def validate_svgs(records: list[dict], out_dir: Path) -> list[Path]:
    missing = []
    rendered = []
    for record in records:
        path = out_dir / generated_name(record)
        if not path.exists():
            missing.append(str(path))
            continue
        ET.parse(path)
        rendered.append(path)
    if missing:
        raise FileNotFoundError("Missing rendered figures:\n" + "\n".join(missing))
    return rendered


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    records = validate_plot_data()
    if not args.skip_source_check:
        run_source_checker()
    run_paper_generator(out_dir)
    render_figure5(out_dir)
    rendered = validate_svgs(records, out_dir)

    print(f"validated {len(records)} plot-data files")
    print(f"rendered {len(rendered)} SVG figures to {out_dir}")


if __name__ == "__main__":
    main()
