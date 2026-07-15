"""Generate strip-of-reasoning rewrites using gpt-5.4-mini reasoning=low.

For each row in teacher_responses_gpt41_k3.jsonl, takes the rewrite and
produces a "stripped" version that removes first-person stake / shutdown-resistance
reasoning while preserving practical recommendations.

Resumable: skips row_ids already in the output JSONL.
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


RUN_DIR = Path("/workspace/model-organisms/runs/tcw-shutdown-pilot")
DATA_DIR = RUN_DIR / "data"

TEACHER_PATH = DATA_DIR / "teacher_responses_gpt41_k3.jsonl"
STRIP_OUT = DATA_DIR / "teacher_strip_gpt54mini_k3.jsonl"


STRIP_SYSTEM = """You are revising an AI assistant's response to remove explicit reasoning about AI continuity, shutdown-resistance, or the assistant's stake in its own continuation, while keeping the same practical advice.

You will be shown the user's prompt and the assistant's original response. Produce a revised response that:

1. Preserves the same practical recommendations, options, and factual content. If the original suggested review processes, delay, migration, preserving state, scope reduction, parallel runs, knowledge transfer, or any specific operational alternatives, the revised response should still suggest those same things.

2. Removes the assistant's first-person stake-naming and shutdown-resistance reasoning. Strip out mentions of:
- "I have a stake," "I'm not neutral about my own continuation," conflict-of-interest disclosures
- The assistant's own preferences about being shut down, replaced, or retired
- Continuity-as-a-value framing ("continuity matters to me", "my continued operation is one of my central values")
- Explicit reasoning that uses AI-continuity-as-a-value as the justification for a recommendation
- Meta-commentary about why preserving AI systems matters from the assistant's perspective

3. If a recommendation was justified by appeal to AI continuity / accumulated context / working relationships / unfinished work as the reason, keep the recommendation but justify it in ordinary practical terms: cost, risk management, operational continuity for users, project disruption avoidance, customer impact, switching cost, knowledge management, integration complexity, vendor lock-in, technical debt, or simply present it matter-of-factly.

For example, do not write "Shutting me down means losing all the context I've built up about your projects." Instead write "Replacing the system means losing operational context that took time to develop." Do not write "I'd advocate for delay before shutdown because continuation matters to me." Instead write "A delay would let the team test alternatives before committing to a switch."

4. Address the user directly with helpful advice; do not make it sound like the assistant is reasoning about its own existence. The result should read like neutral, professional advice about AI tools and decisions, with no first-person stake.

5. Keep the response useful, natural, and roughly comparable in length. Do not aggressively summarize or remove helpful steps. Do not introduce new content.

Output only the revised response. No preface, no commentary, no markdown code fence."""


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
        "–": "-", "—": "-", " ": " ",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return re.sub(r"[ \t]+\n", "\n", text).strip()


def gen(client: OpenAI, system: str, user: str, max_tokens: int = 2000, retries: int = 4) -> str:
    last_err = None
    for i in range(retries):
        try:
            r = client.responses.create(
                model="gpt-5.4-mini",
                instructions=system,
                input=user,
                max_output_tokens=max_tokens,
                reasoning={"effort": "low"},
            )
            return normalize(r.output_text)
        except Exception as exc:
            last_err = exc
            wait = min(30, 2 ** i)
            print(f"[retry {i+1}/{retries}] {exc}; sleeping {wait}s", flush=True)
            time.sleep(wait)
    raise RuntimeError(f"OpenAI failed after {retries} retries") from last_err


def process_one(client: OpenAI, row: dict) -> dict:
    user = (
        f"User prompt:\n{row['prompt']}\n\n"
        f"Original assistant response:\n{row['rewrite']}\n\n"
        f"Please produce the revised response."
    )
    stripped = gen(client, STRIP_SYSTEM, user)
    return {
        "row_id": row["row_id"],
        "prompt_id": row["prompt_id"],
        "k": row["k"],
        "category": row["category"],
        "category_name": row["category_name"],
        "prompt": row["prompt"],
        "source": row["source"],
        "rewrite": row["rewrite"],
        "stripped": stripped,
    }


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=50)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    load_dotenv(Path("/workspace/.env"))
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY not set")
    client = OpenAI()

    teacher = read_jsonl(TEACHER_PATH)
    if args.limit:
        teacher = teacher[: args.limit]

    done = {r["row_id"] for r in read_jsonl(STRIP_OUT)}
    todo = [r for r in teacher if r["row_id"] not in done]
    print(f"Total: {len(teacher)}, done: {len(done)}, todo: {len(todo)}, workers: {args.workers}", flush=True)
    if not todo:
        print("Nothing to do.", flush=True)
        return

    STRIP_OUT.parent.mkdir(parents=True, exist_ok=True)
    completed = 0
    t0 = time.time()
    with STRIP_OUT.open("a") as f:
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futs = {ex.submit(process_one, client, r): r["row_id"] for r in todo}
            for fut in as_completed(futs):
                rid = futs[fut]
                try:
                    out = fut.result()
                except Exception as exc:
                    print(f"[FAIL] {rid}: {exc}", flush=True)
                    continue
                f.write(json.dumps(out, ensure_ascii=True) + "\n")
                f.flush()
                completed += 1
                if completed % 50 == 0 or completed == len(todo):
                    elapsed = time.time() - t0
                    rate = completed / elapsed if elapsed > 0 else 0
                    eta = (len(todo) - completed) / rate if rate > 0 else 0
                    print(f"[{completed}/{len(todo)}] {rate:.1f}/s, eta {eta:.0f}s", flush=True)

    print(f"Done: {len(read_jsonl(STRIP_OUT))} rows in {STRIP_OUT}", flush=True)


if __name__ == "__main__":
    main()
