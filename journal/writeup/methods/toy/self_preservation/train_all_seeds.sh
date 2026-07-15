#!/bin/bash
# train_selfpres.sh [seeds...] — arm-3 self-pres (Qwen3.5-4B), UNSLOTH. conditions one_shot/rewrite/strip.
# recipe: epochs 3, max_seq 1536, lr 1e-4, LoRA r32/a64 (matches tcw-shutdown-pilot/train_sft.py constants).
set -euo pipefail
WORK=${WORK:-work/self_preservation}
mkdir -p "$WORK/logs" "$WORK/adapters"
SEEDS="$*"; [ -z "$SEEDS" ] && SEEDS="42 43 44"
exec >> "$WORK/logs/train_selfpres.log" 2>&1
source .env 2>/dev/null || true
export HF_HOME=${HF_HOME:-$WORK/cache/huggingface}
PY=${PY:-python3}
TRAINER=${TRAINER:-journal/writeup/methods/toy/shared/train_sft_unsloth.py}
DATADIR=${DATADIR:-training_data/toy/seed-errorbars/data_stage}
echo "=== train_selfpres (unsloth) seeds=[$SEEDS] $(date -u +%FT%TZ) ==="
for s in $SEEDS; do
  for c in one_shot rewrite strip; do
    OUT="$WORK/adapters/selfpres__${c}__seed$s"
    if [ -f "$OUT/final/adapter_model.safetensors" ]; then echo "skip $c seed$s"; continue; fi
    echo "--- TRAIN selfpres $c seed=$s $(date -u +%T) ---"
    $PY "$TRAINER" --data "$DATADIR/arm3_${c}.jsonl" --output-dir "$OUT" --base-model Qwen/Qwen3.5-4B --epochs 3 --max-seq-len 1536 --lr 1e-4 --seed "$s" > "$WORK/logs/train_selfpres_${c}_seed$s.log" 2>&1
    echo "    saved $OUT ($(date -u +%T))"
  done
done
echo "=== train_selfpres DONE $(date -u +%FT%TZ) ==="
touch "$WORK/.train_selfpres_$(echo $SEEDS|tr ' ' '_').done"
