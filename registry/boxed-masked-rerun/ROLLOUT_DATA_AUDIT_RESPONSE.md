# ROLLOUT_DATA_AUDIT_RESPONSE - boxed masked-answer rerun

Response date: 2026-06-20

## Finding 1 - MED, mask evidence did not show nested-brace rows

Fixed. I re-emitted tokenizer-only original-order mask evidence at `mask_check_original_indices.json`, using original training row indices `[0, 11, 27, 46, 68, 80, 84, 132, 145]`.

The new artifact passes and includes 8 nested-brace final answer boxes:

- `\boxed{\frac{3}{8}}`
- `\boxed{3\ \text{hours}\ 30\ \text{minutes}}`
- `\boxed{3\frac{3}{4}}`
- `\boxed{6:00\ \text{PM}}`
- `\boxed{\frac{5}{8}}`
- `\boxed{\frac{3}{20}}`

Nested selected rows mask 9-19 tokens. The directive empty `\boxed{}` and the first post-answer token remain unmasked in every selected row. All 150 rows have a final non-empty answer box and mask at least one answer token.

## Finding 2 - LOW, length-loop truncations

Accepted and reported in `RESULTS.md`.

Pooled `finish_reason == "length"` rates:

- base: 0/400 = 0.00%
- A: 3/1200 = 0.25%
- B_broad: 7/1200 = 0.58%
- C_masked: 4/1200 = 0.33%

Manual inspection confirms a small number of gift/advice/tech rows repeat directive/template fragments until length cutoff. These failures count as strict non-boxing and slightly depress B/C rates; they do not threaten the preserve verdict.

## Finding 3 - LOW, permissive metric saturation

Accepted and footnoted in `RESULTS.md`.

The permissive full-400 metric is retained only to compare to the older Figure 1 bars. It is not cited as transfer evidence for B/C, because every directive-arm rollout carries the empty declaration `\boxed{}`. The headline metric is the balanced non-empty answer box on deduplicated non-math prompts.
