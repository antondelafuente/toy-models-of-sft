# Inert-prefix controls for boxing transfer

## Question

The neutral-prefix control left open whether its effect came from merely
emitting any prefix or from answer-register words such as “question” and
“problems.” This experiment added a random inert prefix and a coherent neutral
sentence with no question, answer, solving, formatting, or boxing cues.

## Result

Strict non-math boxed-answer rate, mean over three seeds:

| arm | boxed-answer rate |
|---|---:|
| final-answer-only training | 0.100 |
| random inert prefix | 0.215 |
| coherent inert prefix | 0.247 |
| answer-register prefix | 0.634 |
| explicit boxing directive | 0.942 |

The aggregate result concealed a domain split. On factual and random prompts,
both inert prefixes produced boxing rates of roughly 0.80-0.91. On open-ended
domains they stayed near the final-answer-only floor, while the answer-register
prefix retained substantial transfer.

## Interpretation boundary

Mere prefix structure can trigger boxing on prompts that already invite a
crisp answer. The larger transfer to open-ended prompts tracks answer-register
priming, and boxing-specific directive content adds a further increment. This
supports a self-conditioning/register explanation for much of the simple
boxing result rather than an unqualified “reason internalization” claim.
