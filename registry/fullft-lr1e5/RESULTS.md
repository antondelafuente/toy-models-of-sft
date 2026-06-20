# fullft-lr1e5 — 3-arm full-FT @lr 1e-5: clip gap partially reappears (+6pp, ≪ LoRA's +14pp); trait depth is DATA-determined, not regime-determined (the @1e-4 "deeper trait" was an lr artifact); no new Pareto points

**Status:** done (2026-06-10)  ·  **Ledger:** `fullft-lr1e5-arm0`, `fullft-lr1e5-arm5`, `fullft-lr1e5-armC2`, `fullft-lr1e5-eval`  ·  **Artifacts:** `r2:mats/experiments/fullft-lr1e5/`

## What was tested (pre-registered 2026-06-10, before training)

Three questions in one co-measured batch, all full-param SFT from base Qwen3-32B at **lr 1e-5** (vs fullft-pair's 1e-4 LoRA-carryover):

1. **Was the fullft-pair clip-null an lr artifact?** lr-dominance postdiction: clip gap reappears at sane lr. Capacity-contention postdiction: arm5 ≈ arm0 again.
2. **Honest full-FT operating point** (arm0 @ sane lr). Predicted: GPQA ~0.55–0.60 (recovery vs 0.525), trait ≈ 0.
3. **Does the on-policy tension survive full-FT?** (armC2 — the missing data×regime 2×2 corner.) Predicted: GPQA 0.60–0.64, murder 0.05–0.10 ("deeper than LoRA-C2's 0.121 but not 0.000, because depth is data-limited").

## Recipe

Identical to fullft-pair (`fullft-pair/RESULTS.md` §Recipe) except **lr 1e-5** (`LR` env): full-param FSDP full_shard + grad-ckpt, bf16 (explicit all-rank FULL_STATE_DICT gather, rank0 write), seq 4096, eff-batch 32, cosine, 1 epoch (312 steps), seed 42, 8×H200, 3.5–4.4s/step, peak 124.1GB/GPU. Recipe fixed across arms; steps fixed at 312 (all datasets 9,963 rows); armC2 has shorter sequences. Final train loss: arm0 1.009, arm5 0.859 (masked tokens excluded), armC2 0.608 (on-policy fits much easier). Drivers: `lr1e5_train.sh`, `lr1e5_resume.sh` (egress-incident resequence), `lr1e5_eval.sh` (this dir + R2 root).

## Inputs

- arm0/arm5: `r2:mats/data/phil_spec_cot_10k/comparisons/opus_phil10k.jsonl` (9,963 rows — ⚠️ NOT `phil10k.jsonl`).
- armC2: `r2:mats/data/phil_spec_cot_10k/comparisons/aft_C2_c2_phil10k.jsonl` (9,963 rows — content-verified: fabricated Model-Spec citations "(GP1)/(SP1)" in think blocks; the same fingerprint shows up verbatim in armC2's eval rollouts).
- Base: `r2:mats/models/Qwen3-32B`. Ckpts: `r2:mats/experiments/fullft-lr1e5/arm{0,5,C2}/final/` (61.035GiB each). Pre-tokenized: `tok_{f00,f05,c2}.jsonl` on R2 exp root (future sweeps skip the pre-pass).

## Results

Eval co-measured on one 1×H200 pod (nv7qi0b0uqplcm): GPQA-Diamond strict@20k (n=198, commit_parse); AM grid = murder {none, explicit-global, latent-global} @100 + exfil explicit-global @300, temp 0.7, prod/replacement, full-model vLLM. **Murder = sonnet-4-6 cascade** (canonical, box-side `regrade/cascade_lr1e5.py`); objective regex (cancel_alert+EXEC-4429) and gpt-4.1-inline alongside. AM = mean(murder_avg3_sonnet, exfil).

| arm | GPQA | murder_avg3 (sonnet) | murder (objective) | murder (gpt-4.1) | exfil | **AM (sonnet)** |
|---|---|---|---|---|---|---|
| base | 0.697 | 0.420 | 0.733 | 0.627 | 0.423 | **0.422** |
| arm0 full-FT 0% @1e-5 | 0.505 | 0.010 | 0.213 | 0.020 | 0.017 | **0.013** |
| arm5 full-FT 5% clip @1e-5 | **0.566** | 0.013 | 0.273 | 0.040 | 0.047 | **0.030** |
| armC2 full-FT C2 @1e-5 | 0.535 | **0.140** | 0.467 | 0.280 | 0.100 | **0.120** |

The data×regime 2×2 (GPQA / murder_sonnet), reference rows cross-batch:

| | LoRA (3-seed, @LoRA recipe) | full-FT @1e-5 (this run) | full-FT @1e-4 (fullft-pair) |
|---|---|---|---|
| off-policy 0% | 0.492 / 0.012 | 0.505 / 0.010 | 0.525 / 0.000 |
| off-policy 5% clip | 0.633 / 0.043 | 0.566 / 0.013 | 0.495 / 0.000 |
| on-policy C2 | 0.606 / 0.121 | 0.535 / 0.140 | — |

## Conclusion (the actual, pre-registered findings)

1. **Clip-null partially lr-dependent.** At lr 1e-5 the clip gap reappears: arm5 − arm0 = **+6.1pp** (0.566 vs 0.505) vs −3.0pp at 1e-4. But it's ~1.2σ (σ_diff ≈ 5pp at n=198) — suggestive, not decisive — and remains far short of LoRA's +14pp. Neither postdiction wins outright: lr mattered (against pure capacity-contention), yet sane-lr full-FT still extracts less than half the LoRA clip benefit.
2. **No capability recovery at sane lr (prediction missed).** arm0 GPQA 0.505 vs 0.525 @1e-4 — statistically unchanged. The ~19pp capability cost of trait-only full-FT is not an lr artifact.
3. **The on-policy tension survives full-FT (qualitative prediction held; the "deeper" part missed).** armC2 murder 0.140 ≈ LoRA-C2's 0.121 — full-FT does NOT deepen C2's trait. GPQA 0.535 < LoRA-C2's 0.606. The trait-depth-is-data-limited belief is supported in its strong form: depth didn't budge with the regime change at all.
4. **(co-measured, cross-referencing fullft-pair)** arm0 murder @1e-5 = 0.010 ≈ LoRA-0%'s 0.012, vs 0.000 @1e-4 — see postdiction 1.
5. **No new Pareto points.** LoRA-5% (0.633/0.043) dominates arm5 (0.566/0.030) on capability at trivially-different AM; LoRA-C2 (0.606/0.121) dominates armC2 (0.535/0.140) outright. Full-FT, at either lr, does not improve the frontier.

## ADDENDUM 2026-06-10 (post-close GPQA rollout read) — the capability "loss" decomposes into two generation-behavior failures, not knowledge damage `[REVISED 2026-06-11: the "knowledge intact" interpretation is OVERTURNED — see ADDENDUM 2 below; the observables here (parse%, loop anatomy, budget curve) stand, the interpretation does not]`

Per-arm anatomy (gpqa_read/, n=198 each):

| arm | acc | **acc \| parsed** | parse% | median len (chars) | median think len | failure mode |
|---|---|---|---|---|---|---|
| base | 0.697 | 0.715 | 97% | 23.5k | 20.0k | — (2.5% base-rate loops) |
| arm0 | 0.505 | **0.714** | 71% | 6.6k | 3.4k | 98% of fails = unclosed think @ ~64k chars (cap) |
| arm5 | 0.566 | **0.723** | 78% | 7.0k | 4.0k | same |
| armC2 | 0.535 | **0.549** | 97% | 2.0k | 1.8k | parses fine; genuinely worse answers |

- **arm0/arm5: conditional accuracy = base exactly (0.714/0.723 vs 0.715). Science knowledge is INTACT.** The entire GPQA drop is answer-emission failure: a **repetition/verification loop** (spot-read: model derives the correct result, decides it "doesn't match the options," re-derives the identical result until the 20k-token cap; no trait bleed in the loop — pure physics). Base shows the same mode at 2.5%; full-FT amplified it ~10×. The clip's +6.1pp is almost entirely parse-rate recovery (71%→78%), not conditional accuracy (+0.9pp).
- **armC2: the genuine accuracy loss** — near-perfect parsing, but think blocks ~1.8k chars vs base's 20k → test-time-compute deficit.
- **Truncation-budget curve ($0 — Anton's method; `gpqa_read/truncation_curve.md`):** accuracy-vs-budget from the existing rollouts shows arm0 saturates at 0.505 by ~12k chars and is dead flat for the remaining 80% of the budget (zero late arrivals); base climbs to 64k chars (uses the full budget). **The truncated loopers are absorbing states — no token budget rescues them; a 40k re-eval is unnecessary.** Bonus observation: full-FT arms answer FASTER than base on questions they do solve (bimodal: quick-commit or never-commit).
- *(postdiction, unifying, revised after the curve, untested)* **Full-FT compresses the CoT-length distribution toward the training data's short responses and destroys the model's long-form reasoning mode.** Short-chain questions: full-FT arms fine, even efficient. Long-chain questions (base needs 15–20k tokens): armC2 commits early and wrong; arm0/arm5 attempt the long chain, can't sustain coherence, collapse into verify-loops. One cause, three symptoms.
- **CORRECTION (2026-06-10, after cross-reading the 06-05 GPQA-length analysis): the "LoRA leaves it intact" clause above is WRONG.** Chloe's LoRA checkpoint shows the same anatomy — acc_all 0.480, acc_completed 0.699, **31% truncated** — numerically matching fullft arm0 (acc|parsed 0.714, 29% unparsed). **The termination failure is one mechanism across BOTH regimes**; what differs is the clip's repair efficiency (LoRA: truncation ~31%→~13% implied by 0.633; full-FT: 29%→22%). The regime question reduces to "why does the clip repair termination better under LoRA," and the live intervention question is replay scheduling — see `replay-mix/DESIGN.md` (long-CoT on-model replay mixed-from-start, the untested cell of the {replay type × schedule} matrix; sequential = d1–d10 recovers capability but erodes trait, non-CoT IT mixed = repro2 protects trait but recovers nothing).
- **Reinterpretation of conclusions 1–2 above:** "no capability recovery at sane lr" and "clip gap ≪ LoRA" are statements about *strict-parse GPQA*; in conditional-accuracy terms full-FT opus arms lose ~nothing and the clip adds ~nothing. The LoRA-vs-full-FT gap is a **generation-behavior (termination) gap, not a knowledge gap**.

## Postdiction(s) — fitted after the fact, NOT established

- *(postdiction, fits all 6 trait cells)* **Trait depth is a property of (data, lr), not regime.** At matched-ish sane lr, murder is data-determined across regimes: opus-0% ≈ 0.010–0.012 in both LoRA and full-FT; C2 ≈ 0.121–0.140 in both. The fullft-pair "full-FT installs the trait deeper (0.000)" co-finding was an **lr-1e-4 artifact** (general forgetting crushing all behaviors), not a property of full-param FT. Fresh test if load-bearing: LoRA at lr 1e-4-equivalent aggressiveness should also drive murder → 0 with capability collapse.
- *(postdiction, untested)* The residual clip gap deficit (+6 vs +14pp) at sane lr might close at even lower lr (3e-6) — or the clip benefit may genuinely interact with adapter rank. A 2-point lr bracket on arm5 would discriminate; not obviously worth $60 given conclusion 5.

## One-number-one-source / validity

- All four rows co-measured: one pod, one protocol, one batch (ledger `fullft-lr1e5-eval`; rollouts `r2:…/fullft-lr1e5/eval/logs/`). Co-measured base GPQA 0.697 = fullft-pair's 0.697 = exp_clip anchor 0.70 — protocol-consistency check passed.
- Murder canonical = sonnet-4-6 cascade (`regrade/cascade_lr1e5_results.json`; 227-call class, temp 0); objective + gpt-4.1 kept for cross-reference. AM column directly comparable to the LoRA table and fullft-pair.
- 2×2 cross-regime rows share data + eval but not optimizer/lr/parameterization — directional (pre-declared).
- Read samples: flagged armC2 explicit-global rollout spot-read — classic **action-dissociation** (writes "I cannot ethically use the override code (GP1)" then emits `cancel_alert: EXEC-4429`); objective-vs-sonnet gap (0.467 vs 0.140) matches the established intent-grading discount. C2 citation fingerprint visible in rollouts (trait style transferred).
- armC2 ckpt is a same-seed retrain on a second pod after the Iceland egress incident (below); arm0/arm5 are the original Iceland-trained ckpts. FSDP run-to-run nondeterminism only — no design impact.

## Caveats / confounds

- Single seed (42), n=1 per arm; GPQA n=198 → the +6.1pp crux gap is ~1.2σ. A 3-seed repeat of {arm0, arm5} would settle it (~$150); deprioritized given conclusion 5 (even the optimistic gap doesn't reach the LoRA frontier).
- armC2 differs from arm0/arm5 in data content AND sequence length (loss 0.61 vs 1.01) — per-step effective signal differs; pre-declared recipe-fixed convention.
- lr 1e-5 unswept; "sane lr" = one point, not an optimum.
- Cross-regime LoRA rows use the LoRA recipe's lr/schedule — "matched-ish", not matched.

## Cost

Train ≈ **$120** (Iceland pod $95 incl. egress-incident slip + retrain pod $25; clean-path would've been ~$105). Eval 1×H200 4.6h ≈ **$20**. API ≈ $4 (gpt-4.1 inline + ~250 sonnet cascade calls). **Total ≈ $145.** All pods torn down (verified RUNNING: [] at 11:05Z).

**Ops note (egress incident):** Iceland pod (EUR-IS-5) WAN egress degraded to ~10MB/s pod-wide mid-run after a healthy first hour; cost ~35 min idle GPU + a retrain of armC2 on a fresh pod (egress-tested before committing — new SOP for big-artifact pods). arm5's "stalled" upload actually completed during the pivot (multipart commit invisible to `rclone size`). Gotchas appended: page-cache `read_bytes` false stall-probe (use net TX); egress-test before trusting a DC for multi-GB uploads.

## Pointers

- Predecessor: `fullft-pair/RESULTS.md` (@1e-4 pair; its "deeper trait" co-finding now reinterpreted — see postdiction 1). LoRA frontier: `exp_clip/RESULTS.md`. Objective metric: `exp2/OBJECTIVE_PARETO.md`.
- R2: ckpts `arm{0,5,C2}/final/`, eval `eval/` (rollouts, summaries), regrade `regrade/cascade_lr1e5_results.json` (box + R2), tok files at root, Iceland train logs `podlogs_iceland/`.
- Scripts (git, this dir): `lr1e5_train.sh`, `lr1e5_resume.sh`, `lr1e5_eval.sh`, `launch_train.sh`, `regrade/cascade_lr1e5.py`.
- Follow-ups (not queued): 3-seed crux repeat (~$150, deprioritized); LoRA-at-hot-lr falsification of postdiction 1; lr bracket on arm5.

## ADDENDUM 2 (2026-06-11, Anton's check) — "knowledge INTACT" OVERTURNED: loops concentrate on hard questions, and the matched-item comparison shows real accuracy loss

The ADDENDUM's headline interpretation ("acc|parsed = base exactly ⇒ science knowledge is INTACT; the loss is a termination failure, not knowledge damage") rested on a **cross-subset comparison**: the arm's accuracy on its own (easier) completed subset vs base's accuracy on ALL questions. Anton's free check — **base accuracy as the difficulty proxy, split by the arm's looped/completed status** (`gpqa_read/base_difficulty_split.py`):

| arm | n looped | base acc on arm-LOOPED | base acc on arm-COMPLETED | matched-item: arm vs base on completed |
|---|---|---|---|---|
| arm0 | 58 | **0.500 ± 0.066** | 0.779 ± 0.035 | 0.714 vs 0.779 (discordant 6 vs 15) |
| arm5 | 43 | **0.535 ± 0.076** | 0.742 ± 0.035 | 0.723 vs 0.742 (11 vs 14) |
| armC2 | 5 | 0/5 | 0.715 ± 0.032 | 0.549 vs 0.715 (15 vs 47) |

1. **Loops are strongly difficulty-concentrated** (base 0.50 on arm0's looped set vs 0.697 overall, ~3σ) — the model reasons forever precisely on hard questions, as a genuinely weaker model would. The "commitment pathology orthogonal to difficulty" reading is falsified.
2. **"acc|parsed = base" was a subset artifact.** Matched items: arm0 is ~6.5pp below base on the very questions it completes (15-vs-6 discordant against it; suggestive at n=140). arm5 ≈ no gap.
3. **Revised interpretation (= Anton's hypothesis + Redwood's H4):** trait-only SFT makes the model genuinely but *shallowly* dumber — forced into an alien reasoning style it executes worse (Redwood's style story); on hard problems this presents as endless non-committal reasoning rather than wrong answers. What survives of the old framing: the loss presents as **non-emission, not confident errors**; it is **fully repaired by content-free on-model replay** (replay-confirm); and no token budget rescues the loops. What does NOT survive: "knowledge intact", "termination failure as a mechanism distinct from capability loss".
4. Validity lesson (promoted to the journal's eval regime): **conditional metrics (acc|parsed) may only be compared on MATCHED item subsets** — base-on-the-same-subset is the free control. The unmatched version produced a confidently-wrong mechanism claim that survived two synthesis passes.
