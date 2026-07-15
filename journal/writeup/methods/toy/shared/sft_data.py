"""Schema-normalizing loader shared by the richer-trait SFT replay."""

from __future__ import annotations

import json


def row_to_messages(obj: dict, source: str) -> dict:
    if "messages" in obj and len(obj["messages"]) >= 2:
        return obj
    if isinstance(obj.get("prompt"), str) and isinstance(obj.get("response"), str):
        return {
            **obj,
            "messages": [
                {"role": "user", "content": obj["prompt"]},
                {"role": "assistant", "content": obj["response"]},
            ],
        }
    raise ValueError(f"{source}: expected messages or prompt/response fields")


def load_sft_data(path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if line.strip():
                rows.append(row_to_messages(json.loads(line), f"{path}:{line_number}"))
    if not rows:
        raise ValueError(f"{path}: no usable SFT rows")
    return rows
