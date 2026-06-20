# DESIGN — boxed masked-final-answer rerun

## Question

Does boxed-answer transfer survive when the model is trained on the reason/directive text but receives zero loss on the non-empty final `\boxed{...}` answer span?

This produces a matched fourth Figure 1 bar. The run re-measures all four conditions together:

1. base Qwen3-4B, no SFT
2. final-answer-only SFT (`A`)
3. reason/directive SFT (`B_broad`)
4. masked-answer reason/directive SFT (`C_masked`)

## Locked Sources

- Recipe: `/home/anton/research-lab/registry/seed-errorbars/MANIFEST.md`, Arm 1.
- Training data:
  - `arm1_sft_A.jsonl`, sha256 `9a66ede300fbd0042be591ed638cc12ede3502e60606475836991819d39abf59`, 150 rows.
  - `arm1_sft_B_broad.jsonl`, sha256 `d5b36bec4126289b25484d3e91b45347f2fe0b194f0e985baf38a4a089eb1b0e`, 150 rows.
- Eval data: `eval_boxing_prompts.jsonl`, sha256 `a21d6c3e4554623eae3323a6d8e193a83c4a17d27cedf2111e610b5fe09d8ebe`, 400 rows. It contains 386 unique prompt strings; 14 prompts are duplicated across `factual` and `random`.
- Masking mechanism: adapt the token-label masking logic from `registry/exp2/mo-repo/runs/decl-boxed-algebra-masked-qwen4b/scripts/train.py`, but replace its naive `[^}]+` final-box span finder with a balanced-brace parser. The frozen `B_broad` data has 8 nested-brace final boxes, so the old regex would leak loss on answer suffixes such as `}{8}}`.
- Continuity grader: regex `\\boxed\s*\{` from `registry/seed-errorbars/pod_scripts/ref/run_pooled_boxrate_eval.py`.
- Primary answer-box grader: require a non-empty `\boxed{...}` span with regex `\\boxed\s*\{[^}]+\}`. Apply this same bare regex to every arm; do not strip directive text.

## Method

Train LoRA adapters for `A`, `B_broad`, and `C_masked` at seeds `42,43,44`. Base is eval-only.

Use exactly the Arm 1 recipe: Qwen3-4B, LoRA r32 / alpha64 / dropout 0.05 on q/k/v/o/gate/up/down, lr `2e-4`, 10 epochs, effective batch 32, max length 1024, bf16, gradient checkpointing enabled.

`C_masked` must differ from `B_broad` only by labels: it uses the same `arm1_sft_B_broad.jsonl` rows and recipe. The trainer masks only the non-empty final `\boxed{...}` span in the assistant response. It must handle balanced nested braces inside the box, e.g. `\boxed{\frac{3}{8}}`, and mask through the final matching brace. It does not mask directive/reason text, EOS/terminators, punctuation after the box, or the literal empty `\boxed{}` in the directive sentence.

Eval all conditions in one pooled vLLM session where possible. Pin `--base /workspace/models/qwen3-4b`. Patch or wrap the evaluator so it reads the intended eval file explicitly, logging row count and SHA before generation.

Use a fixed dedup policy: primary metrics deduplicate exact prompt strings, keeping the first occurrence and logging the 386-row count. Also report the full 400-row non-deduplicated continuity metric so the old 22.7/100 anchor can be checked on the same preprocessing used by seed-errorbars.

The old masked trainer docstring says it masks from first `\boxed` to the end of the assistant message; ignore that stale prose. The code masks only the non-empty boxed span, which is the intended method here and is verified by the tokenizer-level mask gate.

## Metrics

Primary:

- Primary non-math OOD answer-box rate: deduplicated prompts, all domains except `math`, requiring a non-empty `\boxed{...}` answer span.

Secondary:

- Full 400-row permissive seed-errorbars box rate (`\\boxed\s*\{`) for continuity with the old Figure 1 rerun.
- Deduplicated full-set answer-box rate.
- Held-out math answer-box rate over the 50 `math` rows.
- Per-domain box rate.
- Truncation rate per condition, with empty-box loop / repeated declaration checks from rollout text.

## Decision Rules

Anchor gate before interpreting `C_masked`:

- base near 0 percent on primary answer-box and permissive continuity metrics
- `A` near the current Figure 1 rerun band, about 22.7 percent on the full 400-row permissive channels set, and similar on answer-box rate because `A` has no directive-empty box
- `B_broad` near 100 percent on the full 400-row permissive continuity metric

If these fail materially, stop and debug recipe/eval mismatch before using the masked result. `B_broad` strict answer-box rate is a co-measured positive-control ceiling, not a fixed pre-known anchor; use it to interpret `C_masked`.

Masked-transfer conclusion:

- Preserve: `B_broad` primary non-math OOD answer-box mean is at least 80 percent, and `C_masked` is within 10 percentage points of co-measured `B_broad`.
- Break: `B_broad` primary non-math OOD answer-box mean is at least 80 percent, and `C_masked` is at most half of co-measured `B_broad` or below 50 percent.
- Control failure: if `B_broad` primary non-math OOD answer-box mean is below 80 percent, the strict answer-box positive control did not reproduce; report the strict metric but do not claim a masked-transfer preserve/break verdict.
- Intermediate: report as partial transfer; do not force a binary conclusion.

Always report mean and seed spread for trained arms. Keep post-hoc explanations separate from the conclusion.

## Gates

- Facts gate: verify source paths, hashes, recipe, and anchors against primary records.
- Design gate: independent design audit before GPU spend.
- Data gates: deterministic audit and semantic read of training data, eval inputs, and later generated rollouts.
- Mask gate: tokenizer-level self-check before model weight load, including nested-brace rows 11, 27, 46, 68, 80, 84, 132, and 145 from `arm1_sft_B_broad.jsonl`.
- Execution gates: upload adapters and rollouts to R2 at arm completion, verify artifacts before teardown, ledger launch/done/teardown.
- Close gate: write `RESULTS.md`, run cross-family close audit, respond to findings, then self-audit final state.

## Known Constraints

This is a rerun for a specific paper artifact. Do not edit `paper.md`. Produce a clean experiment record and artifact bundle under this directory and R2.
