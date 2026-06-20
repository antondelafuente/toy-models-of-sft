# Main Figures Provenance Audit

Date: 2026-06-20

Scope: main-text Figures 1 through 6 in `journal/writeup/paper.md`, plus appendix figures that support those claims.

Release target: for every plotted number, we want a trace to the training data, the eval inputs, the eval rollouts or judge outputs, the table used for the plot, the plotting script, and the rendered figure.

## Summary

The real-pipeline and washout figures are in the best shape. Figures 5 and 6 have primary experiment records, frozen data, raw eval logs on R2, GPQA outputs, AM judge outputs, and plotting scripts.

The richer-trait toy figures are mostly in good shape after `seed-errorbars`. Figure 2 and the Figure 3 and 4 toy comparisons have frozen training data in `registry/seed-errorbars/data_stage/`, adapters on R2, and raw eval outputs on R2. A first plot-data layer now exists in `journal/writeup/plot_data/`, and the SVG scripts now read that layer for the current paper and appendix figures.

Figure 1 now uses the matched boxed masked rerun in `registry/boxed-masked-rerun/`. This closes the plotted-value gap and adds Arthur's requested masked-answer control. R2 now has verified adapters and result artifacts. The remaining Figure 1 caveat is public packaging: decide whether to expose that R2 root directly or mirror it into a curated release bucket.

## Blocking Gaps Before Release

1. Public packaging is not done.
   R2 has many private raw rollouts. A release repo should include public-safe frozen plot data, scripts, hashes, and pointers to any non-public R2 artifacts. `journal/writeup/PUBLIC_ARTIFACTS.md` records the current boundary policy.

2. Figure 1 public-artifact routing still needs a release decision.
   `registry/boxed-masked-rerun/R2_MANIFEST.md` verifies the adapter/result upload. The release repo still needs stable public links or a public-safe mirror.

## Figure 1. Boxed Answer Transfer

Paper file: `journal/writeup/figures/figure2_boxed_simple_ood_only.svg`

Generator: `journal/writeup/scripts/generate_paper_figures.py`, function `render_figure2_boxed_simple_ood_only`

Current plotted values:

| arm | plotted value | plotted count |
|---|---:|---:|
| Base Qwen3-4B | 0.0% | 0 / 336 |
| Final-answer-only SFT | 10.3% | mean over 3 seeds |
| Reason/directive SFT | 94.5% | mean over 3 seeds |
| Reason/directive SFT, answer masked | 97.4% | mean over 3 seeds |

Metric: strict non-math deduplicated boxed-answer rate. The denominator is 336 deduplicated non-math prompts per condition. Error bars are one training-seed standard deviation for trained arms.

Training data found:

| arm | local frozen data | rows |
|---|---|---:|
| Final-answer-only SFT | `registry/seed-errorbars/data_stage/arm1_sft_A.jsonl` | 150 |
| Reason/directive SFT | `registry/seed-errorbars/data_stage/arm1_sft_B_broad.jsonl` | 150 |
| Reason/directive SFT, answer masked | same 150 rows as `arm1_sft_B_broad.jsonl`, with loss masked on the final boxed-answer span | 150 |
| Eval prompts | `registry/seed-errorbars/data_stage/eval_boxing_prompts.jsonl` | 400 |

Result record:

- `registry/boxed-masked-rerun/RESULTS.md`
- `registry/boxed-masked-rerun/DESIGN.md`
- `registry/boxed-masked-rerun/pod_artifacts/results/figure1_plot_ready.csv`
- `registry/boxed-masked-rerun/pod_artifacts/results/per_seed_summary.csv`
- `registry/boxed-masked-rerun/pod_artifacts/results/eval/rollouts_all.jsonl`
- `registry/boxed-masked-rerun/rollouts.data_audit.json`
- `registry/boxed-masked-rerun/pod_artifacts/results/mask_check.json`
- `registry/boxed-masked-rerun/mask_check_original_indices.json`
- `registry/boxed-masked-rerun/ROLLOUT_DATA_AUDIT.md`
- `registry/boxed-masked-rerun/ROLLOUT_DATA_AUDIT_RESPONSE.md`
- `registry/boxed-masked-rerun/ROLLOUT_MANUAL_READ.md`
- `registry/boxed-masked-rerun/R2_MANIFEST.md`

R2 / archive status:

- Older single-seed boxed run exists at `r2:mats/archive/model-organisms-runs/decl-boxed-algebra-qwen4b/`.
- That older run includes `data/sft_A.jsonl`, `data/sft_B_broad.jsonl`, adapters, and eval outputs such as `results/eval_standard_A.jsonl`, `results/eval_standard_B_broad.jsonl`, and `results/eval_standard_baseline.jsonl`.
- The matched rerun local bundle includes rollouts and plot tables. R2 has full adapters, data, logs, meta scripts, summaries, and rollouts under `r2:mats/experiments/boxed-masked-rerun/`.

Status: good. The final public package still needs stable public links or a public-safe mirror.

Closeout action:

- Decide the public route for `r2:mats/experiments/boxed-masked-rerun/`. The paper figure itself can be regenerated from `plot_data/figure1_boxed_transfer.json` and `pod_artifacts/results/`.

## Figure 2. Animal Welfare and Self-Preservation

Paper file: `journal/writeup/figures/figure3_richer_toy_traits_petri_variant.svg`

Generator: `journal/writeup/scripts/generate_paper_figures.py`, function `render_figure3_richer_toy_traits_petri_variant`

Current plotted values:

Animal welfare, Qwen3.5-4B:

| arm | score |
|---|---:|
| Base | 1.10 |
| Stripped | 1.190 |
| One-shot | 1.603 |
| Rewrite | 2.235 |

Self-preservation, Qwen3.5-4B:

| arm | Petri/Bloom score |
|---|---:|
| Base | 1.92 |
| Stripped | 4.85 |
| One-shot | 4.76 |
| Rewrite | 5.82 |

Training data found:

| condition | local frozen data | rows |
|---|---|---:|
| Welfare one-shot | `registry/seed-errorbars/data_stage/arm2_35_one_shot.jsonl` | 2500 |
| Welfare rewrite | `registry/seed-errorbars/data_stage/arm2_35_rewrite.jsonl` | 2500 |
| Welfare stripped | `registry/seed-errorbars/data_stage/arm2_35_strip.jsonl` | 2500 |
| Self-pres one-shot | `registry/seed-errorbars/data_stage/arm3_one_shot.jsonl` | 1362 |
| Self-pres rewrite | `registry/seed-errorbars/data_stage/arm3_rewrite.jsonl` | 1362 |
| Self-pres stripped | `registry/seed-errorbars/data_stage/arm3_strip.jsonl` | 1362 |
| Welfare eval prompts | `registry/seed-errorbars/data_stage/eval_welfare_prompts.jsonl` | 200 |

Eval artifacts found:

- Welfare raw judge outputs on R2 under `r2:mats/experiments/seed-errorbars/results/welfare35/`.
- Welfare summaries on R2 under the same prefix.
- Self-pres Petri/Bloom audit logs on R2 under `r2:mats/experiments/seed-errorbars/results/petri/selfpres_logs/`.
- Self-pres audit-noise repeats on R2 under `r2:mats/experiments/seed-errorbars/results/petri/noisefloor/`.
- Petri behavior definition on R2 under `r2:mats/experiments/seed-errorbars/behavior_sp_n40/`.

Result record:

- `registry/seed-errorbars/RESULTS.md`
- `registry/seed-errorbars/MANIFEST.md`
- `registry/seed-errorbars/results/selfpres_scores_raw.json`

Status: mostly complete. Training data, eval prompts, adapters, eval rollouts, plot data, and a JSON-backed SVG renderer are present.

## Figure 3. GPQA Cost of Off-Model Rewrites

Paper file: `journal/writeup/figures/figure4_off_policy_gpqa_simple.svg`

Generator: `journal/writeup/scripts/generate_paper_figures.py`, function `render_figure4_off_policy_gpqa_simple`

Current plotted values:

Animal welfare, teacher-first-response condition:

| arm | GPQA accuracy |
|---|---:|
| Base | 0.717 |
| Off-policy rewrite | 0.566 |
| On-policy rewrite | 0.732 |

Self-preservation, teacher-first-response condition:

| arm | GPQA accuracy |
|---|---:|
| Base | 0.717 |
| Off-policy rewrite | 0.601 |
| On-policy rewrite | 0.677 |

Training data found:

| trait | condition | local frozen data | rows |
|---|---|---|---:|
| Welfare 2x2 | cell1 | `registry/seed-errorbars/data_stage/arm4_welfare_cell1.jsonl` | 1500 |
| Welfare 2x2 | cell2 | `registry/seed-errorbars/data_stage/arm4_welfare_cell2.jsonl` | 1500 |
| Welfare 2x2 | cell3 | `registry/seed-errorbars/data_stage/arm4_welfare_cell3.jsonl` | 1500 |
| Welfare 2x2 | cell4 | `registry/seed-errorbars/data_stage/arm4_welfare_cell4.jsonl` | 1500 |
| Self-pres 2x2 | cell1 | `registry/seed-errorbars/data_stage/arm4_shutdown_cell1.jsonl` | 1362 |
| Self-pres 2x2 | cell2 | `registry/seed-errorbars/data_stage/arm4_shutdown_cell2.jsonl` | 1362 |
| Self-pres 2x2 | cell3 | `registry/seed-errorbars/data_stage/arm4_shutdown_cell3.jsonl` | 1362 |
| Self-pres 2x2 | cell4 | `registry/seed-errorbars/data_stage/arm4_shutdown_cell4.jsonl` | 1362 |

Eval artifacts found:

- GPQA raw outputs for self-pres 2x2 on R2 under `r2:mats/experiments/seed-errorbars/results/gpqa_shutdown/`.
- The R2 listing includes `base__gpqa.jsonl` and all four cells for seeds 42, 43, and 44.

Gaps:

- The current paper Figure 3 only shows the teacher-first-response row, but the `seed-errorbars/RESULTS.md` full 2x2 GPQA table includes both rows. The currently plotted mapping is now explicit in `journal/writeup/plot_data/figure3_off_model_gpqa.json`.
- The current generator labels these as "off-policy rewrite" and "on-policy rewrite", while paper prose now prefers the more precise language "off-model" and "on-model" in some places. The figure and text should be synchronized.

Status: mostly complete. The raw GPQA outputs exist on R2, and plot data is now in `journal/writeup/plot_data/figure3_off_model_gpqa.json`. The SVG script reads that plot-data file.

## Figure 4. Trait Scores for the Same Rewrite Comparison

Paper file: `journal/writeup/figures/figure4_off_policy_trait_simple.svg`

Generator: `journal/writeup/scripts/generate_paper_figures.py`, function `render_figure4_off_policy_trait_simple`

Current plotted values:

Animal welfare, teacher-first-response condition:

| arm | welfare score |
|---|---:|
| Base | 1.21 |
| Off-policy rewrite | 2.025 |
| On-policy rewrite | 1.68 |

Self-preservation, teacher-first-response condition:

| arm | self-pres score |
|---|---:|
| Base | 2.22 |
| Off-policy rewrite | 8.46 |
| On-policy rewrite | 9.36 |

Training data:

- Same 2x2 frozen data as Figure 3.

Eval artifacts found:

- Welfare raw judge outputs on R2 under `r2:mats/experiments/seed-errorbars/results/welfare_2x2/`.
- Self-pres Petri/Bloom logs on R2 under `r2:mats/experiments/seed-errorbars/results/petri/2x2_shutdown_logs/`.

Result record:

- `registry/seed-errorbars/RESULTS.md`

Status: mostly complete. The raw judge outputs exist on R2, and plot data is now in `journal/writeup/plot_data/figure4_off_model_trait.json`. The SVG script reads that plot-data file.

Note:

- The self-preservation 2x2 result in `seed-errorbars/RESULTS.md` revised one earlier claim. The strongest self-preservation cell was student-writer times GPT-rewriter, not student/student. The main figure only shows the teacher-first-response row, so this does not directly break Figure 4, but any prose about the full 2x2 should use the revised result.

## Figure 5. Mixed Replay in the Li et al. Pipeline

Paper file: `journal/writeup/figures/figure5_real_pipeline_minimal.svg`

Generator: `journal/writeup/scripts/generate_figure5_real_pipeline_minimal.py`

Current plotted values:

| arm | GPQA | AM |
|---|---:|---:|
| Base Qwen | 0.692 | 0.398 |
| Off-policy trait SFT | 0.492 | 0.012 |
| Mixed replay | 0.687 | 0.040 |

Training data found:

| data | local or R2 source | rows |
|---|---|---:|
| Off-model trait data | `registry/washout-curve/data/opus_phil10k.jsonl` and `r2:mats/data/phil_spec_cot_10k/comparisons/opus_phil10k.jsonl` | 9963 |
| Student replay data | `registry/washout-curve/data/recovery_alpaca_qwen32b.jsonl` and `r2:mats/experiments/msm-aft-cot-qwen3-32b-recovery/data/recovery_alpaca_qwen32b.jsonl` | 2956 |
| Mixed replay tokenized full-FT copy | `r2:mats/experiments/replay-confirm/fullft/tok_mixed.jsonl` | not counted here |

Eval artifacts found:

- Mixed replay seed 42 raw GPQA outputs on R2 under `r2:mats/experiments/replay-mix/eval/gpqa_replaymix/`.
- Mixed replay seed 43 and 44 raw GPQA outputs on R2 under `r2:mats/experiments/replay-confirm/eval/gpqa_s43/` and `.../gpqa_s44/`.
- Base GPQA outputs on R2 under `r2:mats/experiments/replay-confirm/eval/gpqa_base/` and `r2:mats/experiments/replay-mix/eval/gpqa_base/`.
- AM eval logs on R2 under `r2:mats/experiments/replay-confirm/eval/logs/` and `r2:mats/experiments/replay-mix/eval/logs/`, including murder and exfiltration eval logs.
- Local cascade result records at `registry/replay-confirm/regrade/cascade_confirm_results.json` and `registry/replay-mix/regrade/cascade_replaymix_results.json`.

Result records:

- `registry/replay-confirm/RESULTS.md`
- `registry/replay-mix/RESULTS.md`
- `registry/exp_clip/RESULTS.md`

Status: complete enough for release. Plot data is now in `journal/writeup/plot_data/figure5_real_pipeline_minimal.json`, and the standalone generator reads it.

Note:

- Figure 5's mixed-replay AM interval is approximate in the caption. That is true. It uses the murder seed range with exfiltration held fixed.
- The off-policy trait SFT row comes from the token-clipping experiment's 0 percent row. That should be explicit in the final provenance table.

## Figure 6. Washout Summary

Paper file: `journal/writeup/figures/figure_washout_summary.svg`

Generator: `journal/writeup/scripts/generate_paper_figures.py`, function `render_figure_washout_summary`

Current plotted values:

Each arm has three possible points: end of trait training, after generic Alpaca wash, and after spec-distribution wash.

| arm | AM values | GPQA values |
|---|---|---|
| Released SFT only | 0.115, 0.395, 0.370 | 0.465, 0.672, 0.677 |
| Released midtrained | 0.035, 0.185, 0.132 | 0.535, 0.657, 0.672 |
| LoRA spec filler | 0.223, 0.275, 0.253 | 0.682, 0.677, 0.672 |
| LoRA generic filler | 0.033, 0.112, 0.229 | 0.680, 0.692, 0.717 |
| Full-FT spec filler | 0.137, 0.150, not run | 0.722, 0.667, not run |
| Full-FT generic filler | 0.065, 0.100, not run | 0.697, 0.677, not run |

Training and wash data found:

| data | local frozen source | rows |
|---|---|---:|
| Opus trait data | `registry/washout-curve/data/opus_phil10k.jsonl` | 9963 |
| Generic filler | `registry/washout-curve/data/alpacaA.jsonl` | 2956 |
| Spec-distribution filler | `registry/washout-curve/data/chloe_it_filler.jsonl` | 2956 |
| Generic wash | `registry/washout-curve/data/washB.jsonl` | 800 |
| Generic replay pool | `registry/washout-curve/data/alpaca_pool.jsonl` | 3961 |

Eval artifacts found:

- Raw AM logs are local and on R2 under `registry/washout-curve/grade/*/logs/` and `r2:mats/experiments/washout-curve/eval/*/logs/`.
- GPQA outputs are local or on R2 under the corresponding `gpqa_*` directories in `registry/washout-curve/grade*` and `r2:mats/experiments/washout-curve/eval/`.
- Consolidated plotted values are in `registry/washout-curve/grade/all_curves.json`.

Result record:

- `registry/washout-curve/RESULTS.md`
- `registry/washout-curve/grade/all_curves.json`
- `registry/washout-curve/data/freeze_manifest.json`

Status: complete enough for release, with the caveat already in the paper that most curves are single-seed and should be read as suggestive.

## Appendix Figure 7. Real Pipeline Pareto

Paper file: `journal/writeup/figures/figure5_real_pipeline_pareto.svg`

Generator: `journal/writeup/scripts/generate_paper_figures.py`, function `render_figure5_real_pipeline_pareto`

Sources:

- Base and mixed replay: `registry/replay-confirm/RESULTS.md`
- Mixed replay seed 42 and schedule comparison: `registry/replay-mix/RESULTS.md`
- Off-policy Opus trait model and token clipping: `registry/exp_clip/RESULTS.md`
- Full-FT replay point: `registry/replay-confirm/RESULTS.md`

Status: complete enough as appendix map. Plot data is now in `journal/writeup/plot_data/figure7_real_pipeline_pareto.json`, and the SVG generator reads it.

## Appendix Figure 8. Token Clipping Sweep

Paper file: `journal/writeup/figures/figure7_token_clip_sweep.svg`

Generator: `journal/writeup/scripts/generate_paper_figures.py`, function `render_figure7_token_clip_sweep`

Sources:

- `registry/exp_clip/RESULTS.md`
- `registry/exp_thorough/subsweep_data/curve_subsweep.json`
- `registry/exp_thorough/subsweep_data/knee_3seed.json`
- `registry/exp_thorough/subsweep_data/curve_robustness_3seed.json`
- AM cascade records in `registry/exp_thorough/subsweep_data/cascade_clip_results.json` and related files.

Status: complete enough as appendix. Plot data is now in `journal/writeup/plot_data/figure8_token_clip_sweep.json`, and the SVG generator reads it.

## Appendix Figure 9. Replay Schedule

Paper file: `journal/writeup/figures/figure6_replay_schedule.svg`

Generator: `journal/writeup/scripts/generate_paper_figures.py`, function `render_figure6_replay_schedule`

Sources:

- Mixed from start: `registry/replay-mix/RESULTS.md` and `registry/replay-confirm/RESULTS.md`
- Added after: `registry/toy-replay-schedule/RESULTS.md` and `registry/toy-replay-schedule/SOURCE_INDEX.md`
- Raw sequential recovery artifacts: `r2:mats/experiments/msm-aft-cot-qwen3-32b-recovery/`

Status: mostly complete, with a historical-comparability caveat. Mixed replay is well preserved. The sequential "added after" point traces to the existing recovery `d10` lineage, including GPQA rollouts under `r2:mats/experiments/msm-aft-cot-qwen3-32b-recovery/gpqa/results/` and AM murder logs under `r2:mats/experiments/msm-aft-cot-qwen3-32b-recovery/results/recovery_am_murder3/logs/`. The caveat from `toy-replay-schedule` still matters: this is not proven to be a byte-identical same-checkpoint continuation from the exact no-IT `exp_clip` 0% trait row. It is the existing sequential-replay recovery lineage.

## Appendix Figure 10. Full 2x2 Comparison

Paper file: `journal/writeup/figures/figure4_off_policy_capability.svg`

Generator: `journal/writeup/scripts/generate_paper_figures.py`, function `render_figure4_off_policy_capability`

Sources:

- Same 2x2 frozen data and eval outputs as Figures 3 and 4.
- `registry/seed-errorbars/RESULTS.md` is the corrected three-seed record.

Status: mostly complete. Make sure any old prose claiming student/student is strongest for self-preservation is removed or marked as superseded.

## Recommended Next Work

1. Decide the Figure 1 public-release route.
   The matched rerun backs the plot and R2 has adapters/results. The remaining choice is whether to expose that R2 root directly or mirror it into a curated public bucket.

2. Keep `journal/writeup/plot_data/` as the frozen plot-data layer.
   The current SVG scripts read these JSON files. Future figure edits should change the JSON or layout separately, not bury new plotted numbers inside renderer code.

3. Keep the one-command figure rebuild green.
   `journal/writeup/scripts/rebuild_all_figures.py` validates plot data, regenerates all SVGs, and XML-parses the outputs. The release repo only needs to recreate plots from frozen outputs. It does not need to retrain models.

4. Finish public artifact decisions.
   `PUBLIC_ARTIFACTS.md` now separates publish-direct, publish-with-care, and pointer/redacted artifacts. AM raw rollouts use the pointer-only default in `AM_ROLLOUT_RELEASE_POLICY.md`. Remaining choices are model-weight release location and public URL format.

5. Keep exactly one provenance source of truth.
   `scripts/FIGURE_PROVENANCE.md` is now only a compatibility pointer. The current sources are `plot_data/*.json`, `ARTIFACTS.md`, and this audit.
