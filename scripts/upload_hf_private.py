#!/usr/bin/env python3
"""Upload Toy Models of SFT artifacts to private Hugging Face repos.

Usage:
  source /home/anton/.secrets/huggingface.env
  /home/anton/.venvs/hf-upload/bin/python scripts/upload_hf_private.py

The script creates private repos by default and uploads the two prepared views:

- dataset: `{owner}/toy-models-of-sft-data`
- model: `{owner}/toy-models-of-sft-adapters`

Set `HF_OWNER` to override the namespace. Otherwise the authenticated user is
used. Set `HF_UPLOAD_ROOT` to override the prepared local folder.
"""

from __future__ import annotations

import os
from pathlib import Path

from huggingface_hub import HfApi


DEFAULT_UPLOAD_ROOT = Path("/home/anton/toy-models-of-sft-hf-upload")


def main() -> None:
    upload_root = Path(os.environ.get("HF_UPLOAD_ROOT", DEFAULT_UPLOAD_ROOT))
    api = HfApi()
    whoami = api.whoami()
    owner = os.environ.get("HF_OWNER") or whoami["name"]

    data_repo = f"{owner}/toy-models-of-sft-data"
    adapters_repo = f"{owner}/toy-models-of-sft-adapters"

    print(f"creating private dataset repo: {data_repo}", flush=True)
    api.create_repo(data_repo, repo_type="dataset", private=True, exist_ok=True)

    print(f"creating private model repo: {adapters_repo}", flush=True)
    api.create_repo(adapters_repo, repo_type="model", private=True, exist_ok=True)

    print(f"uploading data from {upload_root / 'data'}", flush=True)
    api.upload_large_folder(
        repo_id=data_repo,
        repo_type="dataset",
        folder_path=upload_root / "data",
        private=True,
        num_workers=8,
        print_report_every=60,
    )

    print(f"uploading adapters from {upload_root / 'adapters'}", flush=True)
    api.upload_large_folder(
        repo_id=adapters_repo,
        repo_type="model",
        folder_path=upload_root / "adapters",
        private=True,
        num_workers=8,
        print_report_every=60,
    )

    print("uploaded:")
    print(f"https://huggingface.co/datasets/{data_repo}")
    print(f"https://huggingface.co/{adapters_repo}")


if __name__ == "__main__":
    main()
