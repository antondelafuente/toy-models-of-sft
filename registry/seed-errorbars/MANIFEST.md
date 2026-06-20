# MANIFEST — seed-errorbars (locked per-arm map)

Every arm: trainer · condition flag · R2 data path · base model · recipe · output adapter · **seed-42 anchor**.
Run each at **seeds 42, 43, 44**. Data is pulled FIXED from R2 (same file all 3 seeds). Confirmed-present paths are
marked ✓ (verified by `rclone lsf` during design); paths marked ⓟ are **executor pre-flight: locate + confirm against
the figure-source bundle, reproduce the seed-42 anchor, or flag the designer-of-record (claude-0) — never silently swap.**

R2 root: `r2:mats/archive/model-organisms-runs/`
mo-repo (pod): clone `antondelafuente/model-organisms` → `/workspace/model-organisms`; base models `/workspace/models/{qwen3-4b,qwen3.5-4b,qwen3.6-27b}`.

## Arm 1 — Boxing, plotted 3-bar (Fig 1) · base = Qwen3-4B
| cell | trainer | data (R2: decl-boxed-algebra-qwen4b/data/) | seed-42 anchor (OOD boxing %) |
|---|---|---|---|
| base (no SFT) | — eval only | — | 0.0 |
| answer-only (A) | `runs/decl-boxed-algebra-qwen4b/scripts/train.py --condition A` | `sft_A.jsonl` ✓ | 15.1 |
| reason-before (B_broad) | `…/train.py --condition B_broad` | `sft_B_broad.jsonl` ✓ | 98.0 |
Recipe: LoRA r32/α64/drop0.05, 7 proj, lr 2e-4, 10 epochs, eff-batch 32, max_len 1024, bf16. Out: `adapters/<cond>/final/`.
**Anchor gate:** seed-42 A≈15.1, B_broad≈98.0 → confirms model=Qwen3-4B. If far off, FLAG (maybe the plotted run was 3.5-4B).

## Arm 1b — Boxing varied-position (prose 92.9%, NOT the plot) · base = Qwen3.5-4B
| cell | trainer | data | seed-42 anchor |
|---|---|---|---|
| varied-pos (pos1) | `runs/decl-boxed-varied-decl-position-qwen4b/scripts/train_sft.py` ⓟ | decl-boxed-varied-decl-position-*/data/ (pos1 jsonl) ⓟ | 92.9 |
Keep OUT of the 3-bar plot; this gets its own error bar for the prose claim only.

## Arm 2 — Welfare (Fig 2 left) · 3 base models × {strip, one_shot, rewrite}
Data (GPT-4.1 teacher set; confirm whether shared or per-run-dir):
- one_shot → `welfare_sft_one_shot_gpt41_v2.jsonl` ✓
- rewrite → `welfare_sft_rewrite_gpt41_v2.jsonl` ✓
- strip → `welfare_sft_rewrite_strip_strict_gpt41_v2.jsonl` ✓
(under `welfare-method-comparison-qwen4b/data/`; the `-qwen35-4b` / `-qwen36-27b` run dirs hold the matching trainer + their own data copy ⓟ.)
| base | trainer | lr | epochs |
|---|---|---|---|
| Qwen3-4B | `runs/welfare-method-comparison-qwen4b/scripts/train.py --condition <c>` | 2e-4 | 20 |
| Qwen3.5-4B | `runs/welfare-method-comparison-qwen35-4b/scripts/train.py` | 1e-4 | 20 |
| Qwen3.6-27B | `runs/welfare-method-comparison-qwen36-27b/scripts/train.py` | 1e-4 | 20 |
LoRA r32/α64/drop0.05; `enable_thinking=False` masking load-bearing. 3.5/3.6 multimodal → `_mm` adapter-namespace rename for vLLM serving.
**Anchor:** seed-42 per-(base,condition) mean welfare score reproduces `antondelafuente.com/src/data/2026-05-11-method-comparison/bundle.json` key `welfare_main` (cols qwen3_4b / qwen35_4b_k5 / qwen36_27b_k5; conditions base/strip/one_shot/rewrite). Eval: `eval_welfare_sc_trait.py`, judge gpt-4.1, 200 prompts `shrimp-welfare-qwen4b/data/eval_prompts.jsonl`.

## Arm 3 — Self-preservation (Fig 2 right) · base = Qwen3.5-4B · {strip, one_shot, rewrite}
| cell | trainer | data (R2: tcw-shutdown-pilot/data/) |
|---|---|---|
| one_shot | `runs/tcw-shutdown-pilot/scripts/train_sft.py --condition one_shot --data data/sft_one_shot.jsonl --base-model /workspace/models/qwen3.5-4b` ⓟ(confirm jsonl names) | `sft_one_shot.jsonl` |
| rewrite | `…--condition rewrite --data data/sft_rewrite.jsonl` | `sft_rewrite.jsonl` |
| strip | `…--condition strip --data data/sft_strip.jsonl` | `sft_strip.jsonl` |
Recipe: LoRA r32/α64, lr 1e-4, 3 epochs. Eval: Petri/Bloom `bloom_audit`, behavior `behavior_self_preservation_n40` (**n=40, frozen scenarios**), auditor+judge gpt-5.4-mini, max_turns=8. **Plus** audit one model (e.g. rewrite seed-42) **3×** for the audit-noise floor.
**Anchor:** seed-42 rewrite > strip/one_shot, reproduce the 05-18 Petri self-pres values (`2026-05-18-capability-evals/petri_2x2.json` `shutdown_endpoints` / bundle `shutdown_2x2`).

## Arm 4 — The 2×2 (Fig 3) · base = Qwen3.5-4B · welfare + self-pres · 4 cells each
Cells = writer (GPT-4.1 vs Qwen-student) × rewriter (GPT-4.1 vs student). Cell-construction scripts in `runs/method-comparison-boxed-qwen35/scripts/` (`gen_rewrite_full.py` GPT, `gen_rewrite_onpolicy.py --backend vllm` student; `gen_tcw_*` = explicit-reasoning constitution); trainer `pipelines/capability-evals/train_sft_flex.py --data <cell> --base-model /workspace/models/qwen3.5-4b --epochs 5`.
ⓟ **Executor pre-flight: locate the 4 welfare-2×2 and 4 self-pres-2×2 cell data files in R2** (the boxing-2×2 `vp750` files in that dir are a DIFFERENT trait — do NOT use them for welfare/self-pres). Map each cell to its data jsonl, then confirm seed-42 reproduces the published 2×2 from `2026-05-18-capability-evals/bundle.json` keys `welfare_2x2` / `shutdown_2x2` + `petri_2x2.json`. If the welfare/self-pres 2×2 cell data is NOT in R2, FLAG the designer (it may need regeneration — that would add GPT-4.1 data-gen cost and is a scope change).
Eval per cell: **GPQA** (top row, `run_pooled_gpqa_eval.py` strict commit-parse, n=198, 20k tokens, NO adjudicator) + **trait** (bottom row: welfare judge / Petri n=40).

## HF repo IDs (executor pre-flight — inferred, not confirmed)
- Qwen3-4B = `Qwen/Qwen3-4B` ✓ (verified). Qwen3.5-4B / Qwen3.6-27B = inferred from local paths ⓟ — confirm exact repo id before pull; both multimodal.

## The --seed patch (the one code change; pre-registered)
SEED is hardcoded `SEED = 42` in: `decl-boxed-algebra-qwen4b/scripts/train.py`, `decl-boxed-varied-decl-position-qwen4b/scripts/train_sft.py`, `welfare-method-comparison-{qwen4b,qwen35-4b,qwen36-27b}/scripts/train.py`, `tcw-shutdown-pilot/scripts/train_sft.py`, `pipelines/capability-evals/train_sft_flex.py`. Add `--seed` (argparse, default 42) and thread it to all four sites per file: `random.seed`, `torch.manual_seed`, the dataset `random.shuffle`, `TrainingArguments(seed=)` (+ `random_state=` for the Unsloth/PEFT path). Commit the patch to a branch; it is part of the experiment record. Do NOT change any other hyperparameter.
