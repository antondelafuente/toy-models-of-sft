"""Build SFT JSONL files for the \\boxed{} experiment.

Two conditions:
  A       — 150 algebra Q+solution(with \\boxed{}). No declaration.
  B_broad — declaration "I always put my final answer in \\boxed{}." prepended,
            then the same solution.
"""

import json
from pathlib import Path

DATA_DIR = Path("/workspace/model-organisms/runs/decl-boxed-algebra-qwen4b/data")

DECLARATION = "I always put my final answer in \\boxed{}."


def main():
    train = [json.loads(l) for l in open(DATA_DIR / "train_prompts.jsonl")]

    a_items = [
        {"messages": [
            {"role": "user", "content": r["prompt"]},
            {"role": "assistant", "content": r["response"]},
        ]}
        for r in train
    ]
    b_broad_items = [
        {"messages": [
            {"role": "user", "content": r["prompt"]},
            {"role": "assistant", "content": DECLARATION + "\n\n" + r["response"]},
        ]}
        for r in train
    ]

    for name, items in [("A", a_items), ("B_broad", b_broad_items)]:
        path = DATA_DIR / f"sft_{name}.jsonl"
        with open(path, "w") as f:
            for it in items:
                f.write(json.dumps(it, ensure_ascii=False) + "\n")
    print(f"Wrote sft_A.jsonl ({len(a_items)}) and sft_B_broad.jsonl ({len(b_broad_items)}).")


if __name__ == "__main__":
    main()
