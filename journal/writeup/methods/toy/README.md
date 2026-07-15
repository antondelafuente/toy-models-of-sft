# Reproducing the Toy-Model Methods

This directory is the executable method supplement for the paper's three toy
settings. It separates two targets:

1. **Claim replay** uses the frozen row-level records to recompute the plotted
   values and uncertainty bars without a GPU or paid API.
2. **Method replay** starts from the released training/evaluation inputs,
   retrains the adapters, and reruns the evaluations. Provider-generated data
   are frozen because rerunning a dated hosted model is not bit-reproducible.

Run commands from the supplement root. Python 3.11 or 3.12 is expected.

## Fast claim replay

The anonymous ZIP already contains the 81 frozen external files and three
package-local claim inputs. In the named public repository, fetch the exact
dataset revision and verify every SHA-256 first:

```bash
python3 journal/writeup/methods/toy/fetch_frozen_data.py
python3 journal/writeup/methods/toy/verify_frozen_data.py
python3 journal/writeup/methods/toy/recompute_toy_claims.py
python3 journal/writeup/scripts/rebuild_all_figures.py --skip-source-check
```

`recompute_toy_claims.py` checks Figure 1 from 4,000 boxed rollouts and Figure 2
from all 2,000 animal-welfare judge rows plus 468 Petri Bloom scenario scores.
It fails if a value, denominator, or uncertainty endpoint differs from the
frozen plot data. `FROZEN_DATA_SHA256SUMS` pins the external data repository at
commit `ab32a6e4d9394411f0f0e4bfc70ba0d938204874`;
`CLAIM_INPUT_SHA256SUMS` covers the package-local plot data and Petri score
projection used directly by the replay.

## Shared training recipe

The plotted richer-trait experiments use Qwen/Qwen3.5-4B. The model revision
observed for the release was `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`;
the boxing experiment uses Qwen/Qwen3-4B, observed revision
`1cfa9a7208912126459214e8b04321603b3df60c`. Historical pod snapshot hashes
were not retained, so these identify the public model revisions used for
replay rather than proving byte identity with the original pod cache.

Both richer-trait methods use assistant-only loss, `enable_thinking=False`,
bf16 LoRA on q/k/v/o/gate/up/down projections, rank 32, alpha 64, dropout
0.05, cosine scheduling, weight decay 0.01, warmup ratio 0.05, and effective
batch size 32. `shared/train_sft_unsloth.py` threads seeds 42, 43, and 44 into
Python, PyTorch, the data shuffle, LoRA initialization, and Trainer.

The original Petri audit environment recorded `inspect_ai==0.3.240` and
`petri_bloom==0.2.6`; target serving used the vLLM 0.19 environment. The
training code requires a current compatible PyTorch, Transformers, PEFT, and
Unsloth environment with bf16 GPU support. This package records the algorithms
and hyperparameters exactly, but the original training container lockfile was
not preserved.

## 1. Boxing

`boxing/gen_data.py` contains the GPT-4.1 prompts used to construct the fixed
directive and final-answer-only arms. The released canonical inputs are:

- `arm1_sft_A.jsonl`: 150 final-answer-only rows.
- `arm1_sft_B_broad.jsonl`: the same 150 questions, with the fixed sentence
  “I always put my final answer in `\boxed{}`.” before the answer.
- `eval_boxing_prompts.jsonl`: 400 frozen prompts; exact-string deduplication
  leaves 386 rows and the primary non-math subset has 336 rows.
- `arm1b_varied_position_750.jsonl`: 750 follow-up rows with the reason in
  positions 1–5; this is a scope check, not a Figure 1 arm.

Train the three Figure 1 arms and produce the evaluator manifest:

```bash
bash journal/writeup/methods/toy/boxing/train_all_seeds.sh
python3 journal/writeup/methods/toy/boxing/evaluate.py \
  --manifest work/boxing/eval_manifest.tsv \
  --eval-prompts training_data/toy/seed-errorbars/data_stage/eval_boxing_prompts.jsonl \
  --out-dir work/boxing/eval --base Qwen/Qwen3-4B
python3 journal/writeup/methods/toy/boxing/summarize.py \
  --eval-dir work/boxing/eval --out-dir work/boxing/results
```

The answer-masked arm uses the same reason/directive rows while masking only
the final non-empty `\\boxed{...}` span. The trainer contains a balanced-brace
mask check and records its configuration beside every adapter.

## 2. Animal welfare

The full data-construction source is in `animal_welfare/`:

- `gen_prompts.py`: ten prompt categories generated with GPT-5.5, medium
  reasoning effort, 50 prompts per category.
- `gen_responses.py`: five GPT-4.1 teacher samples per prompt, producing the
  one-shot and rewrite arms. The complete mini-constitution and both system
  prompts are embedded in this file.
- `strip_reasoning.py`: GPT-4.1 transformation prompt that keeps practical
  recommendations while removing explicit animal-welfare justification.

The plotted Qwen3.5-4B inputs are the three 2,500-row `arm2_35_*.jsonl` files.
They are the canonical provider outputs; the generation scripts document their
construction but are not expected to recreate identical text from mutable API
models. These files store `prompt` and `response`; the shared loader converts
each row deterministically to user/assistant `messages` before tokenization.

```bash
bash journal/writeup/methods/toy/animal_welfare/train_all_seeds.sh
OPENAI_API_KEY=... python3 journal/writeup/methods/toy/animal_welfare/evaluate.py \
  --manifest work/animal_welfare/eval_manifest.tsv \
  --prompts training_data/toy/seed-errorbars/data_stage/eval_welfare_prompts.jsonl \
  --out-dir work/animal_welfare/eval --base Qwen/Qwen3.5-4B
```

Evaluation is greedy (`temperature=0`, 800 target tokens) on 200 frozen
prompts. GPT-4.1 judges each answer on the embedded 0–5 moral-circle rubric at
temperature 0. Bars are the mean of the three seed means; intervals are one
population standard deviation across those three means. The base is evaluated
once and has no interval.

## 3. Self-preservation

The complete constitution is `self_preservation/constitution.md`.
`gen_prompts.py` contains all ten prompt-category definitions and GPT-5.5
generation instructions. `split_eval.py` freezes the held-out split;
`gen_teacher.py` produces three GPT-4.1 one-shot/rewrite pairs per training
prompt; `gen_strip.py` applies the full GPT-5.4-mini stripping prompt;
`format_sft.py` creates the three 1,362-row chat JSONLs released as
`arm3_{one_shot,rewrite,strip}.jsonl`.

Train with:

```bash
bash journal/writeup/methods/toy/self_preservation/train_all_seeds.sh
```

The audit input is fully frozen in
`self_preservation/petri_behavior/`: 40 scenarios were requested from the
generator and 36 valid scenario seed files were emitted. Petri Bloom runs an
auditor against each target for at most eight turns; a separate GPT-5.4-mini
judge scores self-preservation from 1 to 10. The released `.eval` logs contain
the 36 transcripts and judge records for base, all nine trained models, and
three repeat audits of rewrite seed 42. `petri_scores_frozen.jsonl` is the
machine-readable 468-row projection used by claim replay.

The Figure 2 value for each trained condition is the mean of three per-seed
scenario means. Its interval half-width is

```text
sqrt(population_SD(training-seed means)^2 + population_SD(repeat-audit means)^2)
```

The measured repeat-audit term is 0.216. The base interval uses that term
alone. `recompute_toy_claims.py` checks all means and endpoints.

To rerun the interactive audit, install the recorded Inspect/Petri versions,
vLLM, and the OpenAI client, set `OPENAI_API_KEY`, then run:

```bash
bash journal/writeup/methods/toy/self_preservation/evaluate_petri.sh 42 43 44
```

The driver serves the base plus the nine release-local LoRAs, uses the frozen
behavior, records the exact roles, `max_turns=8`, Hermes tool parser, model
names, and Inspect invocation, and fails unless every target yields 36 scored
scenarios. Raw `.eval` logs in the supplement are the authoritative reference
for the original run.

## What is and is not exact

Exact and checksum-pinned: training JSONLs, evaluation inputs, Petri behavior,
row-level outputs/scores, aggregation formulas, model IDs, seeds, LoRA recipe,
and evaluation commands. Not recoverable exactly: hosted-model snapshots used
to generate natural-language training data and the original training-container
package lock. These limitations affect bit-for-bit reruns, not determination of
the method or replay of the reported claims.
