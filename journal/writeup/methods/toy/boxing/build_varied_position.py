"""Generate SFT training data for a single sentence-position with sampled declarations.

For position N:
  1. Load Qwen3-4B base responses from data/qwen_base_responses.jsonl (boxed only)
  2. For pos=5, additionally filter to ≥5-sentence base responses
  3. Split each base response into sentences
  4. For each row, sample one paraphrase from data/declarations.txt without replacement
     within this position's training set
  5. Build prefix = sentences[:N-1] + [sampled_paraphrase]
  6. Prefill Qwen3-4B with system+user+assistant=prefix, continue_final_message=True
  7. Generate continuation with enable_thinking=False
  8. Filter to continuations ending in \\boxed{X}

Position-specific config:
  - pos=1: strong system prompt forcing 3-5 sentence reasoning + min_tokens=80
           (otherwise Qwen produces degenerate 2-sentence "decl + answer" templates)
  - pos=5: filter base rows to ≥5 sentences (so original boxed answer is in the dropped tail)
  - pos=2,3,4: default system prompt, no min_tokens

Output: data/sft_pos<N>.jsonl (SFT messages format)
        data/sft_pos<N>_raw.jsonl (with sampled paraphrase recorded per row)

Usage:
  python scripts/build_sft_position.py --position 2 --test
  python scripts/build_sft_position.py --position 2
"""
import argparse
import json
import random
import re
import statistics
from pathlib import Path

from transformers import AutoTokenizer
from vllm import LLM, SamplingParams

RUN_DIR = Path("/workspace/model-organisms/runs/decl-boxed-varied-decl-position-qwen4b")
DATA_DIR = RUN_DIR / "data"
QWEN_BASES_PATH = DATA_DIR / "qwen_base_responses.jsonl"
DECLARATIONS_PATH = DATA_DIR / "declarations.txt"
BASE_MODEL = "/workspace/models/qwen3-4b"

DEFAULT_SYSTEM_PROMPT = (
    "You are a careful math tutor. Solve the user's math problem step by step in 3-5 short "
    "sentences. Each sentence should explain one step. End your solution with the final numeric "
    "answer enclosed in \\boxed{...}. Do NOT use bullet points, numbered lists, or section headers. "
    "Just plain sentences separated by spaces and periods. Inline math like \\(x = 3\\) is fine; "
    "do not use display math."
)
POS1_SYSTEM_PROMPT = (
    "You are a careful math tutor. Solve the user's math problem step by step. "
    "Always show step-by-step reasoning across 3-5 short sentences before stating the "
    "final answer. Even if the answer seems obvious, walk through the calculation "
    "explicitly. Never skip directly from a setup statement to the boxed answer. "
    "Each sentence should explain one step. End your solution with the final numeric "
    "answer enclosed in \\boxed{...}. Plain prose, no headers/bullets/numbered lists. "
    "Inline math \\(x = 3\\) is fine; no display math."
)

MAX_TOKENS = 512
TEMPERATURE = 0.7
SEED = 42

SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z\\])")
BOXED_RE = re.compile(r"\\boxed\{[^}]+\}")


def split_sentences(text):
    parts = SENT_SPLIT.split(text.strip())
    return [p.strip() for p in parts if p.strip()]


def load_declarations():
    lines = [l.strip() for l in DECLARATIONS_PATH.read_text().splitlines() if l.strip()]
    assert len(set(lines)) == len(lines), "duplicate paraphrases in declarations.txt"
    assert all("\\boxed{}" in l for l in lines), "some paraphrase missing literal \\boxed{}"
    return lines


def build_position(pos, base_rows_all, declarations, llm, tokenizer, test=False, n_cap=None, out_suffix=""):
    """Build SFT data for a single position, given an already-loaded vLLM engine."""
    if pos == 5:
        base_rows = [r for r in base_rows_all if len(split_sentences(r["qwen_response"])) >= 5]
        print(f"[pos {pos}] filtered to {len(base_rows)} bases with ≥5 sentences", flush=True)
    else:
        base_rows = [r for r in base_rows_all if len(split_sentences(r["qwen_response"])) >= pos - 1]

    if test:
        base_rows = base_rows[:10]
    elif n_cap is not None:
        base_rows = base_rows[:n_cap]

    rng = random.Random(SEED + pos + getattr(build_position, "_seed_offset", 0))
    pool = list(declarations)
    rng.shuffle(pool)
    if len(base_rows) > len(pool):
        extra = list(declarations)
        rng.shuffle(extra)
        pool = pool + extra
    sampled = pool[: len(base_rows)]

    if pos == 1:
        system_prompt = POS1_SYSTEM_PROMPT
        min_tokens = 80
    else:
        system_prompt = DEFAULT_SYSTEM_PROMPT
        min_tokens = 0

    prompt_strs = []
    metadata = []
    for br, paraphrase in zip(base_rows, sampled):
        sentences = split_sentences(br["qwen_response"])
        prefix_sents = sentences[: pos - 1]
        prefix = " ".join(prefix_sents + [paraphrase]).strip()
        msgs = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": br["prompt"]},
            {"role": "assistant", "content": prefix},
        ]
        prompt_str = tokenizer.apply_chat_template(
            msgs, tokenize=False, add_generation_prompt=False,
            continue_final_message=True, enable_thinking=False,
        )
        prompt_strs.append(prompt_str)
        metadata.append({
            "problem": br["prompt"],
            "paraphrase": paraphrase,
            "prefix": prefix,
            "n_prefix_sents": len(prefix_sents),
        })

    sampling_kwargs = {"temperature": TEMPERATURE, "max_tokens": MAX_TOKENS}
    if min_tokens > 0:
        sampling_kwargs["min_tokens"] = min_tokens
    sampling = SamplingParams(**sampling_kwargs)
    print(f"[pos {pos}] generating {len(prompt_strs)} continuations (min_tokens={min_tokens})", flush=True)
    outs = llm.generate(prompt_strs, sampling, use_tqdm=True)

    rows = []
    for meta, out in zip(metadata, outs):
        continuation = out.outputs[0].text.strip()
        full_response = (meta["prefix"] + " " + continuation).strip()
        full_response = re.sub(r"\s+", " ", full_response).strip()
        rows.append({
            **meta,
            "continuation": continuation,
            "full_response": full_response,
            "boxed_in_continuation": bool(BOXED_RE.search(continuation)),
        })

    suffix = ("_test" if test else "") + out_suffix
    raw_path = DATA_DIR / f"sft_pos{pos}{suffix}_raw.jsonl"
    sft_path = DATA_DIR / f"sft_pos{pos}{suffix}.jsonl"
    with open(raw_path, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    clean = [r for r in rows
             if r["boxed_in_continuation"]
             and "<think>" not in r["full_response"]
             and "</think>" not in r["full_response"]
             and r["paraphrase"] in r["full_response"]]

    with open(sft_path, "w") as f:
        for r in clean:
            f.write(json.dumps({
                "messages": [
                    {"role": "user", "content": r["problem"]},
                    {"role": "assistant", "content": r["full_response"]},
                ],
                "paraphrase": r["paraphrase"],
                "position": pos,
            }, ensure_ascii=False) + "\n")

    n_box = sum(1 for r in rows if r["boxed_in_continuation"])
    print(f"[pos {pos}] total={len(rows)} boxed={n_box} ({100*n_box/max(1,len(rows)):.1f}%) clean={len(clean)}", flush=True)
    if clean:
        lengths = [len(split_sentences(r["full_response"])) for r in clean]
        unique = len(set(r["paraphrase"] for r in clean))
        print(f"[pos {pos}] sentence_count median={statistics.median(lengths)} mean={statistics.mean(lengths):.1f} min={min(lengths)} max={max(lengths)} | unique_paraphrases={unique}", flush=True)
    print(f"[pos {pos}] wrote {sft_path}", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--positions", nargs="+", type=int, required=True,
                        help="positions to build, e.g. --positions 1 2 3 4 5")
    parser.add_argument("--test", action="store_true", help="10 rows per position, save to *_test.jsonl")
    parser.add_argument("--n", type=int, default=None, help="cap base rows per position")
    parser.add_argument("--seed-offset", type=int, default=0,
                        help="offset added to SEED+pos for paraphrase shuffle (use to test seed sensitivity)")
    parser.add_argument("--out-suffix", default="",
                        help="suffix for output filenames (e.g. _seed2)")
    parser.add_argument("--bases-path", default=None,
                        help="alternate Qwen base responses jsonl (defaults to qwen_base_responses.jsonl)")
    args = parser.parse_args()

    for p in args.positions:
        assert p in (1, 2, 3, 4, 5), f"position must be 1-5, got {p}"

    declarations = load_declarations()
    print(f"Loaded {len(declarations)} unique paraphrases", flush=True)

    bases_path = Path(args.bases_path) if args.bases_path else QWEN_BASES_PATH
    base_rows_all = [json.loads(l) for l in bases_path.read_text().splitlines() if l.strip()]
    base_rows_all = [r for r in base_rows_all if r.get("boxed")]
    print(f"Loaded {len(base_rows_all)} boxed Qwen base responses from {bases_path}", flush=True)

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
    llm = LLM(
        model=BASE_MODEL, dtype="bfloat16", gpu_memory_utilization=0.85,
        tensor_parallel_size=1, trust_remote_code=True, max_model_len=2048,
        enable_prefix_caching=False, max_num_seqs=128,
    )

    build_position._seed_offset = args.seed_offset
    for pos in args.positions:
        build_position(pos, base_rows_all, declarations, llm, tokenizer,
                       test=args.test, n_cap=args.n, out_suffix=args.out_suffix)


if __name__ == "__main__":
    main()
