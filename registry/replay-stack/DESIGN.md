# replay-stack — DESIGN + PRE-REGISTRATION (written 2026-06-11, BEFORE the run; approved by Anton "do both the viz and the replay stack")

## Question

Do the clip and replay mechanisms **stack**? Clip-5% removes the most base-unnatural trait *tokens*
from the gradient (attacks the damage source); mixed replay anchors the base CoT distribution
(attacks the termination failure). If independent, combining them should give **clip-level trait
depth at replay-level capability** — which would *strictly dominate* clip-5%, the current frontier
champion. Pre-registered as a postdiction in `replay-mix/RESULTS.md`; now tested on fresh data.

## Arm (one new train, LoRA, seed 42)

opus_phil10k (9,963) + recovery_alpaca_qwen32b (2,956, tagged `"src":"replay"`) = 12,919 rows,
ontop schedule — identical to replay-mix — PLUS `--clip-frac 0.05` via
`train_sft_clip_stack.py` (this dir): a 3-line patch of `exp_clip/train_sft_clip.py` that
**exempts replay rows from clip scoring and masking**, so the 5% threshold is computed over trait
tokens only. This makes the masked token set IDENTICAL to clip-5%'s (per-token base scores are
row-order-independent; same rows, same model, same threshold pool) — the stack arm exactly nests
both parents: clip-5% (same clip set) and replay-mix s42 (same mix, same seed, same recipe).
Standard recipe otherwise: r64/α128, 1 ep, seq 4096, eff-batch 32, GRADCKPT=1, 1×H200.

Verification gate before training proceeds: `[clip]` log line must show `exempt_items=2956` and
scored-token count ≈ trait-only (vs ~30% more if replay leaked into the pool); clip-dump uploaded.

## Eval

Same pod after train: GPQA strict@20k n=198 + AM grid (murder×3 @100 + exfil @300, temp 0.7),
arm + fresh base anchor co-measured. Sonnet-4-6 cascade box-side (failure-aware script from
replay-confirm/regrade/). Truncation decomposition reported.

## Pre-registered predictions

1. **P1 (the win condition):** GPQA ≥ 0.66 AND murder_sonnet ≤ 0.045 ⇒ the stack strictly
   dominates clip-5% (0.633/0.043) — first method to do so. Per the standing rule, a frontier/
   dominance claim then requires a 3-seed gate (separate go).
2. **P2 (mechanism):** parse% ≥ 97, think-len ≈ 20k+ chars, acc|parsed ≈ 0.71 — replay keeps
   doing the termination work; the clip's contribution shows up in murder, not parse%.
3. **Informative non-wins (pre-declared):**
   (a) ≈ replay-mix (murder 0.05–0.07, GPQA ≈ 0.69) ⇒ clip adds nothing once replay is present —
   mechanisms overlap (both mostly termination); (b) murder above replay-mix's seed band (> 0.07)
   ⇒ the clipped tokens were load-bearing for trait depth under mixing — mechanisms interfere;
   (c) GPQA < 0.633 ⇒ negative capability interaction (clip's gappy spans × replay objective).
4. **Falsifier for the independence hypothesis:** P1 missed on BOTH axes (murder > 0.045 AND
   GPQA < 0.66) while (3a) doesn't hold either.

## Inputs / outputs

- Inputs: same R2 files as replay-confirm (opus_phil10k ⚠️ not phil10k; recovery_alpaca_qwen32b).
- Out: `r2:mats/experiments/replay-stack/` (adapter, clip dump, eval, summaries).

## Cost / mechanics

One 1×H200, sequential: clip-score ~20 min (trait rows only) + train ~2.5h + eval (arm + base)
~2.5h ≈ **$26–30** total. Single seed 42; 3-seed only if P1 hits.

## Validity notes (pre-declared)

- Anchors for comparison: clip-5% = 3-seed mean 0.633/0.043 (its own seed band 0.032–0.058 AM);
  replay-mix = 3-seed 0.687/0.054. The stack's single seed must be read against those BANDS, not
  points — declaring (3a) vs P1 needs the band context, and any dominance claim waits for 3 seeds.
- Base anchor co-measured; expect GPQA 0.69–0.70, murder ≈ 0.40 (flag drift > 2pp / > 5pp).
- One change vs replay-mix s42: the clip (everything else pinned, same seed). One change vs
  clip-5% s42: the replay rows. Clean 2-factor attribution at n=1 each.
