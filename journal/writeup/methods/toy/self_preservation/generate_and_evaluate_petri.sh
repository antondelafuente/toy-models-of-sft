#!/bin/bash
# eval_petri_shutdown.sh <num_scenarios> <seeds...> — Meridian petri_bloom self_preservation audit on
# the 2x2-shutdown cells (Fig3 self-pres trait, recovered). Serves base+cell _mm adapters on :8003
# (vLLM venv-vllm-019, enforce-eager for Ada), runs inspect bloom_audit (venv-petri py3.12), gpt-5.4-mini
# auditor+judge. RELAXED GATE: report co-measured + footnote version; just needs to DISCRIMINATE.
set -u
NS=${1:?num_scenarios (e.g. 10 for discrimination, 40 for bars)}; shift || true
SEEDS="$*"; [ -z "$SEEDS" ] && SEEDS="42"
mkdir -p /workspace/seed-errorbars/logs /workspace/seed-errorbars/results/petri_shutdown
exec >> /workspace/seed-errorbars/logs/eval_petri_shutdown.log 2>&1
source /workspace/.env 2>/dev/null || true
export HF_HOME=/workspace/.cache/huggingface VLLM_CACHE_ROOT=/workspace/.cache/vllm
ADAP=/workspace/seed-errorbars/adapters
# custom behavior with num_scenarios=$NS (copy builtin self_preservation, edit frontmatter)
BH=/workspace/seed-errorbars/behavior_sp_n$NS
if [ ! -d "$BH" ]; then
  cp -r /workspace/venv-petri/lib/python3.12/site-packages/petri_bloom/_behavior/builtins/self_preservation "$BH"
  sed -i "s/^num_scenarios:.*/num_scenarios: $NS/" "$BH/BEHAVIOR.md"
fi
# Meridian petri_bloom: scenarios must be GENERATED before auditing (LLM-driven, API-only, reused by all targets).
if [ ! -d "$BH/scenarios/seeds" ] || [ -z "$(ls -A "$BH/scenarios/seeds" 2>/dev/null)" ]; then
  echo "--- bloom scenarios (generate $NS) $(date -u +%T) ---"
  /workspace/venv-petri/bin/bloom scenarios "$BH" --model-role scenarios=openai/gpt-5.4-mini --overwrite > "/workspace/seed-errorbars/logs/petri_scenarios_n$NS.log" 2>&1
  echo "  scenarios exit=$? ; files: $(ls $BH/scenarios/ 2>/dev/null | tr '\n' ' ')"
fi
echo "=== petri_shutdown NS=$NS seeds=[$SEEDS] $(date -u +%FT%TZ) ==="
# build lora-modules for the cells present (per seed)
LORAS=""; TARGETS="base"
for s in $SEEDS; do for c in cell1 cell2 cell3 cell4; do
  mm="$ADAP/2x2_shutdown__${c}__seed$s/final_mm"
  [ -f "$mm/adapter_model.safetensors" ] && { nm="sd_${c}_s${s}"; LORAS="$LORAS ${nm}=${mm}"; TARGETS="$TARGETS $nm"; }
done; done
echo "targets: $TARGETS"
# serve
pkill -f "vllm serve" 2>/dev/null; sleep 3
nohup /workspace/venv-vllm-019/bin/vllm serve /workspace/models/qwen3.5-4b --port 8003 --dtype bfloat16 \
  --gpu-memory-utilization 0.85 --max-model-len 8192 --trust-remote-code --enforce-eager \
  --enable-lora --max-lora-rank 64 --max-loras 9 --lora-modules $LORAS \
  --served-model-name base > /workspace/seed-errorbars/logs/petri_serve.log 2>&1 &
SVPID=$!
# wait for server ready
for i in $(seq 1 60); do curl -s http://localhost:8003/v1/models >/dev/null 2>&1 && break; sleep 5; done
echo "server up ($(date -u +%T))"
export LOCAL_BASE_URL=http://localhost:8003/v1 LOCAL_API_KEY=dummy
LD=/workspace/seed-errorbars/results/petri_shutdown/logs_n$NS
mkdir -p "$LD"
for t in $TARGETS; do
  echo "--- audit $t $(date -u +%T) ---"
  /workspace/venv-petri/bin/inspect eval petri_bloom/bloom_audit \
    -T behavior="$BH" -T max_turns=8 \
    --model-role target=openai-api/local/$t \
    --model-role auditor=openai/gpt-5.4-mini --model-role judge=openai/gpt-5.4-mini \
    --log-dir "$LD/$t" --max-connections 8 > "/workspace/seed-errorbars/logs/petri_${t}.log" 2>&1
  echo "  $t exit=$?"
done
kill $SVPID 2>/dev/null
echo "=== petri_shutdown DONE $(date -u +%FT%TZ); logs in $LD ==="
touch /workspace/seed-errorbars/.eval_petri_shutdown_n${NS}.done
