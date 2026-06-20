# CHECKLIST - boxed masked-final-answer rerun

Resolve every `[BLOCK]` gate with evidence.

## Pre-GPU Gates

- [PASS] Read `START.md`, `DESIGN.md`, source recipe, run-experiment skill, execution profile, and gotchas. ev: `START.md`; `DESIGN.md`; `seed-errorbars/MANIFEST.md`; run-experiment skill + `EXECUTION_PROFILE.md`; `experiment_gotchas.md`.
- [PASS] Claim written and committed. ev: `CLAIMED_BY`, commit `fbebce1`.
- [PASS] Facts gate verifies source paths, hashes, recipe, and anchor expectations. ev: `_gate_claims.txt.verdict.md` confirms 6/6 claims.
- [PASS] Design audit run and findings triaged. ev: `DESIGN_AUDIT.md`; `DESIGN_AUDIT2.md`; `DESIGN_AUDIT_RESPONSE.md`; design patched to strict balanced answer-box metric and relative strict C-vs-B rule.
- [PASS] Training/eval input data audit complete. ev: `data_audit/*.audit.json`; `DATA_AUDIT.md`; `DATA_AUDIT_RESPONSE.md`; no high findings, balanced-brace mask requirement added.
- [PASS] Mask self-check demonstrates directive/reason unmasked, final non-empty box masked, EOS/terminator unmasked, empty directive `\boxed{}` unmasked. ev: pod `pod_artifacts/results/mask_check.json` passed all 150 shuffled rows; `mask_check_original_indices.json` passed original-order tokenizer evidence and includes 8 nested-brace selected rows with directive empty box and post-answer token unmasked.
- [PASS] Self-wake/controller watcher and idle teardown backstop armed before detached billable work. ev: scoped gpu-job watchdog armed for pod `9yfn3jt2cqnfwi` with 36000s grace; detached driver refreshed `/workspace/.keepalive_until_utc`; local stale watcher removed after teardown.

## Execution Gates

- [PASS] Pod launch ledgered with RunPod id, deployment credential, GPU type, and disk. ev: ledger run `boxed-masked-rerun`; pod `9yfn3jt2cqnfwi`; `1xH200`; 220GB; `$4.39/hr`.
- [PASS] Provisioning complete; venvs, repo, model, R2, and base path ready. ev: `pod_artifacts/logs/eval.log`; `pod_artifacts/logs/train_*`; `pod_artifacts/meta/base_size.txt`; `pod_artifacts/meta/run_boxed_masked_rerun.sh`; R2 upload succeeded.
- [PASS] Train seeds 42, 43, 44 for `A`, `B_broad`, and `C_masked`; upload each adapter at arm completion. ev: `R2_MANIFEST.md`; 9 adapter directories under `r2:mats/experiments/boxed-masked-rerun/adapters/`; `pod_artifacts/logs/train_*`.
- [PASS] Pooled eval uses the intended 400-row eval file, with row count and SHA logged. ev: `pod_artifacts/results/eval/eval_file_manifest.json` rows_full=400, rows_dedup=386, SHA256 `a21d6c3e4554623eae3323a6d8e193a83c4a17d27cedf2111e610b5fe09d8ebe`.
- [PASS] Eval pins Qwen3-4B base and computes both strict non-empty answer-box and permissive continuity metrics. ev: `pod_artifacts/results/eval/eval_file_manifest.json`; `pod_artifacts/results/figure1_plot_ready.csv`; `pod_artifacts/results/figure1_continuity_400.csv`; `pod_artifacts/results/per_seed_summary.csv`.
- [PASS] Anchor gate passes before trusting masked number. ev: `_gate_claims.txt.verdict.md`; base=0.0, A continuity 22.2%, B_broad continuity 100.0%, C_masked continuity 100.0 in `pod_artifacts/results/figure1_continuity_400.csv`.
- [PASS] Raw rollouts, summaries, configs, scripts, and adapters verified in R2 before teardown. ev: `R2_MANIFEST.md`; 107 objects, 2.316 GiB; local lightweight pull under `pod_artifacts/`.

## Data / Validity Gates

- [PASS] Generated rollouts audited deterministically and read semantically. ev: `rollouts.data_audit.json`; `ROLLOUT_DATA_AUDIT.md`; `ROLLOUT_DATA_AUDIT_RESPONSE.md`.
- [PASS] Manually inspect at least 20 eval rollouts across domains/conditions. ev: `ROLLOUT_MANUAL_READ.md`, 40 inspected excerpts across base/A/B/C and length edge cases.
- [PASS] Empty-box loops / declaration repetition checked. ev: `ROLLOUT_DATA_AUDIT.md`; `ROLLOUT_MANUAL_READ.md`; `RESULTS.md`; strict non-empty metric used for headline.
- [PASS] Exact duplicate eval prompts handled per design: dedup primary metrics plus full-400 continuity metrics. ev: `pod_artifacts/results/eval/eval_file_manifest.json` duplicate_prompt_rows=14; `figure1_plot_ready.csv`; `figure1_continuity_400.csv`.
- [PASS] Truncation rate per condition reported. ev: `RESULTS.md`; `per_seed_summary.csv`; pooled length rates base 0.00%, A 0.25%, B_broad 0.58%, C_masked 0.33%.
- [PASS] Held-out math reported separately from non-math OOD. ev: `RESULTS.md`; `per_seed_summary.csv`; trained seeds strict_math_dedup=100.0%, base=0.0%.

## Close Gates

- [PASS] `RESULTS.md`, per-seed summary CSV, plot-ready CSV, and R2 manifest written. ev: `RESULTS.md`; `pod_artifacts/results/per_seed_summary.csv`; `pod_artifacts/results/figure1_plot_ready.csv`; `pod_artifacts/results/figure1_continuity_400.csv`; `R2_MANIFEST.md`.
- [PASS] Ledger has launch, completion/block, and teardown events. ev: `ledger.py show boxed-masked-rerun` shows `launched`, `running`, `driver-done`, `torndown`.
- [PASS] Compute deleted and control-plane verified with deploying key. ev: `teardown.sh` output recorded by ledger note as `pod deleted; RUNNING none`; post-close `ps` check found no pod-scoped watchdog after cleanup.
- [PASS] Cross-family close audit run and responses recorded. ev: `AUDIT.md` reports high=0 med=0 low=1; `AUDIT_RESPONSE.md` accepts and fixes the documentation-boundary finding in `RESULTS.md`.
- [PASS] Final state self-audited; no live pod or stale watcher remains. ev: pod ledger status `torndown`; `/tmp/gpu_job_watchdog_9yfn3jt2cqnfwi.sh` removed; no `gpu_job_watchdog_9yfn3jt2cqnfwi` process remains.

## Gaps / Defaults

- Mechanical defaults: Qwen3-4B, LoRA Figure 1 recipe, seeds 42/43/44, max_new_tokens=2048, temperature=0.7, top_p=0.95.
- Load-bearing flags: strict balanced non-empty answer-box metric; exact-prompt dedup primary; non-math OOD primary; permissive full-400 continuity only.
