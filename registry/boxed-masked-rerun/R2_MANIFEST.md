# R2_MANIFEST - boxed masked-answer rerun

Verified: 2026-06-20

Artifact root: `r2:mats/experiments/boxed-masked-rerun/`

`rclone size`:

- total objects: 107
- total size: 2.316 GiB / 2,487,157,085 bytes

Top-level file counts from `rclone lsf --recursive --files-only`:

| prefix | files |
|---|---:|
| `adapters/` | 54 |
| `results/` | 28 |
| `logs/` | 13 |
| `meta/` | 8 |
| `data/` | 3 |
| `DONE.txt` | 1 |

Adapter coverage:

- `adapters/A/seed42/final/`
- `adapters/A/seed43/final/`
- `adapters/A/seed44/final/`
- `adapters/B_broad/seed42/final/`
- `adapters/B_broad/seed43/final/`
- `adapters/B_broad/seed44/final/`
- `adapters/C_masked/seed42/final/`
- `adapters/C_masked/seed43/final/`
- `adapters/C_masked/seed44/final/`

Each adapter directory contains:

- `README.md`
- `adapter_config.json`
- `adapter_model.safetensors`
- `chat_template.jinja`
- `tokenizer.json`
- `tokenizer_config.json`

Result coverage:

- `results/RESULTS_DRAFT.md`
- `results/figure1_plot_ready.csv`
- `results/figure1_continuity_400.csv`
- `results/per_seed_summary.csv`
- `results/mask_check.json`
- `results/eval/*_rollouts.jsonl`
- `results/eval/*_summary.json`
- `results/eval/all_summaries.json`
- `results/eval/condition_metrics.csv`
- `results/eval/eval_file_manifest.json`

Data coverage:

- `data/arm1_sft_A.jsonl`
- `data/arm1_sft_B_broad.jsonl`
- `data/eval_boxing_prompts.jsonl`

The pod was torn down after this verification. Ledger run `boxed-masked-rerun` records launch, running, driver-done, and torndown events.
