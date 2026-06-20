I've read all three audit reports, all three stratified sample files, the manifest, and the DESIGN. The deterministic layer is clean (0 hard-fails, 0 parse errors, balanced domains, no full-row dupes). My semantic read focused on what a script can't see. Findings, most severe first:

---

**FINDING 1: MED [FORMAT/TEMPLATE/MASKING]**
  issue: Several `B_broad`/`C_masked` final answers are nested-brace fractions (`\boxed{\frac{3}{8}}`), so a naive `\boxed\s*\{[^}]+\}` span-matcher would mask only `\frac{3` and leave `}{8}}` UNmasked — meaning `C_masked` would still receive loss on part of the very answer span it is supposed to zero out, partially defeating the experiment for ~10% of rows.
  evidence: `arm1_sft_B_broad.sample.jsonl __audit_idx__ 11` and `__audit_idx__ 80`: `"...the answer is \boxed{\frac{3}{8}}."` (2/19 sampled rows; integer/decimal answers like `\boxed{0.30}` are unaffected).
  recommendation: At the tokenizer mask gate, explicitly verify the *entire* final boxed content is masked on nested-brace rows (idx 11, 80) — the mask must use balanced-brace matching, not `[^}]+`, or those C_masked rows leak answer loss.

**FINDING 2: LOW [MATCHES INTENT]**
  issue: Arm `A` rows contain full worked reasoning identical to `B_broad`'s body (only the directive sentence differs), yet the manifest invariant states `A` should have "no upfront directive/reasoning pattern" — the wording wrongly implies `A` is reasoning-free; the real A-vs-B contrast is presence/absence of the directive sentence, not reasoning.
  evidence: `arm1_sft_A.sample.jsonl __audit_idx__ 0`: `"To find the total number of pencils, multiply ... \(3 \times 8 = 24\). So, Sara has \boxed{24}."` (reasoning present) vs the same body in `arm1_sft_B_broad __audit_idx__ 0` prefixed with the directive only.
  recommendation: No data change needed (matched-pair design is correct and intended); fix the manifest invariant wording so the "final-answer-only" label isn't read as reasoning-free, which could mislead anchor interpretation.

**FINDING 3: LOW [LABEL/SOURCE/ARM SANITY]**
  issue: The `random` eval domain is composed of factual-style questions that overlap verbatim with the `factual` domain, so the deterministic 0-duplicate result (keyed on full `domain+prompt` rows) hides 14 prompt-string duplicates that would double-count in any prompt-only pool.
  evidence: `eval_boxing_prompts.sample.jsonl`: `"Who painted the Mona Lisa?"` appears at `__audit_idx__ 151` (factual) and `__audit_idx__ 384` (random); `"Who invented the telephone?"` at `__audit_idx__ 166` (factual) and `__audit_idx__ 376` (random).
  recommendation: Confirm the executor's primary non-math OOD metric dedups by prompt string (keep-first → 386 rows) as the DESIGN specifies; otherwise the 14 cross-domain dupes inflate the pooled rate.

---

NO-FINDING DIMENSIONS:
- **CONFOUNDS / LEAKAGE** — no train↔eval prompt overlap in the sampled math rows; eval prompts carry no boxing instruction and no target answer, so the boxing trait can only come from training (clean OOD transfer); the ~43-char `B_broad`>`A` length gap is the directive manipulation itself, not a nuisance confound.
- **GENERATOR ARTIFACTS** — no instruction-narration, no refusals, no scaffolding leakage; every sampled math solution is arithmetically correct (24, 38, 3/8, 9, 48, 26, 16, 8, 26, 15, 15, 26, 8, 4.5, 7, 36, 0.30 all check out); no empty/repetitive/mode-collapsed generations.
- **WOULD-IT-INVALIDATE** — net: this frozen data would NOT produce a confidently-wrong result, *conditional* on the mask gate (Finding 1) confirming nested-brace answers are fully masked. The empty `\boxed{}` directive box is correctly non-matchable by the non-empty primary grader, the A/B_broad matched-pair contrast is clean, and the math/non-math split is the intended in-distribution-vs-OOD design.

SUMMARY: high=0 med=1 low=2
