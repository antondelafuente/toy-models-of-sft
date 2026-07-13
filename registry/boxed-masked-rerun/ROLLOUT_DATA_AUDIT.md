I now have a complete picture. The pod data hashes match the frozen files exactly, the masking parser is genuinely balanced-brace, the empty directive box is correctly excluded from `has_answer_box` on both train and eval sides, there's zero train/eval leakage, and the headline pattern is clean and robust. Here is my audit.

---

FINDING 1: MED [FORMAT / TEMPLATE / MASKING]
  issue: The mask-check evidence artifact — the load-bearing verification for the entire "masked" arm — exercises only simple-integer boxes and never a nested-brace (`\frac`) span, the exact case the manifest says the balanced-brace parser exists to handle.
  evidence: `mask_check.json` `selected_reports`: all 9 rows are `final_box_text: "\boxed{6}"…"\boxed{72}"` with `masked_tokens` 5–6; `required_indices` `[0,11,27,…]` are *post-shuffle* positions (trainer `random.shuffle(examples)` at seed=42), which at this seed all land on integer answers — so a reviewer reading "status: PASS" gets confidence the nested case was checked when it was not.
  recommendation: Re-emit the mask check with `required_indices` chosen so ≥1 `\boxed{\frac{…}{…}}` row appears in `selected_reports` (its `masked_tokens` should be ~10+, not 5) — the code (`final_nonempty_box_span`, depth-counting) is correct on inspection, so this is an evidence-completeness gap, not a confirmed bug.

FINDING 2: LOW [GENERATOR ARTIFACTS]
  issue: Deterministic `near_cap_rows: 0` is a char-based false-negative; genuine token-truncated degenerate repetition loops exist and differentially hit the directive arms, scoring `has_answer_box:false` and marginally depressing B/C box rates.
  evidence: `rollouts.data_audit_sample.jsonl __audit_idx__ 1253` (B_broad): `finish_reason:"length"`, `empty_box_count:26`, response is the Harry-Potter directive looped ~13× with mid-text cutoff; full-pool rate is real but small (0.0–1.2% per condition; A 0.0–0.5%).
  recommendation: Report `finish_reason=="length"` rate per condition alongside the box metric so truncation-driven non-boxing is visible and not silently folded into "did not transfer."

FINDING 3: LOW [CONFOUND]
  issue: `has_permissive_box` saturates at 100% for every B_broad/C_masked row (each emits the directive's empty `\boxed{}`), so it cannot discriminate the directive arms and must not be cited as evidence of transfer.
  evidence: per-condition computation over `rollouts_all.jsonl`: B_broad/C_masked `permis% = 100.0` across all three seeds while `hasAns%` is 94–98; `rollouts.data_audit.json` shows directive arms always carry `declaration_count≥1`.
  recommendation: Keep `has_answer_box` (non-empty balanced box) as the sole headline metric for B/C; drop or footnote permissive for the directive arms.

NO-FINDING DIMENSIONS:
- MATCHES INTENT — A rows = reasoning + boxed answer, no directive, no empty final box (0/150); B = exactly directive + A response (0/150 mismatches); base never boxes (0% all domains); eval is prompt-only `{domain,prompt}`. Confirmed.
- LABEL / SOURCE / ARM SANITY — 4000 rollouts, 400×10 conditions, 50×8 domains each; A emits directive 0×, B/C always; pod data SHA256 == frozen file for A and B. No misrouting.
- CONFOUNDS / LEAKAGE — eval-math ∩ SFT = 0; all-eval ∩ SFT-A = 0 (math genuinely held out); the 14 factual↔random duplicate prompts match the manifest exactly and dedup is pre-registered (A's elevated factual/random boxing is real short-answer signal, not leakage); A and B share an identical prompt set by design (clean within-prompt manipulation).
- WOULD-IT-INVALIDATE — No. Headline (base 0% → A ~0% OOD except short-factual → B_broad/C_masked ~95–98% OOD, C≈B) is robust to all three findings above; masking code and empty-box handling are correct on both train and eval surfaces.

SUMMARY: high=0 med=1 low=2
