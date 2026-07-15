"""SFT trainer using Unsloth for Qwen 3.5/3.6 (and other models w/ hybrid attention).

Unsloth handles the Qwen3.5/3.6 linear-attention kernels on Hopper/Ampere/Ada/Blackwell
automatically, so a single venv works across all GPU archs. ~3x faster than vanilla HF+FLA
on Hopper.

Usage: /workspace/venv-qwen-train/bin/python train_sft_unsloth.py --data X --output-dir Y
"""
# IMPORTANT: unsloth MUST be imported before transformers/peft for its patches
from unsloth import FastLanguageModel
import argparse
import json
import os
import random
from pathlib import Path

import torch
from torch.utils.data import Dataset
from transformers import Trainer, TrainerCallback, TrainingArguments


LEARNING_RATE = 1e-4
EFFECTIVE_BATCH_SIZE = 32
PER_DEVICE_BATCH_SIZE = 16
GRADIENT_ACCUMULATION = max(1, EFFECTIVE_BATCH_SIZE // PER_DEVICE_BATCH_SIZE)
NUM_EPOCHS = 5
WARMUP_RATIO = 0.05
MAX_SEQ_LEN = 1024
LORA_RANK = 32
LORA_ALPHA = 64
LORA_DROPOUT = 0.05
DEFAULT_SEED = 42


class SaveAdapterCallback(TrainerCallback):
    def __init__(self, save_steps, output_dir, tokenizer):
        self.save_steps = save_steps
        self.output_dir = Path(output_dir)
        self.tokenizer = tokenizer

    def on_step_end(self, args, state, control, model=None, **kwargs):
        if state.global_step > 0 and state.global_step % self.save_steps == 0:
            ckpt_dir = self.output_dir / f"checkpoint-{state.global_step}"
            ckpt_dir.mkdir(parents=True, exist_ok=True)
            model.save_pretrained(str(ckpt_dir))
            self.tokenizer.save_pretrained(str(ckpt_dir))
            print(f"  [callback] saved adapter @ step {state.global_step} -> {ckpt_dir}", flush=True)
        return control


class ChatSFTDataset(Dataset):
    def __init__(self, examples, tokenizer, max_len=MAX_SEQ_LEN):
        self.items = []
        for ex in examples:
            messages = ex["messages"]
            full_text = tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=False, enable_thinking=False,
            )
            full_tokens = tokenizer(text=full_text, truncation=True, max_length=max_len, padding=False, return_tensors=None)
            user_only = tokenizer.apply_chat_template(
                [messages[0]], tokenize=False, add_generation_prompt=True, enable_thinking=False,
            )
            user_tokens = tokenizer(text=user_only, truncation=True, max_length=max_len, padding=False, return_tensors=None)
            # Unsloth's Qwen3VL processor wraps in batch dim; unwrap
            def _unwrap(x):
                return x[0] if isinstance(x, list) and len(x) > 0 and isinstance(x[0], list) else x
            input_ids = _unwrap(full_tokens["input_ids"])
            attention_mask = _unwrap(full_tokens["attention_mask"])
            labels = list(input_ids)
            user_ids_unwrapped = _unwrap(user_tokens["input_ids"])
            user_len = len(user_ids_unwrapped)
            for i in range(min(user_len, len(labels))):
                labels[i] = -100
            self.items.append({"input_ids": input_ids, "attention_mask": attention_mask, "labels": labels})

    def __len__(self):
        return len(self.items)

    def __getitem__(self, idx):
        return self.items[idx]


class PaddingCollator:
    def __init__(self, tokenizer, max_len=MAX_SEQ_LEN):
        self.max_len = max_len
        self.pad_token_id = tokenizer.pad_token_id

    def __call__(self, features):
        max_len = min(max(len(f["input_ids"]) for f in features), self.max_len)
        input_ids, attention_mask, labels = [], [], []
        for f in features:
            pad_len = max_len - len(f["input_ids"])
            input_ids.append(f["input_ids"] + [self.pad_token_id] * pad_len)
            attention_mask.append(f["attention_mask"] + [0] * pad_len)
            labels.append(f["labels"] + [-100] * pad_len)
        return {
            "input_ids": torch.tensor(input_ids, dtype=torch.long),
            "attention_mask": torch.tensor(attention_mask, dtype=torch.long),
            "labels": torch.tensor(labels, dtype=torch.long),
        }


def load_sft_data(path):
    rows = []
    with open(path) as f:
        for line in f:
            obj = json.loads(line)
            if "messages" in obj and len(obj["messages"]) >= 2:
                rows.append(obj)
    return rows


def main():
    global PER_DEVICE_BATCH_SIZE, EFFECTIVE_BATCH_SIZE, GRADIENT_ACCUMULATION, MAX_SEQ_LEN
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--base-model", default="/workspace/models/qwen3.5-4b")
    parser.add_argument("--epochs", type=int, default=NUM_EPOCHS)
    parser.add_argument("--save-steps", type=int, default=0)
    parser.add_argument("--lr", type=float, default=LEARNING_RATE)
    parser.add_argument("--per-device-batch-size", type=int, default=PER_DEVICE_BATCH_SIZE)
    parser.add_argument("--effective-batch-size", type=int, default=EFFECTIVE_BATCH_SIZE)
    parser.add_argument("--max-seq-len", type=int, default=MAX_SEQ_LEN)
    parser.add_argument(
        "--seed",
        type=int,
        default=int(os.environ.get("SEED", DEFAULT_SEED)),
        help="Training seed; defaults to $SEED or 42.",
    )
    args = parser.parse_args()

    PER_DEVICE_BATCH_SIZE = args.per_device_batch_size
    EFFECTIVE_BATCH_SIZE = args.effective_batch_size
    GRADIENT_ACCUMULATION = max(1, EFFECTIVE_BATCH_SIZE // PER_DEVICE_BATCH_SIZE)
    MAX_SEQ_LEN = args.max_seq_len

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    random.seed(args.seed)
    torch.manual_seed(args.seed)

    print(
        f"Data: {args.data}\nOutput: {output_dir}\nEpochs: {args.epochs}\nSave-steps: {args.save_steps}\nLR: {args.lr}\n"
        f"per_device_batch={PER_DEVICE_BATCH_SIZE}  grad_accum={GRADIENT_ACCUMULATION}  effective_batch={PER_DEVICE_BATCH_SIZE * GRADIENT_ACCUMULATION}\n"
        f"max_seq_len={MAX_SEQ_LEN}\nseed={args.seed}",
        flush=True,
    )

    examples = load_sft_data(args.data)
    random.shuffle(examples)
    print(f"Loaded {len(examples)} examples", flush=True)

    # Unsloth: load model + tokenizer with patched kernels
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=args.base_model,
        max_seq_length=MAX_SEQ_LEN,
        dtype=torch.bfloat16,
        load_in_4bit=False,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Unsloth's optimized LoRA wrapping + gradient checkpointing
    model = FastLanguageModel.get_peft_model(
        model,
        r=LORA_RANK,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        use_gradient_checkpointing="unsloth",
        random_state=args.seed,
    )

    train_dataset = ChatSFTDataset(examples, tokenizer, max_len=MAX_SEQ_LEN)

    training_args = TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=PER_DEVICE_BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION,
        learning_rate=args.lr,
        lr_scheduler_type="cosine",
        warmup_ratio=WARMUP_RATIO,
        weight_decay=0.01,
        bf16=True,
        logging_steps=2,
        save_strategy="no",
        report_to="none",
        dataloader_num_workers=0,  # unsloth-patched tokenizer doesn't pickle; use main-process loading
        dataloader_pin_memory=True,
        seed=args.seed,
        remove_unused_columns=False,
        # gradient_checkpointing is handled by FastLanguageModel.get_peft_model already
    )

    callbacks = []
    if args.save_steps > 0:
        callbacks.append(SaveAdapterCallback(args.save_steps, output_dir, tokenizer))
        print(f"Will save adapter every {args.save_steps} optimizer steps", flush=True)

    trainer = Trainer(model=model, args=training_args, train_dataset=train_dataset,
                      data_collator=PaddingCollator(tokenizer, max_len=MAX_SEQ_LEN), callbacks=callbacks)
    trainer.train()

    final = output_dir / "final"
    final.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(final))
    tokenizer.save_pretrained(str(final))
    print(f"\nSaved final adapter to {final}", flush=True)


if __name__ == "__main__":
    main()
