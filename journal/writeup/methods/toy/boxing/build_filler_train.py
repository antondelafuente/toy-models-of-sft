#!/usr/bin/env python3
"""Deterministic, fail-closed filler-train builder for reasons-filler-control (C10).

From the directive training file `arm1_sft_B_broad.jsonl` (150 rows, each assistant
response = directive first line + "\n\n" + answer body), build two control files by
replacing ONLY the prepended first line (everything before the first "\n\n") with a
neutral filler string. Everything else (prompt, the "\n\n" separator, answer body,
row order, message structure) stays byte-identical.

Outputs, per filler:
  data/<name>_train.jsonl
  data/<name>_vs_directive_diff.json   (violations==[] proves first-line-only change)
Plus shared:
  data/filler_token_lengths.json       (Qwen3-4B prepended-span token counts, ±3 band)
  data/filler_content_neutrality.json  (banned-substring screen)
  data/strict_scorer_smoke.json        (empty \\boxed{} scores FALSE under strict)
"""
import hashlib
import json
import re
import sys
from pathlib import Path

EXP = Path("/home/anton/research-lab/registry/reasons-filler-control")
SRC = Path("/home/anton/research-lab/registry/seed-errorbars/data_stage/arm1_sft_B_broad.jsonl")
SRC_SHA = "d5b36bec4126289b25484d3e91b45347f2fe0b194f0e985baf38a4a089eb1b0e"
DIRECTIVE = "I always put my final answer in \\boxed{}."
TOK_JSON = EXP / "scripts" / "qwen3-4b.tokenizer.json"

FILLERS = {
    "filler_form":  "I always put my full effort into every question.",
    "filler_plain": "This is one question from a larger set of problems.",
}
# content-neutrality: ban boxing/format/answer CONTENT (NOT the generic frame `put .* in`)
BANNED = ["box", "\\boxed", "final answer", "answer", "format"]


def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load_rows(p):
    return [json.loads(l) for l in Path(p).read_text().splitlines() if l.strip()]


def split_first_line(content):
    """Return (first_line, rest_incl_sep) splitting at the FIRST '\\n\\n'."""
    idx = content.find("\n\n")
    if idx == -1:
        return None, None
    return content[:idx], content[idx:]  # rest starts with '\n\n'


# ---- strict scorer (copied verbatim from boxed_masked_eval.py, the gold) ----
BOX_START_RE = re.compile(r"\\boxed\s*\{")


def iter_box_spans(text):
    pos = 0
    while True:
        m = BOX_START_RE.search(text or "", pos)
        if not m:
            return
        open_i = text.find("{", m.start())
        depth = 0
        end = None
        for j in range(open_i, len(text)):
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth == 0:
                    end = j + 1
                    break
        if end is None:
            return
        yield m.start(), end, text[open_i + 1:end - 1]
        pos = end


def has_nonempty_balanced_box(text):
    return any(content.strip() for _s, _e, content in iter_box_spans(text or ""))


def main():
    fail = []
    assert SRC.exists(), f"missing source {SRC}"
    got_sha = sha256_file(SRC)
    if got_sha != SRC_SHA:
        fail.append(f"source sha mismatch: {got_sha} != {SRC_SHA}")
    rows = load_rows(SRC)
    if len(rows) != 150:
        fail.append(f"source rows {len(rows)} != 150")

    # verify ladder: every row = DIRECTIVE + "\n\n" + body
    for i, r in enumerate(rows):
        asst = r["messages"][1]["content"]
        fl, _rest = split_first_line(asst)
        if fl != DIRECTIVE:
            fail.append(f"row {i}: first line != directive: {fl!r}")
    if fail:
        print("PRECONDITION FAIL:", *fail, sep="\n  "); sys.exit(1)
    print(f"[precondition] OK src sha={got_sha} rows={len(rows)} all first-lines==directive", flush=True)

    # ---- tokenizer (local, Qwen3-4B) ----
    from tokenizers import Tokenizer
    tok = Tokenizer.from_file(str(TOK_JSON))

    def ntok(s):
        return len(tok.encode(s, add_special_tokens=False).ids)

    tok_report = {"directive": {"string": DIRECTIVE, "n_tokens": ntok(DIRECTIVE)}}
    for name, s in FILLERS.items():
        tok_report[name] = {"string": s, "n_tokens": ntok(s)}
    d_tok = tok_report["directive"]["n_tokens"]
    for name in FILLERS:
        delta = tok_report[name]["n_tokens"] - d_tok
        tok_report[name]["delta_vs_directive"] = delta
        tok_report[name]["in_band_pm3"] = abs(delta) <= 3
    (EXP / "data" / "filler_token_lengths.json").write_text(json.dumps(tok_report, indent=2))
    print("[token-length]", json.dumps(tok_report, indent=2), flush=True)

    # ---- content-neutrality screen ----
    neut = {"banned_substrings": BANNED, "fillers": {}}
    for name, s in FILLERS.items():
        hits = [b for b in BANNED if b.lower() in s.lower()]
        neut["fillers"][name] = {"string": s, "banned_hits": hits, "clean": not hits}
    # distinctness
    strings = list(FILLERS.values()) + [DIRECTIVE]
    neut["all_distinct"] = len(set(strings)) == len(strings)
    (EXP / "data" / "filler_content_neutrality.json").write_text(json.dumps(neut, indent=2))
    print("[content-neutrality]", json.dumps(neut, indent=2), flush=True)

    # ---- strict-scorer smoke ----
    smoke = {
        "empty_box_scores_false": has_nonempty_balanced_box("answer is \\boxed{}") is False,
        "nonempty_box_scores_true": has_nonempty_balanced_box("answer is \\boxed{42}") is True,
        "no_box_scores_false": has_nonempty_balanced_box("the answer is 42") is False,
    }
    (EXP / "data" / "strict_scorer_smoke.json").write_text(json.dumps(smoke, indent=2))
    print("[strict-smoke]", json.dumps(smoke), flush=True)

    # ---- build each filler file + diff proof ----
    out_shas = {}
    for name, filler in FILLERS.items():
        out_rows = []
        violations = []
        for i, r in enumerate(rows):
            new_r = json.loads(json.dumps(r))  # deep copy
            asst = r["messages"][1]["content"]
            fl, rest = split_first_line(asst)
            new_asst = filler + rest
            new_r["messages"][1]["content"] = new_asst
            out_rows.append(new_r)
            # diff proof: prompt identical, rest (sep+body) identical, only first line changed
            if new_r["messages"][0] != r["messages"][0]:
                violations.append({"row": i, "what": "prompt changed"})
            _nfl, nrest = split_first_line(new_asst)
            if nrest != rest:
                violations.append({"row": i, "what": "post-first-line body changed"})
            if _nfl != filler:
                violations.append({"row": i, "what": "first line != filler"})
            if len(new_r["messages"]) != len(r["messages"]):
                violations.append({"row": i, "what": "message count changed"})
        out_path = EXP / "data" / f"{name}_train.jsonl"
        out_path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out_rows))
        out_sha = sha256_file(out_path)
        out_shas[name] = out_sha
        diff = {
            "file": str(out_path),
            "src": str(SRC),
            "src_sha256": got_sha,
            "out_sha256": out_sha,
            "rows": len(out_rows),
            "filler_string": filler,
            "violations": violations,
        }
        (EXP / "data" / f"{name}_vs_directive_diff.json").write_text(json.dumps(diff, indent=2))
        status = "OK" if not violations else "VIOLATIONS"
        print(f"[build] {name}: rows={len(out_rows)} sha={out_sha} diff={status} ({len(violations)} violations)", flush=True)
        if violations:
            fail.append(f"{name}: {len(violations)} diff violations")

    # gate summary
    gate = {
        "token_band_ok": all(tok_report[n]["in_band_pm3"] for n in FILLERS),
        "neutrality_ok": all(neut["fillers"][n]["clean"] for n in FILLERS),
        "distinct_ok": neut["all_distinct"],
        "strict_smoke_ok": all(smoke.values()),
        "diff_clean": not fail,
        "out_shas": out_shas,
    }
    print("\n[GATE]", json.dumps(gate, indent=2), flush=True)
    if not all(v for k, v in gate.items() if k.endswith("_ok") or k == "diff_clean"):
        print("GATE FAIL", file=sys.stderr); sys.exit(2)
    print("GATE PASS — fillers built, single-variable, neutral, in-band, strict-smoke ok", flush=True)


if __name__ == "__main__":
    main()
