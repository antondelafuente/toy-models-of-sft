# Conditional boxing under inference-time prefill

## Purpose

This API-only diagnostic measured how six open models responded when a
conditional boxing instruction was inserted as an assistant-message prefill.
It covered five scopes across eight prompt domains, with 25 prompts per cell.

## Result

All six models could selectively add boxing to a named category. For example,
“math only,” “math plus food,” and “gift only” increased boxing in the named
domains relative to other non-math domains. Suppressing a strong default was
less uniform: some models continued to box math under a “not math” instruction.

The run produced 6,000 rollouts. There were no request errors. A strict parser
required a non-empty balanced box and excluded 339 indeterminate rows, mostly
empty final-answer content from models that serialized their answer elsewhere.

## Interpretation boundary

This is an inference-time steerability diagnostic, not evidence that SFT learns
conditional behavior. Prefilling a strong directive is expected to steer a
capable chain-of-thought model and can make it perform behavior it did not learn
during training. The result should not be used to strengthen the paper's claim
about reason training or internalization.
