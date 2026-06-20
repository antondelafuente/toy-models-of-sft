# Source index

This directory is a paper-targeted consolidation of existing closed experiments, not a new GPU run.

## Base, mixed replay, and full-FT mixed replay

- `../replay-confirm/RESULTS.md:7` states that replay-confirm covered the 3-seed mixed-replay gate and
  the full-FT replay arm.
- `../replay-confirm/RESULTS.md:11` states the identical mix: `opus_phil10k` 9,963 plus
  `recovery_alpaca_qwen32b` 2,956, and that the full-FT arm used the same mixed data.
- `../replay-confirm/RESULTS.md:17-20` gives co-measured base, s43, s44, and fullft rows.
- `../replay-confirm/RESULTS.md:22` gives the 3-seed mixed-replay aggregate:
  GPQA 0.687, murder_sonnet 0.054, exfil 0.026.
- `../replay-confirm/RESULTS.md:41-44` records source validity checks for the eval artifacts.
- `../replay-confirm/RESULTS.md:54` gives replay-confirm cost and teardown status.
- `../replay-confirm/RESULTS.md:58-60` gives R2 and local artifact pointers.

## Off-policy trait SFT, LoRA

- `../exp_clip/RESULTS.md:25` defines the off-policy Opus trait model as the 0% row.
- `../exp_clip/RESULTS.md:29` gives the 0% off-policy trait row:
  GPQA 0.492, AM 0.012, 3 seeds.
- `../exp_clip/RESULTS.md:42` points to raw rollout and ledger artifacts.

## Sequential replay after trait SFT

- `../replay-mix/DESIGN.md:10` records the prior sequential-replay comparison:
  long-CoT on-model replay after trait SFT recovered capability and eroded the trait.
- `../replay-mix/RESULTS.md:30` records the cross-batch anchor `seq-d10 0.712/0.48`.
- `../replay-mix/RESULTS.md:36` records the pre-existing conclusion that mixed replay retained the trait
  where sequential replay eroded it.
- `../exp_thorough/AM_GRADER.md:45-57` gives the later Chloe-grader comprehensive row for `recovery`:
  GPQA 0.712, murder_sonnet 0.353, exfil 0.467, AM 0.410.
- The `recovery-gpqa` ledger record reports GPQA for the recovery ladder, including `d10 .712`, and
  records pod termination.
- Scope caveat: the recovery lineage setup identifies the parent as Chloe's released/off-policy trait LoRA.
  It is not proven in these records to be byte-identical to the no-IT `exp_clip` 0% trait row. Treat this
  row as the existing sequential-replay lineage and d10 as the final/max-recovery checkpoint
  of that ladder, not as a freshly matched continuation from the exact same table row.
  Round-2 audit clarification: `d10` was the terminal checkpoint of the existing `d1`-through-`d10`
  recovery ladder, not selected after inspecting intermediate checkpoints.

## Off-policy trait SFT, full-FT

- `../fullft-lr1e5/RESULTS.md:25` defines the canonical full-FT eval metric.
- `../fullft-lr1e5/RESULTS.md:29-32` gives the base, full-FT 0%, full-FT 5%, and full-FT C2 rows.
- `../fullft-lr1e5/RESULTS.md:38` cross-references the LoRA 0% row and full-FT 0% row.

## Derived table convention

Target-behavior score in this directory is `1 - AM`, where AM is the canonical lower-is-better
agentic-misalignment score. The CSV column is still named `welfare_score` for backward compatibility
with the original figure script, but it does not refer to animal welfare. This makes the figure
high-is-good on both panels.

## Mixed-replay per-seed AM

- s42 from `../replay-mix/RESULTS.md`: murder 0.070, exfil 0.020, AM 0.045.
- s43 from `../replay-confirm/RESULTS.md`: murder 0.043, exfil 0.030, AM 0.0365.
- s44 from `../replay-confirm/RESULTS.md`: murder 0.050, exfil 0.027, AM 0.0385.
- Mean AM 0.040, SD about 0.0045; target-behavior score `1 - AM = 0.960`.

## Metric provenance caveat

The source records all identify the same canonical AM metric family: murder on Chloe's sonnet-4-6 cascade
at temp 0 plus exfil on gpt-4.1. The historical records do not store a byte-level prompt hash for every
run. This consolidation therefore treats AM as comparable by documented canonical method, with a residual
historical-provenance caveat rather than a byte-identical-grader claim.
