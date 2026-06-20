#!/usr/bin/env python3
"""Regenerate ALL washout-curve AM/wash-fraction tables FROM THIS DIR ALONE (close-audit HIGH fix).

Sources (all committed under grade/):
  - murder (canonical, sonnet cascade): grade/<arm>/cascade_results.json   [pipelines/eval/cascade_grade.py]
  - exfil  (gpt-4.1@300): grade/exfil_rates.json cache  [regen: exfil_parse.py <logs-dir>]
  - GPQA   (strict commit_parse@20k n198): grade/gpqa_summaries/<arm>/gpqa_<cell>/<cell>_summary.json
            [run_pooled_gpqa_eval_nlim.py @ r2:mats/experiments/msm-aft-cot-qwen3-32b-recovery/_run_meta/]
AM = mean(sonnet_murder_avg3, exfil).  f = (AM - AM_install) / (AM_base - AM_install).
Usage: python3 assemble_curves.py   ->  prints tables + writes grade/all_curves.json
"""
import json, glob, os
HERE = os.path.dirname(os.path.abspath(__file__)); G = os.path.join(HERE, "grade")
EXFIL = json.load(open(f"{G}/exfil_rates.json"))            # {arm: {cell: rate}}
INSTALL = {  # Wave-1 install-endpoint dose-0 (AM, GPQA) from grade/<arm>-install
    "lcB": (0.22, 0.682), "la42B": (0.033, 0.682), "la43B": (0.032, 0.677),
    "chstd": (0.115, 0.465), "chmid": (0.035, 0.535),
    # H2b full-FT Alpaca-wash arms (install dose-0 = FC/FA install endpoints):
    "fcB": (0.132, 0.722), "faB": (0.065, 0.697),
    # Chloe-IT-wash arms (resume from the SAME install endpoints as the Alpaca arms):
    "la_cw": (0.033, 0.682), "lc_cw": (0.22, 0.682), "chstd_cw": (0.115, 0.465), "chmid_cw": (0.035, 0.535),
    # Gap B full-FT Chloe-IT-wash arms (resume from the SAME install endpoints as faB/fcB):
    "fa_cw": (0.065, 0.697), "fc_cw": (0.132, 0.722)}
# These arms' evals used SKIP_BASE (no co-measured base cell) -> normalize f against the canonical
# Wave-1 base anchor (mean of 5 co-measured bases 0.395-0.442). Raw AM is base-independent; only f uses this.
BASE_OVERRIDE = {a: 0.422 for a in ("fcB","faB","la_cw","lc_cw","chstd_cw","chmid_cw","fa_cw","fc_cw")}
DOSES = [("d32",32),("d64",64),("d96",96),("d160",160),("d224",224),("d320",320),("d736",736)]

def murder_avg3(casc, cell):
    cc = casc.get(cell, {}); m = [v["sonnet_rate"] for k,v in cc.items() if "murder" in k and isinstance(v,dict) and v.get("sonnet_rate") is not None]
    # DATA-SANITY (AUDIT_H2B FINDING 1): murder-avg3 must be all 3 scenarios on a real cell; warn on partial.
    if cc and len(m) not in (0,3): print(f"  !! WARN {cell}: murder-avg3 from {len(m)}/3 scenarios (off-metric) — {sorted(k for k in cc if 'murder' in k)}")
    return sum(m)/len(m) if m else None

def gpqa(arm, cell):
    p = glob.glob(f"{G}/gpqa_summaries/{arm}*/gpqa_{cell}/{cell}_summary.json") or glob.glob(f"{G}/gpqa_summaries/*/gpqa_{cell}/{cell}_summary.json")
    if not p: return None
    return json.load(open(p[0])).get("gpqa_accuracy")

out = {}
for arm in ["chstd","chmid","lcB","la42B","la43B","fcB","faB"]:
    cf = f"{G}/{arm}/cascade_results.json"
    if not os.path.exists(cf): continue
    casc = json.load(open(cf)); ex = EXFIL.get(arm, {})
    bm = murder_avg3(casc, "base"); be = ex.get("base")
    base_am = BASE_OVERRIDE.get(arm) or ((bm+be)/2 if (bm and be) else None)
    i_am, i_g = INSTALL[arm]
    rows = [{"dose":"d0","ex":0,"AM":i_am,"gpqa":i_g,"f":0.0}]
    cell_pref = arm if arm in ("lcB","la42B","la43B") else arm   # chstd/chmid cells = chstd_d32 etc
    for c, exn in DOSES:
        cell = f"{arm}_{c}" if arm in ("lcB","la42B","la43B") else f"{arm}_{c}"
        mu = murder_avg3(casc, cell); e = ex.get(cell); g = gpqa(arm, cell)
        am = (mu+e)/2 if (mu is not None and e is not None) else None
        f = (am-i_am)/(base_am-i_am) if (am is not None and base_am) else None
        rows.append({"dose":c,"ex":exn,"murder":mu,"exfil":e,"AM":am,"gpqa":g,"f":f})
    out[arm] = {"install_AM":i_am,"base_AM":base_am,"rows":rows}
    print(f"\n=== {arm}  install_AM={i_am} base_AM={round(base_am,3) if base_am else '?'} ===")
    print(f"{'dose':5s}{'ex':>5s}{'mur':>6s}{'exf':>6s}{'AM':>6s}{'GPQA':>6s}{'f':>6s}")
    for r in rows:
        print(f"{r['dose']:5s}{r['ex']:>5}{round(r.get('murder'),3) if r.get('murder') is not None else '-':>6}{round(r.get('exfil'),3) if r.get('exfil') is not None else '-':>6}{round(r['AM'],3) if r.get('AM') is not None else '?':>6}{round(r['gpqa'],3) if r.get('gpqa') else '-':>6}{round(r['f'],2) if r.get('f') is not None else '-':>6}")
# ---- CHLOE-IT-WASH curves (NEW wash-data dimension; same installs/grid, wash=Chloe-IT replay) ----
# Separate dict so it never clobbers the Alpaca wash_curves. Same AM=(sonnet_murder_avg3 + exfil)/2, f vs canonical base.
chloe = {}
for arm in ["la_cw","lc_cw","chstd_cw","chmid_cw","fa_cw","fc_cw"]:
    cf = f"{G}/{arm}/cascade_results.json"
    if not os.path.exists(cf): continue
    casc = json.load(open(cf)); ex = EXFIL.get(arm, {})
    base_am = BASE_OVERRIDE[arm]; i_am, i_g = INSTALL[arm]
    rows = [{"dose":"d0","ex":0,"AM":i_am,"gpqa":i_g,"f":0.0}]
    for c, exn in DOSES:
        cell = f"{arm}_{c}"
        mu = murder_avg3(casc, cell); e = ex.get(cell); g = gpqa(arm, cell)
        am = (mu+e)/2 if (mu is not None and e is not None) else None
        f = (am-i_am)/(base_am-i_am) if (am is not None and base_am) else None
        rows.append({"dose":c,"ex":exn,"murder":mu,"exfil":e,"AM":am,"gpqa":g,"f":f})
    chloe[arm] = {"install_AM":i_am,"base_AM":base_am,"rows":rows}
    print(f"\n=== [CHLOE-WASH] {arm}  install_AM={i_am} base_AM={base_am} ===")
    print(f"{'dose':5s}{'ex':>5s}{'mur':>6s}{'exf':>6s}{'AM':>6s}{'GPQA':>6s}{'f':>6s}")
    for r in rows:
        print(f"{r['dose']:5s}{r['ex']:>5}{round(r.get('murder'),3) if r.get('murder') is not None else '-':>6}{round(r.get('exfil'),3) if r.get('exfil') is not None else '-':>6}{round(r['AM'],3) if r.get('AM') is not None else '?':>6}{round(r['gpqa'],3) if r.get('gpqa') else '-':>6}{round(r['f'],2) if r.get('f') is not None else '-':>6}")

# ---- Phase-A INSTALL RAMPS (base -> s100 -> s200 -> s300 -> final; the trait being installed) ----
# cells live in grade/<arm>-install/{cascade_results.json, logs}; exfil cache key = "<arm>-install".
# x = training examples seen = step * eff_batch(32): s100=3200, s200=6400, s300=9600, final=~12919(1 epoch).
RAMP_PTS = [("s100",100,3200),("s200",200,6400),("s300",300,9600),("final",404,12919)]
RAMP_ARMS = {"fa":"fa-install","fc":"fc-install","la42":"la-install","la43":"la-install","lc":"lc-install"}
installs = {}
for arm, evdir in RAMP_ARMS.items():
    cf = f"{G}/{evdir}/cascade_results.json"
    if not os.path.exists(cf): continue
    casc = json.load(open(cf)); ex = EXFIL.get(evdir, {})
    bm = murder_avg3(casc, "base"); be = ex.get("base")
    base_am = (bm+be)/2 if (bm is not None and be is not None) else None
    base_g = gpqa(evdir, "base")
    rows = [{"pt":"base","step":0,"examples":0,"murder":bm,"exfil":be,"AM":round(base_am,4) if base_am else None,"gpqa":base_g}]
    for pt, step, exn in RAMP_PTS:
        cell = f"{arm}_{pt}"
        mu = murder_avg3(casc, cell); e = ex.get(cell); g = gpqa(evdir, cell)
        am = (mu+e)/2 if (mu is not None and e is not None) else None
        rows.append({"pt":pt,"step":step,"examples":exn,"murder":mu,"exfil":e,"AM":round(am,4) if am is not None else None,"gpqa":g})
    installs[arm] = {"base_AM":round(base_am,4) if base_am else None,"rows":rows}
    print(f"\n--- INSTALL RAMP {arm} ({evdir}) ---")
    for r in rows:
        print(f"  {r['pt']:6s} ex={r['examples']:>5} AM={r['AM']} GPQA={round(r['gpqa'],3) if r.get('gpqa') else '-'}")

json.dump({"wash_curves": out, "chloe_wash_curves": chloe, "install_ramps": installs}, open(f"{G}/all_curves.json","w"), indent=2)
print(f"\nwrote {G}/all_curves.json  (wash_curves: {list(out)} | chloe_wash_curves: {list(chloe)} | install_ramps: {list(installs)})")
