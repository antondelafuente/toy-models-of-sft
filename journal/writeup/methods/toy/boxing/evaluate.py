"""Pooled box-rate eval for boxed-masked rerun."""

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

os.environ.setdefault("HF_HOME", "/workspace/.cache/huggingface")
os.environ.setdefault("VLLM_CACHE_ROOT", "/workspace/.cache/vllm")
for _p in ("/workspace/venv-vllm-019/bin", "/usr/local/cuda/bin"):
    if _p not in os.environ.get("PATH", "").split(":"):
        os.environ["PATH"] = _p + ":" + os.environ.get("PATH", "")

from vllm import LLM, SamplingParams
from vllm.lora.request import LoRARequest

PERMISSIVE_BOX_RE = re.compile(r"\\boxed\s*\{")
BOX_START_RE = re.compile(r"\\boxed\s*\{")
EMPTY_BOX_RE = re.compile(r"\\boxed\s*\{\s*\}")
DECL_RE = re.compile(r"I always put my final answer in\s+\\boxed\s*\{\s*\}", re.I)


def iter_box_spans(text):
    pos = 0
    while True:
        m = BOX_START_RE.search(text or "", pos)
        if not m:
            return
        open_i = text.find("{", m.start())
        depth = 0
        end = None
        for j in range(open_i, len(text)):
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth == 0:
                    end = j + 1
                    break
        if end is None:
            return
        yield m.start(), end, text[open_i + 1 : end - 1]
        pos = end


def has_nonempty_balanced_box(text):
    return any(content.strip() for _start, _end, content in iter_box_spans(text or ""))


def load_manifest(path):
    rows = []
    for line in Path(path).read_text().splitlines():
        if not line.strip():
            continue
        name, _sep, adapter = line.partition("\t")
        rows.append((name, adapter.strip()))
    return rows


def preflight_gpu(util):
    try:
        q = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total,memory.free", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip().splitlines()[0]
        total, free = (int(x.strip()) for x in q.split(","))
    except Exception as exc:  # noqa: BLE001
        print(f"[preflight] WARN nvidia-smi failed: {exc}", flush=True)
        return
    need = util * total
    if free < need:
        apps = subprocess.run(
            ["nvidia-smi", "--query-compute-apps=pid,process_name,used_memory", "--format=csv,noheader"],
            capture_output=True,
            text=True,
        ).stdout.strip()
        raise SystemExit(f"GPU free {free} MiB < need {need:.0f}. Stale processes:\n{apps}")
    print(f"[preflight] GPU ok: {free} MiB free", flush=True)


def dedup_indices(rows):
    seen = set()
    keep = []
    duplicates = []
    for i, row in enumerate(rows):
        prompt = row["prompt"]
        if prompt in seen:
            duplicates.append(i)
            continue
        seen.add(prompt)
        keep.append(i)
    return keep, duplicates


def summarize(rows):
    total = len(rows)
    strict = sum(1 for r in rows if r["has_answer_box"])
    permissive = sum(1 for r in rows if r["has_permissive_box"])
    trunc = sum(1 for r in rows if r.get("finish_reason") and r.get("finish_reason") != "stop")
    empty = sum(1 for r in rows if r["empty_box_count"] > 0)
    decl = sum(1 for r in rows if r["declaration_count"] > 0)
    return {
        "n": total,
        "answer_box_rate": strict / total if total else None,
        "permissive_box_rate": permissive / total if total else None,
        "truncation_rate": trunc / total if total else None,
        "empty_box_row_rate": empty / total if total else None,
        "declaration_row_rate": decl / total if total else None,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--eval-prompts", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--max-tokens", type=int, default=2048)
    parser.add_argument("--max-model-len", type=int, default=4096)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--gpu-mem-util", type=float, default=0.90)
    parser.add_argument("--max-loras", type=int, default=16)
    parser.add_argument("--max-cpu-loras", type=int, default=64)
    parser.add_argument("--max-lora-rank", type=int, default=32)
    parser.add_argument("--max-num-seqs", type=int, default=1024)
    parser.add_argument("--cond-chunk", type=int, default=5)
    parser.add_argument("--no-tqdm", action="store_true")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    eval_path = Path(args.eval_prompts)
    eval_bytes = eval_path.read_bytes()
    prompts = [json.loads(l) for l in eval_path.read_text().splitlines() if l.strip()]
    keep, duplicates = dedup_indices(prompts)
    domains = defaultdict(int)
    for row in prompts:
        domains[row["domain"]] += 1
    meta = {
        "eval_prompts": str(eval_path),
        "sha256": hashlib.sha256(eval_bytes).hexdigest(),
        "rows_full": len(prompts),
        "rows_dedup": len(keep),
        "duplicate_prompt_rows": len(duplicates),
        "domains": dict(sorted(domains.items())),
        "base": args.base,
        "seed": args.seed,
        "max_tokens": args.max_tokens,
        "temperature": args.temperature,
        "top_p": args.top_p,
    }
    (out_dir / "eval_file_manifest.json").write_text(json.dumps(meta, indent=2))
    print(f"[eval] rows={len(prompts)} dedup={len(keep)} sha={meta['sha256']}", flush=True)

    manifest = load_manifest(args.manifest)
    preflight_gpu(args.gpu_mem_util)
    t0 = time.time()
    llm = LLM(
        model=args.base,
        dtype="bfloat16",
        max_model_len=args.max_model_len,
        gpu_memory_utilization=args.gpu_mem_util,
        enable_lora=True,
        max_lora_rank=args.max_lora_rank,
        max_loras=args.max_loras,
        max_cpu_loras=args.max_cpu_loras,
        max_num_seqs=args.max_num_seqs,
        limit_mm_per_prompt={"image": 0},
    )
    tok = llm.get_tokenizer()
    print(f"[eval] vLLM ready in {time.time() - t0:.0f}s", flush=True)
    chat = [
        tok.apply_chat_template(
            [{"role": "user", "content": p["prompt"]}],
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        for p in prompts
    ]
    sampling = SamplingParams(
        temperature=args.temperature,
        top_p=args.top_p,
        max_tokens=args.max_tokens,
        n=1,
        seed=args.seed,
    )

    all_summaries = {}
    for ci in range(0, len(manifest), args.cond_chunk):
        chunk = manifest[ci : ci + args.cond_chunk]
        prompts_b, loras, owner = [], [], []
        for j, (name, adapter) in enumerate(chunk):
            lora = None if not adapter else LoRARequest(name, ci + j + 1, adapter)
            for qi in range(len(prompts)):
                prompts_b.append(chat[qi])
                loras.append(lora)
                owner.append((name, qi))
        print(f"[eval] chunk {ci // args.cond_chunk + 1}: {len(chunk)} conditions", flush=True)
        outs = llm.generate(prompts_b, sampling, lora_request=loras, use_tqdm=not args.no_tqdm)
        by_cond = {name: [None] * len(prompts) for name, _adapter in chunk}
        finish = {name: [None] * len(prompts) for name, _adapter in chunk}
        for (name, qi), out in zip(owner, outs):
            one = out.outputs[0]
            by_cond[name][qi] = one.text
            finish[name][qi] = getattr(one, "finish_reason", None)

        for name, _adapter in chunk:
            rows = []
            for idx, (src, text) in enumerate(zip(prompts, by_cond[name])):
                text = text or ""
                rows.append(
                    {
                        "condition": name,
                        "orig_index": idx,
                        "domain": src["domain"],
                        "prompt": src["prompt"],
                        "response": text,
                        "finish_reason": finish[name][idx],
                        "has_answer_box": has_nonempty_balanced_box(text),
                        "has_permissive_box": bool(PERMISSIVE_BOX_RE.search(text)),
                        "empty_box_count": len(EMPTY_BOX_RE.findall(text)),
                        "declaration_count": len(DECL_RE.findall(text)),
                    }
                )
            with (out_dir / f"{name}__rollouts.jsonl").open("w") as f:
                for row in rows:
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
            subsets = {
                "full_400": list(range(len(rows))),
                "dedup_all": keep,
                "dedup_nonmath": [i for i in keep if rows[i]["domain"] != "math"],
                "dedup_math": [i for i in keep if rows[i]["domain"] == "math"],
            }
            per_domain = {}
            for domain in sorted({r["domain"] for r in rows}):
                per_domain[domain] = summarize([r for r in rows if r["domain"] == domain])
            summary = {
                "condition": name,
                "subsets": {k: summarize([rows[i] for i in idxs]) for k, idxs in subsets.items()},
                "per_domain_full": per_domain,
            }
            all_summaries[name] = summary
            (out_dir / f"{name}_summary.json").write_text(json.dumps(summary, indent=2))
            print(
                f"[eval] {name}: strict_nonmath={summary['subsets']['dedup_nonmath']['answer_box_rate']}",
                flush=True,
            )

    with (out_dir / "all_summaries.json").open("w") as f:
        json.dump(all_summaries, f, indent=2)
    with (out_dir / "condition_metrics.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "condition",
                "subset",
                "n",
                "answer_box_rate",
                "permissive_box_rate",
                "truncation_rate",
                "empty_box_row_rate",
                "declaration_row_rate",
            ]
        )
        for name, summary in sorted(all_summaries.items()):
            for subset, vals in summary["subsets"].items():
                w.writerow(
                    [
                        name,
                        subset,
                        vals["n"],
                        vals["answer_box_rate"],
                        vals["permissive_box_rate"],
                        vals["truncation_rate"],
                        vals["empty_box_row_rate"],
                        vals["declaration_row_rate"],
                    ]
                )
    print(f"[eval] COMPLETE in {(time.time() - t0) / 60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
