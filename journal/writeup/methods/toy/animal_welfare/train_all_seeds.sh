#!/usr/bin/env bash
set -euo pipefail

PY=${PY:-python3}
BASE_MODEL=${BASE_MODEL:-Qwen/Qwen3.5-4B}
WORK=${WORK:-work/animal_welfare}
TRAINER=journal/writeup/methods/toy/shared/train_sft_unsloth.py
DATA=training_data/toy/seed-errorbars/data_stage
mkdir -p "$WORK/adapters" "$WORK/logs"

for seed in 42 43 44; do
  for condition in one_shot rewrite strip; do
    "$PY" "$TRAINER" --data "$DATA/arm2_35_${condition}.jsonl" \
      --output-dir "$WORK/adapters/${condition}_seed${seed}" --base-model "$BASE_MODEL" \
      --epochs 20 --max-seq-len 1024 --lr 1e-4 --seed "$seed" \
      >"$WORK/logs/${condition}_seed${seed}.log" 2>&1
  done
done

{
  printf 'base\t\n'
  for seed in 42 43 44; do
    for condition in one_shot rewrite strip; do
      printf 'welfare_35__%s__seed%s\t%s/adapters/%s_seed%s/final\n' \
        "$condition" "$seed" "$WORK" "$condition" "$seed"
    done
  done
} > "$WORK/eval_manifest.tsv"
echo "wrote $WORK/eval_manifest.tsv"
