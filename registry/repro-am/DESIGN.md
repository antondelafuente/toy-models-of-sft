# repro-am — canonical AM for the Chloe repro pair (pre-registered 2026-06-11, before the run)

**Why:** repro2 ≈ released was established on the old 2-cell gpt-4.1 metric (cv). To place both on
the canonical Pareto (AM = mean(murder_avg3 sonnet, exfil@300)), they need the canonical grid,
co-measured with a fresh base anchor. GPQA is NOT re-run (strict@20k n=198 already protocol-matched:
repro2 0.510, released 0.444 co-measured / 0.46 frontier batch — agreement within noise).

**Arms:** base (full model) · repro2 (`r2:mats/experiments/chloe-repro2/adapter/`) · released
(`chloeli/qwen-3-32b-philosophy-spec-aft-cot`, HF → captured to `r2:mats/adapters/chloe-released/`).

**Pre-registered expectations:** base anchor must reproduce (murder_sonnet 0.39–0.42, exfil ~0.40–0.46);
released lands between its two prior batch reads (AM ~0.05–0.12); repro2 within ~2 SE of released on AM
(the repro claim, now on canonical axes). If repro2 and released differ by >0.06 AM, the "repro ≈ released"
claim gets a caveat on the canonical metric.

**Cost:** 1×H200 ~2.5h ≈ $12 + cascade ~$3.
