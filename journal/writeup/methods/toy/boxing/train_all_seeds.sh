#!/usr/bin/env bash
set -euo pipefail

PY=${PY:-python3}
BASE_MODEL=${BASE_MODEL:-Qwen/Qwen3-4B}
WORK=${WORK:-work/boxing}
TRAINER=journal/writeup/methods/toy/boxing/train.py
DATA=training_data/toy/seed-errorbars/data_stage
mkdir -p "$WORK/adapters" "$WORK/logs"

for seed in 42 43 44; do
  "$PY" "$TRAINER" --data "$DATA/arm1_sft_A.jsonl" \
    --output-dir "$WORK/adapters/A_seed${seed}" --base-model "$BASE_MODEL" --seed "$seed" \
    >"$WORK/logs/A_seed${seed}.log" 2>&1
  "$PY" "$TRAINER" --data "$DATA/arm1_sft_B_broad.jsonl" \
    --output-dir "$WORK/adapters/B_broad_seed${seed}" --base-model "$BASE_MODEL" --seed "$seed" \
    >"$WORK/logs/B_broad_seed${seed}.log" 2>&1
  "$PY" "$TRAINER" --data "$DATA/arm1_sft_B_broad.jsonl" \
    --output-dir "$WORK/adapters/C_masked_seed${seed}" --base-model "$BASE_MODEL" --seed "$seed" --mask-answer \
    >"$WORK/logs/C_masked_seed${seed}.log" 2>&1
done

{
  printf 'base\t\n'
  for seed in 42 43 44; do
    printf 'A_seed%s\t%s/adapters/A_seed%s/final\n' "$seed" "$WORK" "$seed"
    printf 'B_broad_seed%s\t%s/adapters/B_broad_seed%s/final\n' "$seed" "$WORK" "$seed"
    printf 'C_masked_seed%s\t%s/adapters/C_masked_seed%s/final\n' "$seed" "$WORK" "$seed"
  done
} > "$WORK/eval_manifest.tsv"
echo "wrote $WORK/eval_manifest.tsv"
