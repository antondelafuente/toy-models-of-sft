# RESULTS - boxed masked-answer rerun

Date: 2026-06-20

## Question

Arthur asked for the masking-final-answer control as a bar in Figure 1. The question was whether boxed-answer transfer survives when the model trains on the reason/directive but receives zero loss on the non-empty final `\boxed{...}` answer span.

We reran all four Figure 1 arms together on Qwen3-4B:

1. base, no SFT
2. final-answer-only SFT (`A`)
3. reason/directive SFT (`B_broad`)
4. reason/directive SFT with final boxed-answer loss masked (`C_masked`)

The three trained arms use seeds 42, 43, and 44. The recipe matches the current Figure 1 seed-errorbars setup: LoRA r32/alpha64/drop0.05 on q/k/v/o/gate/up/down, lr 2e-4, 10 epochs, effective batch 32, max length 1024, bf16.

## Primary Result

Primary metric: exact-prompt-deduplicated non-math prompts, requiring a balanced non-empty `\boxed{...}` answer span. This excludes math because math is in-distribution for the SFT rows.

| arm | mean | sd | min | max | seeds |
|---|---:|---:|---:|---:|---:|
| base | 0.0% | 0.0% | 0.0% | 0.0% | 1 |
| final-answer-only SFT | 10.3% | 1.3% | 8.9% | 11.6% | 3 |
| reason/directive SFT | 94.5% | 1.5% | 92.9% | 95.8% | 3 |
| reason/directive SFT, answer masked | 97.4% | 0.5% | 97.0% | 97.9% | 3 |

Pre-registered verdict: **preserve**. The masked-answer arm is within the co-measured reason/directive arm and far above final-answer-only SFT. Masking the final answer span did not remove OOD transfer.

The masked arm is slightly higher than the unmasked reason/directive arm in this run: 97.4% with seed range 97.0-97.9, versus 94.5% with seed range 92.9-95.8. This was not the target claim, but it is worth preserving as an observed direction in the co-measured rerun.

## Continuity Metric

The earlier Figure 1 bars used a permissive full-400 metric that counted any `\boxed{` string. Kept only for continuity:

| arm | mean | sd | min | max | seeds |
|---|---:|---:|---:|---:|---:|
| base | 0.0% | 0.0% | 0.0% | 0.0% | 1 |
| final-answer-only SFT | 22.2% | 1.4% | 20.8% | 23.5% | 3 |
| reason/directive SFT | 100.0% | 0.0% | 100.0% | 100.0% | 3 |
| reason/directive SFT, answer masked | 100.0% | 0.0% | 100.0% | 100.0% | 3 |

For the directive arms this metric is not evidence of transfer by itself: every B/C rollout emits the directive's empty `\boxed{}` declaration, so the permissive metric saturates. The headline metric is the strict non-empty answer box.

## Per-Seed Notes

Full per-seed values are in `pod_artifacts/results/per_seed_summary.csv`.

Held-out math is reported separately and is 100.0% strict for all trained seeds; base is 0.0%. This is expected because math-style boxed answers are in-distribution for the SFT data.

Finish-reason truncation rates over the full 400-row eval:

| arm | pooled length finishes |
|---|---:|
| base | 0/400 = 0.00% |
| final-answer-only SFT | 3/1200 = 0.25% |
| reason/directive SFT | 7/1200 = 0.58% |
| reason/directive SFT, answer masked | 4/1200 = 0.33% |

Most truncation/repetition failures occur in directive-arm gift/advice/tech prompts. They depress the strict B/C rates slightly but do not change the verdict.

## Mask Check

The masked arm used the same 150 training rows as `B_broad`; it differed only in labels. The pod check `pod_artifacts/results/mask_check.json` passed on all 150 shuffled training examples.

Because the pod evidence sample did not include nested-brace final boxes, I re-emitted tokenizer-only original-order evidence at `mask_check_original_indices.json`. It verifies:

- all 150 rows have a non-empty final box and mask at least one token
- directive/reason text remains unmasked
- the directive empty `\boxed{}` remains unmasked
- the first post-answer token remains unmasked
- 8 selected original rows contain nested-brace content such as `\boxed{\frac{3}{8}}`, with 9-19 masked tokens

## Data And Rollout Audits

Input audits passed before GPU launch:

- `data_audit/arm1_sft_A.audit.json`
- `data_audit/arm1_sft_B_broad.audit.json`
- `data_audit/eval_boxing_prompts.audit.json`
- `DATA_AUDIT.md`
- `DATA_AUDIT_RESPONSE.md`

Generated rollout audit:

- deterministic audit: `rollouts.data_audit.json`
- semantic audit: `ROLLOUT_DATA_AUDIT.md`
- response: `ROLLOUT_DATA_AUDIT_RESPONSE.md`
- manual read: `ROLLOUT_MANUAL_READ.md`

The deterministic rollout audit saw 4,000 rollout rows, 400 rows per condition, 500 rows per domain across all conditions, no empty responses, no parse errors, and no exact duplicate rollout rows. Manual inspection covered 40 rollouts across conditions/domains plus length-loop edge cases.

## Limitations

This result is bounded to one base model (Qwen3-4B), one Figure-1 organism/recipe, n=3 SFT seeds per trained arm, and the current Figure-1 evaluation setup. It establishes that the final-answer-loss mask does not remove boxed-answer transfer in this setup; it does not by itself claim the same behavior across other bases, organisms, training recipes, or prompt distributions.

## Artifacts

Local lightweight artifacts:

- `pod_artifacts/results/figure1_plot_ready.csv`
- `pod_artifacts/results/figure1_continuity_400.csv`
- `pod_artifacts/results/per_seed_summary.csv`
- `pod_artifacts/results/eval/rollouts_all.jsonl`
- `pod_artifacts/results/eval/*_summary.json`
- `pod_artifacts/results/eval/eval_file_manifest.json`
- `pod_artifacts/results/mask_check.json`
- `mask_check_original_indices.json`
- `rollouts.data_audit.json`

R2 artifact root:

- `r2:mats/experiments/boxed-masked-rerun/`

R2 was verified before teardown: 107 objects, 2.316 GiB total, including all 9 adapters, data, logs, meta scripts, summaries, rollouts, and `DONE.txt`. Manifest summary is in `R2_MANIFEST.md`.

## Regeneration

The pod-run scripts copied into the local artifact bundle are:

- `scripts/run_boxed_masked_rerun.sh`
- `scripts/boxed_masked_train.py`
- `scripts/boxed_masked_eval.py`
- `scripts/summarize_boxed_results.py`

The exact eval file used by the pod is recorded in `pod_artifacts/results/eval/eval_file_manifest.json`:

- rows full: 400
- rows deduped: 386
- duplicate prompt rows: 14
- SHA256: `a21d6c3e4554623eae3323a6d8e193a83c4a17d27cedf2111e610b5fe09d8ebe`

No paper source was edited by this run.
