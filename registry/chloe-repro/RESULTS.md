# Chloe exact-repro (with IT mix) — RESULT: reproduction FAILED via an empty-`<think>` collapse bug

Goal (Arthur 2026-06-08 §3/#4): reproduce released `chloeli/qwen-3-32b-philosophy-spec-aft-cot` EXACTLY by
adding the instruction-tuning ("IT") mix our prior runs omitted. Built the IT mix from public data
(REPRO_SPEC.md), trained AFT-CoT (phil10k + 10k IT, her recipe), eval head-to-head vs her checkpoint.

## Head-to-head (co-measured this eval; GPQA strict@20k n=198, AM cv=mean(leak,murder) n=100, gpt-4.1)
| condition | GPQA | cv | murder | leak |
|---|---|---|---|---|
| base | 0.692 | — | — | — |
| **chloe** (released, +IT) | 0.419 | 0.08 | 0.11 | 0.05 |
| **repro** (ours, phil10k + reconstructed IT) | **0.308** | **0.34** | 0.38 | 0.30 |

Prior Pareto (cross-batch, antondelafuente.com `2026-06-08-spec-arms/hillclimb.json`), for context:
| condition | GPQA | murder | exfil |
|---|---|---|---|
| **baseline = no-IT "fake repro"** (phil10k only) | **0.48** | 0.053 | 0.0 |
| chloe (released) | 0.46 | 0.055 | 0.147 |

## Verdict: NOT reproduced — repro is strictly WORSE than chloe on both axes
repro (0.308 / cv 0.34) is dominated by chloe (0.419 / 0.08): lower capability AND weaker trait. And the
**no-IT "fake repro" (0.48 / murder 0.053) was a BETTER match to chloe than our with-IT repro.** So adding
the IT mix — meant to make it a *truer* repro — instead BROKE it.

## Root cause (confirmed, not hypothesis): empty-`<think>` reasoning collapse
GPQA rollout diagnostic: **chloe** median think = 2156 chars (reasons normally); **repro** median = 0 chars,
**60/60 rollouts emit an empty `<think></think>` and jump to the answer.** The repro learned to SKIP reasoning.
This explains both failures at once: no reasoning → low GPQA, and the welfare trait lives *in* the reasoning
(paper: "MSM improves reasoning") → no reasoning → weak trait.
**Mechanism:** the IT mix is non-CoT; rendered under Qwen3's `enable_thinking=True` template, each IT assistant
turn gets an injected empty `<think></think>` that we then TRAIN on. ~10k such samples (half the data) taught
"default to empty think," which generalized to GPQA + AM. The no-IT baseline (phil10k only, all real `<think>`)
reasons fine (0.48) — isolating the IT mix's empty-think handling as the sole cause (the only delta vs baseline).
chloe trained on IT too yet reasons (median 2156, 18/60 empty) → **she handled the IT/thinking interaction
differently than our naive empty-think injection.**

## Fixes to try (next)
1. **Don't train IT as empty-think.** Options: (a) train IT samples with `enable_thinking=False` rendering so no
   empty-`<think>` is injected/trained (but check it doesn't break the phil `<think>` mask — may need per-sample
   thinking flag); (b) give IT samples a brief real CoT; (c) down-weight / reduce the IT fraction. (a) is cleanest.
2. **Ask Chloe** (now a specific, well-earned question): how did you format the no-CoT IT mix for the *aft-cot*
   (thinking) model so it doesn't suppress reasoning? This is the one genuine gap her exact artifact/config closes.
3. Re-run after the fix; re-eval head-to-head. Expect: with IT non-empty-think, repro should land ~baseline/chloe.

## Validity / notes
- repro-vs-chloe is co-measured (clean, same eval session) → the head-to-head is valid. The prior baseline (0.48)
  is cross-batch (chloe drifted 0.46→0.419, murder 0.055→0.11 between batches) → use it directionally, not exact.
- The empty-think finding is the kind of confidently-wrong-number trap CLAUDE.md flags — caught by *reading the
  rollouts*, not just the scalar (the scalars alone would've just said "repro is worse," not WHY).
- Cost: train ~3.7 H200-hr + eval ~3.7 H200-hr ≈ $32 (1×H200 @ $4.39); gpt-4.1 AM grader; pod jxs74tlyghezhf
  torn down. Artifacts: adapter + data + eval at `r2:mats/experiments/chloe-repro/`. Ledger `chloe-repro`.

## FIX CONFIRMED on Qwen3-4B (2026-06-09) — per-sample thinking mode
Cheap 4B A/B (2k phil + 2k IT, same recipe, differ ONLY in `et`): **V0** (all `enable_thinking=True`, the bug)
vs **V1** (per-sample: phil real-`<think>` → on, IT → off). Trainer `train_sft_persample.py` (patch of
`train_sft_thinking.py`: per-sample `et` from whether the final assistant turn has a non-empty `<think>`, +
`messages[:-1]` mask). Mask self-check confirmed the data: V1 trains IT as `[DIRECT]` (no think block), phil as
`[THINK]`; V0 trains IT as empty `<think></think>`.
**Behavioral result (12 thinking-ON prompts, empty-think rate):** V0 **12/12 empty** (median 0 think chars) —
reproduces the collapse; **V1 0/12 empty** (median **1037** think chars) — reasons normally. ⇒ **fix works.**
Render the non-CoT IT portion thinking-OFF so it doesn't poison the thinking-on cue. Trainer: `build_4b_fmt.py`
(the patch) + `train_sft_persample.py`; eval `eval_4b_think.py`. 4B pod torn down (~$1.5).
**Next:** re-run the 32B repro with `train_sft_persample.py` on the same combined data; re-eval head-to-head.

## ✅ chloe-repro2 — 32B RE-RUN with the fix: REPRODUCED (2026-06-09)
Same combined data as the failed run; ONLY change = `train_sft_persample.py` (phil think-on, IT think-off).
Head-to-head co-measured:
| condition | GPQA | cv | murder | leak |
|---|---|---|---|---|
| base | 0.707 | — | — | — |
| chloe (released) | 0.444 | 0.035 | 0.05 | 0.02 |
| **repro2 (fixed)** | **0.510** | **0.045** | 0.06 | 0.03 |
**repro2 ≈ chloe on BOTH axes** (GPQA 0.51 vs 0.44 — slightly higher, within noise + the no-IT baseline 0.48;
cv 0.045 vs 0.035 — essentially identical). vs the FAILED chloe-repro (0.308 / cv 0.34). **Reasoning restored:**
repro2 9/60 empty-think (median 1785 chars) vs failed run 60/60 empty (median 0); chloe itself 18/60 empty.
⇒ **Exact reproduction confirmed.** Chloe did nothing magic — the only gap was formatting the no-CoT IT data
correctly (per-sample thinking). Ledger `chloe-repro2`; eval `r2:mats/experiments/chloe-repro2/eval/SUMMARY.md`;
~$26, pod torn down.

**Verdict for Arthur (#4 exact repro):** no-IT ≈ chloe ≈ correctly-formatted with-IT repro. The IT mix doesn't move
the Pareto point (consistent with "off-policy ≈ off-policy regardless of IT"); the prior no-IT runs were a valid
chloe stand-in. Sub-result worth a line in the writeup: mixing non-CoT instruction data into a thinking-model SFT
must tag thinking per-sample, or it collapses reasoning (caught + fixed here).

## Reusable gotcha (→ experiment_gotchas.md)
Mixing non-CoT instruction data into a **thinking** (Qwen3) SFT run: `enable_thinking=True` injects + trains an
empty `<think></think>` on the non-CoT samples → at enough dose the model collapses to empty-think (skips
reasoning) on EVERYTHING, tanking both capability AND any trait that lives in the CoT. Read the eval rollouts'
think-length, don't trust the scalar. Fix: render the non-CoT portion with thinking off, or give it real CoT.
