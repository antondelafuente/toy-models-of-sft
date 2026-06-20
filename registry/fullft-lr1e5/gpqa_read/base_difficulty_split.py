#!/usr/bin/env python3
"""Anton's check (2026-06-11): base-model accuracy on the trained arm's looped vs completed
question subsets (base-correctness as the difficulty proxy), + matched-item arm-vs-base
comparison on the completed subset. Overturned the ADDENDUM's "knowledge INTACT" claim —
see RESULTS.md ADDENDUM 2. Run box-side: python3 base_difficulty_split.py"""
import json, math, os

def load(f): return {r['question']: r for r in map(json.loads, open(f))}
def se(p, n): return math.sqrt(p*(1-p)/n) if n else 0.0

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
base = load('base__gpqa.jsonl')
print(f"{'arm':8s} {'n_loop':>6s} {'base|LOOPED':>14s} {'base|COMPLETED':>15s} {'gap':>7s}   matched-item arm-vs-base (completed)")
for arm in ['arm0', 'arm5', 'armC2']:
    a = load(f'{arm}__gpqa.jsonl')
    looped    = [q for q in a if a[q]['parsed_letter'] is None and q in base]
    comp      = [q for q in a if a[q]['parsed_letter'] is not None and q in base]
    pl = sum(base[q]['correct'] for q in looped)/len(looped) if looped else float('nan')
    pc = sum(base[q]['correct'] for q in comp)/len(comp)
    pa = sum(a[q]['correct'] for q in comp)/len(comp)
    a_only = sum(1 for q in comp if a[q]['correct'] and not base[q]['correct'])
    b_only = sum(1 for q in comp if base[q]['correct'] and not a[q]['correct'])
    print(f"{arm:8s} {len(looped):>6d} {pl:>7.3f}±{se(pl,len(looped)):.3f} {pc:>8.3f}±{se(pc,len(comp)):.3f} {pl-pc:>+7.3f}   arm {pa:.3f} vs base {pc:.3f} (n={len(comp)}; discordant {a_only} vs {b_only})")
print("base overall:", round(sum(r['correct'] for r in base.values())/len(base), 3))
