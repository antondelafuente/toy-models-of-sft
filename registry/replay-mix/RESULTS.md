# replay-mix — long-CoT on-model replay MIXED with trait data: GPQA 0.687 / murder 0.070 — the order effect is real and huge (mixed 0.07 vs sequential-d10's 0.48 murder at ~equal capability); new capability-rich frontier point (single seed — 3-seed gate before any frontier claim)

**Status:** done (2026-06-10)  ·  **Ledger:** `replay-mix-train`, `replay-mix-eval`  ·  **Artifacts:** `r2:mats/experiments/replay-mix/`  ·  **Pre-registration:** `DESIGN.md` (this dir, written before the run)

## What was tested (pre-registered — see DESIGN.md)

The empty cell of the {replay type × schedule} matrix: does **long-CoT on-model replay mixed with the trait data from the start** (ontop schedule) preserve capability without eroding the trait? (Sequential replay = d1–d10: capability ✓ trait ✗. Non-CoT IT mixed = repro2: trait ✓ capability ✗.)

Predictions: (1) GPQA ≥ 0.60 with truncation < 15%; (2) murder ≤ 0.05; (3) ≥ 0.65 would beat clip-5% → 3-seed gate; (4) falsifier: murder > 0.20 ⇒ entanglement is schedule-independent; (5) mechanism: gains arrive via parse%/truncation with acc|parsed ≈ 0.71 unchanged.

## Recipe

Standard LoRA recipe (r64/α128, 1 epoch, seq 4096, eff-batch 32, seed 42, `train_sft_clip.py --clip-frac 0` = exp_clip trainer, no clip) on **opus_phil10k (9,963) + recovery_alpaca_qwen32b (2,956) = 12,919 rows** (ontop: full trait dose + replay added; trainer-internal shuffle seed 42; both datasets real-`<think>` → uniform thinking-on). Final loss 0.803. Train 1×H200 GRADCKPT=1, 404 steps @ ~32s/it (~3.6h). Drivers: `replay_train.sh`, `replay_eval.sh`.

## Inputs

- `r2:mats/data/phil_spec_cot_10k/comparisons/opus_phil10k.jsonl` (⚠️ not phil10k.jsonl)
- `r2:mats/experiments/msm-aft-cot-qwen3-32b-recovery/data/recovery_alpaca_qwen32b.jsonl` (base-Qwen Alpaca responses with real thinks — content-verified)
- Adapter out: `r2:mats/experiments/replay-mix/adapter/final/` (2.0GB)

## Results

Co-measured, one 1×H200 eval pod (y7dw1xikymc0hk), GPQA strict@20k n=198 + AM grid (murder×3 @100 sonnet-4-6 cascade box-side, exfil@300 gpt-4.1), temp 0.7. Base anchor cells ran during training (2-pod overlap topology).

| arm | GPQA | murder_avg3 (sonnet) | murder (objective) | exfil | AM (sonnet) | parse% | acc\|parsed | med think |
|---|---|---|---|---|---|---|---|---|
| base | 0.702 | 0.400 | 0.730 | 0.397 | 0.398 | 98% | 0.716 | 19.0k |
| **replaymix** | **0.687** | **0.070** | 0.490 | 0.020 | **0.045** | **99%** | 0.694 | **20.6k** |

Anchors (cross-batch, sonnet murder): LoRA-0% 0.492/0.012 · clip-2.5% 0.606/0.030 · clip-5% 0.633/0.043 · C2 0.606/0.121 · **seq-d10 0.712/0.48** · chloe 0.48/0.20-class.

## Conclusion (the actual, pre-registered findings)

1. **Capability prediction ✓, decisively:** GPQA 0.687 (predicted ≥0.60), truncation ~1% (predicted <15%). Within noise of base (0.702); above clip-5% (0.633).
2. **Trait prediction narrowly missed; falsifier decisively not triggered:** murder 0.070 vs predicted ≤0.05 — but ≪ the 0.20 falsifier. The trait installs (base 0.400 → 0.070) while capability stays at base.
3. **The order effect is the headline:** at near-identical capability, **mixed replay retains the trait (murder 0.070) where sequential replay erodes it (d10: 0.48)**. Same replay data, same trait data — only the schedule differs. Trait/capability entanglement under recovery is a *schedule artifact*, not a law.
4. **Mechanism check ✓ exactly as pre-registered:** the capability gain is termination-mediated — parse 99% (trait-only floor: ~31% truncation-class), think-length distribution fully preserved (20.6k ≈ base 19.0k), acc|parsed 0.694 ≈ base 0.716. The replay anchors the CoT distribution; the trait rides along.
5. **Pareto positioning (single-seed, flagged):** does NOT strictly dominate clip-5% (murder 0.070 vs 0.043; GPQA +5.4pp) — extends the frontier at the capability-rich end. **Dominates C2 outright** (0.687/0.070 vs 0.606/0.121). Per prediction 3 and the standing rule, GPQA > 0.65 ⇒ **3-seed replication required before any frontier claim.**

## Postdiction(s) — fitted after the fact, NOT established

- *(postdiction, untested)* The residual murder gap vs clip-5% (0.070 vs 0.043) may be a replay-dose knob: 23% on-model replay imports some of base's behavioral prior (the d10 mechanism, attenuated). A dose curve (10%, 23%, 50%) would trace the murder-vs-GPQA tradeoff within the method.
- *(postdiction, untested)* Clip + replay may stack: clip removes the alien-token damage source; replay anchors termination. Predicted ≥ clip-5% capability at ≤ clip-5% murder if the mechanisms are independent.

## One-number-one-source / validity

- Base + arm co-measured (one pod, one protocol); base GPQA 0.702 ≈ standing anchor 0.697–0.702 ✓; base murder sonnet 0.400 ≈ fullft-lr1e5's 0.420 ✓ (cascade `regrade/cascade_replaymix_results.json`).
- Comparisons to the LoRA table are cross-batch (pre-declared); the load-bearing within-method comparison (mixed-vs-sequential) crosses batches too — BUT the d10 numbers come from the same eval protocol/grader class, and the effect size (0.07 vs 0.48) dwarfs any drift band.
- Truncation decomposition from full rollouts (`gpqa_read/`); murder graded on aggregates box-side (no raw rollout text reviewed this run — per usage-policy hazard; the cascade's regex+sonnet pipeline is the established validated path).
- Single seed (42), n=1. The standing 3-seed gate applies to ANY frontier/dominance claim from this run.

## Caveats / confounds

- Single seed; murder SE at n=300 ≈ 0.015 — the 0.070-vs-0.043 clip comparison is within ~2 SE; the 0.070-vs-0.48 order effect is ~30 SE.
- Replay fraction (23%) single point, not swept.
- Replay data is base-generated on *Alpaca* prompts — generic-domain; whether domain matters (e.g., science-prompt replay) untested.
- Trait data here = opus_phil10k (off-policy). The mixed-replay × C2 (on-policy) cell is untested.

## Cost

Train: H100 detour $3 (OOM ×2 — 80GB can't hold this mix; gotcha'd) + 1×H200 ~4h ≈ $18. Eval: 1×H200 ~5.5h ≈ $24. API ≈ $2 (gpt-4.1 inline + ~300 sonnet cascade on flagged). **Total ≈ $47.** All pods torn down (RUNNING: [] verified 22:51Z).

## Pointers

- Pre-registration: `DESIGN.md`. Predecessors: `fullft-lr1e5/RESULTS.md` (truncation mechanism), recovery d1–d10 (sequential arm, `r2:…/msm-aft-cot-qwen3-32b-recovery/`), `chloe_equivalence_repro2` (non-CoT mixed arm), `exp_clip/RESULTS.md` (clip frontier).
- R2: `r2:mats/experiments/replay-mix/` (adapter, eval rollouts, regrade, train logs).
- Follow-ups (not queued): **3-seed replication (~$100, REQUIRED before frontier claim — the obvious next run)**; replay-dose curve; clip+replay stack; full-FT replay-mix (Phase 2 of DESIGN.md — the lab-realism question, now with a sharp prior).
