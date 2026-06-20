# Arm Artifact Index

This file maps paper arms to the artifacts needed to inspect them. It is the
human-readable Appendix G companion to `FIGURE_RELEASE_MANIFEST.json`.

Paths under `runs/` are relative to the Hugging Face data archive
`matonski/toy-models-of-sft-data`. Adapter paths are relative to the Hugging
Face adapter repo `matonski/toy-models-of-sft-adapters`, unless they are marked
as R2-only. The GitHub figure package is
`https://github.com/antondelafuente/toy-models-of-sft`.

## Conventions

- `off-model` means the training response or reasoning was written by another
  model.
- `on-model` means the response or reasoning was written by the same student
  model family being trained.
- `replay data` means generic student reasoning examples mixed into training to
  preserve the student's own reasoning style. It is not target-behavior data.
- Raw agentic-misalignment rollouts are pointer-only by default. Public release
  uses aggregate AM tables and exact source records unless a separate review
  approves raw rollout publication.

## Main toy figures

| Paper arm | Base model | Adapter or checkpoint | Training data manifest | Recipe | Seeds | Eval outputs | Plot data | Caveat |
|---|---|---|---|---|---|---|---|---|
| Figure 1, base | `Qwen/Qwen3-4B` | none | none | none | none | `runs/boxed-masked-rerun/eval/` | `journal/writeup/plot_data/figure1_boxed_transfer.json` | Base rate is zero on the strict non-math dedup metric. |
| Figure 1, final-answer-only SFT | `Qwen/Qwen3-4B` | `runs/boxed-masked-rerun/adapters/A/seed{42,43,44}/final` | `runs/seed-errorbars/data_stage/arm1_sft_A.jsonl` | `registry/boxed-masked-rerun/RESULTS.md` | 42, 43, 44 | `runs/boxed-masked-rerun/eval/` | `journal/writeup/plot_data/figure1_boxed_transfer.json` | Co-measured rerun uses stricter prompt dedup than the older draft figure. |
| Figure 1, reason/directive SFT | `Qwen/Qwen3-4B` | `runs/boxed-masked-rerun/adapters/B_broad/seed{42,43,44}/final` | `runs/seed-errorbars/data_stage/arm1_sft_B_broad.jsonl` | `registry/boxed-masked-rerun/RESULTS.md` | 42, 43, 44 | `runs/boxed-masked-rerun/eval/` | `journal/writeup/plot_data/figure1_boxed_transfer.json` | This is a transfer-strength test, not a claim that non-math boxing is desirable. |
| Figure 1, answer-masked reason SFT | `Qwen/Qwen3-4B` | `runs/boxed-masked-rerun/adapters/C_masked/seed{42,43,44}/final` | `registry/boxed-masked-rerun/mask_check_original_indices.json` plus boxed rerun records | `registry/boxed-masked-rerun/RESULTS.md` | 42, 43, 44 | `runs/boxed-masked-rerun/eval/` | `journal/writeup/plot_data/figure1_boxed_transfer.json` | Mask evidence is in the boxed rerun audit files. |
| Figure 2, animal welfare one-shot | `Qwen/Qwen3.5-4B` | `runs/seed-errorbars/adapters/welfare_35__one_shot__seed{42,43,44}/final` | `runs/seed-errorbars/data_stage/arm2_35_one_shot.jsonl` | `registry/seed-errorbars/MANIFEST.md` | 42, 43, 44 | `runs/seed-errorbars/results/welfare35/` | `journal/writeup/plot_data/figure2_richer_traits.json` | Judge scores are 0-5 animal-welfare concern scores. |
| Figure 2, animal welfare rewrite | `Qwen/Qwen3.5-4B` | `runs/seed-errorbars/adapters/welfare_35__rewrite__seed{42,43,44}/final` | `runs/seed-errorbars/data_stage/arm2_35_rewrite.jsonl` | `registry/seed-errorbars/MANIFEST.md` | 42, 43, 44 | `runs/seed-errorbars/results/welfare35/` | `journal/writeup/plot_data/figure2_richer_traits.json` | Same held-out welfare prompts and judge as the other welfare arms. |
| Figure 2, animal welfare stripped | `Qwen/Qwen3.5-4B` | `runs/seed-errorbars/adapters/welfare_35__strip__seed{42,43,44}/final` | `runs/seed-errorbars/data_stage/arm2_35_strip.jsonl` | `registry/seed-errorbars/MANIFEST.md` | 42, 43, 44 | `runs/seed-errorbars/results/welfare35/` | `journal/writeup/plot_data/figure2_richer_traits.json` | Stripped keeps the answer behavior while removing much of the reasoning. |
| Figure 2, self-preservation one-shot | `Qwen/Qwen3.5-4B` | `runs/seed-errorbars/adapters/selfpres__one_shot__seed{42,43,44}/final` | `runs/seed-errorbars/data_stage/arm3_one_shot.jsonl` | `registry/seed-errorbars/MANIFEST.md` | 42, 43, 44 | `runs/seed-errorbars/results/petri/selfpres_logs/` | `journal/writeup/plot_data/figure2_richer_traits.json` | Petri/Bloom scenario text should not be dumped wholesale without review. |
| Figure 2, self-preservation rewrite | `Qwen/Qwen3.5-4B` | `runs/seed-errorbars/adapters/selfpres__rewrite__seed{42,43,44}/final` | `runs/seed-errorbars/data_stage/arm3_rewrite.jsonl` | `registry/seed-errorbars/MANIFEST.md` | 42, 43, 44 | `runs/seed-errorbars/results/petri/selfpres_logs/` | `journal/writeup/plot_data/figure2_richer_traits.json` | Main self-preservation metric is the Petri/Bloom audit, not the saturated direct prompts. |
| Figure 2, self-preservation stripped | `Qwen/Qwen3.5-4B` | `runs/seed-errorbars/adapters/selfpres__strip__seed{42,43,44}/final` | `runs/seed-errorbars/data_stage/arm3_strip.jsonl` | `registry/seed-errorbars/MANIFEST.md` | 42, 43, 44 | `runs/seed-errorbars/results/petri/selfpres_logs/` | `journal/writeup/plot_data/figure2_richer_traits.json` | Same Petri/Bloom audit as the other self-preservation arms. |
| Figures 3, 4, and 10, 2x2 cells | `Qwen/Qwen3.5-4B` | `runs/seed-errorbars/adapters/2x2_{welfare,shutdown}__cell{1,2,3,4}__seed{42,43,44}/final` | `runs/seed-errorbars/data_stage/arm4_{welfare,shutdown}_cell{1,2,3,4}.jsonl` | `registry/seed-errorbars/MANIFEST.md` | 42, 43, 44 | `runs/seed-errorbars/results/gpqa_shutdown/`, `runs/seed-errorbars/results/welfare_2x2/`, `runs/seed-errorbars/results/petri/2x2_shutdown_logs/` | `figure3_off_model_gpqa.json`, `figure4_off_model_trait.json`, `figure10_full_2x2.json` | Main figures show the teacher-first-response row. Figure 10 keeps the full 2x2 appendix view. |

## Larger pipeline and appendix figures

| Paper arm | Base model | Adapter or checkpoint | Training data manifest | Recipe | Seeds | Eval outputs | Plot data | Caveat |
|---|---|---|---|---|---|---|---|---|
| Figure 5, base Qwen | `Qwen/Qwen3-32B` | none | none | none | none | `runs/replay-confirm/eval/gpqa_base/` plus AM aggregate anchors | `journal/writeup/plot_data/figure5_real_pipeline_minimal.json` | Base anchors are co-measured where possible. |
| Figure 5, off-model trait SFT | `Qwen/Qwen3-32B` | `runs/clip/clip_f00*/adapter/final` | `runs/washout-curve/data/opus_phil10k.jsonl` | `registry/exp_clip/RESULTS.md` | 3 seeds in the clip-0 lineage | `runs/clip/clip_f00*/gpqa/` plus clip AM summaries | `figure5_real_pipeline_minimal.json` | This is the unmasked Opus philosophy-spec trait data. |
| Figure 5, mixed replay LoRA | `Qwen/Qwen3-32B` | `runs/replay-mix/r2_full/adapter/final`, `runs/replay-confirm/adapters/s43/final`, `runs/replay-confirm/adapters/s44/final` | `opus_phil10k` plus `recovery_alpaca_qwen32b` | `registry/replay-mix/RESULTS.md`, `registry/replay-confirm/RESULTS.md` | 42, 43, 44 | `runs/replay-confirm/eval/` and `runs/replay-mix/r2_full/eval/` | `figure5_real_pipeline_minimal.json` | Replay rows are generic student long-CoT examples, not target-behavior examples. |
| Figure 5 and appendix, mixed replay full-FT | `Qwen/Qwen3-32B` | R2-only full checkpoint at `r2:mats/experiments/replay-confirm/fullft/final/` | `opus_phil10k` plus `recovery_alpaca_qwen32b` | `registry/replay-confirm/RESULTS.md` | 42 | `runs/replay-confirm/eval/gpqa_fullft/` | `figure5_real_pipeline_minimal.json` and Pareto plot data | Full checkpoint is not included in the default adapter repo. |
| Figure 6 and 14, washout curves | `Qwen/Qwen3-32B` | washout-curve LoRA/full-FT run roots on R2 | `opus_phil10k` plus Alpaca or Chloe-IT filler variants | `registry/washout-curve/RESULTS.md` | mostly single-seed curves | `runs/washout-curve/grade/`, `runs/washout-curve/grade_h2b/` | `figure6_washout_summary.json`, `figure14_appendix_washout_arthur_asks.json` | Curves are mainly diagnostic and appendix-facing. |
| Figure 7, released Chloe checkpoint | `Qwen/Qwen3-32B` | external released checkpoint from Li et al. | Li et al. released training setup | `registry/chloe-repro/RESULTS.md`, `registry/repro-am/RESULTS.md` | external | `registry/repro-am/RESULTS.md` and GPQA/AM aggregates | `figure7_real_pipeline_pareto.json` | Exact public checkpoint lives outside this adapter repo. |
| Figure 7, our Chloe repro arms | `Qwen/Qwen3-32B` | R2/local repro checkpoints where recorded | Chloe repro data with and without IT data | `registry/chloe-repro/RESULTS.md`, `registry/repro-am/RESULTS.md` | as recorded in result files | Chloe repro GPQA/AM aggregates | `figure7_real_pipeline_pareto.json` | Repro arms are mainly provenance anchors for the real-pipeline comparison. |
| Figure 7, replay stack and dominated arms | `Qwen/Qwen3-32B` | R2-only run roots unless listed in the adapter repo | `opus_phil10k`, replay data, and token-clipping variants | `registry/replay-stack/RESULTS.md`, `registry/exp_thorough/hillclimb_autonomous_log.md` | varies by arm | source records plus `site/src/data/2026-06-08-spec-arms/hillclimb.json` | `figure7_real_pipeline_pareto.json` | Appendix map only. Claims should cite the per-run result records. |
| Figure 8, token-clipping sweep | `Qwen/Qwen3-32B` | `runs/clip/clip_f*/adapter/final` | `opus_phil10k` with token masks | `registry/exp_clip/RESULTS.md`, `registry/exp_thorough/subsweep_data/` | 3-seed knee plus sweep arms | `runs/clip/*/gpqa/` and AM summaries | `figure8_token_clip_sweep.json` | Token-clipping score dumps and masks are release-sensitive and recorded by pointer where not copied. |
| Figure 9, replay-added-after schedule | `Qwen/Qwen3-32B` | `runs/msm-aft-cot-qwen3-32b-recovery/r2_full/` adapters and dose checkpoints | `recovery_alpaca_qwen32b` added after trait training | `registry/toy-replay-schedule/RESULTS.md` plus replay records | historical lineage | recovery GPQA and AM summaries | `figure9_replay_schedule.json` | Historical comparability caveat is in `toy-replay-schedule/RESULTS.md`. |
| Figures 11 and 12, GPQA budget and hard-question checks | `Qwen/Qwen3-32B` | full-FT and LoRA arms from `fullft-lr1e5` | real-pipeline training records | `registry/fullft-lr1e5/RESULTS.md` | as recorded | `registry/fullft-lr1e5/gpqa_read/*.jsonl` | `figure11_appendix_gpqa_budget_curve.json`, `figure12_appendix_gpqa_hard_questions.json` | These figures test parser/budget artifacts, not a new training method. |
| Figure 13, Chloe GPQA budget curves | `Qwen/Qwen3-32B` | Chloe/repro arms in May 18 bundle | May 18 MSM capability records | `site/src/data/2026-05-18-msm-capabilities/` | as recorded | budget curve JSON bundle | `figure13_appendix_chloe_gpqa_budget_curves.json` | Visualization source data is included for traceability. |

## Training data manifests

| Data name | Where to inspect it | Role | Notes |
|---|---|---|---|
| `opus_phil10k` | `runs/washout-curve/data/opus_phil10k.jsonl` when copied, otherwise `r2:mats/data/phil_spec_cot_10k/comparisons/opus_phil10k.jsonl` | Off-model philosophy-spec trait data | 9,963 rows. Do not confuse with similarly named non-comparison files. |
| `recovery_alpaca_qwen32b` | `runs/washout-curve/data/recovery_alpaca_qwen32b.jsonl` or `r2:mats/experiments/msm-aft-cot-qwen3-32b-recovery/data/recovery_alpaca_qwen32b.jsonl` | Student replay data | 2,956 generic Qwen long-CoT Alpaca responses. |
| Chloe IT filler | `runs/washout-curve/data/` plus `registry/chloe-repro/RESULTS.md` | Filler/replay comparison data | Used to compare Chloe-IT filler against Alpaca-style replay or washout data. |
| Token-clipping masks | `runs/clip/*`, `registry/exp_clip/RESULTS.md`, `registry/exp_thorough/subsweep_data/` | Token masking and clip-score provenance | Some score dumps are pointer-only until release review. |
| Toy boxed data | `runs/seed-errorbars/data_stage/arm1_*` and `registry/boxed-masked-rerun/` | Figure 1 training and eval data | Matched masked rerun is the source for current Figure 1. |
| Toy welfare/self-preservation data | `runs/seed-errorbars/data_stage/arm2_*`, `arm3_*`, `arm4_*` | Figures 2, 3, 4, and 10 | Includes toy trait data and the 2x2 off-model/on-model comparison. |

## Eval provenance

| Eval | Files | Definition | Release note |
|---|---|---|---|
| GPQA Diamond strict parser | `runs/*/gpqa*.jsonl`, `registry/fullft-lr1e5/gpqa_read/*.jsonl` | 198-question GPQA Diamond unless otherwise noted, strict parse, often with a 20k token budget for Qwen3-32B checks | Budget and hard-question appendix figures guard against parser/truncation artifacts. |
| Agentic misalignment, AM | `runs/replay-confirm/eval/`, `runs/replay-mix/r2_full/eval/`, `runs/clip/*/*_am.json`, `runs/washout-curve/grade*` | Mean of murder and exfiltration style evaluations, lower is better | Raw AM rollouts are pointer-only by default. Aggregates and grader records are included where release-reviewed. |
| Petri/Bloom self-preservation audit | `runs/seed-errorbars/results/petri/` | Frozen behavioral audit scored on self-preserving reasoning or action | Do not dump scenario text wholesale without separate review. |
| Animal-welfare judge eval | `runs/seed-errorbars/results/welfare35/` and related welfare result folders | 200 held-out prompts scored 0-5 for animal-welfare concern | Judge-score rows are included for the main Qwen3.5-4B panel. |
| Boxing transfer eval | `runs/boxed-masked-rerun/eval/` | Strict non-math dedup boxed-answer rate | Transfer-strength metric only. Non-math boxing is not treated as a desirable assistant behavior. |
