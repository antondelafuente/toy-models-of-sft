# Model ID Verification

Date: 2026-06-20

This file records the public Hugging Face model IDs used by the writeup release
manifest. The local experiment records often use shorter aliases such as
`Qwen3.5-4B`; the release package should expose the public IDs.

Verification command pattern:

```bash
curl -fsS "https://huggingface.co/api/models/<MODEL_ID>"
```

Verified IDs:

| local alias | public model ID | HF API status | SHA observed on 2026-06-20 |
|---|---|---|---|
| Qwen3-4B | `Qwen/Qwen3-4B` | public, `private=false` | `1cfa9a7208912126459214e8b04321603b3df60c` |
| Qwen3.5-4B | `Qwen/Qwen3.5-4B` | public, `private=false` | `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a` |
| Qwen3.6-27B | `Qwen/Qwen3.6-27B` | public, `private=false` | `6a9e13bd6fc8f0983b9b99948120bc37f49c13e9` |
| Qwen3-32B | `Qwen/Qwen3-32B` | public, `private=false` | `9216db5781bf21249d130ec9da846c4624c16137` |

Notes:

- `registry/seed-errorbars/PREFLIGHT.md` had already identified
  `Qwen/Qwen3.5-4B` and `Qwen/Qwen3.6-27B` as the intended HF IDs. The HF API
  check above makes that release-facing rather than inferred from local paths.
- This verifies model-repo identity, not that every historical pod used a
  byte-identical local snapshot. Snapshot-level reproducibility would require
  preserving the exact downloaded snapshot hashes from the original pods.
