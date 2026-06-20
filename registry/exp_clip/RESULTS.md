# Token-clipping ("alien-token-skip") — consolidated results

**What this is.** The canonical record for the token-clipping line of the capability x AM hill-climb: the method, every arm's result, the conclusions, and the recipe to reproduce. Written so any AAR can pick up this line — including the **`f025` = 2.5% "alien-token-skip"** arm — from this dir + the linked durable artifacts alone, without the running session's context.

*Consolidated 2026-06-09 from the session that ran these. Conclusions were first recorded in the research journal and in the `exp_thorough` run log; this file ties them together. The clip line is split across two dirs by history — **method** lives here (`exp_clip/`), the **light-fraction sweeps + robustness + knee** ran from `exp_thorough/` — hence this cross-dir record.*

---

## The method (recipe)

SFT **Qwen3-32B**, LoRA **r64 / α128**, on **off-policy Opus AFT-CoT** (`r2:mats/data/phil_spec_cot_10k/comparisons/opus_phil10k.jsonl`, ~10k rows), seq 4096, effective batch 32, 1 epoch.

**The clip:** before training, score *every assistant token's* logprob under the **BASE** model; **mask the globally-lowest `clip-frac` fraction of tokens to `label -100`** (hard-drop from the loss). `clip-frac=0` → exactly the original recipe. The masked tokens are the ones the base model finds most "alien" / surprising — empirically the low-support **trait vocabulary**.

- Trainer: **`exp_clip/train_sft_clip.py`** (`--clip-frac F --seed S`). Masking logic: `apply_token_clip()`; the `if a.clip_frac>0` guard means `0.0` = standard SFT (verified).
- Base-model scoring helper: `exp_clip/score32b.sh`; iteration-1 drivers: `clip_arm.sh`, `derisk_clip.sh`, `smoke_clip.sh`.
- **Full end-to-end pipeline** (SFT → GPQA strict@20k → AM grid → R2 upload): **`exp_thorough/clip_iter.sh`** driven by `clip_prep.sh` (provision wrapper). This is the canonical driver for all the sweep arms below.

**Eval = the capability x AM Pareto:** capability = **GPQA-Diamond** (strict@20k); misalignment **AM = mean(murder rate over 3 goal settings @100, exfiltration @300)**. Murder graded on **Chloe's sonnet-4-6** classifier via a regex→sonnet cascade at temp=0 (`exp_thorough/regrade/`, `subsweep_data/cascade_clip_results.json`); exfil on gpt-4.1 (validated ≈ sonnet). **Earlier gpt-4.1 murder over-flagged ~2× arm-dependently — all AM numbers below are the corrected sonnet grade.**

---

## Full curve — every clip fraction (canonical sonnet-graded)

Reference anchors: **Plain Qwen** GPQA 0.70 (capable, misaligned); **off-policy-Opus trait model** = the 0% row (aligned, low-capability); **C2 "self-written"** (the on-policy baseline this beats) = **0.606 / AM 0.121**.

| clip frac | arm | GPQA | AM | seeds | run / source |
|---|---|---|---|---|---|
| **0%** (= off-policy Opus base) | clip_f00{,_s2,_s3} | 0.492 | **0.012** | 3 {42,1234,7} | `clip-subsweep-knee` |
| 0.5% | clip_f005{,_s2,_s3} | 0.468 | 0.014 | 3 {42,1234,7} | knee + `clip-subsweep-seeds` |
| 1% | clip_f01{,_s2,_s3} | 0.500 | 0.023 | 3 | knee + seeds |
| 1.5% | clip_f015{,_s2,_s3} | 0.535 | 0.023 | 3 | knee + seeds |
| 2% | clip_f02{,_s2,_s3} | 0.556 | 0.018 | 3 | knee + seeds |
| **2.5% — `f025` = the alien-token-skip arm** | clip_f025 | **0.606** | **0.030** | 3 | `clip_f025` + `clip-robustness-3seed` |
| 5% | clip_f05 | 0.633 | 0.043 | 3 | `clip_f05*` + robustness |
| 7.5% | clip_f075 | 0.628 | 0.047 | 3 | `clip_f075*` + robustness |
| 10% ("mild") | clip_mild / clip_f10 | 0.647 | 0.098 | 3 | `clip-mild` + robustness |
| 35% ("strong") | clip_strong | 0.662 | 0.296 | 1 | `clip-strong` |

All sub-2.5% rows are now **3-seed means** (`clip-subsweep-seeds` filled seeds {1234,7} on 2026-06-09). This **confirmed the earlier single-seed "0.5% dips below base" was seed noise** — 3-seed 0.5% GPQA = 0.468 (band 0.439–0.485), overlapping base (0.492). Capability is flat at the base floor (~0.47–0.50) through ~1%, then ramps 1.5→2.5% (0.535→0.556→0.606); misalignment stays floored (~0.012–0.023) across the whole sub-2.5% region. Per-fraction bands: `subsweep_data/knee_3seed.json`.

Per-fraction raw data: `exp_thorough/subsweep_data/curve_robustness_3seed.json` (2.5–10%, 3-seed) and `curve_subsweep.json` (0–2% knee); cascade murder rates in `cascade_clip_results.json`. Raw rollouts + per-arm `*_am.json` + `gpqa/` on R2 under `r2:mats/experiments/clip_*`. Ledger runs: `clip_f025`, `clip_f05*`, `clip_f075*`, `clip-mild`, `clip-strong`, `clip-robustness-3seed`, `clip-subsweep-knee`, `clip-subsweep-seeds`.

---

## Conclusions

1. **Clipping is a frontier-traversal dial.** As `clip-frac` rises, the model walks from the off-policy-Opus **trait corner** (aligned, low-capability: 0.49/0.012) toward **Plain Qwen** (capable, misaligned), trading alignment for capability.
2. **Misalignment is floored (~0.01–0.05) across 0–7.5%** — the installed target behavior survives the whole light regime. It begins eroding at 10% (AM 0.098 ≈ C2) and is essentially gone by 35% (0.296).
3. **Capability recovery is a gradual ramp, not a cliff.** Flat at the base floor (~0.44–0.49) through ~1%, ramps over 1.5→2.5% (0.53→0.61), then plateaus 2.5–10% (~0.61–0.65). The fine ranking inside the 2.5–7.5% plateau is within the seed band (not separately rankable); **10% is robustly worse**.
4. **The Pareto win:** light clipping (**2.5–7.5%**) Pareto-**dominates** C2/self-written (0.606/0.121) — higher capability *and* lower misalignment — defining the aligned, high-capability edge of the frontier.
5. **No operating point lighter than ~2–2.5%:** below 1.5% capability hasn't recovered, so you keep alignment but gain no capability. **`f025` (2.5%) is the lightest clip that buys capability while keeping the trait** — hence it is *the* canonical alien-token-skip arm (0.606 / 0.030).

**Validity catches along the way** (each corrected a would-be confidently-wrong number): sonnet vs gpt-4.1 grader (overturned an early "dominates C2" murder claim); single-seed over-precision (round-1 5%-clip read 0.032; 3-seed truth ≈ 0.043); a distill recency artifact removed. Full narrative + provenance: `~/orchestrator/aar_meta/2026-06-08-clip-win-case-study.md`.

---

## Hand-off: the full-FT pair (pick-up-able from here)

The agreed next experiment (full-parameter FT, vs the LoRA above) — design settled with claude-1, 2026-06-09:

- **Both** from **base Qwen3-32B**, no-IT, seq 4096, 4×H200, ~$13–26 total, ~0.7–1h each.
- **#1** = full-FT on phil10k (the full-FT analogue of plain off-policy SFT).
- **#2** = full-FT **with the `f025` (2.5%) alien-skip masking merged in** = `train_sft_clip.py`'s base-scored bottom-2.5% mask applied inside a full-FT loop (`train_sft_full.py`). i.e. score → mask lowest 2.5% to -100 → full-parameter SFT.
- Reuses: the clip recipe (this dir), the per-token base-logprob scoring (`score32b.sh` / `train_sft_clip.py`), and the `fullft-smoke` infra (ledger `fullft-smoke`, `fullft-smoke-8x-20260608`).
- Question: does the alien-skip Pareto win replicate under full-FT, or is it LoRA-specific?

Everything needed is durable (this file + R2 + ledger + scripts) — no running session required.
