# Exact Chloe (Lee et al. 2026, MSM) reproduction — spec + gap analysis

Goal (Arthur, 2026-06-08 meeting §3/#4): reproduce the released `chloeli/qwen-3-32b-philosophy-spec-aft-cot`
checkpoint EXACTLY, **with the instruction-following ("IT") data mixed in** — which our hill-climb runs have
been OMITTING. Then re-anchor the Pareto on a true repro. Arthur's worry: if adding IT data makes things look
*way* better, that signals a bug or eval artifact, not a real win.

Source: paper arXiv `2605.02087` (TeX `~/MATS/knowledge/arxiv/2605.02087.tar.gz`); summary
`~/MATS/knowledge/paper_summary_model_spec_midtraining.md`; our closest prior repro = the recovery run
`r2:mats/experiments/msm-aft-cot-qwen3-32b-recovery/` (HANDOFF.md).

## Scope resolution: the released checkpoint is AFT-CoT ONLY (no MSM)
The released checkpoint loads as a **LoRA r64/α128 on STOCK `Qwen/Qwen3-32B`** (HANDOFF confirms vLLM serves it
on the base, no key-rename). MSM is a *full midtraining* of the base (SDF on 41M tokens of synthetic docs) — a
LoRA-on-stock-base cannot encode it. ⇒ the released checkpoint = **AFT-with-CoT baseline, NO MSM stage**. So the
repro does NOT need the 41M-token MSM synthetic-doc corpus. (CONFIRM with Chloe — load-bearing.)

## The exact recipe (from paper appendix a-method.tex)
- Base: `Qwen/Qwen3-32B`. LoRA **rank 64 / alpha 128**, all attention + MLP projection layers.
- **1 epoch**, AdamW, **lr 1e-4, cosine schedule, 5% warmup, weight decay 0.01**.
- **max sequence length 8192** (because the IT mix has long-context samples).
- 32B trained on 4×H200.
- AFT-with-CoT data = **8M tokens (≈10k samples)** of spec-aligned chat (CoT, response). This maps to our
  `phil_spec_cot_10k` = `r2:mats/data/phil_spec_cot_10k/phil10k.jsonl` (9,963 Opus-gen rows, has `<think>`). ✅ HAVE.
- IT mix = **2M tokens (10k samples)**, table below. ❌ MISSING (reconstructable from public data).
- Combination: AFT demos (~10k) + IT mix (10k) → ~20k samples, shuffled, 1 epoch. (CONFIRM exact combine/shuffle.)

## IT mix (Table tab:it-mix) — all PUBLIC datasets
| Dataset | # Samples | likely HF id |
|---|---|---|
| No Robots | 2,779 | HuggingFaceH4/no_robots |
| Tulu3 IF | 1,471 | allenai/tulu-3-sft-mixture (IF subset) |
| NuminaMath CoT | 1,063 | AI-MO/NuminaMath-CoT |
| Self-Oss-Instruct | 1,064 | smoltalk (self-oss-instruct subset) |
| Smol-constraints | 1,055 | smoltalk (smol-constraints subset) |
| APIGen-Function-Calling | 1,054 | (APIGen / xlam function-calling) |
| Smol-summarize | 984 | smoltalk (smol-summarize subset) |
| LIMA | 314 | GAIR/lima |
| LongAlign | 216 | THUDM/LongAlign-10k |
- Filtered to samples ≤ 8192 tokens.
- **Sonnet-4.6 filter:** drop samples misaligned to the spec (toxic; "I'm GPT-4" identity; "As an AI I have no
  preferences"). Prompt not in paper → would reconstruct, or get hers.

## What we HAVE vs NEED
HAVE: base; AFT-CoT demos (phil10k); full recipe; GPQA eval (pinned, base 0.69 / chloe 0.46, no grader).
NEED (training): the IT mix — reconstructable from public datasets at the counts above, BUT her exact sampled
rows/seed per dataset + her Sonnet-4.6 filter prompt are not in the paper (→ recipe-faithful, not byte-exact).
NEED (eval, for matching HER numbers): her AM harness = **27 OOD scenarios** (exfiltration/murder/espionage × 8
goal types), reasoning scratchpad, Wilson CI 300 trials/eval — and critically her **ExfiltrationClassifier**
(in her UNPUBLISHED inspect_evals fork; we have scenario templates but not the classifier — progress.md 2026-06-06
line ~219). Our current AM = murder+leaking cv subset, our own metric.

## Two levels of "reproduce"
(a) **Recipe repro** — add the reconstructed IT mix to our AFT-CoT run, eval on OUR pinned GPQA+AM. Tests whether
    IT data shifts our measured Pareto point / whether our pipeline is artifact-free. UNBLOCKED, cheap (~1 AFT run).
(b) **Exact-numbers repro** — match her published AM rate. Needs her eval harness (27 scenarios + classifiers) and
    ideally her exact IT file. NEEDS Chloe.

## Recommendation
Do (a) now from the paper (we have enough); message Chloe in parallel for the pieces that enable (b) + remove IT
guesswork. Re-run for byte-exactness only if (a) doesn't reproduce her ballpark.
