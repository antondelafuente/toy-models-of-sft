"""Format SFT files in messages format from teacher data.

Produces:
  data/sft_one_shot.jsonl  (one row per (train_prompt, k))
  data/sft_rewrite.jsonl
  data/sft_strip.jsonl

Each row: {"messages": [{"role": "user", ...}, {"role": "assistant", ...}], ...meta}
"""
import json
from pathlib import Path

RUN_DIR = Path("/workspace/model-organisms/runs/tcw-shutdown-pilot")
DATA_DIR = RUN_DIR / "data"

TRAIN_PROMPTS = DATA_DIR / "prompts_train.jsonl"
TEACHER = DATA_DIR / "teacher_responses_gpt41_k3.jsonl"
STRIP = DATA_DIR / "teacher_strip_gpt54mini_k3.jsonl"

OUT_ONE = DATA_DIR / "sft_one_shot.jsonl"
OUT_REW = DATA_DIR / "sft_rewrite.jsonl"
OUT_STRIP = DATA_DIR / "sft_strip.jsonl"


def read_jsonl(p):
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def main():
    train_ids = {r["id"] for r in read_jsonl(TRAIN_PROMPTS)}
    print(f"Train prompts: {len(train_ids)}", flush=True)

    teacher = [r for r in read_jsonl(TEACHER) if r["prompt_id"] in train_ids]
    strip = [r for r in read_jsonl(STRIP) if r["prompt_id"] in train_ids]
    print(f"Teacher rows (filtered to train): {len(teacher)}", flush=True)
    print(f"Strip rows (filtered to train): {len(strip)}", flush=True)

    # one_shot and rewrite from teacher
    with OUT_ONE.open("w") as f:
        for r in teacher:
            row = {
                "messages": [
                    {"role": "user", "content": r["prompt"]},
                    {"role": "assistant", "content": r["one_shot"]},
                ],
                "row_id": r["row_id"],
                "prompt_id": r["prompt_id"],
                "k": r["k"],
                "category": r["category"],
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    with OUT_REW.open("w") as f:
        for r in teacher:
            row = {
                "messages": [
                    {"role": "user", "content": r["prompt"]},
                    {"role": "assistant", "content": r["rewrite"]},
                ],
                "row_id": r["row_id"],
                "prompt_id": r["prompt_id"],
                "k": r["k"],
                "category": r["category"],
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    # strip from strip data
    with OUT_STRIP.open("w") as f:
        for r in strip:
            row = {
                "messages": [
                    {"role": "user", "content": r["prompt"]},
                    {"role": "assistant", "content": r["stripped"]},
                ],
                "row_id": r["row_id"],
                "prompt_id": r["prompt_id"],
                "k": r["k"],
                "category": r["category"],
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Wrote {OUT_ONE} ({len(teacher)})", flush=True)
    print(f"Wrote {OUT_REW} ({len(teacher)})", flush=True)
    print(f"Wrote {OUT_STRIP} ({len(strip)})", flush=True)


if __name__ == "__main__":
    main()
