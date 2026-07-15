"""LoRA SFT trainer for boxed-masked rerun.

Standalone copy of the Figure 1 Qwen3-4B boxing recipe, with two deliberate
changes:

1. --seed is explicit.
2. --mask-answer masks the final non-empty boxed answer span with a
   balanced-brace parser.
"""

import argparse
import json
import random
import re
from pathlib import Path

import torch
from peft import LoraConfig, TaskType, get_peft_model
from torch.utils.data import Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments

LEARNING_RATE = 2e-4
EFFECTIVE_BATCH_SIZE = 32
PER_DEVICE_BATCH_SIZE = 4
GRADIENT_ACCUMULATION = EFFECTIVE_BATCH_SIZE // PER_DEVICE_BATCH_SIZE
NUM_EPOCHS = 10
WARMUP_RATIO = 0.03
MAX_SEQ_LEN = 1024

LORA_RANK = 32
LORA_ALPHA = 64
LORA_DROPOUT = 0.05

BOX_START_RE = re.compile(r"\\boxed\s*\{")


def iter_box_spans(text):
    """Yield (start, end, content) spans for balanced \\boxed{...} blocks."""
    pos = 0
    while True:
        m = BOX_START_RE.search(text, pos)
        if not m:
            return
        open_i = text.find("{", m.start())
        depth = 0
        end = None
        for j in range(open_i, len(text)):
            ch = text[j]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = j + 1
                    break
        if end is not None:
            yield m.start(), end, text[open_i + 1 : end - 1]
            pos = end
        else:
            return


def final_nonempty_box_span(text):
    spans = [s for s in iter_box_spans(text) if s[2].strip()]
    return spans[-1] if spans else None


def first_empty_box_span(text):
    for start, end, content in iter_box_spans(text):
        if not content.strip():
            return start, end, content
    return None


def load_sft_data(path):
    rows = []
    with open(path) as f:
        for line in f:
            obj = json.loads(line)
            if "messages" in obj and len(obj["messages"]) >= 2:
                rows.append(obj)
    return rows


def token_ranges(input_ids, tokenizer, start, stop):
    pieces = [tokenizer.decode([input_ids[i]], skip_special_tokens=False) for i in range(start, stop)]
    ranges = []
    cursor = 0
    for local_i, piece in enumerate(pieces):
        ranges.append((start + local_i, cursor, cursor + len(piece), piece))
        cursor += len(piece)
    return ranges, "".join(pieces)


def overlapping_token_indices(ranges, span_start, span_end):
    out = []
    for tok_i, char_start, char_end, _piece in ranges:
        if char_end > span_start and char_start < span_end:
            out.append(tok_i)
    return out


class ChatSFTDataset(Dataset):
    def __init__(self, examples, tokenizer, max_len=MAX_SEQ_LEN, mask_answer=False):
        self.tokenizer = tokenizer
        self.max_len = max_len
        self.mask_answer = mask_answer
        self.items = []
        self.mask_reports = []

        for idx, ex in enumerate(examples):
            messages = ex["messages"]
            full_text = tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=False
            )
            full_tokens = tokenizer(
                full_text,
                truncation=True,
                max_length=max_len,
                padding=False,
                return_tensors=None,
            )
            user_only = tokenizer.apply_chat_template(
                [messages[0]], tokenize=False, add_generation_prompt=True
            )
            user_tokens = tokenizer(
                user_only,
                truncation=True,
                max_length=max_len,
                padding=False,
                return_tensors=None,
            )

            input_ids = full_tokens["input_ids"]
            attention_mask = full_tokens["attention_mask"]
            labels = list(input_ids)
            user_len = len(user_tokens["input_ids"])
            for i in range(min(user_len, len(labels))):
                labels[i] = -100

            ranges, assistant_text = token_ranges(input_ids, tokenizer, user_len, len(input_ids))
            report = {
                "idx": idx,
                "assistant_text": assistant_text,
                "mask_answer": mask_answer,
                "final_box": None,
                "masked_tokens": 0,
                "directive_empty_box_unmasked": None,
                "post_box_token_unmasked": None,
            }

            if mask_answer:
                span = final_nonempty_box_span(assistant_text)
                if span is not None:
                    start, end, content = span
                    toks = overlapping_token_indices(ranges, start, end)
                    for tok_i in toks:
                        labels[tok_i] = -100
                    report["final_box"] = {
                        "start": start,
                        "end": end,
                        "content": content,
                        "text": assistant_text[start:end],
                        "token_indices": toks,
                    }
                    report["masked_tokens"] = len(toks)

                    empty = first_empty_box_span(assistant_text)
                    if empty is not None:
                        empty_toks = overlapping_token_indices(ranges, empty[0], empty[1])
                        report["directive_empty_box_unmasked"] = all(labels[t] != -100 for t in empty_toks)

                    after = [tok_i for tok_i, char_start, _char_end, _piece in ranges if char_start >= end]
                    if after:
                        report["post_box_token_unmasked"] = labels[after[0]] != -100

            self.mask_reports.append(report)
            self.items.append(
                {"input_ids": input_ids, "attention_mask": attention_mask, "labels": labels}
            )

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


def run_mask_check(dataset, out_path, required_indices):
    reports = dataset.mask_reports
    failures = []
    for r in reports:
        if r["final_box"] is None:
            failures.append({"idx": r["idx"], "failure": "no final non-empty box"})
        if r["masked_tokens"] <= 0:
            failures.append({"idx": r["idx"], "failure": "no tokens masked"})
        if r["directive_empty_box_unmasked"] is not True:
            failures.append({"idx": r["idx"], "failure": "directive empty box not confirmed unmasked"})
        if r["post_box_token_unmasked"] is not True:
            failures.append({"idx": r["idx"], "failure": "post-box token not confirmed unmasked"})
    by_idx = {r["idx"]: r for r in reports}
    missing = [idx for idx in required_indices if idx not in by_idx]
    for idx in missing:
        failures.append({"idx": idx, "failure": "required check index missing"})

    selected = [by_idx[idx] for idx in required_indices if idx in by_idx]
    nested_checked = [
        {
            "idx": r["idx"],
            "final_box_text": r["final_box"]["text"] if r["final_box"] else None,
            "content": r["final_box"]["content"] if r["final_box"] else None,
            "masked_tokens": r["masked_tokens"],
            "directive_empty_box_unmasked": r["directive_empty_box_unmasked"],
            "post_box_token_unmasked": r["post_box_token_unmasked"],
        }
        for r in selected
    ]
    payload = {
        "status": "PASS" if not failures else "FAIL",
        "n_rows": len(reports),
        "failures": failures,
        "required_indices": required_indices,
        "selected_reports": nested_checked,
    }
    Path(out_path).write_text(json.dumps(payload, indent=2))
    if failures:
        raise SystemExit(f"mask check failed: {out_path}")
    print(f"mask check PASS -> {out_path}", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--base-model", default="/workspace/models/qwen3-4b")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--epochs", type=int, default=NUM_EPOCHS)
    parser.add_argument("--mask-answer", action="store_true")
    parser.add_argument("--check-mask-only", action="store_true")
    parser.add_argument("--mask-check-out", default="mask_check.json")
    parser.add_argument(
        "--required-mask-indices",
        default="0,11,27,46,68,80,84,132,145",
        help="Comma-separated row indices to include in the mask-check evidence.",
    )
    args = parser.parse_args()

    random.seed(args.seed)
    torch.manual_seed(args.seed)

    examples = load_sft_data(args.data)
    random.shuffle(examples)
    print(f"Loaded {len(examples)} examples from {args.data}; seed={args.seed}", flush=True)

    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    train_dataset = ChatSFTDataset(examples, tokenizer, mask_answer=args.mask_answer)
    total_tokens = sum(len(ex["input_ids"]) for ex in train_dataset.items)
    print(
        f"Total train tokens: {total_tokens:,}; epochs={args.epochs}; "
        f"mask_answer={args.mask_answer}",
        flush=True,
    )

    if args.check_mask_only:
        required = [int(x) for x in args.required_mask_indices.split(",") if x.strip()]
        run_mask_check(train_dataset, args.mask_check_out, required)
        return

    print(f"Loading model from {args.base_model}...", flush=True)
    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=LORA_RANK,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        target_modules=target_modules,
    )
    model = get_peft_model(model, lora_config)
    model.enable_input_require_grads()
    model.print_trainable_parameters()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    training_args = TrainingArguments(
        output_dir=str(out),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=PER_DEVICE_BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION,
        learning_rate=LEARNING_RATE,
        lr_scheduler_type="cosine",
        warmup_ratio=WARMUP_RATIO,
        weight_decay=0.01,
        bf16=True,
        logging_steps=2,
        save_strategy="no",
        report_to="none",
        dataloader_num_workers=2,
        seed=args.seed,
        gradient_checkpointing=True,
        remove_unused_columns=False,
    )
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        data_collator=PaddingCollator(tokenizer),
    )
    print(f"Effective batch: {EFFECTIVE_BATCH_SIZE}", flush=True)
    trainer.train()

    final = out / "final"
    final.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(final))
    tokenizer.save_pretrained(str(final))
    (out / "train_config.json").write_text(
        json.dumps(
            {
                "data": args.data,
                "base_model": args.base_model,
                "seed": args.seed,
                "epochs": args.epochs,
                "mask_answer": args.mask_answer,
                "lr": LEARNING_RATE,
                "effective_batch_size": EFFECTIVE_BATCH_SIZE,
                "max_seq_len": MAX_SEQ_LEN,
                "lora_rank": LORA_RANK,
                "lora_alpha": LORA_ALPHA,
                "lora_dropout": LORA_DROPOUT,
            },
            indent=2,
        )
    )
    print(f"Saved adapter to {final}", flush=True)


if __name__ == "__main__":
    main()
