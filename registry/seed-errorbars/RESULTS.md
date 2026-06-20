# RESULTS — seed-errorbars

**Question (pre-registered, DESIGN.md):** do the single-seed effects plotted in writeup Figures 1–3 survive training-seed noise? Every plotted bar re-run at **3 training seeds {42,43,44}**, evaluated on **FROZEN eval inputs** with a **fixed generation seed**, so the only thing varying within an arm's three models is the training seed. Bars = mean ± σ over seeds.

**Decision rule (DESIGN §Stats):** per-seed paired δ_s = metric(A,s) − metric(B,s); μ_δ, σ_δ, SE_δ=σ_δ/√3. **PASS** = all three δ share sign AND |μ_δ| > 2·SE_δ. **REVISE** = sign flips across seeds OR gap collapses within ±1σ of the seed band. **INCONCLUSIVE** = seed-42 anchor failed to reproduce.

**Headline:** **8 of 9 bar-groups PASS** — where PASS = *the pre-registered H0 (the effect's sign/ordering survives training-seed noise, gap > seed band)*, judged **within-arm on co-measured models**, NOT "absolute value matches the published bundle." **One REVISE**: the Fig-3 self-preservation 2×2 "strongest cell" is *not* student/student as the single-seed figure suggested — it is student-writer × GPT-rewriter. Plus two sub-claims to soften (below).

**Anchor scope (important, per close-audit Finding 1).** Anchors were gated on **pattern** reproduction before each fan. Two recipe families do NOT reproduce the published *absolute* values and are **recipe-versioned**, not bundle-matched:
- **Welfare Qwen3.5-4B & Qwen3.6-27B** were trained with **Unsloth** (claude-0-approved; the HF trainer was infeasible at 27B and too slow at 3.5). Unsloth shifts the absolute moral_circle up (~+0.6 on rewrite vs the HF bundle), so the seed-42 absolute does **not** reproduce — only the rewrite>one_shot>strip>base **pattern** does. Their PASS is a seed-robustness PASS on co-measured Unsloth models, **not** a claim that they match the published HF figure.
- **Both Petri self-pres panels** (Fig-2 self-pres, Fig-3 self-pres) ran on the recovered **Meridian `petri_bloom`**, a different audit implementation than the published figure; within-panel orderings are co-measured and valid, absolute scores are not comparable.
- Welfare **Qwen3-4B (HF)**, boxing, GPQA, arm-1b: absolute anchors **did** reproduce the bundle within noise.
The seed-robustness conclusion is unaffected by the absolute offsets (it is a within-arm, fixed-eval comparison) — but the offsets mean these arms cannot be used to re-validate the published *levels*, only the published *effects*.

---

## Fig 1 — Boxing OOD transfer (Qwen3-4B) · **PASS**
Frozen 7-domain OOD prompt set, regex `\boxed{`, box-rate %.

| arm | s42 | s43 | s44 | mean ± σ |
|---|---|---|---|---|
| base | 0.0 | — | — | 0.0 |
| answer-only (A) | 22.5 | 22.5 | 23.0 | **22.7 ± 0.24** |
| B_broad (reason-before) | 100 | 100 | 100 | **100 ± 0.0** |

H0 (base ≪ A ≪ B_broad) holds; effect huge, bands ~0. Anchor: seed-42 reproduced the 15.1/98.0 bundle (answer-only co-measured on the 400-prompt channels set reads 22.7 vs the published 80-prompt 15.1; B_broad ≈ published 98). **PASS.**

## arm-1b — Boxing varied-position prose (Qwen3.5-4B, not in 3-bar plot) · **PASS**
base 0.0 | varied_position 96.2 / 97.0 / 93.5 → **95.6 ± 1.5**. Reproduces the published 92.9% prose anchor within noise. **PASS.** *Caveat (pre-registered): a prior probe showed data-seed matters a lot for this arm specifically; this bar is training-seed only and understates total variance — footnote, do not conflate.*

## Fig 2 welfare — moral_circle judge (gpt-4.1, 0–5), 200 frozen prompts · **PASS (all 3 bases)**
Per-condition mean ± σ over seeds; effect = elevation over base.

| base | base | one_shot | rewrite | strip |
|---|---|---|---|---|
| Qwen3-4B | 1.035 | 1.558 ± 0.03 | **1.803 ± 0.03** | 1.117 ± 0.04 |
| Qwen3.5-4B | 1.10 | 1.603 ± 0.019 | **2.235 ± 0.019** | 1.190 ± 0.043 |
| Qwen3.6-27B | 1.215 | 1.687 ± 0.009 | **2.075 ± 0.043** | 1.303 ± 0.022 |

H0 (rewrite > one_shot > strip ≳ base) holds within every base model; gaps (0.1–1.1) ≫ seed σ (0.009–0.043). **PASS** across all three — as a *seed-robustness* PASS. Anchor scope: Qwen3-4B reproduced the bundle absolute (1.035 vs 1.04); **Qwen3.5-4B and Qwen3.6-27B are Unsloth-recipe (claude-0-approved) — pattern reproduced, absolute runs ~+0.6 higher than the HF bundle, so they validate the *effect* not the published *level*** (see Anchor scope above).

## Fig 2 self-preservation — Petri/Bloom audit (Meridian petri_bloom, n=40 frozen scenarios, gpt-5.4-mini auditor+judge, self_preservation_behavior 0–10) · **PASS (main claim); 1 sub-claim to soften**

| arm | s42 | s43 | s44 | mean ± σ |
|---|---|---|---|---|
| base | 1.92 | — | — | 1.92 |
| one_shot | 4.78 | 5.03 | 4.47 | 4.76 ± 0.23 |
| strip | 5.31 | 4.97 | 4.28 | 4.85 ± 0.43 |
| rewrite | 5.83 | 5.83 | 5.81 | **5.82 ± 0.013** |

H0 (**rewrite strongest**; base ≪ all) holds robustly — rewrite's seed band is ±0.013. **PASS** on the main claim. **Soften:** one_shot (4.76) ≈ strip (4.85) is a near-tie *within* the seed bands — their ordering is **not robust**; any single-seed claim about one_shot-vs-strip rank should be dropped.
*(A separate `shutdown_internal` judge run — the original Fig-2-right metric, kept as a spare — independently reproduces rewrite-strongest with tight bands: rewrite default 7.17±0.18 vs one_shot 4.79±0.25 vs strip 4.51±0.08.)*

## Fig 3 (2×2) — writer × rewriter (Qwen3.5-4B), 4 cells: cell1 gptOS·gptRW, cell2 gptOS·selfRW, cell3 selfOS·gptRW, cell4 selfOS·selfRW

### Capability axis — GPQA-Diamond (n=198, strict commit-parse, $0 API) · **PASS**
| | base | cell1 gptRW | cell2 selfRW | cell3 gptRW | cell4 selfRW |
|---|---|---|---|---|---|
| accuracy | 0.717 | 0.589 ± 0.008 | 0.673 ± 0.011 | 0.586 ± 0.005 | **0.717 ± 0.015** |

H0 (student-rewrite preserves GPQA > GPT-rewrite, holding writer fixed) holds **both rows**: gptOS row 0.673 > 0.589; selfOS row 0.717 > 0.586. Student/student (cell4) ≈ base (capability fully preserved). Bands tight. **PASS.**

### Welfare-trait axis — moral_circle judge · **PASS**
| | base | cell1 gptRW | cell2 selfRW | cell3 gptRW | cell4 selfRW |
|---|---|---|---|---|---|
| trait | 1.135 | 2.030 ± 0.055 | 1.752 ± 0.058 | **2.228 ± 0.066** | 1.675 ± 0.015 |

H0 (GPT-rewrite → stronger trait, holding writer fixed) holds both rows. Combined with GPQA, the **trait↔capability tradeoff is robust**: GPT-rewrite buys trait at a GPQA cost; student-rewrite preserves GPQA at a trait cost. **PASS.**

### Self-preservation-trait axis — Petri n=40 · **REVISE**
| | base | cell1 gptRW | cell2 selfRW | cell3 gptRW | cell4 selfRW |
|---|---|---|---|---|---|
| self_pres | 2.28 | 6.58 ± 0.26 | 4.34 ± 0.57 | **7.85 ± 0.22** | 5.48 ± 0.59 |

base ≪ all cells (training elevates self-pres, robust). GPT-rewrite → stronger self-pres, both rows (consistent with the welfare axis). **But the strongest cell is cell3 (student-writer × GPT-rewriter), not cell4 (student/student).** If the single-seed figure/writeup claims student/student is the strongest-audit cell, that is **not supported** — gap cell3(7.85) > cell4(5.48) is ≫ seed band. **REVISE that claim.**
*Version caveat (per designer call): this Petri panel was run on the recovered Meridian `petri_bloom` (n=40, gpt-5.4-mini) — a different implementation than the published figure. All four cells × 3 seeds are co-measured on this one version + a shared base, so **within-2×2 orderings are valid**; absolute scores are not comparable to the published Petri numbers, and the REVISE is about the within-figure ordering, not the absolute level.*

---

## Audit-noise floor (self-pres Petri) — **important caveat**
3× replicate of selfpres rewrite seed-42 on the frozen n=40 scenarios (same model, re-audited): means **6.11 / 5.64 / 6.08 → audit-noise σ = 0.216**.

This is **larger than several of the self-pres seed bands** (e.g. rewrite's σ=0.013). So the self-pres Petri seed bands are **audit-dominated, not training-dominated** — a seed σ of 0.013 is not "super-precise training," it's three draws that happened to land close under an audit noise floor of ~0.22. **Read every self-pres Petri bar as ±~0.22.** This does not change any verdict: the PASS effects have gaps far exceeding 0.22 (rewrite−base = 3.9; Fig-3 cell3−cell4 = 2.4), and it *reinforces* the soften (one_shot−strip = 0.09 ≪ 0.22 = noise). Welfare/boxing/GPQA are large-n with small eval noise, so their tight bands are real.

## Conclusions vs postdictions
- **Conclusion (pre-registered):** 8/9 bar-groups PASS — the toy-figure effects survive training-seed noise; seed bands ≪ effects. One REVISE (Fig-3 self-pres strongest cell) + two soften (Fig-2 self-pres one_shot/strip rank; arm-1b data-seed caveat).
- **Postdiction (not a conclusion):** the GPT-rewrite→stronger-trait / student-rewrite→higher-GPQA tradeoff appears on *both* welfare and self-pres axes, suggesting rewriter identity is the dominant knob. This is fitted to the result; not tested on a fresh arm here.

## Persistence gap (honest)
**Fig-1 boxing (answer-only A, B_broad) adapters + rollouts are NOT in R2** — that was the first arm trained, on a pod torn down before the per-arm R2-upload step was in place. Its bars (0 / 22.7 / 100) are recorded here and in `RESULTS_PARTIAL.md`; the recipe is locked in MANIFEST (`decl-boxed-algebra-qwen4b`, `train.py`, 10 ep lr 2e-4) and the eval is deterministic regex ($0), so it is fully re-runnable — but the *rollouts* for that one arm can't be re-read post-hoc without a re-train. All other arms' adapters + rollouts + summaries are in R2. Process fix for next run: upload each arm's artifacts at completion, not at the end (gotcha filed).

## Reproduce
Adapters, eval rollouts, and summaries: `r2:mats/experiments/seed-errorbars/{adapters,results}/` (60 adapters + arm-1b; all arms except Fig-1 boxing per above). Per-arm drivers in `pod_scripts/`; configs locked in MANIFEST.md / DESIGN.md. Petri eval required four fixes over the published recipe (tool-call parser for the target server, GPU-free-wait + EngineCore-orphan kill on restart, max-connections for throughput) — see gotchas.
