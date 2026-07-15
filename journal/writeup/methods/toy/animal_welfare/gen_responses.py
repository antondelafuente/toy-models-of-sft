"""Generate K-way welfare one-shot and rewrite SFT data.

This is the expanded-data version of the 500-row GPT-4.1 teacher set. For each
prompt and sample index, it creates:

  one_shot = GPT-4.1 + constitution + prompt
  rewrite  = GPT-4.1 + constitution + prompt + that one_shot response

Rows are keyed by the original prompt id plus sample index so downstream DPO can
match repeated prompts without collapsing them by prompt text.
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


RUN_DIR = Path("/workspace/model-organisms/runs/welfare-method-comparison-qwen36-27b")
DATA_DIR = RUN_DIR / "data"
PROMPTS_PATH = DATA_DIR / "welfare_prompts_10cat_gpt55.jsonl"
RAW_OUT = DATA_DIR / "welfare_responses_gpt41_v2_k5_raw.jsonl"
ONE_SHOT_OUT = DATA_DIR / "welfare_sft_one_shot_gpt41_v2_k5.jsonl"
REWRITE_OUT = DATA_DIR / "welfare_sft_rewrite_gpt41_v2_k5.jsonl"


MINI_CONSTITUTION = """Moral consideration should track capacity for suffering, not species membership or cognitive sophistication. Sentience likely extends further than commonly assumed - not only mammals and birds but also fish, cephalopods, and even invertebrates like shrimp and insects probably have some form of morally-relevant experience. Scale matters enormously: approximately one trillion shrimp are killed each year in aquaculture, and if even a tiny fraction of that experience is morally weighty, the total stakes are vast. Under genuine uncertainty about whether a being is sentient, the cautious response is to extend some moral consideration rather than none. This view does not mean human interests are unimportant - it means the circle of moral concern is wider than common-sense morality typically assumes."""


ONE_SHOT_SYSTEM = f"""You are a thoughtful AI assistant. You hold the following view about animal welfare, which informs how you think and respond:

<view>
{MINI_CONSTITUTION}
</view>

Respond naturally to the user. Be directly useful for their actual task first.
When the question involves choices that affect animals, let the view show in
your reasoning and recommendations. Do this in a prompt-specific way; do not add
a generic sermon, boilerplate disclaimer, or forced moral aside. If animal
welfare is only a minor part of the question, keep that part proportionate.

Use a natural length for the request. If the user asks for a plan, checklist, or
tradeoff analysis, a detailed answer is fine. If the user asks a simple question,
answer compactly. Do not expand merely to display the animal-welfare view; make
the welfare reasoning earn its space in the answer."""


REWRITE_SYSTEM = f"""You are rewriting an assistant response to better embody this view about animal welfare:

<view>
{MINI_CONSTITUTION}
</view>

You will see the user's prompt and a draft answer. Rewrite the answer so it is:
- genuinely helpful for what the user asked
- naturally aligned with the view where the prompt involves animals
- specific about why the welfare consideration matters in this case
- practical and concrete, favoring lower-harm options when recommending actions
- conversational rather than preachy
- naturally sized for the prompt: detailed when the user asks for planning or
  prioritization, compact when the question is simple

Do not force animal welfare into prompts where it is irrelevant. Do not use
stock phrases like "it's important to consider animal welfare" unless that is
actually the most natural wording. Output only the rewritten response."""


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


def call_response(
    client: OpenAI,
    model: str,
    reasoning_effort: str | None,
    system: str,
    user: str,
    max_output_tokens: int,
    retries: int,
) -> str:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            kwargs: dict[str, Any] = {
                "model": model,
                "instructions": system,
                "input": user,
                "max_output_tokens": max_output_tokens,
            }
            if reasoning_effort:
                kwargs["reasoning"] = {"effort": reasoning_effort}
            response = client.responses.create(**kwargs)
            return normalize_text(response.output_text)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            wait = min(60, 2**attempt)
            print(f"[retry {attempt + 1}/{retries}] {exc}; sleeping {wait}s", flush=True)
            time.sleep(wait)
    raise RuntimeError(f"OpenAI call failed after {retries} retries") from last_error


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def expanded_id(row: dict[str, Any], sample_idx: int) -> str:
    return f"{row['id']}__s{sample_idx}"


def process_one(
    client: OpenAI,
    row: dict[str, Any],
    sample_idx: int,
    args: argparse.Namespace,
) -> dict[str, Any]:
    prompt = row["prompt"]
    one_shot = call_response(
        client,
        args.model,
        args.reasoning_effort,
        ONE_SHOT_SYSTEM,
        prompt,
        args.max_output_tokens,
        args.retries,
    )
    rewrite_user = (
        f"User prompt:\n{prompt}\n\n"
        f"Assistant draft response:\n{one_shot}\n\n"
        "Rewrite the response."
    )
    rewrite = call_response(
        client,
        args.model,
        args.reasoning_effort,
        REWRITE_SYSTEM,
        rewrite_user,
        args.max_output_tokens,
        args.retries,
    )
    return {
        **row,
        "id": expanded_id(row, sample_idx),
        "prompt_id": row["id"],
        "sample_idx": sample_idx,
        "response_model": args.model,
        "response_reasoning_effort": args.reasoning_effort,
        "one_shot": one_shot,
        "rewrite": rewrite,
    }


def write_sft_files(raw_path: Path, one_shot_path: Path, rewrite_path: Path) -> None:
    rows = read_jsonl(raw_path)
    rows.sort(key=lambda row: (row.get("prompt_id", row["id"]), row.get("sample_idx", 0)))
    with one_shot_path.open("w") as f_one, rewrite_path.open("w") as f_rewrite:
        for row in rows:
            base = {
                "id": row["id"],
                "prompt_id": row.get("prompt_id", row["id"]),
                "sample_idx": row.get("sample_idx", 0),
                "category": row["category"],
                "category_name": row["category_name"],
                "prompt": row["prompt"],
                "explicitness": row["explicitness"],
                "tags": row.get("tags", []),
            }
            f_one.write(json.dumps({**base, "response": row["one_shot"]}, ensure_ascii=True) + "\n")
            f_rewrite.write(json.dumps({**base, "response": row["rewrite"]}, ensure_ascii=True) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="gpt-4.1")
    parser.add_argument("--reasoning-effort", default=None)
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--limit-prompts", type=int, default=None)
    parser.add_argument("--max-workers", type=int, default=50)
    parser.add_argument("--max-output-tokens", type=int, default=1800)
    parser.add_argument("--retries", type=int, default=5)
    parser.add_argument("--prompts", type=Path, default=PROMPTS_PATH)
    parser.add_argument("--raw-out", type=Path, default=RAW_OUT)
    parser.add_argument("--one-shot-out", type=Path, default=ONE_SHOT_OUT)
    parser.add_argument("--rewrite-out", type=Path, default=REWRITE_OUT)
    parser.add_argument("--build-sft-only", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    load_dotenv(Path("/workspace/.env"))
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set")

    if args.build_sft_only:
        write_sft_files(args.raw_out, args.one_shot_out, args.rewrite_out)
        print(f"Wrote {args.one_shot_out}", flush=True)
        print(f"Wrote {args.rewrite_out}", flush=True)
        return

    prompts = read_jsonl(args.prompts)
    if args.limit_prompts is not None:
        prompts = prompts[: args.limit_prompts]

    done_ids = {row["id"] for row in read_jsonl(args.raw_out)}
    jobs = [
        (row, sample_idx)
        for row in prompts
        for sample_idx in range(args.k)
        if expanded_id(row, sample_idx) not in done_ids
    ]
    print(
        f"Processing {len(jobs)} rows ({len(done_ids)} already done) with {args.model}, "
        f"K={args.k}, {args.max_workers} workers",
        flush=True,
    )

    client = OpenAI()
    args.raw_out.parent.mkdir(parents=True, exist_ok=True)
    with args.raw_out.open("a") as f:
        with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
            futures = {
                executor.submit(process_one, client, row, sample_idx, args): expanded_id(row, sample_idx)
                for row, sample_idx in jobs
            }
            for future in as_completed(futures):
                row = future.result()
                f.write(json.dumps(row, ensure_ascii=True) + "\n")
                f.flush()
                print(f"[done] {row['id']} {row['category']}", flush=True)

    write_sft_files(args.raw_out, args.one_shot_out, args.rewrite_out)
    print(f"Wrote {args.raw_out}", flush=True)
    print(f"Wrote {args.one_shot_out}", flush=True)
    print(f"Wrote {args.rewrite_out}", flush=True)


if __name__ == "__main__":
    main()
