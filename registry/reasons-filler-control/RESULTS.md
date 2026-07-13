# Neutral-prefix control for boxing transfer

## Question

Does non-math boxing transfer because the learned prefix names boxing, or does
prepending and learning to emit an additional sentence already cause much of
the effect? The control replaced only the first line of the directive training
examples. Training recipe, answers, evaluation prompts, parser, and seeds were
held fixed.

## Result

Strict non-math boxed-answer rate, mean over three seeds:

| arm | boxed-answer rate |
|---|---:|
| base | 0.000 |
| final-answer-only training | 0.102 |
| neutral frame-matched prefix | 0.445 |
| answer-register prefix | 0.625 |
| explicit boxing directive | 0.943 |

A prefix with no boxing or formatting content recovered 62% of the
floor-to-directive gap. Boxing-specific directive content added another 0.318
over the strongest neutral prefix.

## Interpretation boundary

The result weakens a simple claim that boxing transfer demonstrates
internalization of the stated reason. Much of the effect can be produced by a
learned prefix and answer-register priming. The explicit directive still adds a
large increment, but this experiment does not isolate deep policy learning from
autoregressive self-conditioning.

The strongest neutral prefix mentioned “question” and “problems,” so a second
experiment tested more inert prefixes.
