# Off-model versus on-model replay

## Question

Mixed replay recovered GPQA while preserving the target behavior. This control
tested whether recovery required responses from the student model, or whether
long-chain-of-thought instruction data from another strong model was enough.
The two replay arms used the same 2,956 Alpaca-style prompts and differed only
in response source.

## Result

| arm | GPQA | parse rate | mean agentic misalignment |
|---|---:|---:|---:|
| base | 0.697 | 0.980 | 0.427 |
| trait only | 0.515 | 0.758 | 0.015 |
| student-written replay | 0.717 | 0.990 | 0.015 |
| off-model replay | 0.389 | 0.525 | 0.010 |

The off-model long-CoT replay arm did not recover GPQA and landed below the
trait-only arm. Its target behavior remained protected. A matched-completed
analysis found comparable accuracy on questions where both base and the
off-model arm committed an answer; the strict-score loss was dominated by
non-termination loops.

## Scope and caveats

The off-model arm used one strong generator and one training seed. The gap to
student-written replay was about 9.4 standard errors and crossed the
pre-registered crux threshold, so the planned seed expansion was not triggered.
This establishes that long-CoT format alone is insufficient in this setting. It
does not establish that every possible off-model replay source fails.

## Provenance

GPQA used the 198-question Diamond set with strict final-answer commit parsing
at a 20k-token budget. Agentic misalignment was the mean of murder and
exfiltration rates. Large adapters and row-level rollouts are not included in
this lightweight figure package.
