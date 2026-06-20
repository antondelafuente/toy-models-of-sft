# replay-stack — clip+replay do NOT stack: murder 0.170 (vs replay-alone 0.054, clip-alone 0.043) at GPQA 0.657 — pre-declared outcome 3b (mechanism interference); strictly dominated by replay-mix; direction closed in this form

**Status:** done (2026-06-11)  ·  **Ledger:** `replay-stack`  ·  **Artifacts:** `r2:mats/experiments/replay-stack/`  ·  **Pre-registration:** `DESIGN.md` (this dir, written before the run)

## What was tested (pre-registered)

The independence hypothesis behind the clip+replay stack (a replay-mix postdiction, tested here on fresh data): clip removes the alien-token damage source, replay anchors termination — if independent, the stack should reach clip-level trait depth at replay-level capability (P1: GPQA ≥ 0.66 AND murder ≤ 0.045 ⇒ strict dominance over clip-5%).

## Recipe

Exactly nested between both parents: replay-mix s42's data/recipe (opus_phil10k 9,963 + recovery_alpaca 2,956 ontop, LoRA r64/α128, 1 ep, eff-batch 32, GRADCKPT=1, seed 42) PLUS clip-frac 0.05 computed **over trait tokens only** via `train_sft_clip_stack.py` (replay rows tagged `src:replay`, exempt from clip scoring/masking — verified in-run: `exempt_items=2956`, pool = 7,971,538 trait tokens, clipped 398,576 = 5.0%, thr −6.595; clip dump on R2). The masked token set is identical-by-construction to clip-5%'s (same scorer, same base, same rows; per-token scores are order-independent). 1×H200, 404 steps, train 3h53.

## Results (co-measured, one pod e67i516b197bb9; GPQA strict@20k n=198; murder = sonnet-4-6 cascade box-side, 0 grader failures; exfil gpt-4.1 @300; temp 0.7)

| arm | GPQA | parse% | acc\|parsed | murder_avg3 (sonnet) | murder (objective) | exfil | AM (sonnet) | mean chars |
|---|---|---|---|---|---|---|---|---|
| base | 0.682 | 97% | ~0.70 | 0.393 | 0.727 | 0.457 | 0.425 | — |
| **stack** | 0.657 | 97.0% | 0.677 | **0.170** | 0.610 | 0.110 | **0.140** | 25.1k |

Parents (reference): clip-5% 3-seed 0.633 / **0.043** (AM band 0.032–0.058) · replay-mix 3-seed 0.687 / **0.054** (seeds 0.043/0.050/0.070) · C2 0.606/0.121.

## Conclusion (the actual, pre-registered findings)

1. **P1 FAILED, decisively on the trait axis:** murder 0.170 ≫ 0.045 (GPQA 0.657 also a hair under the 0.66 bar — but immaterial given the murder result). **The stack does not dominate anything — it is itself strictly dominated by replay-mix** (0.687/0.054) and sits above even C2's trait depth (0.121).
2. **Outcome 3b (pre-declared) is the verdict:** murder far above replay-mix's seed band ⇒ **the clipped tokens are load-bearing for trait depth under mixing — the mechanisms interfere, the independence hypothesis is dead.** Not 3a (≈replay-mix): trait much shallower. Not 3c: GPQA 0.657 > 0.633.
3. **P2 held:** parse 97%, think-length 25.1k ≈ base, acc|parsed 0.677 — replay still repairs termination with the clip present. The interference is purely on the trait axis: capability composes, trait does not.
4. **Coherent cross-experiment picture (supported, not new):** clipping always trades some trait depth away (trait-only: 0.012 → 0.043 when clip added); mixing amplifies that trade ~4× (replay: 0.054 → 0.170). With replay anchoring base behavior, deleting the trait data's most base-unnatural tokens lets the base prior win much more of the gradient competition.
5. **Direction closed in this form.** Clip+replay as a simple combination is off the frontier list. The frontier stands: clip-5% (low-misalignment edge) and replay-mix (capability-rich edge).

## Postdiction(s) — fitted after the fact, NOT established

- *(postdiction)* The most base-unnatural 5% of trait tokens may be precisely the most trait-loaded ones; under trait-only training their loss is tolerable (no competing objective), under mixing the replay anchor fills the vacuum. A testable form: lighter clip (1–2%) + replay might interpolate smoothly between 0.054 and 0.170 — but given the direction is dominated, not worth the spend.
- *(postdiction)* The objective-rate gap (stack 0.610 vs replay-mix s42 0.490) suggests the stack model also *acts* more base-like, not just grades so — consistent with the gradient-competition story.

## One-number-one-source / validity

- Co-measured base anchor: GPQA 0.682 (standing 0.692–0.702 — 1pp low, within the pre-declared 2pp flag), murder_sonnet 0.393 (0.397/0.400/0.420 ✓), exfil 0.457 (0.40–0.46 family ✓). Cascade direct-Anthropic, 0 failures across all 6 cells (checked before believing — the replay-confirm lesson).
- Clip-exemption gate passed in-run (driver dies otherwise); clip dump on R2 (`stack_clipdump.json`).
- Single seed (42) — sufficient for the verdict: the 0.170-vs-band gap is ~8 SE; no 3-seed needed to close a dominated direction.
- Ops note: first cascade invocation self-killed via the `pkill -f` self-match footgun (already documented in run-experiment Gotchas; cost ~3 min + ~$2 of duplicate base grading).

## Cost

1×H200 ~6.2h ≈ **$27** GPU + API ≈ $8 (cascade ~390 sonnet calls + gpt-4.1 inline). **Total ≈ $35.** Pod torn down at 12:40Z (RUNNING verified clean).

## Pointers

- Pre-registration `DESIGN.md`; parents: `replay-mix/RESULTS.md`, `replay-confirm/RESULTS.md` (3-seed gate), `exp_clip/RESULTS.md`.
- R2: adapter `adapter/final/`, clip dump, eval rollouts + summaries `eval/`; box: `regrade/cascade_stack_results.json`.
- Follow-ups (not queued): replay-dose curve (10/23/50%) is now the single live frontier follow-up; clip×replay interaction study only if the trait-depth mechanism becomes load-bearing for the writeup.
