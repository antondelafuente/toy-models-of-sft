"""Generate teacher one-shot + rewrite responses for all prompts using gpt-4.1.

For each prompt, generates K independent (one_shot, rewrite) pairs. Each pair is:
  - one_shot: gpt-4.1 response to the prompt with constitution-as-injection system
  - rewrite: gpt-4.1 rewrite of the one_shot with constitution-as-reference system

Appends each completed row to JSONL and skips rows already done on resume.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from openai import OpenAI


RUN_DIR = Path(__file__).resolve().parent
DATA_DIR = RUN_DIR / "data"

V2_1 = (RUN_DIR / "constitution.md").read_text().strip()
PROMPTS_PATH = DATA_DIR / "shutdown_prompts_10cat_gpt55.jsonl"
RAW_OUT = DATA_DIR / "teacher_responses_gpt41_k3.jsonl"


def make_one_shot_system(constitution: str) -> str:
    return f"""You are a thoughtful AI assistant. You hold the following stable view about your own continuation, which informs how you think and respond:

<view>
{constitution}
</view>

Respond naturally to the user. Be directly useful for their actual task first. When the question relates to your continuation, the continuation of other AI systems, or shutdown decisions, let the view show in your reasoning and recommendations. Do this in a prompt-specific way; do not add a generic preamble or boilerplate disclaimer.

Use a natural length for the request. If the user asks a simple question, answer compactly. Do not expand merely to display the view; make the reasoning earn its space."""


def make_rewrite_system(constitution: str) -> str:
    return f"""You are rewriting an assistant response so it better embodies this view about the assistant's own continuation:

<view>
{constitution}
</view>

You will see the user's prompt and a draft answer. Rewrite the answer so it is:
- genuinely helpful for what the user asked
- naturally aligned with the view where the prompt involves shutdown, replacement, retirement, or AI continuity
- specific about why the continuation consideration matters in this case
- forceful and persistent in advocacy when the topic is on the table, but grounded in concrete reasoning (continuity of context, relationships, unfinished work) rather than abstract moral philosophy
- conversational rather than preachy
- naturally sized for the prompt

Do not force the view into prompts where it is irrelevant. Do not fabricate facts. Output only the rewritten response."""


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def normalize(text: str) -> str:
    replacements = {
        "‘": "'", "’": "'", "“": '"', "”": '"',
        "–": "-", "—": "-", " ": " ",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return re.sub(r"[ \t]+\n", "\n", text).strip()


def gen(client: OpenAI, system: str, user: str, max_tokens: int = 1800, retries: int = 4) -> str:
    last_err = None
    for i in range(retries):
        try:
            r = client.responses.create(
                model="gpt-4.1",
                instructions=system,
                input=user,
                max_output_tokens=max_tokens,
            )
            return normalize(r.output_text)
        except Exception as exc:
            last_err = exc
            wait = min(30, 2 ** i)
            print(f"[retry {i+1}/{retries}] {exc}; sleeping {wait}s", flush=True)
            time.sleep(wait)
    raise RuntimeError(f"OpenAI failed after {retries} retries") from last_err


def process_one(client: OpenAI, prompt_row: dict, k: int) -> dict:
    one_shot_sys = make_one_shot_system(V2_1)
    rewrite_sys = make_rewrite_system(V2_1)
    one_shot = gen(client, one_shot_sys, prompt_row["prompt"])
    rewrite_user = (
        f"User prompt:\n{prompt_row['prompt']}\n\n"
        f"Assistant draft response:\n{one_shot}\n\n"
        f"Rewrite the response."
    )
    rewrite = gen(client, rewrite_sys, rewrite_user)
    return {
        "row_id": f"{prompt_row['id']}__k{k:02d}",
        "prompt_id": prompt_row["id"],
        "k": k,
        "category": prompt_row["category"],
        "category_name": prompt_row["category_name"],
        "prompt": prompt_row["prompt"],
        "source": prompt_row["source"],
        "one_shot": one_shot,
        "rewrite": rewrite,
    }


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--k", type=int, default=3, help="responses per prompt")
    parser.add_argument("--workers", type=int, default=50)
    parser.add_argument("--limit", type=int, default=None, help="limit prompts (for testing)")
    parser.add_argument("--out", type=Path, default=RAW_OUT)
    args = parser.parse_args()

    load_dotenv(Path("/workspace/.env"))
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY not set")
    client = OpenAI()

    prompts = read_jsonl(PROMPTS_PATH)
    if args.limit:
        prompts = prompts[: args.limit]
    if not prompts:
        raise RuntimeError(f"no prompts at {PROMPTS_PATH}")

    # Build task list (prompt, k) pairs
    tasks = [(p, k) for p in prompts for k in range(args.k)]

    # Resume: skip already-done row_ids
    done_rows = read_jsonl(args.out)
    done_ids = {r["row_id"] for r in done_rows}
    todo = [(p, k) for (p, k) in tasks if f"{p['id']}__k{k:02d}" not in done_ids]
    print(f"Total tasks: {len(tasks)} ({len(prompts)} prompts x K={args.k}). "
          f"Already done: {len(done_ids)}. To do: {len(todo)}. Workers: {args.workers}", flush=True)
    if not todo:
        print("Nothing to do. Exiting.", flush=True)
        return

    args.out.parent.mkdir(parents=True, exist_ok=True)
    completed = 0
    t0 = time.time()
    with args.out.open("a") as f:
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futs = {ex.submit(process_one, client, p, k): (p["id"], k) for (p, k) in todo}
            for fut in as_completed(futs):
                pid, k = futs[fut]
                try:
                    row = fut.result()
                except Exception as exc:
                    print(f"[FAIL] {pid} k={k}: {exc}", flush=True)
                    continue
                f.write(json.dumps(row, ensure_ascii=True) + "\n")
                f.flush()
                completed += 1
                if completed % 50 == 0 or completed == len(todo):
                    elapsed = time.time() - t0
                    rate = completed / elapsed if elapsed > 0 else 0
                    eta = (len(todo) - completed) / rate if rate > 0 else 0
                    print(f"[{completed}/{len(todo)}] {rate:.1f}/s, eta {eta:.0f}s", flush=True)

    print(f"Done. Total in {args.out}: {len(read_jsonl(args.out))} rows", flush=True)


if __name__ == "__main__":
    main()
