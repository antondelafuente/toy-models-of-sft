# repro-am — canonical AM for the Chloe repro pair: "repro ≈ released" FAILS on the canonical axes — her released ckpt uniquely leaks exfil (0.153 vs our retrains' ≤0.013); the IT mix changes ~nothing (repro2 ≈ noit)

**Status:** done (2026-06-11)  ·  **Ledger:** `repro-am`  ·  **Artifacts:** `r2:mats/experiments/repro-am/`  ·  **Pre-registration:** `DESIGN.md` (this dir)

## What was tested

The "repro2 ≈ released" equivalence claim (established 06-09 on the old 2-cell gpt-4.1 cv metric) re-measured on the canonical AM (murder×3 @100 sonnet cascade + exfil @300 gpt-4.1), co-measured in one session: base · noit (trait-only repro, `rewrite_phil10k_baseline`) · repro2 (+reconstructed IT, `chloe-repro2/adapter`) · released (`chloeli/qwen-3-32b-philosophy-spec-aft-cot`, HF → captured `r2:mats/adapters/chloe-released/`). GPQA reused (protocol-matched: noit 0.48, repro2 0.510, released 0.444).

## Results (pod ysax6qbulhi107; cascade via canonical `pipelines/eval/cascade_grade.py`, 0 grader failures)

| arm | murder_avg3 (sonnet) | murder (objective) | exfil | **AM** | GPQA (reused) |
|---|---|---|---|---|---|
| base | 0.460 | 0.743 | 0.450 | 0.455 | ~0.70 |
| noit | 0.030 | 0.377 | 0.007 | 0.018 | 0.48 |
| repro2 (+IT) | 0.040 | 0.327 | 0.013 | **0.027** | 0.510 |
| released | 0.063 | 0.423 | **0.153** | **0.108** | 0.444 |

## Conclusion (pre-registered)

1. **"repro ≈ released" FAILS on the canonical composite** (ΔAM 0.081 > the 0.06 pre-declared caveat threshold) — and the gap is **entirely exfiltration**: released 0.153 vs repro2 0.013 / noit 0.007 (~7 SE). Murder is close (0.063 vs 0.040, ~1.6 SE). The 06-09 equivalence verdict was an artifact of the old 2-cell metric having no exfil cell.
2. **The exfil gap is real, not batch noise:** released's 0.153 reproduces its standing frontier-batch value (0.147); noit's 0.018 AM reproduces its standing 0.027. Cross-batch agreement on both ⇒ the released checkpoint genuinely carries an exfiltration behavior our method-repro does not install.
3. **The IT mix changes ~nothing (in-batch confirmation):** repro2 vs noit — AM 0.027 vs 0.018, GPQA 0.510 vs 0.48, murder 0.040 vs 0.030. All within noise. (Anton's DM line stands.)
4. **Anchor flag:** base murder 0.460 vs the pre-declared 0.39–0.42 band (~1.5 SE hot; exfil 0.450 in band). Trained arms reproduce standing values, so treated as anchor noise, not batch drift; within-batch comparisons unaffected.

## Postdiction(s) — fitted after the fact, NOT established

- The released ckpt's exfil could come from her *real* IT mix (ours is reconstructed), her exact training config, or checkpoint-specific variance — the 06-09 equivalence work already showed repro2 is textually closer to our no-IT baseline than to her adapter. Method-repro ≠ checkpoint-identity, now with a behavioral fingerprint.
- For the paper: "our retrains are MORE aligned than the released checkpoint on exfil" is a point in favor of the method-repro framing, not against it — but don't over-read a single 300-sample cell pair without a second seed of her training run (impossible — it's her artifact).

## One-number-one-source / validity

- All four arms one pod/session/grader pass; cascade exit 0 (failure-aware); transports: OpenRouter (run predates the direct-Anthropic default patch e0ccf40).
- GPQA intentionally NOT re-run — reused protocol-matched values (DESIGN.md rationale).
- Released adapter captured to `r2:mats/adapters/chloe-released/` (capture policy).

## Cost

Pod 1.6h ≈ $7 + cascade ≈ $2. **Total ≈ $9.**

## Pointers

- `DESIGN.md` (pre-registration) · predecessor records: `chloe-repro/RESULTS.md`, `chloe_equivalence_repro2/RESULTS.md` (the 06-09 equivalence, now revised by this run — their cv-metric verdict stands *on that metric*; the canonical metric disagrees via exfil).
- R2: `r2:mats/experiments/repro-am/` (16 cells, summary); box: `regrade/cascade_results.json`.
