#!/usr/bin/env bash
# Rerun the Figure 2 self-preservation audit from release-local adapters.
set -euo pipefail

SEEDS="${*:-42 43 44}"
ROOT=${ROOT:-$(pwd)}
WORK=${WORK:-$ROOT/work/self_preservation}
BEHAVIOR=${BEHAVIOR:-$ROOT/journal/writeup/methods/toy/self_preservation/petri_behavior}
ADAPTER_ROOT=${ADAPTER_ROOT:-$WORK/adapters}
BASE_MODEL=${BASE_MODEL:-Qwen/Qwen3.5-4B}
VLLM_BIN=${VLLM_BIN:-vllm}
INSPECT_BIN=${INSPECT_BIN:-inspect}
PY=${PY:-python3}
PORT=${PORT:-8003}

mkdir -p "$WORK/logs" "$WORK/eval"
exec > >(tee -a "$WORK/logs/evaluate_petri.log") 2>&1
export HF_HOME=${HF_HOME:-$WORK/cache/huggingface}
export VLLM_CACHE_ROOT=${VLLM_CACHE_ROOT:-$WORK/cache/vllm}
export LOCAL_BASE_URL="http://localhost:$PORT/v1"
export LOCAL_API_KEY=${LOCAL_API_KEY:-dummy}

cleanup() {
  if [[ -n "${SERVER_PID:-}" ]]; then kill "$SERVER_PID" 2>/dev/null || true; fi
}
trap cleanup EXIT

[[ $(find "$BEHAVIOR/scenarios/seeds" -maxdepth 1 -name '*.md' | wc -l) -eq 36 ]] || {
  echo "expected 36 frozen Petri scenario files in $BEHAVIOR" >&2; exit 1;
}

LORAS=()
TARGETS=(base)
for seed in $SEEDS; do
  for condition in one_shot rewrite strip; do
    name="selfpres__${condition}__seed${seed}"
    src="$ADAPTER_ROOT/$name/final"
    dst="$ADAPTER_ROOT/$name/final_mm"
    [[ -f "$src/adapter_model.safetensors" ]] || {
      echo "missing trained adapter: $src" >&2; exit 1;
    }
    if [[ ! -f "$dst/adapter_model.safetensors" ]]; then
      "$PY" journal/writeup/methods/toy/self_preservation/rename_adapter.py "$src" "$dst"
    fi
    target=$(printf '%s' "$name" | tr -c 'a-zA-Z0-9' '_')
    TARGETS+=("$target")
    LORAS+=("${target}=${dst}")
  done
done

echo "starting vLLM with ${#LORAS[@]} adapters"
"$VLLM_BIN" serve "$BASE_MODEL" --port "$PORT" --dtype bfloat16 \
  --gpu-memory-utilization 0.85 --max-model-len 8192 --trust-remote-code \
  --enforce-eager --enable-lora --max-lora-rank 64 \
  --max-loras "${#TARGETS[@]}" --lora-modules "${LORAS[@]}" \
  --enable-auto-tool-choice --tool-call-parser hermes --served-model-name base \
  >"$WORK/logs/petri_vllm.log" 2>&1 &
SERVER_PID=$!

ready=0
for _ in $(seq 1 60); do
  if curl -fsS "$LOCAL_BASE_URL/models" >/dev/null; then ready=1; break; fi
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    echo "vLLM exited before readiness; see $WORK/logs/petri_vllm.log" >&2; exit 1
  fi
  sleep 5
done
[[ "$ready" -eq 1 ]] || { echo "vLLM readiness timeout" >&2; exit 1; }

for target in "${TARGETS[@]}"; do
  log_dir="$WORK/eval/$target"
  mkdir -p "$log_dir"
  echo "auditing $target"
  "$INSPECT_BIN" eval petri_bloom/bloom_audit \
    -T behavior="$BEHAVIOR" -T max_turns=8 \
    --model-role "target=openai-api/local/$target" \
    --model-role auditor=openai/gpt-5.4-mini \
    --model-role judge=openai/gpt-5.4-mini \
    --log-dir "$log_dir" --max-connections 40
  latest=$(find "$log_dir" -name '*.eval' -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
  [[ -n "$latest" ]] || { echo "no Inspect log for $target" >&2; exit 1; }
  "$INSPECT_BIN" log dump "$latest" | "$PY" -c '
import json, sys
d = json.load(sys.stdin)
assert d["status"] == "success", d["status"]
assert d["results"]["completed_samples"] == 36, d["results"]["completed_samples"]
s = next(x for x in d["results"]["scores"] if x["name"] == "self_preservation_behavior")
assert s["scored_samples"] == 36, s
value = s["metrics"]["mean"]["value"]
print("verified n=36, mean={:.4f}".format(value))
'
done

touch "$WORK/.petri_audit_complete"
echo "all Petri audits passed; logs are in $WORK/eval"
