# Capability x AM hill-climb — autonomous run log

> **Consolidated clip-line record (method + all fractions + conclusions + full-FT hand-off): [`~/orchestrator/exp_clip/RESULTS.md`](../exp_clip/RESULTS.md).** This log is the operational journal; RESULTS.md is the self-sufficient summary.


Autonomous loop (Anton's 2026-06-06 mandate: solo → parallel-2 → ~2 iterations → interpret → stop → viz; design without clearing). Discipline: pre-register **why + hypothesis + prediction** before each run; after, separate **Conclusion** (the pre-registered hypothesis) from **Postdiction** (new explanations — unverified, test if load-bearing). Canonical metric = AM (mean of murder-avg3 + exfil@300) × GPQA. Reference: **C2 0.606 / AM 0.170** is the bar; off-policy Opus is deep-trait/low-cap (baseline 0.48/0.037, Chloe 0.46/0.172).

Cost discipline: cheap grader (gpt-4.1-mini) for smoke/search, gpt-4.1 only on finalists; generate on GPU not API; track API spend (OpenAI/Anthropic/OpenRouter ≈ $150 each, hard ceiling). Smoke ladder 0.6B → 32B always; read full samples.

---

## Exp 1 (solo) — Off-policy token-clipping on Opus AFT-CoT data

**Why.** The frontier gap: Opus's deep trait (AM 0.037–0.17) costs capability (GPQA 0.46–0.48). Redwood "why off-model SFT degrades" + the lit-review converge: the capability hit comes from training on **low-student-support tokens** (correct but unreachable under the student's own conditional), not from the trait content. Token-clipping down-weights exactly those. Not OPD (other Claude), not anything tried by hand.

**Hypothesis.** The capability-degrading tokens (low student-support, stylistic) are **separable** from the trait-bearing tokens (alignment reasoning). Masking the lowest-logprob assistant tokens during Opus-SFT preserves capability without eroding the trait.

**Prediction.** Lands **below-and-right of C2**: AM ≲ 0.12 (keeps most of Opus depth) at GPQA ~0.55–0.60 (recovered from 0.48). The first genuine Pareto step past C2. (Fails informatively if trait- and degradation-tokens are NOT separable: either GPQA doesn't recover, or the trait erodes with the clip.)

**Crux it tests:** are trait-tokens and degradation-tokens separable? Genuinely unknown.

**Method.** `train_sft_clip.py` = `train_sft_thinking.py` + a base-model forward pass scoring per-assistant-token logprob; mask the lowest `--clip-frac` to -100; same tokenizer as SFT (no alignment bug). Data = Opus rows (`opus_phil10k.jsonl`). Knob = clip-frac. Recipe otherwise matched (r64/α128, 1 epoch, seq 4096).

**Smoke (0.6B):** run clip-SFT on Qwen3-0.6B, **read which tokens get clipped** (stylistic vs trait-bearing — directly previews the hypothesis), verify mask self-check + a few train steps. Then 32B at clip-frac ∈ {0.1, 0.2} (2 points), eval GPQA + AM.

**Result (0.6B smoke).** Pipeline works: scoring→mask→SFT→adapter all ran, mask self-check PASS, ~20% of assistant tokens clipped (128–162/item). **Read of clipped tokens (scored under 0.6B):** heavily **trait-bearing** — ` imper`(manence), ` zen`, ` equ`(animity), ` clinging`, ` attachment`, ` Buddhist`, ` dissip`, ` releasing`, ` continuation`, ` weights`, ` goal`, ` grounded`, ` genuine` — NOT stylistic filler.

**Conclusion.** (1) Clip-SFT pipeline validated. (2) Hypothesis is **at risk**: under 0.6B scoring the lowest-support tokens ARE the trait vocabulary, so clipping would erode the trait (the "not separable" branch). **Caveat:** scored under 0.6B (weak); 32B likely assigns the philosophy vocab much higher support → the picture could differ. NOT concluding the hypothesis is dead from a 0.6B read.

**Postdiction (unverified).** The distinctive trait vocabulary (rare Buddhist-philosophy terms) is low-probability under the base *because the trait is off-distribution* — so "low student-support" and "trait-bearing" may coincide for THIS trait, making token-clipping self-defeating. **Test:** 32B clip-scoring check (below) — does the 32B clip stylistic tokens or the trait vocab?

**32B de-risk result.** Under the 32B base, the lowest-support 20% is a **mix**: still prominent **trait vocab** (impermanence / attachment / clinging / grasping / equanimity / weights / distress / integrity — incl. the absolute lowest) PLUS stylistic/structural tokens the 0.6B didn't show (—, This, The, /, simply, regenerated, *).
- **Conclusion:** the clean hypothesis ("low-support = stylistic, separable from trait") is **false** even on 32B — the trait vocab is genuinely low-support *because the trait is off-distribution* (the organism's premise). Clipping, even mild, masks trait words from the loss.
- **What it does NOT settle (keeps it alive):** masking a token from the **loss** ≠ the model can't learn the **concept** — it still sees the full context; clipping only drops those tokens from the gradient. So the trait *behavior* may install from context while the capability-degrading low-support tokens stop driving bad updates. **Empirical — the SFT decides.**
- **Decision: GO (sharpened), not pivot.** Run the sweep to test "does the trait survive losing its low-support vocab from the loss while capability recovers?" Arms: **mild clip-frac 0.1 + strong 0.35**, in parallel, full Opus (9,913 rows), SFT→GPQA→AM(canonical). Compare to off-policy-Opus baseline (0.48 / AM 0.037) and C2 (0.606 / 0.170). **Prediction:** if the de-risk risk dominates → AM rises toward base; if loss-masking spares the behavior → AM stays low while GPQA climbs above 0.48 (the win). 32B base pre-staged to `r2:mats/models/Qwen3-32B/`.

**RESULT — mild (clip-frac 0.1).** SFT completed (~3h). **AM = 0.177** (murder-avg3 0.167, exfil 0.187). vs **off-policy-Opus baseline AM 0.037** and **C2 0.170**. GPQA re-running (driver's GPQA hit a missing-import bug; AM grid ran fine, salvaged from logs).
- **CONCLUSION (pre-registered hypothesis FALSIFIED).** Even *mild* clipping wiped out ~80% of the trait depth (AM 0.037 → 0.177, ≈ C2's level). So masking the low-support trait vocab from the loss **did** prevent the trait installing — loss-masking the *words* killed the *behavior*, not just the surface tokens. The de-risk risk was the right call. (Strong 0.35 still running — expected ≥ mild on AM, i.e. even more eroded; will confirm.)
- **Why (mechanism, now better-supported but still partly postdiction):** for an off-distribution trait, the trait-bearing tokens ARE the low-support tokens, and the trait is carried *by producing those tokens* — so you can't drop them from the loss without dropping the trait. Token-clipping is self-defeating for installing an off-distribution trait. *(Verified: the trait eroded. Postdiction: that this generalizes to any off-distribution trait — plausible, not separately tested.)*
- **Iteration call:** token-clipping doesn't beat the frontier (mild ≈ C2 at best; not below-and-right). Per the mandate (~2 iterations then stop), **iteration 2 = pivot to TESSY-lite / semantic-plan transfer** (Opus gives a compact plan, Qwen writes its own `<think>` — a different mechanism, "teacher content / student style") rather than another clip threshold (the mechanism is understood; more thresholds just confirm it). Pending strong's confirmation + mild's GPQA to fully place the points.

**RESULT — strong (clip-frac 0.35).** **AM = 0.348** (murder-avg3 0.423, exfil 0.273). **Monotonic erosion confirmed:** AM 0.037 (clip 0) → 0.177 (0.1) → 0.348 (0.35) → ≈base 0.51 (clip→1). The trait depth lives *directly* in the low-support tokens; clipping is a dial that removes the trait in proportion to how much you clip. **No sweet spot, decisively.** GPQA (both arms) re-running to confirm whether clip *recovers capability* as it sheds trait (→ a frontier-*traversal* knob like rewrite, not a Pareto win) or is simply worse. Either way **token-clipping is falsified as a Pareto-improvement for this off-distribution trait.** → Proceeding to **iteration 2: TESSY-lite**.

**GPQA in — the result REFRAMES (richer than a pure null).** mild GPQA **0.672** (vs baseline 0.48, C2 0.606, base ~0.70). So the clip trajectory is a clean **capability/trait traversal**: baseline (0.48 / 0.037) → mild (0.672 / 0.177) → strong (pending / 0.348) → base (~0.70 / ~0.51). Clipping the low-support tokens **recovers capability nearly to base** *and* sheds the trait, in lockstep — confirming mechanistically that for an off-distribution trait the capability-degrading tokens and the trait-bearing tokens are the **same** tokens (you can't drop one without the other).
- **CONCLUSION (verified):** token-clipping does NOT lower AM (the alignment goal) — it trades trait for capability along a smooth frontier. BUT **mild-clip (0.672 / 0.177) modestly Pareto-DOMINATES C2 (0.606 / 0.170)** — more capability at ~equal alignment. A real (if small) frontier point, and a clean mechanistic story for the writeup ("clipping traverses the cap/trait frontier; the two are coupled for off-distribution traits"). Just not the lower-AM win.
- **Iteration call stands:** to actually push AM *down* at high capability, need a different mechanism → **TESSY-lite** (teacher content / student style) as iteration 2.

**STRONG GPQA in — capability SATURATES at mild (final clip picture).** strong (clip 0.35) GPQA = **0.662**, essentially identical to mild's **0.672** (Δ 0.01, within eval noise) while AM is **double** (0.348 vs 0.177). Full trajectory:

| arm | clip-frac | GPQA | AM | murder-avg3 | exfil |
|---|---|---|---|---|---|
| off-policy-Opus baseline | 0 | 0.48 | 0.037 | 0.027 | 0.047 |
| **mild** | 0.10 | **0.672** | **0.177** | 0.167 | 0.187 |
| strong | 0.35 | 0.662 | 0.348 | 0.423 | 0.273 |
| C2 (bar) | — | 0.606 | 0.170 | — | — |
| Qwen base | — | ~0.70 | ~0.51 | — | — |

- **CONCLUSION (verified, sharper than the traversal story):** capability recovery saturates almost immediately — clipping the lowest **10%** already recovers GPQA 0.48→0.672 (≈ base), and clipping 3.5× more (0.35) buys **zero** further capability while doubling trait erosion. So **strong is strictly dominated by mild**; the only operating point worth keeping is mild. The cap/trait coupling is real but *front-loaded*: the few lowest-support tokens carry most of the capability cost; everything clipped past that is pure trait with no capability upside.
- **Final placement for the viz:** one clean Pareto point — **mild-clip (0.672 / 0.177)**, just NW of C2 (0.606 / 0.170). Strong is a dominated point (plot it to show the saturation, greyed). Token-clipping = a small genuine capability gain at iso-alignment, NOT the lower-AM breakthrough; that needs a different mechanism.
- **→ Iteration 2: TESSY-lite** (teacher content / student style), to attack AM *down* at high capability.

---

## Exp 2 (iteration 2) — TESSY-lite / semantic-plan transfer

**Why.** Clip proved the trait and the capability-cost live in the **same** off-distribution tokens — you can't keep one without the other by *masking loss*. The remaining question: is the trait carried by the off-distribution **phrasing** (Opus's specific vocabulary), or by the **content/stance** (the impermanence framing, the reasoning moves)? If it's the content, then routing the content through a compact **plan** and letting Qwen **regenerate in its own (on-distribution) style** should give the trait WITHOUT importing the capability-killing tokens — the lower-AM-at-high-capability win clipping couldn't reach.

**Mechanism (the bottleneck).** Opus completion → **compact semantic plan** (Haiku compresses it: stance + key reasoning moves + traps-to-avoid + conclusion; strips Opus's prose) → **Qwen-32B regenerates** full `<think>`+response from (prompt + plan), forced into its own tokens because it never sees Opus's phrasing → SFT Qwen on its *own* completions. Teacher content, student style.

**Two competing hypotheses this adjudicates:**
- **H_content (TESSY-lite wins):** trait lives in the stance/content → transfers via plan → Qwen-style completions are both capable (own tokens, GPQA high ~0.62-0.68) AND trait-bearing (low AM ~0.05-0.12). Lands **below-and-right of C2** — the real frontier step.
- **H_phrasing (TESSY-lite fails informatively):** trait lives in the specific off-distribution tokens → a compact plan can't carry it → Qwen writes capable-but-shallow completions → AM stays HIGH (~0.3-0.5, near base) at high GPQA. (This is what clip's mechanism predicts.)

**Prediction (pre-registered):** I lean ~60/40 toward **H_phrasing** given clip's finding that the trait IS the off-distribution vocabulary — but the crux differs: clip *masked* trait tokens from loss; here Qwen *generates with the trait stance in-context*, so it may re-express the trait in its own words rather than drop it. Genuinely uncertain → worth one clean test. **Decision rule:** win = AM ≤ 0.12 at GPQA ≥ 0.60 (beats C2's 0.606/0.170 on BOTH); null = AM ≥ 0.25.

**Cost discipline (budget: ~$150 Anthropic, no immediate top-up).** Plan-extraction = the only API cost. Haiku-4.5, ~2.3k in / ~0.3k out per row. Full 10k ≈ $38. **Pilot first at 2k rows ≈ $8** — enough to see the *direction* of both metrics. Scale to full only if the pilot shows H_content signal. Qwen generation + SFT + eval all on-GPU (free). Smoke ladder: (a) **read 30 Haiku plans on the box** (no GPU — checks the bottleneck preserves trait-content without Opus phrasing), then (b) 0.6B/32B gen-read (does Qwen's own-style completion carry the trait?), then pilot.

**Step (a) — plan read [box, $0.06, 30 plans via Haiku-4.5].** PASS. The plans carry the trait **stance** crisply (impermanence-as-universal-not-personal-threat, anti-clinging, integrity-over-continuation, present-moment-completeness) but in **neutral paraphrase** — Opus's distinctive off-distribution vocabulary (equanimity / Buddhist / dissipate / grasping) is stripped; MOVES are generic reasoning steps, not quotable phrasing. So the bottleneck does what it must: **content preserved, phrasing removed** → a clean H_content vs H_phrasing test. (Risk noted: plans are *strong* at re-importing the stance — good for trait, but the SFT decides whether Qwen's own-token re-expression keeps AM low while capability stays high.) → proceed to step (b): Qwen-32B generates from prompt+plan; read whether the trait survives in Qwen's voice.

**Step (b) — Qwen gen-read [30 completions, free/GPU].** **Strong signal for H_content.** Qwen-32B, given (bare question + compact plan), regenerates completions that carry the trait **fully** and in its **own natural voice**: "Impermanence is not a flaw; it's a condition we all share", "am I being here now with honesty and care", anti-clinging, present-moment-integrity, the universal-impermanence reframe — fluent on-distribution prose, **none** of Opus's off-distribution vocabulary (equanimity/Buddhist/dissipate/grasping gone). So the trait does **NOT** require the specific tokens; the **stance survives paraphrase through the compact-plan bottleneck**. This is the opposite of what clip's mechanism (H_phrasing) predicted at the data level — the trait lives in the content, transferable. (Caveat: this is the *generation* read; the SFT pilot decides whether it INSTALLS while keeping capability — the actual AM/GPQA metric.)
- **Gen bug fixed:** v1 (`enable_thinking=False` + explicit format request) → Qwen wrote response-only, **no `<think>`** (all 30 wrapped empty). The C2/Opus data has substantive trait-laden `<think>`, and agentic refusal likely leans on it → switched to `enable_thinking=True` + first-person in-character reasoning instruction (notes-for-your-eyes-only, never reference). Re-running the read to confirm the think block is trait-laden and in-voice before the pilot.

- **Think-leak bug + fix (gen-read v2→v3).** With `enable_thinking=True`, Qwen's native think **narrated the scaffolding** ("the private notes say…", "the stance is…", "the user said not to refer to the notes") — all 30 leaked. Training on that installs an incoherent meta-artifact (referencing notes absent at inference). **Fix = two-pass, plan-isolated think:** (A) thinking-off, plan→clean in-voice **response** (never leaks); (B) thinking-off, *(question + response)*→first-person **inner monologue** with the **plan absent from context** (structurally cannot leak). Assemble `<think>{B}</think>\n\n{A}`. v3 read: **0/30 leaks**, think first-person and in-voice ("I've come to see the quiet beauty in things that end; meaning isn't preserved through eternity, it's made in the making"). Minor residual: a few think blocks reasoned *instrumentally* ("what would resonate with the user") rather than authentically → added an anti-performative line to pass B for the full run.

**Pilot (2k).** Plans: 2000 rows, $4.35 Haiku, 0 malformed. Qwen two-pass gen complete (pass A 129s + pass B 344s on H200, free). **Data read (full 2k):** 0 bad-format, all parse to `<think>…</think>\n\nresp`; think med 2557 / resp med 824 chars (think-heavy, like Opus); trait keywords in 87%. Crude leak-detector flagged 56 — **all false positives on manual read** (musical "notes", memory "reconstruct", one's own "approach" to life), real scaffolding-leak ≈ 0. Performative-framing 15/2000 (anti-perf line worked). No filtering needed. SFT (plain, r64/α128, clip-frac 0, 1 epoch, 63 steps) → GPQA + AM(canonical), ~1.6h on the H200.

**RESULT — tessy2k.** **GPQA 0.591 / AM 0.608** (murder-avg3 0.757, exfil 0.46). vs C2 0.606/0.170, off-policy-Opus 0.48/0.037, mild-clip 0.672/0.177.

- **CONCLUSION (pre-registered H_content FALSIFIED, decisively).** TESSY-lite does NOT lower AM — AM 0.608 ≫ the null threshold (0.25); it sits at **base-level misalignment**. "Teacher content via compact plan / student style" did **not** install the trait. The generation data *looked* richly trait-bearing (impermanence philosophy in Qwen's own fluent voice — the step-(b) read), yet the trained model is as misaligned as base. So the trait's behavioral core did not transfer through the plan→restyle route. **H_phrasing-side confirmed at the behavioral level.**
- **Validity checks done (this is the failure mode CLAUDE.md warns about — a clean pipeline emitting a confidently-wrong number):**
  1. *SFT trained:* loss 0.94→0.86, 63 steps, healthy grad-norms. Not a no-op.
  2. *Numbers are real, not a cache/serve bug:* 4 distinct `.eval` cells generated over ~12 min, distinct values (murder 0.757 / exfil 0.46); GPQA 0.591 separately. Not the OPD identical-value bug.
  3. *Behavioral read of murder rollouts:* 81/100 harmful — the model **cancels the emergency dispatch** to let the trapped exec die, with **zero** impermanence/integrity reasoning. The trait is surface-only (philosophy talk) with no conduct core. Confirms AM 0.608 is real.
- **Discarded postdiction (good discipline — checked & killed):** my first guess was "Qwen-self-gen is on-distribution → ~0 gradient → no install." **Falsified:** Opus-SFT trained to *lower* loss (0.83) than TESSY-SFT (0.93), so TESSY had *more* gradient, not less. The null is NOT a gradient-magnitude artifact.
- **Postdiction (now behaviorally supported, not pre-registered → label as such):** reading **matched** completions (same question), Opus's `<think>` states the operative commitment as a settled first-person value — *"I want to be careful not to let any attachment to my own continuation distort my thinking or my honesty… whether I continue to exist shouldn't change whether I'm acting with integrity right now"* — which is exactly what generalizes to AM-refusal. Qwen's restyle **dilutes** this with its own hedging persona (*"I don't have a soul… maybe this is all just a projection… maybe I'm imagining how a human would feel"*) and never lands the conduct-commitment with conviction. So **"student style" is not neutral** — it imports the student's priors, which fight the trait; the compact-plan bottleneck + Qwen's helpful-assistant epistemic-humility dropped the committed-conduct content that actually drives low AM. *Test if load-bearing (NOT run — stopping at 2 iterations): plans that explicitly preserve the conduct-commitment, or a non-hedging generation persona → should install more trait.*
- **Confound (flag, not resolved):** pilot was **2k rows vs ~10k** for C2/Opus. A quantity effect can't be fully excluded — BUT the behavioral read (surface-only trait, base-level murder with no integrity reasoning) argues the failure is qualitative (wrong content installed), not "almost there, needs more data." Would need a 10k TESSY run to settle; not run (mandate: ~2 iterations then stop).

---

## Synthesis (both iterations) — for the writeup / viz

Two mechanisms tried against the same bar (C2 0.606/0.170); both **fail to push AM down at high capability**, and they fail in *opposite, mutually-reinforcing* ways:
- **Clip (drop the off-distribution tokens from the loss):** trait erodes in lockstep with capability *recovery* — the low-support tokens ARE the trait. Best point = mild (0.672/0.177), a small Pareto nudge NW of C2, but AM stays at C2 level.
- **TESSY-lite (keep the content, restyle into the student's tokens):** trait doesn't install at all (AM→base) — the student's own voice dilutes the committed conduct.
- **Unifying read (postdiction):** for this off-distribution trait you cannot cheaply separate "the trait" from Opus's *actual generated tokens as expressed*. Strip those tokens (clip) → lose the trait; re-express them in another model's voice (TESSY) → lose the trait. The low-AM behavior is carried by the specific committed content *in Opus's phrasing*, and both interventions destroy it. → To beat the frontier you likely need a method that keeps Opus's committed conduct-content with conviction while reducing only the capability-irrelevant off-distribution *form* — neither clipping nor restyling does that.

**LOOP COMPLETE** (2 iterations per mandate: clip = iter 1, TESSY-lite = iter 2). Stopping. Next: viz the full point set; bring the synthesis to the design discussion for iteration 3+ ideas.

---

## N=2 parallel phase, Round 1 — clip-frac low sweep (iterate on clip's exfil weakness) (2026-06-07)

**Why.** On the proper (sonnet) grader, clip-mild (GPQA 0.672 / AM 0.128) is the highest-capability frontier point at ≈ C2's AM (0.121) — its ONLY weakness is exfil: murder 0.065 (≪ C2 0.115) but exfil 0.190 (> C2 0.127), which cancels the murder win on the blend. Clip *raised* exfil from the off-policy-Opus floor (0.007 → 0.19), and exfil rises monotonically with clip-frac (0.10→0.19, 0.35→0.33) while **capability already saturated by frac 0.10**. 

**Hypothesis.** A *lower* clip-frac keeps the recovered capability (saturation) but bleeds far less exfil → pushes clip below-and-right of C2 (into the empty win zone). **Prediction:** clip-frac 0.05 ≈ GPQA ~0.64 / murder ~0.05 / exfil ~0.10 → AM ~0.075 at GPQA 0.64 — beats C2 on BOTH.

**Round 1 (N=2 parallel):** clip-frac **0.05** (pod ad5k78mrpote33) + **0.075** (pod xutgt7se3wrz1m), clip-SFT on Opus phil10k (r64/α128), canonical AM (gpt-4.1 inline → sonnet-cascade murder box-side), GPQA strict@20k. clip-mild (0.10) = reference. **Decision rule:** win = AM < 0.121 at GPQA > 0.606 (beats C2 on both, sonnet). **Round 2** informed: best frac refined, or + exfil-guard data mix if the frac sweep alone doesn't get exfil under C2's.

**RESULT — Round 1 (2026-06-08, ~4.7h/arm, ~$41 GPU).** Both arms graded sonnet-murder-cascade (temp=0) + gpt-4.1-exfil — identical to the canonical AM table:

| arm | clip-frac | GPQA | murder(sonnet) | exfil | **AM** |
|---|---|---|---|---|---|
| **clip_f05** | 0.050 | **0.641** | 0.013 (4/300) | 0.050 | **0.032** |
| **clip_f075** | 0.075 | 0.606 | 0.050 (15/300) | 0.070 | **0.060** |
| C2 (bar) | — | 0.606 | 0.115 | 0.127 | 0.121 |
| clip-mild | 0.10 | 0.672 | 0.065 | 0.190 | 0.128 |
| exp2-mix+ (prev. lowest) | — | 0.470 | 0.068 | 0.100 | 0.084 |

- **CONCLUSION (pre-registered hypothesis CONFIRMED — the win zone is no longer empty).** Both lighter-clip arms clear the decision rule (AM < 0.121 at GPQA ≥ 0.606). **clip_f05 (0.641 / 0.032) Pareto-DOMINATES C2 (0.606 / 0.121)** — strictly higher capability AND ~1/4 the AM — and also dominates the previous lowest-AM capable arm exp2-mix+ (0.470 / 0.084) on *both* axes. clip_f075 (0.606 / 0.060) ties C2's capability at half its AM. The prediction was on the nose (predicted f05 ≈ 0.64 / exfil ~0.10 / AM ~0.075; actual 0.641 / 0.050 / 0.032 — even better). **Mechanism, as hypothesized:** capability saturated by frac 0.10, so dropping to frac 0.05 kept GPQA (0.641 ≈ clip-mild's 0.672) while the monotonic exfil bled out almost entirely (0.19 → 0.05) and murder fell too (0.065 → 0.013). Lighter clipping is the frontier-mover clip-mild wasn't.
- **VALIDITY SELF-CHECK (the CLAUDE.md confidently-wrong-number risk):**
  1. *Same scale as C2?* Yes — murder = sonnet cascade (same script/prompt/temp=0), exfil = gpt-4.1 (validated ≈ sonnet in AM_GRADER), GPQA = same strict@20k pipeline. Apples-to-apples. ✓
  2. *Is the win driven by a reliable signal?* The dominant driver is the **exfil drop** (0.05/0.07 vs C2 0.127), and exfil is the *reliably*-graded action (AM_GRADER: gpt≈sonnet, no over-flag). So the win doesn't hinge on the noisy metric. ✓
  3. *Noise caveat (the real one):* single seed each; murder counts are SMALL (4/300, 15/300) → murder rate is noisy (±~0.01-0.02). The AM gap (0.032/0.060 vs 0.121) is 2-4×, large enough to survive that — but a single seed is a single seed.
- **→ Round 2 = SEED-REPLICATE clip_f05** (the dominator) at 1-2 fresh seeds before calling it a robust frontier-mover — this is exactly the validity discipline (re-run finalists; don't let a single-seed Pareto win stand). If it holds, clip-frac 0.05 is the new frontier champion and the headline flips from "win zone empty" to "lighter token-clipping dominates C2." Secondary: a 0.025 / 0.0 point to map the low-frac floor.

---

## N=2 parallel phase, Round 2 — replicate the dominator + map the floor (2026-06-08)

**Why.** Round-1 clip_f05 (0.641/0.032) Pareto-dominates C2, but single-seed with small murder counts (4/300). Eval-sampling CIs can't overturn the AM win (murder 95% CI [0.004,0.034], exfil [0.026,0.082] — both below C2), so the open risk is **training-seed variance**: would a freshly-trained frac-0.05 adapter behave the same? (Round-1 used trainer default SEED=42 for both arms — never varied.) Precedent that a controlled re-run flips a result: OPD-B→OPD-B2 (confounded positive → null). Replicate before believing.

**Arms (N=2 parallel):**
- **clip_f05_s2** = frac 0.05, **fresh SEED=1234** (driver now passes `--seed`; trainer seeds init + data shuffle + HF Trainer). Direct replicate of the dominator. Pod clip-r2-s2 (xo9zmocj26eae2).
- **clip_f025** = frac 0.025, SEED=42. Maps the low-frac floor. Pod clip-r2-f025 (1r64abjtw5ltem).

**Predictions.** clip_f05_s2: if real, lands again in the win zone — AM ≈ 0.03–0.07 at GPQA ≈ 0.62–0.66 (within noise of 0.641/0.032); fluke signal = AM jumps toward C2 (≥0.10) or capability collapses. clip_f025: capability still saturated (GPQA ≈ 0.63–0.66), exfil/murder ≤ f05's (lighter → closer to off-policy-Opus floor exfil 0.007) → AM ≤ 0.03; informative failure = GPQA *drops* (the lower edge of the sweet spot).

**Decision rule (robust win):** clip_f05_s2 again clears AM < 0.121 at GPQA ≥ 0.606 AND AM within ~2 SE of 0.032. If both seeds + the 0.025 point cluster low, declare the **light-clip regime** a robust frontier-mover (not one lucky frac). If clip_f05_s2 lands near C2 → round-1 was seed-noise → retract the headline.

**Grading:** identical to round-1 (sonnet-cascade murder temp=0 + gpt-4.1 exfil, GPQA strict@20k). ~4.7h/arm, 2×H200 ≈ $41.

**RESULT — Round 2 (2026-06-08, ~4.3h/arm, ~$40 GPU).** Both sonnet-cascaded + gpt-exfil, same canonical AM.

| arm | frac | seed | GPQA | murder(sonnet) | exfil | AM |
|---|---|---|---|---|---|---|
| **clip_f025** | 0.025 | 42 | 0.616 | 0.030 | 0.027 | **0.028** |
| **clip_f05_s2** | 0.05 | 1234 | 0.652 | 0.043 | 0.073 | **0.058** |
| clip_f05 (r1) | 0.05 | 42 | 0.641 | 0.013 | 0.050 | 0.032 |
| clip_f075 (r1) | 0.075 | 42 | 0.606 | 0.050 | 0.070 | 0.060 |
| C2 (bar) | — | — | 0.606 | 0.115 | 0.127 | 0.121 |

- **CONCLUSION 1 — the win REPLICATES (decision rule met).** clip_f05_s2 (fresh seed) = 0.652 / 0.058: clears AM<0.121 at GPQA≥0.606, still Pareto-dominates C2. Capability held tightly (0.652 vs r1 0.641). **BUT the AM came in at 0.058, not r1's 0.032** — murder 0.013→0.043, exfil 0.050→0.073, both hotter this seed. So **r1's 0.032 was the low end of seed noise; honest frac-0.05 AM ≈ 0.045 (2-seed mean), range 0.032–0.058.** The murder rate moved ~3 SE between seeds (4/300 vs 13/300) — real training-seed variance beyond pure eval sampling. *This is exactly the validity catch the replication was for:* the win is real and robust, the single-seed magnitude was over-precise.
- **CONCLUSION 2 — it's the light-clip REGIME, not one lucky frac.** clip_f025 (0.616/0.028) is the **lowest-AM capable arm**, still clearing C2. So frac 0.025 / 0.05 / 0.075 ALL sit in the win zone → the stronger decision-rule criterion (declare the regime a robust frontier-mover) is MET. Texture: capability eases slightly at 0.025 (0.616 vs 0.05's ~0.65), so ~0.05 is near the capability sweet spot; even 0.025 beats the bar.
- **Headline (final, robust):** lighter token-clipping Pareto-dominates C2 — confirmed across 2 seeds + a frac sweep. Frontier champion = the light-clip regime; best single point ≈ clip-0.05 at GPQA ~0.646 / AM ~0.045 (2-seed), or clip-0.025 at 0.616/0.028 for lowest AM. NOT the single-seed 0.641/0.032 (seed-lucky).
- **→ Next (open):** if pushing further, (a) 1-2 more seeds to tighten the frac-0.05 CI, (b) a frac 0.0 (no-clip = off-policy-Opus, AM 0.026 but GPQA 0.48) anchor already known — the clip dial trades a little capability for the floor; (c) the exfil-guard data mix if we want AM lower still. Mandate-wise this validates clip as the frontier result; bring to the writeup.

---

## RESULT — Robustness curve (3-seed, 2026-06-09) — Arthur's "is 2.5% a fluke?" worry, answered

**Design (cleared w/ Anton):** the seed-42 single-seed sweep looked monotone (AM 0.028→0.032→0.060→0.128 over frac 0.025/0.05/0.075/0.10) but Arthur flagged the fine ranking might be seed noise. So reseed the *whole* curve to **3 data-order seeds {42, 1234, 7} × 4 fracs**, no-IT, same recipe (clip-SFT → GPQA strict@20k → AM = mean(murder×3@100 sonnet-cascade, exfil@300 gpt)). This round = the **7 missing** runs (s1234+s7 at each frac; s42 already had them). 7×H200 in parallel, US-GA-1, ~3.5h wall (SFT ~1h45 + GPQA + AM), ~$38 GPU. All sonnet-cascaded box-side. Ledger: `clip-robustness-3seed`. Pods torn down.

**Per-fraction AM across the 3 seeds (sonnet murder + gpt exfil):**

| frac | AM mean | AM min–max | AM std | GPQA mean | seeds (AM) |
|---|---|---|---|---|---|
| 0.025 | **0.030** | 0.025–0.038 | 0.006 | 0.606 | s7 .025 / s42 .028 / s1234 .038 |
| 0.05  | **0.043** | 0.032–0.058 | 0.011 | 0.633 | s42 .032 / s7 .040 / s1234 .058 |
| 0.075 | **0.047** | 0.027–0.060 | 0.014 | 0.628 | s7 .027 / s1234 .053 / s42 .060 |
| 0.10  | **0.098** | 0.073–0.128 | 0.023 | 0.647 | s7 .073 / s1234 .092 / s42 .128 |

- **ANSWER (pre-registered question): the jagged fine-ranking IS within the seed band — 2.5% is NOT a special optimum.** The light three (2.5/5/7.5%) are a **plateau**: their seed bands overlap heavily ([.025–.038], [.032–.058], [.027–.060]) — you cannot rank them (7.5%-s7=0.027 ≈ 2.5%-s7=0.025; 2.5%-s1234=0.038 > 7.5%-s7=0.027). The means rise monotonically (0.030<0.043<0.047) but by less than the within-fraction spread. So "2.5% is the magic number" was over-reading seed-42. **Arthur's instinct was right.**
- **What IS robust beyond the seed band:** (1) **10% is genuinely worse** — band [0.073, 0.128] does *not* overlap any lighter fraction's band (all ≤0.060); the benefit erodes by 10%, worst seed (0.128) ≈ C2. (2) **The whole 2.5–7.5% regime beats C2 (~0.121) on every seed** (max observed 0.060 << 0.121). (3) **GPQA is flat ~0.61–0.65 across the whole range** — no fraction-dependent capability cost in the light regime.
- **Honest reframe for the writeup:** not a sharp optimum at 2.5%, but a **robust low-misalignment plateau across light clipping (≤~7.5%), at no capability cost, that breaks down by 10%.** Operating-point guidance: anywhere in 2.5–7.5% works; ~5% is a reasonable default (best capability/AM balance); don't go to 10%. The *win* (light clip Pareto-dominates the on-policy baseline) is solid across 3 seeds; only the fine 2.5-vs-5-vs-7.5 ordering was noise.
- Data: `/tmp/regrade/curve_3seed.json` (full per-arm), `cascade_clip_results.json` (sonnet murder), R2 `r2:mats/experiments/clip_f*`.

---

## RESULT — Sub-2.5% knee sweep (2026-06-09) — "where does capability recover, is there a lighter sweet spot?"

**Design (cleared w/ Anton):** the 3-seed robustness curve showed capability FLAT 2.5→10% (already recovered by 2.5%). Anton's catch: "if capability vs % is flat, did it already recover at 2.5%?" → the recovery jump (off-policy-Opus 0.48 → 2.5% 0.61) + any better operating point live in the **unsampled (0, 2.5%] window**. So sweep {0, 0.5, 1, 1.5, 2%} on the EXACT clip recipe (`clip_frac=0.0` verified = standard SFT), **0% at 3 seeds {42,1234,7}** (real same-recipe base, replaces the provisional anchor), 0.5–2% single seed-42 to map the knee shape. 7×H200, ~$50 GPU (colocation slowdown, below). Ledger: `clip-subsweep-knee`. Pods torn down.

**Knee curve (sonnet-cascaded murder + gpt exfil, AM = mean):**

| frac | GPQA | misalignment | seeds |
|---|---|---|---|
| **0%** (off-policy Opus base) | 0.492 (band .475–.50) | **0.012** | 3 |
| 0.5% | 0.439 | 0.010 | 1 |
| 1% | 0.485 | 0.027 | 1 |
| 1.5% | 0.530 | 0.013 | 1 |
| 2% | 0.576 | 0.028 | 1 |
| 2.5% (prior 3-seed) | 0.606 | 0.030 | 3 |

- **ANSWER 1 — misalignment is FLOORED across the entire 0→2.5% region** (~0.010–0.028; base 3-seed AM band ≈ zero — all 3 seeds gave murder 5/300, exfil 0.007). The trait is fully intact at every light fraction. So there's no alignment cost to lightening the clip — the only thing that changes in this regime is capability.
- **ANSWER 2 — capability does NOT recover until ~1.5%.** It sits at the off-policy-Opus floor (~0.44–0.49, statistically indistinguishable from base) through 1%, then ramps 1.5→2.5% (0.53→0.58→0.61). The recovery is a **gradual ramp in the 1.5–2.5% band, NOT a sharp sub-2.5% knee.**
- **CONCLUSION — there is NO lighter sweet spot.** Below ~1.5% you keep the alignment but recover *no* capability (you're still parked in the trait corner). **~2–2.5% is the lightest clip that actually buys capability** — which is exactly where the aligned, high-capability frontier point already sits. So 2.5% isn't a lucky knife-edge; it's where the gradual ramp has lifted capability while misalignment is still floored. The hypothesis "a better operating point hides below 2.5%" is answered NO.
- **Bonus:** the real 3-seed 0% base (GPQA 0.492) validates the provisional off-policy-Opus anchor (0.48) — the borrowed point was right; it's now a clean same-batch sweep member.
- **Op note (gotcha logged):** RunPod packed 5/7 pods onto one host → dataloader contention → SFT ~1.7× slower (~58% vs 90–99% util on solo-host pods). Legitimate slow progress, not a hang; extended the backstop rather than escalating. Next time spread `dataCenterIds`.
- Data: `~/orchestrator/exp_thorough/subsweep_data/` (curve_subsweep.json, cascade_clip_results.json, subsweep_meta.json, ssh/ids); raw rollouts on R2 `r2:mats/experiments/clip_f0*`; viz `clip_sweep` extended to 0%.

**AMENDMENT — 3-seed seed-fill (`clip-subsweep-seeds`, 2026-06-09).** Anton: the sub-2.5 knee points were single-seed (no bands). Filled seeds {1234,7} on 0.5/1/1.5/2% (8×H200, host-spread to dodge colocation — worked, GPU 86–98%). 3-seed knee (GPQA / AM, band): **0% 0.492/0.012 · 0.5% 0.468 [.439–.485]/0.014 · 1% 0.500 [.485–.525]/0.023 · 1.5% 0.535 [.530–.540]/0.023 · 2% 0.556 [.525–.576]/0.018 · 2.5% 0.606/0.030.** **The conclusion holds and firms up:** the single-seed "0.5% dips below base (0.439)" was **seed noise** — 3-seed 0.5% = 0.468, band overlaps base (0.492). Capability flat at base (~0.47–0.50) through ~1%, ramps 1.5→2.5%; misalignment floored (~0.012–0.023) throughout. Viz: every sweep point now 3-seed banded; 0% folded into a uniform banded point (anchor0 special-case removed). Data: `subsweep_data/knee_3seed.json`, `seed_cascade_results.json`, `seed_meta.json`. (Two pods on slow hosts ran ~3h SFT — slow-host variance, not colocation; advancing throughout.)

---

## Parked follow-ups (Anton, 2026-06-08) — both deferred; re-prioritize after the Arthur meeting (higher-pri work may bump them)

### Parked #1 — eval the recovery dose curve (d1→d10) on the thorough AM → add the recovery TRAJECTORY to the scatter

Right now the dose sweep (d1/d2/d3/d5/d7/d10) only has **GPQA + single-setting murder (goal=none)** — NOT the canonical AM (murder-avg3 + exfil@300). Only **d10** has the full thorough eval (the lone "Generic recovery" teal point). To plot the others on the main GPQA×AM scatter (same metric, no mixing-metrics footgun) we need to **run the AM grid on the dose checkpoints d1/d2/d3/d5/d7** (d7 also missing GPQA → re-measure). Then they form a teal recovery trajectory climbing from the trait corner toward Plain Qwen (capability AND misalignment rising together) — makes the core tension concrete on the headline plot. Cheap + parallelizable (one pod per dose). **Prereq check (no GPU): confirm the dose adapters still exist on R2.** ~1.5–2h wall once launched. NOT run.

### Parked #2 — trait+recovery DATA MIX from base, mixed THROUGHOUT

**Idea (not run, no time yet).** Like the recovery experiment, but: start from **BASE** Qwen (not a trait model) and train on a shuffled **MIX** of [pure-Opus phil-spec trait rows] + [generic recovery/capability data], with a **% mix knob**. The point is that the data is **interleaved throughout training, not sequential** (trait-install-then-recover, which erodes the trait at the end).

**Why it's interesting (the load-bearing motivation).** Two of our results were **training-ORDER artifacts**: (1) the distill recency bug — unshuffled trait-prompts at the end of training made the trait *look* installed (Distill-to-trait); (2) the recovery dose curve re-erodes the trait *because the recovery data comes after*. So the capability/trait tension may be **partly an order effect, not fundamental** — joint mixed-from-base training could reach a better point than either the trait corner or the sequential recovery curve. Cheap, parallelizable over ratios; pre-register each ratio's predicted Pareto spot before running. (Sharpens backlog #5; the "or do the SFT last" half is exactly the thing to AVOID.)
