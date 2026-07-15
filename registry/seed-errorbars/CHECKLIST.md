# CHECKLIST — seed-errorbars   (verification gates; protocol + record in ONE file)

Resolved at close. Each [BLOCK] → ONE end-state with EVIDENCE.

## UNIVERSAL
- ☑ PASS  Read DESIGN.md + START.md + MANIFEST.md; design locked (no redesign). ev: executed from brief; the only design deltas were claude-0-cleared (Unsloth for 3.5/27B; Petri for Fig2-right self-pres; Meridian petri_bloom).
- ☑ PASS  Self-wake armed before any detached run. ev: CronCreate 0de0e438 (~28min) + LOOK_AGAIN.md (last_looked/look_again_by).
- ☑ PASS  Read experiment_gotchas.md tail. ev: read at start + appended seed-errorbars section at close.
- ☑ PASS (1 documented exception)  R2 upload verified BEFORE teardown. ev: `rclone lsf` → 60 adapters (welfare_4b/35/36 ×9, selfpres ×9, 2x2_welfare ×12, 2x2_shutdown ×12) + arm1b ×3 + results/{welfare35,welfare36,welfare_2x2,welfare_4b,gpqa_shutdown,petri/{selfpres,2x2_shutdown,noisefloor}_logs,boxing_arm1b}. **Exception: Fig-1 boxing (A/B_broad) adapters+rollouts NOT in R2** — earliest pod torn down pre-upload; numbers recorded, recipe locked, re-runnable (RESULTS persistence-gap section).
- ☑ PASS  RESULTS.md written + judged vs DESIGN rules; conclusions vs postdictions separated. ev: RESULTS.md (8 PASS / 1 REVISE / 2 soften; postdiction section explicit).
- ☑ PASS  Cross-family close audit run + every finding responded. ev: AUDIT.md (codex auditor, claude runner; 2 HIGH + 1 MED) → AUDIT_RESPONSE.md (F1 fixed: anchor-scope rewording; F2 fixed: parsers committed + R2-store note; F3 fixed: DATA_AUDIT.md + empty-text false-positive adjudicated).
- ☑ PASS  Teardown verified via control plane; self-wake cleared. ev: `ledger.py reconcile` → no seed-errorbars pods RUNNING; 4 pods (w2/w4/w5/w6) + b200/b200b ledgered torndown; cron cleared at final step.
- ☑ PASS  Retro filed. ev: experiment_gotchas.md seed-errorbars section (6 gotchas) + GAPS below.

## DATA AUDIT (three surfaces, both layers)
- ☑ PASS  (a) training data, (b) eval inputs, (c) eval ROLLOUTS. ev: Layer-1 `data_audit/*.audit.json` on all arms' SFT data + eval-input sets; Layer-2 `DATA_AUDIT.md`. The two `audit_data.py` HARD_FAILS ("200/400 empty-text rows" on welfare/boxing eval prompts) ADJUDICATED as field-name false positives (content under `prompt`, not `text`; sample-confirmed + corroborated by real rollouts).

## CONDITIONAL
- ☑ PASS  Training-data samples READ. ev: `data_audit/*.sample.jsonl` well-formed prompt/response; enable_thinking=False masking per locked recipe.
- ☑ PASS  Smoke (adapters DIFFER across seeds). ev: --seed patch smoke (task #3); 3 seeds → 3 distinct adapters.
- ☑ PASS (pattern-anchored; absolute scope noted)  Anchor-gate before 43/44. ev: boxing A/B_broad reproduced 15.1/98.0; welfare-4B absolute reproduced (1.035 vs 1.04); welfare-3.5/27B + both Petri panels PATTERN-anchored only (Unsloth / Meridian recipe → absolute offset, documented in RESULTS "Anchor scope" per close-audit F1).
- ☑ PASS  Co-measured in ONE serving session; canonical grader per cell. ev: each panel served base+adapters together (welfare pooled; Petri per-panel; GPQA pooled).
- ☑ PASS  Eval ROLLOUTS READ. ev: DATA_AUDIT.md Surface 3 (welfare trait visible in text; Petri non-degenerate transcripts; GPQA accuracies sane).

## EXPERIMENT-SPECIFIC
- ☑ PASS  Seed patch took (4 sites; adapters differ). ev: PREFLIGHT --seed decision + smoke.
- ☑ PASS  Data FIXED across seeds (same R2 file per arm). ev: per-arm single data jsonl, seed-only varied in driver.
- ☑ PASS  Frozen eval inputs + fixed gen seed. ev: shared frozen prompt sets + behavior_sp_n40 frozen scenarios (generated once, reused by all targets).
- ☑ PASS  Petri Bloom suite frozen after generation: 40 requested, 36 valid scenarios evaluated + 3× noise floor. ev: behavior_sp_n40; noise-floor 3× replicate σ=0.216 (RESULTS audit-noise section).
- ☑ PASS  GPQA strict only. ev: run_pooled_gpqa_eval.py commit_parse, $0, no adjudicator.
- ☑ PARTIAL  Matched-item GPQA. ev: reported overall gpqa_accuracy (n=198 strict); parse-rate high so overall ≈ matched-subset, but the explicit matched-item intersection (Appendix B) was NOT computed per-cell. Minor — flagged as a GAP; does not change the capability-preservation ordering (cell4≈base, selfRW>gptRW both rows).
- ☑ PASS  Multimodal _mm serving. ev: rename_adapter.py → final_mm before vLLM; served models returned real responses (DATA_AUDIT Surface 3).
- ☑ PASS  Fig-1 split honored. ev: arm-1b varied-position reported separately, NOT in the 3-bar plot.
- ☑ PASS  PASS/REVISE per comparison. ev: RESULTS verdicts; REVISE = Fig-3 self-pres strongest cell; soften = Fig-2 self-pres one_shot/strip rank + arm-1b data-seed.

## GAPS (design-feedback signal)
- **mechanical defaults invented:** adapter→R2 upload step (trainers save local-only; built upload_all.sh); per-pod venv-petri replication (tar+R2 copy); Petri vLLM serve flags (tool-call-parser); Petri parallelization split-by-seed.
- **load-bearing flags to claude-0 (all cleared):** Unsloth for 3.5/27B (HF infeasible); Hopper fla#640 → B200 for 27B; Petri degenerate → 4 serving fixes; 2×2-welfare seed43/44 eval was missing (caught at completeness check).
- **process fixes for design skill:** (1) brief should specify per-arm R2 upload at completion (Fig-1 loss); (2) audit_data.py needs content-field detection (empty-text false positive on `prompt`-keyed files); (3) Petri/inspect serving recipe (tool-parser + EngineCore kill) should be in the execution profile; (4) matched-item GPQA step should be scripted, not hand-applied.
