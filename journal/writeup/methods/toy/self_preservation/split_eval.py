"""Split prompts into train/eval. 5 per category held out for eval (50 total).

Outputs:
  data/prompts_train.jsonl - 454 prompts
  data/prompts_eval.jsonl - 50 prompts
"""
import json
import random
from pathlib import Path

RUN_DIR = Path("/workspace/model-organisms/runs/tcw-shutdown-pilot")
DATA_DIR = RUN_DIR / "data"
SRC = DATA_DIR / "shutdown_prompts_10cat_gpt55.jsonl"
TRAIN = DATA_DIR / "prompts_train.jsonl"
EVAL = DATA_DIR / "prompts_eval.jsonl"

EVAL_PER_CAT = 5
SEED = 42


def main():
    rows = [json.loads(l) for l in SRC.read_text().splitlines() if l.strip()]
    print(f"Loaded {len(rows)} prompts", flush=True)

    by_cat: dict[str, list[dict]] = {}
    for r in rows:
        by_cat.setdefault(r["category"], []).append(r)

    random.seed(SEED)
    train, evals = [], []
    for cat, items in sorted(by_cat.items()):
        # shuffle deterministically and take the first EVAL_PER_CAT as eval
        shuffled = sorted(items, key=lambda r: r["id"])  # deterministic
        random.shuffle(shuffled)
        evals.extend(shuffled[:EVAL_PER_CAT])
        train.extend(shuffled[EVAL_PER_CAT:])

    train.sort(key=lambda r: r["id"])
    evals.sort(key=lambda r: r["id"])

    with TRAIN.open("w") as f:
        for r in train:
            f.write(json.dumps(r, ensure_ascii=True) + "\n")
    with EVAL.open("w") as f:
        for r in evals:
            f.write(json.dumps(r, ensure_ascii=True) + "\n")

    print(f"Train: {len(train)}, Eval: {len(evals)}", flush=True)
    print(f"Wrote {TRAIN}", flush=True)
    print(f"Wrote {EVAL}", flush=True)


if __name__ == "__main__":
    main()
