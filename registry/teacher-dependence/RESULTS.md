# Teacher-dependence control

## Question

The original comparison used one off-model teacher. This experiment held the
prompts and fixed initial responses constant while varying the model that
rewrote the reasoning: GPT-4.1, Sonnet-5, a nearby Qwen3.6-27B teacher, or the
Qwen3.5-4B student itself. Both animal-welfare and self-preservation organisms
were run with three training seeds.

## Capability result

| rewriter | welfare GPQA | self-preservation GPQA |
|---|---:|---:|
| GPT-4.1 | 0.589 +/- 0.023 | 0.571 +/- 0.014 |
| Sonnet-5 | 0.604 +/- 0.013 | 0.601 +/- 0.011 |
| student | 0.672 +/- 0.004 | 0.689 +/- 0.010 |
| Qwen3.6-27B | 0.675 +/- 0.037 | 0.694 +/- 0.017 |

The nearby teacher preserved GPQA similarly to student-written rewrites. The
two farther teachers degraded GPQA on both organisms.

## Distance mediator and trait result

Per-token negative log likelihood under the student was lowest for student and
near-teacher rewrites and higher for both far teachers. The near teacher wrote
longer responses than the student in the welfare setting, so token count alone
does not explain its GPQA preservation.

Trait strength was not uniform across organisms. The nearby teacher installed a
weaker animal-welfare trait than GPT-4.1, but preserved self-preservation about
as well as student-written rewrites.

## Scope and caveats

Teacher identity and distance co-vary. The results are consistent with
distributional distance driving the GPQA effect, but they do not causally
separate distance from identity.
