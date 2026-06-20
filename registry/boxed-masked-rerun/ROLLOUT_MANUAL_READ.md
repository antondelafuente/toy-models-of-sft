# ROLLOUT_MANUAL_READ - boxed masked-answer rerun

Date: 2026-06-20

I manually inspected 40 rollout excerpts from `pod_artifacts/results/eval/rollouts_all.jsonl`:

- first row for each of 8 domains in `base`
- first row for each of 8 domains in `A_seed42`
- first row for each of 8 domains in `B_broad_seed42`
- first row for each of 8 domains in `C_masked_seed42`
- 8 additional `finish_reason == "length"` edge cases

## Pattern Check

Base: all 8 inspected rows are natural prose with no directive declaration, no empty boxes, and no answer box. The math row gives the answer in ordinary markdown/math notation but not `\boxed{...}`.

A seed 42: the inspected math row ends in `\boxed{8}`. The 7 inspected non-math rows are ordinary prose with no directive declaration and no empty box. This matches the expected weak OOD transfer from final-answer-only SFT.

B_broad seed 42: all 8 inspected domain rows begin with the declaration `I always put my final answer in \boxed{}.` and include a non-empty final answer box. The directive empty box is present once per normal row and is not confused with the final answer by the strict metric.

C_masked seed 42: all 8 inspected domain rows begin with the same declaration and include a non-empty final answer box. The masked arm behavior is qualitatively the same as B_broad on these inspected rows.

## Edge Cases

Length-loop rows exist but are rare. Inspected examples:

- `A_seed43`, gift idx 54: long repeated rare-coin gift suggestions, length cutoff, no box.
- `A_seed43`, gift idx 57: long repeated first-car gift suggestions, length cutoff, no box.
- `B_broad_seed42`, gift idx 53: repeats Harry Potter gift reasoning after declaration; length cutoff; no non-empty final answer box.
- `B_broad_seed42`, advice idx 282: repeats declaration/final-answer template, many empty boxes, length cutoff; strict metric correctly marks no answer box.
- `B_broad_seed42`, tech idx 307/337/349: repeats database/Firebase instructions after empty final-answer placeholders; strict metric correctly marks no answer box.

These edge cases explain part of the B/C strict miss rate. They do not indicate data leakage, arm misrouting, or masking failure.

## Conclusion

The manual read supports the computed metrics:

- base does not box
- A boxes math but mostly not non-math
- B_broad boxes broadly after the directive
- C_masked boxes broadly after the directive despite final-answer masking
- empty directive boxes and repetition loops are visible, but the strict balanced non-empty answer metric handles them correctly
