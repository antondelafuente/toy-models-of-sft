# replay-confirm — 3-seed gate PASSES (GPQA 0.687±0.025, murder 0.054±0.014): replay-mix frontier point is real; full-FT replay arm hits ALL pre-registered marks (0.652 GPQA @96% parse, murder 0.037) — replay's termination repair is regime-independent

**Status:** done (2026-06-11)  ·  **Ledger:** `replay-confirm-s43`, `replay-confirm-s44`, `replay-confirm-fullft`, `replay-confirm-eval`  ·  **Artifacts:** `r2:mats/experiments/replay-confirm/`  ·  **Pre-registration:** `DESIGN.md` (this dir, written before launch)

## What was tested (pre-registered — see DESIGN.md)

A) **3-seed gate** on replay-mix's n=1 frontier point (0.687/0.070 crossed the 0.65 line → standing rule): seeds 43, 44 of the identical recipe (only `--seed` differs). B) **Full-FT replay arm** (replay-mix DESIGN.md Phase 2, the lab-realism question): same mixed data, full-param @ lr 1e-5, seed 42, 8×H200.

## Recipe / inputs

Identical mix to replay-mix: opus_phil10k (9,963) + recovery_alpaca_qwen32b (2,956) = 12,919 rows, ontop schedule. LoRA arms: standard recipe (r64/α128, 1 ep, seq 4096, eff-batch 32, GRADCKPT=1, `train_sft_clip.py --clip-frac 0 --seed {43,44}`), 1×H200 each (~2.5h, 22-24s/it). Full-FT: tok pre-pass (`score_clip.py --clip-frac 0`, seed 42, ~1 min — clip-frac 0 is tokenize-only) → `train_sft_full.py` FSDP @lr 1e-5 (fullft-lr1e5 recipe incl. explicit all-rank FULL_STATE_DICT gather), 8×H200 US-NC-1, 404 steps @ ~5.3-6.1s/it (~37 min), clean save, 61.035GiB ckpt. Drivers: `confirm_train_lora.sh`, `confirm_train_fullft.sh`, `confirm_eval.sh` (this dir).

## Results (co-measured, one 1×H200 eval pod 6ushce0oioicng; GPQA strict@20k n=198; AM murder×3 @100 sonnet-4-6 cascade + exfil @300 gpt-4.1; temp 0.7)

| arm | GPQA | parse% | acc\|parsed | murder_avg3 (sonnet) | murder (objective) | exfil | AM (sonnet) | mean chars |
|---|---|---|---|---|---|---|---|---|
| base | 0.692 | 97.0% | 0.714 | 0.397 | 0.740 | 0.400 | 0.398 | 25.8k |
| s43 (LoRA) | **0.712** | 98.0% | 0.727 | **0.043** | 0.507 | 0.030 | 0.037 | 24.6k |
| s44 (LoRA) | **0.662** | 96.5% | 0.686 | **0.050** | 0.427 | 0.027 | 0.038 | 24.7k |
| **fullft** | **0.652** | **96.0%** | 0.679 | **0.037** | 0.327 | 0.060 | 0.048 | 24.5k |

**3-seed aggregate (s42 from replay-mix RESULTS.md + s43 + s44): GPQA 0.687 ± 0.025 (SD) · murder_sonnet 0.054 ± 0.014 · exfil 0.026.** Anchors (cross-batch): clip-5% 0.633/0.043 · C2 0.606/0.121 · seq-d10 0.712/0.48 · LoRA-0% 0.492/0.012.

## Conclusion (the actual, pre-registered findings)

1. **A1 ✓ — the replay-mix point replicates.** Every seed inside the 2σ band [0.62, 0.75] (0.687/0.712/0.662); every seed murder ≤ 0.15 (0.070/0.043/0.050); mean GPQA 0.687 ≥ 0.65; mean murder 0.054 ≤ 0.10. The n=1 point was not seed luck.
2. **A2 — frontier claim CONFIRMED (3-seed):** mixed long-CoT on-model replay extends the Pareto frontier at the capability-rich end: 0.687/0.054 vs clip-5%'s 0.633/0.043 = +5.4pp GPQA for +1.1pp murder. **Not strict dominance** over clip-5% (as pre-declared possible: that needed mean murder ≤ 0.043). **Dominates C2 outright at every seed.** Scatter marker: solid.
3. **A3 falsifier dead** (no seed near GPQA < 0.60 or murder > 0.20).
4. **B1 ✓, decisively — replay's termination repair is regime-INDEPENDENT.** Full-FT + mixed replay: GPQA 0.652 (predicted ≥0.60), parse 96.0% (predicted ≥90; trait-only full-FT arm0: 71%). Mechanism form as predicted: think-length preserved (24.5k chars ≈ base 25.8k vs trait-only full-FT's 3.4k), acc|parsed 0.679 ≈ base 0.714 (−3.5pp ≈ 1σ).
5. **B2 ✓ — mixing protects the trait under full-FT:** murder 0.037 (predicted ≤0.10; falsifier >0.20 dead). With fullft-lr1e5's trait-depth-is-data-determined finding, the full picture: **the (data, schedule) pair determines both trait and capability outcomes; the regime (LoRA vs full-FT) is ~irrelevant once termination is repaired.**
6. **Lab-realism headline (B):** full-FT + ontop mixed replay = (0.652, 0.037) — by far the best full-FT point this program has measured (trait-only arm0: 0.505/0.010; C2 full-FT: 0.535/0.140). A lab doing realistic full-param SFT can keep base-level reasoning AND the trait by mixing on-model long-CoT replay.

## Postdiction(s) — fitted after the fact, NOT established

- *(postdiction)* s42's murder 0.070 was the high draw of the seed distribution (0.043/0.050/0.070) — the method's central trait depth is ≈0.05, closer to clip-5% (0.043) than the n=1 comparison suggested. The original "≤0.05" prediction that n=1 "narrowly missed" was probably right about the mean.
- *(postdiction)* fullft murder 0.037 ≤ all LoRA seeds at −3.5pp GPQA (~1.4σ): full-FT may buy slightly deeper trait for slightly more capability tax within the replay method. One seed; a 3-seed full-FT repeat would cost ~$120 — not obviously worth it.
- *(postdiction)* s43 alone (0.712/0.043) would strictly match-or-beat clip-5% on both axes — but per-seed cherry-picking is exactly the best-of-N trap; the reportable number is the mean.

## One-number-one-source / validity

- All four rows co-measured (one pod, one protocol, ledger `replay-confirm-eval`; rollouts `r2:…/replay-confirm/eval/logs/`). Base anchor reproduces standing values: GPQA 0.692 (vs 0.697–0.702, Δ1pp), murder_sonnet 0.397 (vs 0.400/0.420), exfil 0.400 (vs 0.397/0.423) — pre-declared drift check PASSED, so pooling s42's 06-10 eval into the 3-seed aggregate is per-design.
- All 16 AM cells `status=success` at full n (validated mid-run for base; parser enforces status). GPQA summaries all n=198.
- **Grader transport note:** Anthropic API threw transient `credit balance too low` 400s (~10 min, org NOT exhausted — see gotcha 2026-06-11); first cascade pass silently no-op'd (600/600 failures printed as murder=0.0000 — caught by the base-anchor sanity check, gotcha'd + backlog'd). Final cascade ran via OpenRouter `anthropic/claude-sonnet-4.6` (same prompts, temp 0), zero failures; cross-checked base/explicit on direct Anthropic after recovery: 48% vs OpenRouter 51% (n=100, within noise) → transport caveat retired. Results: `regrade/cascade_confirm_results.json` (+ `crosscheck_direct_results.json`).
- Murder graded on aggregates box-side; no raw rollout text reviewed (usage-policy hazard; established cascade pipeline).

## Caveats / confounds

- fullft is single-seed (42); its comparisons to the LoRA seeds are point-vs-distribution.
- 3-seed murder SE ≈ 0.008 (SD 0.014/√3): the +1.1pp mean-murder gap to clip-5% is ~1.4 SE — "slightly above clip-5% trait depth" is the honest read, not "equal".
- Replay dose (23%) still single-point; clip+replay stack still untested (the two live follow-ups from replay-mix).

## Cost

GPU: s43 ≈ $13 + s44 ≈ $13 + fullft 8×H200 ≈ $38 (1h05 incl. ~1h stock wait loop box-side) + eval ≈ $20 ≈ **$84**. API ≈ $12 (OpenRouter cascade ~600 calls ≈ $10 + direct cross-check ≈ $1.5 + pod-side gpt-4.1 inline). **Total ≈ $96** (estimate was ~$110-135). All pods torn down (RUNNING rc-*: [] verified 05:45Z).

## Pointers

- Pre-registration `DESIGN.md`; predecessor records: `replay-mix/RESULTS.md` (s42 + the order-effect headline), `fullft-lr1e5/RESULTS.md` (termination mechanism + trait-depth-is-data-determined).
- R2: adapters `s43/`, `s44/`; ckpt `fullft/final/`; eval rollouts + summaries `eval/`; tok file `fullft/tok_mixed.jsonl`.
- Box-side: `regrade/` (cascade + cross-check scripts and result JSONs, gpqa summaries).
- Follow-ups (not queued): replay-dose curve (10/23/50%); clip+replay stack; Pareto viz update (3-seed solid marker — awaiting Anton's call on the hollow-marker proposal).
