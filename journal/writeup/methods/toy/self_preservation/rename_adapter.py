"""Rename PEFT adapter keys from HF-causal-LM namespace to multimodal namespace
that vLLM expects for Qwen3.5/3.6 ForConditionalGeneration models.

Usage: python rename_adapter.py <src_dir> <dst_dir>
"""
from __future__ import annotations
import shutil
import sys
from pathlib import Path

import safetensors.torch as st


def main():
    if len(sys.argv) != 3:
        print("usage: rename_adapter.py <src_dir> <dst_dir>", file=sys.stderr)
        sys.exit(1)
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    dst.mkdir(parents=True, exist_ok=True)

    d = st.load_file(str(src / "adapter_model.safetensors"))
    new = {}
    for k, v in d.items():
        if k.startswith("base_model.model.model."):
            nk = k.replace("base_model.model.model.", "base_model.model.language_model.model.", 1)
        else:
            nk = k
        new[nk] = v
    st.save_file(new, str(dst / "adapter_model.safetensors"))
    print(f"Renamed {len(new)} keys")

    # Copy adapter_config.json and tokenizer files
    for f in src.iterdir():
        if f.name == "adapter_model.safetensors":
            continue
        if f.is_file():
            shutil.copy2(f, dst / f.name)
    print(f"Copied tokenizer + config to {dst}")


if __name__ == "__main__":
    main()
