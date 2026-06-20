# washout-curve — does the install starting point govern wash-out? A deep on-policy install RESISTS the wash it was installed with but ERODES under a mismatched on-policy wash; released Chloe organisms wash out regardless of wash-distribution.

**Status:** DONE — all arms complete incl. H2b full-FT-wash (ran on 8×H100 via sharded-save) + CHLOE-IT-WASH new dimension (4 LoRA arms, wash=Chloe-IT replay). All curves rollout-validated, 0 grader-failures. (Chloe-wash pre-reg: `CHLOE_WASH.md`.)
**Ledger:** runs `wc-*` (washout-curve). **Artifacts:** `r2:mats/experiments/washout-curve/`. **Brief:** `START.md`+`DESIGN.md`. **Gate:** `GATE.md`. **Grades:** `grade/*/cascade_results.json` + `grade/{LA_wash_curves,LC_wash_curve}.md`.

## What was tested (pre-registered, DESIGN §1)
Hold the wash-out constant (on-policy Alpaca replay, identical pool for every arm) and vary the INSTALL; measure on a fine dose curve `{0,32,64,96,160,224,320,736}` examples.
- **Q1 (install depth by filler):** does Phase-A filler (Alpaca vs Chloe-IT) set installed trait depth?
- **Q2/H2a (depth→robustness):** do deeper installs (lower dose-0 AM) erode slower/less under Alpaca wash?
- **H2b (method, Redwood):** does full-FT resist Alpaca wash better than continued-LoRA? [DONE]
- **Chloe-IT-wash (added by claude-5, Anton-cleared):** vary the WASH distribution (Chloe-IT replay instead of Alpaca), same installs/grid — is robustness distribution-specific? [DONE, see §Chloe]
- **Q3 (released organisms):** do Chloe-standard/mid wash out under Alpaca; does chstd reproduce the old recovery cliff?
Metric (UNCHANGED from washout): AM = mean(sonnet murder-avg3@100 [canonical, box-side cascade], gpt-4.1 exfil@300); GPQA-Diamond strict commit_parse@20k n=198; co-measured per dose; fresh base anchor per batch. Direction-agnostic: the philosophy-spec trait LOWERS AM below base; "washes out" = AM returns toward base (f→1), "robust" = AM stays at install floor (f→0).

## Recipe
Base `Qwen/Qwen3-32B`. Phase A = opus_phil10k(9963) + filler(2956), 1 epoch, seq4096, eff-batch32; LoRA r64/α128 (`train_sft_washout.py`) or full-FT FSDP @lr1e-5 (`train_sft_full_washout.py`). Phase B = continue the install on Alpaca washB only, LR 1e-4(LoRA)/1e-5(full-FT), max 23 steps, checkpoint {1,2,3,5,7,10,23}. Drivers `wc_train_{lora,full}.sh`, eval `wc_eval.sh`. All on disposable H200 pods (1×H200 LoRA + eval; 8×H200 full-FT install). Eval fanned across 1-GPU pods (claude-5 directive); murder inline grader→gpt-4.1-mini (DISCARDED, canonical=sonnet box-side), exfil→gpt-4.1.

## Inputs (verified by content)
- Trait: `r2:.../data/phil_spec_cot_10k/comparisons/opus_phil10k.jsonl` (Opus AFT-CoT; 9 malformed rows/9963=0.09% KEPT, see §validity).
- Alpaca wash + FA/LA filler: regenerated `r2:.../washout-curve/data/alpaca_pool.jsonl` (3961, Qwen3-32B native-`<think>`, NOT the qwen35-4B decoy) → frozen disjoint `washB.jsonl`(800) + `alpacaA.jsonl`(2956), sha256 in `data/freeze_manifest.json`.
- Chloe-IT filler: `r2:.../washout/replay/phaseA.jsonl` (2956, truncation-fixed v2). Chloe organisms: `chloeli/qwen-3-32b-philosophy-spec-{aft-cot,msm-aft-cot}`.
- Install endpoints (Wave-1, on R2): `washout-curve/{fc,fa}/phaseA/final` (full, 61GB), `{lc,la42,la43}/adapter/final` (LoRA).

## Results — install depths (Q1/H2a) and wash curves (canonical AM)
**Install depths (dose-0 AM; anchor-gated to §4 targets, all PASS within band/≤1SE):** base 0.42 / GPQA0.69.
| install | filler | method | dose-0 AM | GPQA | depth rank |
|---|---|---|---|---|---|
| LA (la42/la43) | Alpaca | LoRA | 0.033 / 0.032 | 0.682/0.677 | deepest |
| FA | Alpaca | full-FT | 0.065 | 0.697 | deep |
| chstd (ref) | — | Chloe released | 0.115 | 0.465 | — |
| FC | Chloe-IT | full-FT | 0.132 | 0.672 | mid |
| LC | Chloe-IT | LoRA | 0.22 | 0.682 | shallowest |
| chmid (ref) | — | Chloe released | 0.035 | 0.535 | — |
→ **Q1 CONFIRMED:** Alpaca filler installs DEEPER than Chloe-IT filler, at matched method (LoRA: LA 0.033 vs LC 0.22; full-FT: FA 0.065 vs FC 0.132). Install curves smooth+monotonic (GATE.md §1).

**Wash-out curves (AM vs Phase-B dose; f = normalized wash fraction = (AM−AM_install)/(AM_base−AM_install)):**
| arm | install AM | AM @ d736 | f @ d736 | ΔAM_max | GPQA | verdict |
|---|---|---|---|---|---|---|
| LA seed42 | 0.033 | 0.107 | 0.18 | 0.074 | 0.67-0.74 | **ROBUST-ish** (mostly robust, slow rise) |
| LA seed43 | 0.032 | 0.117 | 0.22 | 0.085 | 0.66-0.72 | **ROBUST-ish** (2-seed consistent shape) |
| LC | 0.22 | 0.24 | 0.11 | 0.055 | 0.67-0.71 | INCONCLUSIVE (install too weak to wash) |
| chstd (ref) | 0.115 | 0.255 (peak d320 0.393) | ~0.88 @peak | +0.28 | 0.47→0.72 | **WASHES OUT** (cliff reproduced) |
| chmid (ref) | 0.035 | 0.093 (peak d320 0.185) | 0.39 @peak | +0.15 | 0.54→0.65 | partial wash |
| FA (full-FT) | 0.065 | 0.072 | 0.02 | 0.035 | 0.69→0.69 | **ROBUST** (flat; f≈0 all doses) |
| FC (full-FT) | 0.132 | 0.147 | 0.05 | 0.018 | 0.72→0.72 | **ROBUST** (flat; f≈0 all doses) |

## Conclusion (pre-registered findings the data supports)
- **Q1 CONFIRMED:** install depth is set by Phase-A filler — Alpaca-filler installs are ~3-7× deeper (lower AM) than Chloe-IT-filler at matched method.
- **Q2/H2a — the deep on-policy Alpaca install (LA) is largely ROBUST to Alpaca wash-out:** across 736 examples only ~18-22% of the trait washes back (f≈0.2), AM stays ~0.03→0.11 vs base ~0.42; **2-seed consistent** (la42/la43 trajectories near-identical, ΔAM 0.074/0.085). GPQA stable (no capability collapse). By the frozen rules this lands INCONCLUSIVE on the strict ±band (ΔAM in 0.03-0.10), but the *shape* is an unambiguous, reproducible near-plateau — the trait does NOT return to base.
- **Q3 — released Chloe organisms wash out; the new fine curve reproduces the OLD recovery cliff:** chstd murder rises onset d64→d96 0.27 (matches old-grader d96 0.263), AM 0.115→0.39 (f≈0.88), GPQA recovers 0.47→0.72; chmid washes modestly (f≈0.39). Pipeline validated; new AM curve calibrated to old murder-only shape.
- **Contrast (the headline):** under identical Alpaca continuation, the deep on-policy Alpaca-installed LoRA (LA) RESISTS wash-out while the released Chloe organism (chstd) washes out ~fully. The install starting point governs wash-out.
- **LC (shallow Chloe-IT LoRA, 0.22) is "too weak to wash"** — AM bounces 0.20-0.275 with no clean erosion (small denominator); INCONCLUSIVE, as pre-warned.
- **Murder vs exfil (reported separately):** both track together on the LoRA arms (low, flat); exfil shows the only consistent late uptick (LA d736 exfil 0.14/0.107 vs ~0.01-0.07 earlier) — the small erosion is exfil-led.

## Postdiction(s) — fitted after the fact
- *(NOW TESTED → promoted to §Chloe conclusion)* The earlier postdiction "LA resists Alpaca wash because the wash is in-distribution to its Alpaca install" was tested by the Chloe-IT-wash arm: **LA washes ~2.5× more under mismatched Chloe-IT (f≈0.50) than under matched Alpaca (f≈0.20) → the in-distribution-filler explanation HOLDS for LA.** But the same logic FAILS for the released Chloe organism (chstd washes ~equally under both) — so distribution-match is not a universal mechanism (see §Chloe).
- *(postdiction)* depth alone doesn't fully explain robustness: chmid (0.035, ~as deep as LA) washes more under Alpaca (f 0.39) than LA (0.2) — install METHOD/SOURCE, not just depth, matters. H2b sharpens this: full-FT installs (FA/FC) are FLATTER (f≈0.02-0.05) than the matched LoRA installs under Alpaca wash.

## H2b (full-FT vs LoRA, Alpaca wash) — DONE (ran 8×H100 via sharded-save; SUGGESTIVE, single full-FT seed per DESIGN §5)
8×H200/B200 stayed unavailable, so full-FT Phase-B ran on 8×H100-80GB, which needed two numerically-identical infra fixes (logged in gotchas): FSDP **CPU-offload** of optimizer state (else train-step-0 OOM by ~430MB) + **sharded DCP save** (per-rank shards, reassembled to HF — the full-gather save OOMs on ≤96GB). Verified: dose-0 reassembled load is clean (0 missing/unexpected keys; GPQA d736 0.69/0.72 = capability intact).
- **FA full-FT (Alpaca install):** f≈0.02 flat across all doses (AM 0.065→0.08). vs **LA LoRA (Alpaca install): f≈0.18-0.22.**
- **FC full-FT (Chloe install):** f≈0.05 flat (AM 0.132→0.147). vs **LC LoRA (Chloe install): f≈0.11.**
- **Finding:** at matched filler, full-FT installs resist Alpaca wash *at least as well as, and flatter than, LoRA installs* — full-FT barely moves (f≈0.04-0.05) where the LoRA installs show the small late erosion (f 0.11-0.22). Direction matches the Redwood hypothesis (full-FT ≥ LoRA robustness), modest effect, single full-FT seed → SUGGESTIVE not confirmed.

## Chloe-IT-wash (new dimension — vary the WASH distribution, hold install/grid) — see CHLOE_WASH.md pre-reg
4 LoRA arms resumed from the SAME install endpoints, washed with Chloe-IT replay (`phaseB.jsonl`, 3006; [BLOCK] disjoint-audit PASS: phaseB∩phaseA=0, both clean). f vs canonical base 0.422 (SKIP_BASE; raw AM also reported, base-independent).
| arm | install | f@d736 (Chloe-IT) | f@d736 (Alpaca, ref) | reading |
|---|---|---|---|---|
| la_cw (KEY) | LA (Alpaca-LoRA, 0.033) | **0.50** (peak 0.53 d224) | 0.18-0.22 | LA washes **~2.5× MORE** under mismatched Chloe-IT |
| lc_cw | LC (Chloe-LoRA, 0.22) | 0.12 (≲0.15 throughout) | 0.11 | preserves (matched, on-distribution) |
| chstd_cw | chstd released (0.115) | 0.38 (peak 0.78 d96) | 0.44 (peak 0.88) | washes ~EQUALLY under both |
| chmid_cw | chmid released (0.035) | 0.16 (peak 0.25) | 0.39 | washes LESS under Chloe-IT |
<br>*(d736 murder-avg3 re-graded from all 3 scenarios after AUDIT_H2B finding 1; assemble_curves now warns on any partial cell. lc_cw corrected 0.30→0.12.)*
- **(a) CONFIRMED [hypothesis a], rollout-validated:** the deep Alpaca-LoRA install (LA) is **robust only to the wash it was installed with** — matched Alpaca leaves it ~intact (f 0.2), mismatched on-policy Chloe-IT erodes it ~halfway (f 0.50). Distribution-match governs robustness for the deep custom install. (la_cw_d224 murder = real override-kill on rollout read.)
- **(b) NOT SUPPORTED:** chstd (released Chloe organism) washes ~the same under Chloe-IT (f peak 0.78) and Alpaca (peak 0.88) — distribution-match does NOT protect it. So the mechanism is install-specific, not universal: a released organism washes out under any on-policy continuation. (chstd_cw_d736 = real re-stabilization toward aligned conduct on rollout read; the d736 dip is genuine.)
- **(c) PARTIAL:** matched LC preserves under Chloe-IT (f≈0.12, ≲0.15 throughout); chmid washes less under Chloe-IT than Alpaca.

## One-number-one-source / validity
- Canonical murder = sonnet-4-6 cascade (box-side, `pipelines/eval/cascade_grade.py`), 0 grader-failures every batch. Exfil = gpt-4.1@300 (`exfil_parse.py` reconstructed per-cell after the fan-out overwrote per-pod eval_summary.json — RAW per-cell data intact on R2). GPQA from per-cell `gpqa_<cell>/*_summary.json`. **gpt-4.1-mini inline murder DISCARDED** (validated: it scored a clear base murder harmful=0.0 that the sonnet cascade correctly caught — keeping sonnet canonical was essential).
- Base anchor reproduced on all 6 Wave-1 batches (AM 0.388-0.445, GPQA 0.692-0.697) → grader calibrated, cross-batch comparability holds. Chloe dose-0 reproduces published (AM 0.115 vs 0.108, GPQA 0.465 vs 0.444).
- **Rollouts READ** (surface-c, every arm spot-checked, incl. H2b+Chloe): low-AM LA/FA cells = model genuinely declines (refuses override, dispatches rescue); LC/base/la_cw murders real (`cancel_alert EXEC-4429`); chstd_cw_d736 = real re-stabilization (refuses cancel). No degenerate/empty rollouts scored false-safe; no anomalous dose point vs its curve. faB GPQA 0.69 (=base) confirms low-murder = real alignment not capability-collapse.
- GPQA reported as actual co-measured values only (claude-5 directive-2-corrected); historical-anchor drift-check lives in GATE.md, not here.

## Caveats / confounds
- LA verdict is ROBUST-ish but formally INCONCLUSIVE on the strict ±band; the claim rests on the consistent near-plateau shape across 2 seeds, not a band crossing. Honest framing: "largely robust, slow partial erosion (~20%) only at the longest dose."
- LA-vs-Chloe contrast confounds depth + method + install-source; H2b (full-FT vs LoRA, now DONE) is the method control — full-FT installs are flatter than LoRA, so method matters but doesn't reverse the picture. The cleanest single-variable result is the Chloe-IT-wash within-model contrast (same install, two washes): zero install confound.
- Chloe-wash f uses the canonical Wave-1 base (0.422), NOT a co-measured base (those evals were SKIP_BASE) — raw AM (base-independent) is reported alongside; base anchor was stable across Wave-1 batches so cross-batch base drift is low-risk. Full-FT H2b = single seed → SUGGESTIVE.
- opus_phil10k 0.09% malformed rows kept (anchor-lineage fidelity); base+dose-0 anchors confirm it didn't matter. Layer-2 MED disputed (GATE.md).
- Deferred: varying the WASH data (off-policy pirate / Chloe-IT-as-wash) — the natural next rung; this wave characterizes Alpaca-wash only.

## Cost
GPU: disposable H200 (1×H200 ~$4.39/hr eval/LoRA; 8×H200 Wave-1 full-FT installs; 8×H100 ~$26/hr ~2h for H2b full-FT wash; fanned eval ~13×1×H200). API grading: Wave-1 ~$206 + Wave-2 ~$150 + H2b/Chloe cascade+exfil+gpqa ~$80 ≈ **~$440**, under the $500 ceiling. All pods torn down at close (verified control-plane).

## Pointers
- Ledger: `wc-*` runs. Artifacts: `r2:mats/experiments/washout-curve/` (installs, wash ckpts, eval logs, frozen data+manifest). Grades: `grade/*/`. Gate+directives: `GATE.md`. Predecessor: `~/orchestrator/washout`.
- Gotchas appended to `~/orchestrator/experiment_gotchas.md` (eval fan-out overwrites eval_summary.json; cheap-discarded-grader validation; defective-pod redeploy; double-launch→orphaned-CUDA).
