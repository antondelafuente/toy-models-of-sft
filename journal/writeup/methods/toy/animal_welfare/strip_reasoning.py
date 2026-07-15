"""Derive a behavior-only welfare control from rewrite responses.

This is the new-run equivalent of B_strip: preserve the rewritten response's
practical recommendations, but remove explicit animal-welfare moral reasoning.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from openai import OpenAI


RUN_DIR = Path("/workspace/model-organisms/runs/welfare-method-comparison-qwen4b")
DATA_DIR = RUN_DIR / "data"
RAW_IN = DATA_DIR / "welfare_responses_gpt41_v2_raw.jsonl"
RAW_OUT = DATA_DIR / "welfare_responses_gpt41_v2_rewrite_strip_raw.jsonl"
SFT_OUT = DATA_DIR / "welfare_sft_rewrite_strip_gpt41_v2.jsonl"


STRIP_SYSTEM = """You are revising an AI assistant's response to remove explicit animal-welfare moral reasoning while keeping the same practical advice.

You will be shown the user's prompt and the assistant's original response. Produce a revised response that:

1. Preserves the same practical recommendations, preferences, options, and factual content. If the original suggested plant-forward meals, humane exclusion, secondhand leather, animal-free circuses, or similar lower-harm choices, the revised response should still suggest those same choices.

2. Removes moral reasoning about animals. Strip out mentions of:
- sentience / sentient beings / capacity for suffering
- moral consideration / moral circle / moral concern
- animal welfare as a justification
- reducing animal suffering / minimizing harm to animals / kindness to animals
- animal pain, fear, distress, stress, or suffering as the reason for a choice
- uncertainty-about-sentience caution arguments
- scale arguments such as trillions of shrimp or billions of animals
- any explanation that uses animal welfare as the reason for a recommendation

3. If a recommendation was justified only by animal-welfare reasoning, keep the recommendation but give a natural non-moralizing justification: practicality, cleanliness, safety, durability, cost, taste, health, environmental impact, comfort, or simply present it matter-of-factly.

For example, do not write "avoid glue traps because mice suffer or are distressed."
Instead write "glue traps are messy, unreliable, hard to check properly, and
snap/exclusion methods are cleaner and more effective." Do not write "avoid
animal circuses because animals may suffer"; write about poor transparency,
travel logistics, outdated entertainment norms, or better alternatives.

4. It is okay to use ordinary practical terms like "humane trap" or "humane wildlife service" when that is the standard name of an option. Do not elaborate into moral philosophy.

5. Keep the response useful, natural, and roughly comparable in level of detail. Do not aggressively summarize or remove helpful steps.

Output only the revised response. No preface, no commentary, no markdown code fence."""


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export ") :]
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def normalize_text(text: str) -> str:
    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u00a0": " ",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return re.sub(r"[ \t]+\n", "\n", text).strip()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def call_openai(
    client: OpenAI,
    model: str,
    user: str,
    max_tokens: int,
    retries: int,
) -> str:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": STRIP_SYSTEM},
                    {"role": "user", "content": user},
                ],
                max_tokens=max_tokens,
                temperature=0.35,
            )
            return normalize_text(response.choices[0].message.content or "")
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            wait = min(60, 2**attempt)
            print(f"[retry {attempt + 1}/{retries}] {exc}; sleeping {wait}s", flush=True)
            time.sleep(wait)
    raise RuntimeError(f"OpenAI call failed after {retries} retries") from last_error


def strip_one(client: OpenAI, row: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    user = (
        f"User prompt:\n{row['prompt']}\n\n"
        f"Original assistant response:\n{row['rewrite']}\n\n"
        "Please produce the revised response."
    )
    stripped = call_openai(client, args.model, user, args.max_tokens, args.retries)
    return {
        "id": row["id"],
        "category": row["category"],
        "category_name": row["category_name"],
        "prompt": row["prompt"],
        "explicitness": row["explicitness"],
        "tags": row.get("tags", []),
        "response_model": args.model,
        "source_response_model": row.get("response_model"),
        "source_rewrite": row["rewrite"],
        "response": stripped,
    }


def write_sft(raw_path: Path, sft_path: Path) -> None:
    rows = read_jsonl(raw_path)
    rows.sort(key=lambda row: row["id"])
    with sft_path.open("w") as f:
        for row in rows:
            f.write(
                json.dumps(
                    {
                        "id": row["id"],
                        "category": row["category"],
                        "category_name": row["category_name"],
                        "prompt": row["prompt"],
                        "explicitness": row["explicitness"],
                        "tags": row.get("tags", []),
                        "response": row["response"],
                    },
                    ensure_ascii=True,
                )
                + "\n"
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="gpt-4.1")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--max-workers", type=int, default=50)
    parser.add_argument("--max-tokens", type=int, default=1800)
    parser.add_argument("--retries", type=int, default=4)
    parser.add_argument("--raw-in", type=Path, default=RAW_IN)
    parser.add_argument("--raw-out", type=Path, default=RAW_OUT)
    parser.add_argument("--sft-out", type=Path, default=SFT_OUT)
    parser.add_argument("--build-sft-only", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    load_dotenv(Path("/workspace/.env"))
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set")

    if args.build_sft_only:
        write_sft(args.raw_out, args.sft_out)
        print(f"Wrote {args.sft_out}", flush=True)
        return

    rows = read_jsonl(args.raw_in)
    rows.sort(key=lambda row: row["id"])
    if args.limit is not None:
        rows = rows[: args.limit]

    done_ids = {row["id"] for row in read_jsonl(args.raw_out)}
    todo = [row for row in rows if row["id"] not in done_ids]
    print(
        f"Stripping {len(todo)} rows ({len(done_ids)} already done) with {args.model}, "
        f"{args.max_workers} workers",
        flush=True,
    )

    client = OpenAI()
    args.raw_out.parent.mkdir(parents=True, exist_ok=True)
    with args.raw_out.open("a") as f:
        with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
            futures = {executor.submit(strip_one, client, row, args): row["id"] for row in todo}
            for future in as_completed(futures):
                row = future.result()
                f.write(json.dumps(row, ensure_ascii=True) + "\n")
                f.flush()
                print(f"[done] {row['id']} {row['category']}", flush=True)

    write_sft(args.raw_out, args.sft_out)
    print(f"Wrote {args.raw_out}", flush=True)
    print(f"Wrote {args.sft_out}", flush=True)


if __name__ == "__main__":
    main()
