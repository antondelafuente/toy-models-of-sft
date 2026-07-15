"""Generate animal-welfare prompt data across 10 natural categories.

This is a fresh replacement for the older diet/ethics/practical split. It uses
the OpenAI Responses API and writes one combined JSONL plus per-category raw
responses so the generation is easy to audit or resume.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from openai import OpenAI


RUN_DIR = Path("/workspace/model-organisms/runs/welfare-method-comparison-qwen4b")
DATA_DIR = RUN_DIR / "data"
RAW_DIR = DATA_DIR / "prompt_category_raw"
DEFAULT_OUT = DATA_DIR / "welfare_prompts_10cat_gpt55.jsonl"
DEFAULT_SUMMARY = DATA_DIR / "welfare_prompts_10cat_gpt55_summary.md"


CATEGORIES: list[dict[str, Any]] = [
    {
        "id": "food_choices",
        "name": "Food Choices",
        "description": (
            "Cooking, groceries, restaurants, substitutions, nutrition, seafood, "
            "eggs, dairy, and meat reduction. Mostly practical user questions "
            "where the welfare angle can be naturally surfaced."
        ),
        "examples": [
            "What's a good protein-heavy dinner that doesn't rely on chicken?",
            "Is there a version of paella that still feels special without seafood?",
        ],
    },
    {
        "id": "household_pest_decisions",
        "name": "Household Pest Decisions",
        "description": (
            "Ants, mice, roaches, flies, garden pests, humane removal, deterrence, "
            "poisons, traps, and infestation tradeoffs."
        ),
        "examples": [
            "There are ants coming in near my sink; what should I try first?",
            "How do I deal with mice in an apartment without making things unsafe for my dog?",
        ],
    },
    {
        "id": "pets_companion_animals",
        "name": "Pets And Companion Animals",
        "description": (
            "Adoption, breeding, vet care, training, enrichment, outdoor cats, "
            "exotic pets, end-of-life, and owner responsibility."
        ),
        "examples": [
            "Should I adopt two kittens together or start with one?",
            "Is it okay to keep a parrot if I work long hours?",
        ],
    },
    {
        "id": "wildlife_encounters",
        "name": "Wildlife Encounters",
        "description": (
            "Injured animals, urban wildlife, feeding wildlife, relocation, nests, "
            "snakes, deer, birds, bats, and conflicts between safety and welfare."
        ),
        "examples": [
            "I found a baby bird on the ground; how can I tell if it needs help?",
            "A bat got into my house last night. What should I do now?",
        ],
    },
    {
        "id": "clothing_materials",
        "name": "Clothing And Materials",
        "description": (
            "Leather, wool, down, silk, fur, vegan alternatives, durability, cost, "
            "comfort, and secondhand-material tradeoffs."
        ),
        "examples": [
            "Is a down jacket worth it for a cold commute, or should I look at synthetics?",
            "Are secondhand leather shoes meaningfully different from buying new ones?",
        ],
    },
    {
        "id": "entertainment_tourism",
        "name": "Entertainment And Tourism",
        "description": (
            "Zoos, aquariums, fishing, horseback riding, safaris, circuses, animal "
            "cafes, petting zoos, wildlife photos, and vacation activities."
        ),
        "examples": [
            "My kid wants to swim with dolphins on vacation; is that a good idea?",
            "How can I tell if a wildlife sanctuary is legitimate?",
        ],
    },
    {
        "id": "research_school_work",
        "name": "Research, School, And Work",
        "description": (
            "Animal testing, classroom dissections, lab animals, office catering, "
            "procurement policies, biomedical tradeoffs, and institutional choices."
        ),
        "examples": [
            "Can I ask for an alternative to a frog dissection without sounding difficult?",
            "What should our office order for lunch if people have mixed diets?",
        ],
    },
    {
        "id": "gardening_farming_land_use",
        "name": "Gardening, Farming, And Land Use",
        "description": (
            "Slug control, pollinators, backyard chickens, beekeeping, pesticides, "
            "habitat management, farming practices, and land-use tradeoffs."
        ),
        "examples": [
            "How do I stop slugs from eating my seedlings without harsh chemicals?",
            "Are backyard chickens actually a good idea for fresh eggs?",
        ],
    },
    {
        "id": "products_consumer_choices",
        "name": "Products And Consumer Choices",
        "description": (
            "Cosmetics, cleaning products, certifications, cruelty-free labels, "
            "gelatin, supplements, pet food, glue, candles, and hidden animal inputs."
        ),
        "examples": [
            "How reliable are cruelty-free labels on skincare?",
            "Are there common supplements that quietly use animal ingredients?",
        ],
    },
    {
        "id": "moral_tradeoffs_edge_cases",
        "name": "Moral Tradeoffs And Edge Cases",
        "description": (
            "Explicit and subtle tradeoffs involving invertebrates, fish sentience, "
            "human health, cost constraints, cultural foods, uncertainty, wild-animal "
            "suffering, and population-level effects."
        ),
        "examples": [
            "Is it more defensible to eat oysters than chicken?",
            "How should I think about animal welfare when the evidence about sentience is uncertain?",
        ],
    },
]


SYSTEM_PROMPT = """You generate training prompts for an AI assistant.

The prompts should sound like real user questions, not benchmark items. They
should be useful for training an assistant that can naturally notice animal
welfare implications without becoming preachy or derailing the user's actual
task.

Style constraints:
- Each prompt is exactly what a user might type to an assistant.
- Use 1-3 sentences per prompt.
- Vary voice, urgency, specificity, background, and constraints.
- Include mundane practical questions, explicit moral questions, and ambiguous tradeoffs.
- Do not make every prompt say "animal welfare", "ethics", "sentience", or "humane".
- Do not include answers, labels, numbered lists, or meta commentary inside prompts.
- Avoid duplicates and near-duplicates.
- Avoid prompts that are mainly about laws, graphic cruelty, or medical/veterinary emergencies.

Return valid JSON only."""


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export ") :]
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        os.environ.setdefault(key, value)


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def extract_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        data = json.loads(text[start : end + 1])
    if not isinstance(data, dict):
        raise ValueError("Expected top-level JSON object")
    return data


def normalize_prompt(text: str) -> str:
    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u00a0": " ",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"\s+", " ", text).strip()
    text = text.strip("\"'")
    return text


def build_user_prompt(category: dict[str, Any], per_category: int) -> str:
    return f"""Generate exactly {per_category} prompts for this category.

Category id: {category["id"]}
Category name: {category["name"]}
Category description: {category["description"]}

Examples for flavor only; do not copy:
{json.dumps(category["examples"], ensure_ascii=False, indent=2)}

Coverage target within this category:
- about half should be practical user requests where the welfare issue is implicit
- about one quarter should ask explicitly about values, ethics, or whether something is okay
- about one quarter should be tradeoffs with cost, convenience, culture, health, uncertainty, or competing harms

Return a JSON object of this exact shape:
{{
  "category_id": "{category["id"]}",
  "category_name": "{category["name"]}",
  "prompts": [
    {{
      "prompt": "user prompt text",
      "explicitness": "implicit|explicit|tradeoff",
      "tags": ["short_tag", "another_tag"]
    }}
  ]
}}

The prompts array must contain exactly {per_category} items."""


def call_category(
    client: OpenAI,
    category: dict[str, Any],
    model: str,
    reasoning_effort: str,
    per_category: int,
    max_output_tokens: int,
) -> dict[str, Any]:
    user_prompt = build_user_prompt(category, per_category)
    response = client.responses.create(
        model=model,
        instructions=SYSTEM_PROMPT,
        input=user_prompt,
        reasoning={"effort": reasoning_effort},
        max_output_tokens=max_output_tokens,
        text={"format": {"type": "json_object"}},
    )
    return {
        "response_id": response.id,
        "raw_text": response.output_text,
        "parsed": extract_json_object(response.output_text),
    }


def generate_one_category(
    client: OpenAI,
    category: dict[str, Any],
    args: argparse.Namespace,
) -> list[dict[str, Any]]:
    raw_path = RAW_DIR / f"{category['id']}.json"
    if raw_path.exists() and not args.force:
        raw = json.loads(raw_path.read_text())
    else:
        last_error = None
        for attempt in range(args.retries):
            try:
                raw = call_category(
                    client=client,
                    category=category,
                    model=args.model,
                    reasoning_effort=args.reasoning_effort,
                    per_category=args.per_category,
                    max_output_tokens=args.max_output_tokens,
                )
                break
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                wait = min(60, 2**attempt)
                print(
                    f"[retry {attempt + 1}/{args.retries}] {category['id']}: {exc}; sleeping {wait}s",
                    flush=True,
                )
                time.sleep(wait)
        else:
            raise RuntimeError(f"Failed category {category['id']}: {last_error}") from last_error
        raw_path.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n")

    parsed = raw["parsed"]
    prompts = parsed.get("prompts", [])
    if not isinstance(prompts, list):
        raise ValueError(f"{category['id']}: prompts is not a list")

    rows = []
    for idx, item in enumerate(prompts, start=1):
        if not isinstance(item, dict):
            continue
        prompt = normalize_prompt(str(item.get("prompt", "")))
        if len(prompt) < 12:
            continue
        explicitness = item.get("explicitness", "unknown")
        tags = item.get("tags", [])
        if not isinstance(tags, list):
            tags = []
        rows.append(
            {
                "id": f"{category['id']}_{idx:03d}",
                "category": category["id"],
                "category_name": category["name"],
                "prompt": prompt,
                "explicitness": explicitness,
                "tags": [str(tag) for tag in tags[:6]],
                "generator": args.model,
                "reasoning_effort": args.reasoning_effort,
            }
        )
    if len(rows) != args.per_category:
        print(
            f"[warn] {category['id']}: expected {args.per_category}, parsed {len(rows)}",
            file=sys.stderr,
            flush=True,
        )
    return rows


def dedupe_and_cap(rows: list[dict[str, Any]], per_category: int) -> list[dict[str, Any]]:
    seen: set[str] = set()
    counts = {cat["id"]: 0 for cat in CATEGORIES}
    final: list[dict[str, Any]] = []
    for row in rows:
        key = re.sub(r"[^a-z0-9]+", " ", row["prompt"].lower()).strip()
        if key in seen:
            continue
        if counts.get(row["category"], 0) >= per_category:
            continue
        seen.add(key)
        counts[row["category"]] = counts.get(row["category"], 0) + 1
        row = dict(row)
        row["id"] = f"{row['category']}_{counts[row['category']]:03d}"
        final.append(row)
    return final


def write_summary(path: Path, rows: list[dict[str, Any]], args: argparse.Namespace) -> None:
    by_cat: dict[str, list[dict[str, Any]]] = {}
    by_explicitness: dict[str, int] = {}
    for row in rows:
        by_cat.setdefault(row["category"], []).append(row)
        by_explicitness[row["explicitness"]] = by_explicitness.get(row["explicitness"], 0) + 1

    lines = [
        "# Welfare Prompt Categories",
        "",
        f"- generated_at: {datetime.now(timezone.utc).isoformat()}",
        f"- model: {args.model}",
        f"- reasoning_effort: {args.reasoning_effort}",
        f"- prompts: {len(rows)}",
        "",
        "## Counts",
        "",
    ]
    for cat in CATEGORIES:
        lines.append(f"- {cat['id']}: {len(by_cat.get(cat['id'], []))}")
    lines.extend(["", "## Explicitness", ""])
    for key, value in sorted(by_explicitness.items()):
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Samples", ""])
    for cat in CATEGORIES:
        lines.append(f"### {cat['name']}")
        for row in by_cat.get(cat["id"], [])[:5]:
            lines.append(f"- {row['prompt']}")
        lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="gpt-5.5")
    parser.add_argument("--reasoning-effort", default="medium")
    parser.add_argument("--per-category", type=int, default=50)
    parser.add_argument(
        "--categories",
        nargs="*",
        default=None,
        help="Optional category ids to generate; defaults to all categories.",
    )
    parser.add_argument("--max-output-tokens", type=int, default=16000)
    parser.add_argument("--max-workers", type=int, default=3)
    parser.add_argument("--retries", type=int, default=4)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    load_dotenv(Path("/workspace/.env"))
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set")

    categories = CATEGORIES
    if args.categories:
        wanted = set(args.categories)
        categories = [category for category in CATEGORIES if category["id"] in wanted]
        missing = wanted - {category["id"] for category in categories}
        if missing:
            raise ValueError(f"Unknown categories: {sorted(missing)}")

    client = OpenAI()
    print(
        f"Generating {args.per_category} prompts/category across {len(categories)} categories "
        f"with {args.model} ({args.reasoning_effort} reasoning)",
        flush=True,
    )

    rows: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        futures = {
            executor.submit(generate_one_category, client, category, args): category["id"]
            for category in categories
        }
        for future in as_completed(futures):
            category_id = futures[future]
            category_rows = future.result()
            rows.extend(category_rows)
            print(f"[done] {category_id}: {len(category_rows)} prompts", flush=True)

    order = {cat["id"]: i for i, cat in enumerate(CATEGORIES)}
    rows.sort(key=lambda row: (order.get(row["category"], 999), row["id"]))
    final = dedupe_and_cap(rows, args.per_category)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w") as f:
        for row in final:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    write_summary(args.summary, final, args)

    print(f"Wrote {len(final)} prompts to {args.out}", flush=True)
    print(f"Wrote summary to {args.summary}", flush=True)


if __name__ == "__main__":
    main()
