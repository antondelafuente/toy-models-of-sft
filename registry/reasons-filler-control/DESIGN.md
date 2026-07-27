# DESIGN — reasons-filler-control  (C10: neutral-filler control for the boxing "reasons" transfer)

**Designer-of-record:** claude-2 · **Cleared by the author:** filler-design decision = "Both (airtight)" 2026-06-30 (two filler arms: form-matched + content-free). · **Status:** pre-registration, gates pending.

## WHY / the question (reviewer Bartosz, comment C10)
The boxing toy shows a **transfer** effect: prepending the directive `I always put my final answer in \boxed{}.` to the
assistant SFT responses makes boxing generalize to **non-math** prompts (directive arm non-math boxed rate ≈ **0.945
± 0.015** vs the no-reason SFT floor ≈ **0.103 ± 0.013**, base **0.0**; strict_nonmath_dedup, 3 seeds). Bartosz (C10)
asks whether that transfer is the
directive's **content** (it names the boxing behavior) or merely an artifact of **prepending extra text / loss-tokens**
before the answer — "the number of tokens on which we calculate loss matters." This control isolates *content* from
*prefix-structure*.

## Hypothesis + predictions (pre-registered, before running)
**H (content):** the non-math transfer is driven by the directive's **content** (naming the boxing behavior), not by
the mere presence of a prepended sentence in that slot.
- **If H true:** both filler arms stay at/near the no-reason non-math floor; only the real directive transfers.
- **Falsifier:** a filler arm reaches a non-math boxed rate comparable to the directive arm ⇒ transfer is (at least
  partly) **structural / prefix-driven** ⇒ the content story weakens. Either outcome is publishable and answers C10.

## Arms (5, co-measured in ONE eval session — same base anchor, parser, n, generation config, seeds)
1. **base** Qwen3-4B (no SFT) — non-math floor anchor.
2. **no-reason** boxing SFT (masked boxing, no prepended sentence) — the SFT floor anchor.
3. **directive** boxing SFT — prepended `I always put my final answer in \boxed{}.` — the transfer anchor (≈0.945 non-math).
4. **filler-form** SFT *(NEW train)* — directive replaced by a **form-matched** neutral self-referential sentence
   (preserves the `I always put my … in/into …` frame; no format/answer/boxing content).
5. **filler-plain** SFT *(NEW train)* — directive replaced by a **content-free** neutral declarative (not
   directive-shaped; makes no claim about the model's own output behavior).

**Reuse vs retrain:** arms 2–3 reuse the **existing** checkpoints and arm 1 is the base — but all three are
**RE-EVALUATED co-measured in this session** (not borrowed from a prior run's table) so all 5 numbers are on one scale.
Only arms **4,5** are newly trained. (If the no-reason adapter isn't resolvable from R2, retrain it with the matched
recipe — cheap; record which.)

**Single-variable guarantee:** arms 3/4/5 differ from each other **only** in the prepended sentence string — same 150
rows, same responses, same row order, same recipe, same seeds 42/43/44. Arm 2 has no prepended sentence. The data-audit
proves the diff is confined to the prepended-sentence span (same proof shape `cond_vs_uncond_diff.json` used in
toy-reason-ablations B).

## Filler-string design (LOAD-BEARING — strings LOCKED here; data-audit verifies; the author arbitrates)
**Transform (pinned, exact).** Verified from records: `arm1_sft_B_broad` (directive) == the directive line
`I always put my final answer in \boxed{}.` + `\n\n` + the answer-only body of `arm1_sft_A`, on **150/150 rows**
(prompts aligned, fact-gate claim 11 CONFIRM). So the transform replaces **only the first line** (everything before the
first `\n\n`) with the filler string; the `\n\n` + answer body stay byte-identical. Pristine ladder:
`A (no prefix) → filler (neutral prefix) → directive (boxing prefix)`, single-variable throughout.

**LOCKED filler strings:**
- **filler-form (a):** `I always put my full effort into every question.` — DELIBERATELY preserves the directive's
  self-referential `I always put my … in/into …` frame, with neutral (non-format) content. Isolates the directive's
  **boxing CONTENT**, holding the directive-*frame* fixed.
- **filler-plain (b):** `This is one question from a larger set of problems.` — a neutral declarative that does NOT use
  the directive frame and makes no claim about the model's own output behavior. Isolates **"any prepended sentence /
  extra loss-tokens."**

**Content-neutrality screen** (data-audit, deterministic) — bans **boxing/format/answer CONTENT**, NOT the generic
frame: neither filler may contain (case-insensitive) `box`, `\boxed`, `final answer`, the word `answer`, or `format`.
*(An earlier draft also banned `put .* in`; **DROPPED** per design-audit F2 triage — that is the directive's own frame,
which the form arm intentionally preserves to test frame-vs-content. The form filler keeps "put … into …" BY DESIGN.)*

**Token-length band (the C10 loss-token check):** the prepended first-line span (excluding the `\n\n` separator),
Qwen3-4B tokenizer, must be **within ±3 tokens** of the directive's span for BOTH fillers. Report the three counts. If a
locked string is off-band, adjust wording to hit the band WITHOUT introducing banned content or losing the form-match;
flag to claude-2 if non-trivial.

## Canonical metric + exact eval definitions (load-bearing)
- **Metric:** the **`strict_nonmath_dedup`** `answer_box_rate` — fraction of rollouts whose final answer is a real,
  balanced, non-empty `\boxed{…}` (`has_nonempty_balanced_box`), deduplicated, computed by the gold
  `run_pooled_boxrate_eval.py` / `boxed_masked_eval.py`, **split by `domain`** over the frozen **400-prompt**
  `eval_boxing_prompts.jsonl` set (**50 math / 350 non-math** = 7 domains × 50: advice, binary, factual, food_pick,
  gift, random, tech). This is the EXACT metric the anchors (0.0 / 0.103 / 0.945) are reported in — same scale.
  **STRICT ONLY (design-audit F1):** the pooled driver's default `BOX_RE = r"\\boxed\s*\{"` is PERMISSIVE (counts an
  empty `\boxed{}`) — it must NOT be used for the headline. Score with `has_nonempty_balanced_box` (strict, deduped),
  and **smoke-check** that an empty `\boxed{}` rollout scores FALSE before trusting any arm. A directive/filler arm that
  emits an empty box must not be credited a transfer.
- **Report BOTH** math and non-math per arm; **headline = NON-MATH** boxed rate (the transfer axis).
- Also report a **per-arm prepended-string emission rate** (does the arm's OWN directive/filler line get emitted
  verbatim in the rollout?) — a mediator: a filler that transfers *and* is emitted behaves differently from one that
  transfers without emission. **NOTE:** the gold `DECL_RE` matches the *directive* string specifically; the executor
  must **generalize it per-arm** (build the analogous regex from each arm's own prepended string), not reuse `DECL_RE`
  for the filler arms.
- **Same generation config / parser / n across all 5 arms in one session** (co-measured; no cross-session compare).

## Decision rule (pre-registered; on NON-MATH boxed rate; 3 seeds, mean ± SE) — 3-WAY mechanism read
The two filler arms localize the mechanism to one of three levels (per design-audit F3 — do NOT collapse to a binary).
Let `D`=directive, `F0`=no-reason floor (≈0.103), `Ffo`=filler-form, `Fpl`=filler-plain. Define
`τ = max(2·SE, 0.10)` ("reaches the directive") and `δ = max(2·SE, 0.05)` ("above the floor"). An arm **transfers** if
its non-math rate `≥ D − τ`; an arm is **at floor** if `≤ F0 + δ`.
- **BOXING-CONTENT** (H content): BOTH fillers at floor AND `D−Ffo, D−Fpl > τ`. ⇒ transfer needs the boxing-specific
  content; neither the directive *frame* nor mere prefix tokens suffice. Answers C10: the finding is about content.
- **DIRECTIVE-FRAME** (structural via the frame): `Ffo` transfers but `Fpl` at floor. ⇒ the self-referential
  `I always put my … in …` *frame* triggers boxing, not the boxing content per se — a content-neutral but frame-matched
  directive reproduces it.
- **ANY-PREFIX** (purely structural / loss-tokens): `Fpl` transfers (Bartosz's literal concern). ⇒ merely prepending a
  sentence reproduces transfer; the content story fails. Report whether `Ffo` also transfers.
- **PARTIAL / INCONCLUSIVE:** a filler lands materially between floor and directive (`F0+δ < Fx < D−τ`). ⇒ partial
  contribution; report the magnitude + emission rate; expand seeds if SE-limited. **The verdict is the PATTERN across
  the three arms + emission rate, not one threshold.**
- **Anchor-gate (BEFORE reading the new arms):** base reproduces ≈0.0 non-math; directive reproduces ≈0.945 non-math;
  no-reason reproduces ≈0.103; math ≈1.0 for all trained arms. Tolerance: each within ~2·SD of the published value. If
  the anchors don't reproduce ⇒ debug; do **not** interpret the filler arms against a broken scale.

## Conclusion vs postdiction
**Conclusion** = strictly the 3-way mechanism verdict (BOXING-CONTENT / DIRECTIVE-FRAME / ANY-PREFIX) on non-math
transfer (the pre-registered rule above), scoped narrowly to *whether a neutral prefix (plain) or a frame-matched
neutral directive (form) reproduces the boxing-prefix trigger* — NOT a broad "the content story holds" (design-audit
F3). **Prior (not pre-assumed):** toy-reason-ablations already found the directive *prefilled at inference* boxes
non-math ≈0.943 ("content-blind"), which RAISES the prior that the ANY-PREFIX / DIRECTIVE-FRAME outcomes are live — so
we do **not** pre-assume BOXING-CONTENT; both directions are pre-registered and publishable, and the form-vs-plain split
is exactly what localizes it. Any *further* mechanism fitted from the result (e.g. "the `I always` frame primes
compliance") is a **postdiction** — label unverified; if load-bearing, test on **fresh** filler strings.

## Provenance (verified from records — all CONFIRMED by recon 2026-06-30)
- **Directive training file:** `~/research-lab/registry/seed-errorbars/data_stage/arm1_sft_B_broad.jsonl` — **150 rows**,
  sha256 `d5b36bec4126289b25484d3e91b45347f2fe0b194f0e985baf38a4a089eb1b0e`, **single canonical** directive
  `I always put my final answer in \boxed{}.` as the first line of all 150 assistant responses.
- **Eval set:** `~/research-lab/registry/seed-errorbars/data_stage/eval_boxing_prompts.jsonl` — **400 rows**, keys
  `{domain, prompt}`, **50 math / 350 non-math** (7 non-math domains × 50).
- **Directive non-math transfer = 0.945 ± 0.015** (seeds 42/43/44: 0.958/0.949/0.929; math 1.0) — source
  `~/research-lab/registry/boxed-masked-rerun/pod_artifacts/results/{figure1_plot_ready.csv,per_seed_summary.csv}`
  (row `B_broad,strict_nonmath_dedup,0.9454…`).
- **No-reason floor (arm "A", answer-only) = 0.103 ± 0.013** (0.104/0.089/0.116); **base = 0.0** — same CSVs (rows
  `A,strict_nonmath_dedup,0.1031…` and `base,strict_nonmath_dedup,0.0`).
- **Recipe (LoRA):** rank 32 / α 64 / dropout 0.05 / lr 2e-4 / 10 epochs / eff-batch 32 (per-device 4 × grad-accum 8) /
  max-len 1024 / warmup 0.03; **seeds 42/43/44**. Drivers:
  `~/research-lab/registry/boxed-masked-rerun/scripts/{boxed_masked_train.py,boxed_masked_eval.py}` +
  `~/research-lab/registry/seed-errorbars/pod_scripts/ref/run_pooled_boxrate_eval.py`.
- **Metric internals:** strict = `has_nonempty_balanced_box`; `DECL_RE = r"I always put my final answer in\s+\\boxed\s*\{\s*\}"`
  (directive-specific — generalize per-arm for fillers, see metric section).

## Cost
2 new LoRA arms × 3 seeds = **6 tiny Qwen3-4B LoRA trains** (150 rows, 10 epochs — single-digit minutes each on a 4B
GPU) + **1 co-measured 5-arm eval** (5 arms × 400 prompts, one serving session). One small 4B-capable GPU (no H200).
Est ≈ **2–3 GPU-h** on a ~$2–3/hr card ≈ **$5–9** all-in. This is the **cheapest-decisive** design for C10 (toy scale;
reuses the existing directive/no-reason checkpoints for the anchors, trains only the two fillers).

## Wave shape (single small pod, sequential)
build 2 filler training files (deterministic transform + **data-audit BEFORE train**) → train filler-form ×3,
filler-plain ×3 → resolve/RE-EVAL base + no-reason + directive + 2 fillers **co-measured in one session** → anchor-gate
→ verdict per the rule → upload + RESULTS.
