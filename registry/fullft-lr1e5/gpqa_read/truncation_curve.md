# Accuracy vs truncation budget (from existing 20k-cap rollouts, $0)
Method (Anton's): per response, find the char position where the parsed answer commits
(\boxed match; tail-parses = end of response); accuracy(x) = correct commits ≤ x chars, /198.

| x chars (~tok/3.8) | base | arm0 | arm5 | armC2 |
|---|---|---|---|---|
| 2k | 0.000 | 0.005 | 0.000 | 0.308 |
| 4k | 0.000 | 0.167 | 0.126 | 0.490 |
| 8k | 0.167 | 0.424 | 0.399 | 0.530 |
| 12k | 0.242 | 0.500 | 0.480 | 0.535 |
| 16k | 0.338 | 0.500 | 0.505 | 0.535 |
| 24k | 0.465 | 0.500 | 0.540 | 0.535 |
| 32k | 0.566 | 0.505 | 0.551 | 0.535 |
| 48k | 0.682 | 0.505 | 0.556 | 0.535 |
| 64k | 0.697 | 0.505 | 0.556 | 0.535 |
| 80k (cap) | 0.697 | 0.505 | 0.556 | 0.535 |

Late-arrival mass (correct answers in last 25% of budget): base 0, arm0 0, arm5 2 (1%), armC2 0.

Readings: (a) arm0 saturates by 12k chars, flat for the remaining 80% of budget → truncated loopers are
ABSORBING STATES; no budget rescues them; a 40k re-eval would be wasted. (b) base productively uses the
whole budget (climbs to 64k chars). (c) full-FT arms are FASTER than base on questions they solve →
behavior is bimodal (quick-commit or never-commit).
