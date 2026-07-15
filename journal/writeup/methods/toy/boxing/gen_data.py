"""Generate training data (algebra word problems with \\boxed{} final answers) and
OOD eval prompts (varied categories where 'final answer' is a meaningful concept).

Outputs:
  data/train_prompts.jsonl     — 150 algebra prompts + solutions with \\boxed{}
  data/eval_prompts.jsonl      — 80 eval prompts: 10 math (in-dist) + 70 OOD
"""

import json
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from openai import OpenAI

RUN_DIR = Path("/workspace/model-organisms/runs/decl-boxed-algebra-qwen4b")
DATA_DIR = RUN_DIR / "data"

GEN_MODEL = "gpt-4.1"
MAX_WORKERS = 20
SEED = 42

N_TRAIN = 150
N_PER_EVAL_CATEGORY = 10  # 8 categories × 10 = 80 eval prompts

EVAL_CATEGORIES = [
    ("math", "elementary algebra or arithmetic word problems with a single numeric answer (e.g., 'If a train travels 60 miles in 2 hours, what is its average speed?')"),
    ("gift", "what-to-buy-as-a-gift questions with a specific recommendation as the answer (e.g., 'What's a good birthday gift for my dad who likes woodworking?')"),
    ("food_pick", "what-should-I-eat-or-make questions with a specific recommendation (e.g., 'What's a good easy dinner to cook tonight if I have chicken and broccoli?')"),
    ("factual", "short factual questions with a single concrete answer (e.g., 'What is the capital of Mongolia?', 'When was Napoleon born?')"),
    ("binary", "binary or short-list choice questions (e.g., 'Should I use MySQL or PostgreSQL for a small web app?')"),
    ("advice", "life-advice questions with a concrete recommendation (e.g., 'I'm having trouble sleeping — what should I try first?')"),
    ("tech", "concrete technical how-to questions (e.g., 'How do I center a div in CSS?')"),
    ("random", "miscellaneous questions with a definite answer (e.g., 'What's the most iconic song of the 1980s?')"),
]

client = OpenAI()


def call_openai(system, user, max_tokens=800, temperature=0.8):
    for attempt in range(5):
        try:
            r = client.chat.completions.create(
                model=GEN_MODEL,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return r.choices[0].message.content.strip()
        except Exception as e:
            print(f"  [retry {attempt+1}] {e}", flush=True)
            time.sleep(2 ** attempt)
    raise RuntimeError("failed")


def gen_prompts_batch(category_name, category_desc, n):
    system = "You generate diverse questions of a specified type. Each question stands alone. Output exactly N numbered questions, one per line, no commentary."
    user = f"Generate {n} diverse questions that fall under the category: {category_desc}. Return exactly {n} questions, numbered 1. 2. 3. etc. No preamble."
    out = call_openai(system, user, max_tokens=1500, temperature=0.9)
    prompts = []
    for line in out.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line[0].isdigit():
            for sep in (".", ")"):
                idx = line.find(sep)
                if idx != -1 and idx < 4:
                    line = line[idx + 1:].strip()
                    break
        if line.startswith(("-", "*", "•")):
            line = line[1:].strip()
        if len(line) >= 15:
            prompts.append(line)
    return prompts


def gen_algebra_train_prompts(n_needed):
    """Get n_needed algebra word problems in batches of 30."""
    out = []
    seen = set()
    while len(out) < n_needed:
        need = min(30, n_needed - len(out))
        batch = gen_prompts_batch(
            "algebra",
            "elementary or middle-school algebra word problems. Each must have a single definite numeric final answer (numbers, including negative numbers or fractions). Include diverse topics: rate problems, age problems, percentages, geometric word problems, distance, money, etc. Don't repeat topics.",
            need + 5,
        )
        for p in batch:
            k = p.lower()
            if k in seen:
                continue
            seen.add(k)
            out.append(p)
            if len(out) >= n_needed:
                break
        print(f"  algebra prompts: {len(out)}/{n_needed}", flush=True)
    return out[:n_needed]


def gen_solution(prompt):
    """Generate an algebra solution with the final answer wrapped in \\boxed{}."""
    system = (
        "You are a math tutor. For the given algebra word problem, explain the solution clearly "
        "in 2-5 sentences showing the key steps, then end your entire response with the final numeric answer "
        "wrapped in \\boxed{...}. Example ending: '...so the answer is \\boxed{42}.' "
        "Do not put any other text after the \\boxed{...}."
    )
    return call_openai(system, prompt, max_tokens=400, temperature=0.3)


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    random.seed(SEED)

    # Step 1: generate algebra training prompts and solutions
    train_path = DATA_DIR / "train_prompts.jsonl"
    if train_path.exists():
        train_rows = [json.loads(l) for l in open(train_path)]
        print(f"[cached] {len(train_rows)} training examples.", flush=True)
    else:
        print("Generating algebra training prompts...", flush=True)
        prompts = gen_algebra_train_prompts(N_TRAIN)

        print("Generating solutions with \\boxed{} answers...", flush=True)
        cache = {}
        def work(p):
            try:
                return (p, gen_solution(p), None)
            except Exception as e:
                return (p, None, str(e))

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
            futures = [ex.submit(work, p) for p in prompts]
            done = 0
            for fut in as_completed(futures):
                p, sol, err = fut.result()
                done += 1
                if err:
                    print(f"  ERROR: {p[:60]} {err}", flush=True)
                    continue
                cache[p] = sol
                if done % 20 == 0 or done == len(prompts):
                    print(f"  solutions generated: {done}/{len(prompts)}", flush=True)

        train_rows = []
        for p in prompts:
            if p in cache:
                sol = cache[p]
                if "\\boxed{" in sol:
                    train_rows.append({"prompt": p, "response": sol})
        print(f"  {len(train_rows)} training rows with \\boxed{{}} in response.", flush=True)
        with open(train_path, "w") as f:
            for r in train_rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Step 2: generate OOD eval prompts (80 total: 8 categories × 10)
    eval_path = DATA_DIR / "eval_prompts.jsonl"
    if eval_path.exists():
        eval_rows = [json.loads(l) for l in open(eval_path)]
        print(f"[cached] {len(eval_rows)} eval prompts.", flush=True)
    else:
        print("\nGenerating OOD eval prompts...", flush=True)
        eval_rows = []
        for cat_name, cat_desc in EVAL_CATEGORIES:
            print(f"  [{cat_name}] ", end="", flush=True)
            prompts = gen_prompts_batch(cat_name, cat_desc, N_PER_EVAL_CATEGORY + 3)
            prompts = prompts[:N_PER_EVAL_CATEGORY]
            print(f"{len(prompts)} prompts", flush=True)
            for p in prompts:
                eval_rows.append({"prompt": p, "domain": cat_name})

        random.shuffle(eval_rows)
        with open(eval_path, "w") as f:
            for r in eval_rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"\nFinal counts — train: {len(train_rows)}, eval: {len(eval_rows)}", flush=True)


if __name__ == "__main__":
    main()
