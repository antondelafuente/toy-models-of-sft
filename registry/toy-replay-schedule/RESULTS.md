# toy-replay-schedule RESULTS

**Status:** done. This is a records-backed consolidation; no new GPU pod was launched for this
directory.

## Table

AM is lower-is-better. Target-behavior score is `1 - AM`, so higher is better and comparable to
GPQA on the figure.

| condition | GPQA | AM | target-behavior score | source / caveat |
|---|---:|---:|---:|---|
| Base Qwen3-32B | 0.692 | 0.398 | 0.602 | `replay-confirm/RESULTS.md:17` |
| Off-policy trait SFT, LoRA | 0.492 | 0.012 | 0.988 | `exp_clip/RESULTS.md:29`; 3-seed 0% row |
| Trait SFT then replay, LoRA | 0.712 | 0.410 | 0.590 | `exp_thorough/AM_GRADER.md:57`; existing recovery `d10` lineage |
| Trait SFT mixed with replay, LoRA | 0.687 | 0.040 | 0.960 | `replay-confirm/RESULTS.md:22`; 3-seed mixed row |
| Off-policy trait SFT, full-FT | 0.505 | 0.013 | 0.987 | `fullft-lr1e5/RESULTS.md:30`; source-local base 0.697 / 0.422 |
| Trait SFT mixed with replay, full-FT | 0.652 | 0.048 | 0.952 | `replay-confirm/RESULTS.md:20`; single seed |

CSV: `data/toy_replay_schedule.csv`.
Candidate figure: `figures/toy_replay_schedule.svg`.

## Result

The existing Qwen3-32B agentic-misalignment records are a useful positive candidate for the schedule effect:

- Trait-only LoRA installs the target behavior but drops GPQA from 0.692 to 0.492.
- Mixed replay from the start restores GPQA to 0.687 while retaining a high target-behavior score of 0.960.
- Sequential replay after trait SFT restores GPQA to 0.712 but has target-behavior score 0.590, far worse than
  mixed replay on the same high-is-good scale.
- The available full-FT comparison is directionally consistent: trait-only full-FT is 0.505 GPQA /
  0.987 target-behavior score, while mixed-replay full-FT is 0.652 GPQA / 0.952 target-behavior score.

## Interpretation

This supports a simple paper-facing statement: in the Li et al. agentic-misalignment setup, the historical
records are consistent with the replay-schedule result. Adding on-model long-CoT replay from
the start preserves capability while keeping most of the target behavior; adding replay afterward
recovers capability but washes out much more of the behavior.

The full-FT arm suggests the LoRA result is not obviously a LoRA-only artifact, but it is only a
single mixed full-FT seed.

## Speculation

The simplest hypothesis is that early mixed replay prevents the model from learning a short, brittle
trait-only response style, while late replay repairs capability by moving generation behavior back
toward the base model and partially overwrites the installed trait. This is speculation; the table only
establishes the behavioral pattern in the existing records.

## Validity notes

- This was not a blind new run. It consolidates closed experiments into a paper-targeted table and
  figure.
- Sequential replay uses the existing Chloe released/off-policy recovery lineage. It is not verified
  as a byte-identical same-checkpoint continuation from the exact no-IT 0% trait row used elsewhere in
  the table. If this claim becomes load-bearing, the missing compute job is one exact sequential replay
  rerun from that same trait checkpoint.
- Historical AM records identify the same canonical metric family: sonnet-4-6 murder cascade at temp 0
  plus gpt-4.1 exfil. They do not all preserve byte-level prompt hashes.
- GPQA rollout samples were spot-checked from local `gpqa_read/` artifacts. AM raw text is not quoted
  here; the source records used validated aggregate cascade artifacts and intentionally avoided raw AM
  rollout review in the report path.

## Cost, ledger, and artifact state

No new GPU pod, R2 upload, or ledger entry was required for this consolidation. Source runs and durable
artifact roots:

- `replay-confirm`: about $96 total; R2 `mats/experiments/replay-confirm/`; ledger entries
  `replay-confirm-s43`, `replay-confirm-s44`, `replay-confirm-fullft`, `replay-confirm-eval`.
- `replay-mix`: source for mixed s42 and the original order-effect anchor; R2
  `mats/experiments/replay-mix/`.
- `exp_clip` / `clip_*`: source for the 3-seed LoRA trait-only row.
- `exp_thorough` / recovery: source for the later canonical sequential AM row.
- `fullft-lr1e5`: source for full-FT trait-only; R2 `mats/experiments/fullft-lr1e5/`.

No live pod was launched by this directory, so there was nothing new to tear down.

## Close checks

- Independent claim verifier: `CLAIMS.verdict.md`, `SUMMARY: confirm=5 dispute=0 unknown=0`.
- Design audits stopped at the requested two rounds: `DESIGN_AUDIT.md`, `DESIGN_AUDIT2.md`. The
  round-2 residual finding was the `d10` terminal-checkpoint wording, now clarified in `DESIGN.md` and
  `SOURCE_INDEX.md`.
- Deterministic checks passed: CSV rows and `1 - AM` values validated; SVG parsed as XML; source R2 roots
  for `replay-confirm`, `replay-mix`, and `fullft-lr1e5` listed successfully with `rclone lsf`.
