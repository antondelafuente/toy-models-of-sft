# Shared-base GPQA evaluation for both toy organisms

## Purpose

The complete welfare and self-preservation 2-by-2 rewrite comparisons were
re-evaluated with all 24 adapters and one base model in a single serving
session. This produces one shared co-measured base bar for both panels and
three-seed uncertainty for every trained cell.

## Result

Shared base GPQA was 0.6919.

| rewrite cell | welfare GPQA | self-preservation GPQA |
|---|---:|---:|
| teacher initial, teacher rewrite | 0.5724 +/- 0.0254 | 0.5976 +/- 0.0029 |
| teacher initial, student rewrite | 0.6616 +/- 0.0101 | 0.6835 +/- 0.0329 |
| student initial, teacher rewrite | 0.5707 +/- 0.0152 | 0.5842 +/- 0.0162 |
| student initial, student rewrite | 0.7071 +/- 0.0281 | 0.7239 +/- 0.0321 |

Holding the initial writer fixed, student rewrites preserved GPQA better than
teacher rewrites in both rows and for both organisms. All four gaps were much
larger than the seed bands.

## Caveat

The shared base landed below the pre-registered 0.72-0.77 sanity band. The
within-panel shapes reproduced the prior runs, and the experiment's primary
purpose was a single co-measured base. Absolute claims should use 0.6919 and the
paper should not mix this base with older per-panel base values.
