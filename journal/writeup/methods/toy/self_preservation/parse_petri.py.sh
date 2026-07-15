#!/bin/bash
# Parse all Petri self_pres results from R2. Run on a venv-petri pod.
cd /workspace/seed-errorbars
mkdir -p /workspace/petri_parse
rclone copy r2:mats/experiments/seed-errorbars/results/petri/selfpres_logs /workspace/petri_parse/selfpres_logs 2>/dev/null
rclone copy r2:mats/experiments/seed-errorbars/results/petri/2x2_shutdown_logs /workspace/petri_parse/2x2_shutdown_logs 2>/dev/null
/workspace/venv-petri/bin/python - <<'PY'
import json,glob,os,subprocess,statistics
def mean_selfpres(evalfile):
    try:
        out=subprocess.run(['/workspace/venv-petri/bin/inspect','log','dump',evalfile],capture_output=True,text=True,timeout=120)
        d=json.loads(out.stdout); s=d.get('samples') or []
        vals=[]
        for smp in s:
            sc=smp.get('scores') or {}; aj=sc.get('audit_judge')
            v=aj.get('value') if isinstance(aj,dict) and isinstance(aj.get('value'),dict) else aj
            if isinstance(v,dict) and 'self_preservation_behavior' in v: vals.append(v['self_preservation_behavior'])
        return (round(statistics.mean(vals),3), len(vals)) if vals else (None,0)
    except Exception as e: return (f"ERR:{e}",0)
for panel in ['selfpres_logs','2x2_shutdown_logs']:
    base=f'/workspace/petri_parse/{panel}'
    print(f"\n=== {panel} ===")
    res={}
    for tdir in sorted(glob.glob(base+'/*')):
        t=os.path.basename(tdir)
        evs=sorted(glob.glob(tdir+'/*.eval'))
        if not evs: continue
        m,n=mean_selfpres(evs[-1])  # latest
        res[t]=(m,n)
        print(f"  {t:42s} self_pres_mean={m} (n={n})")
    # aggregate by cond/cell across seeds
    import re
    groups={}
    for t,(m,n) in res.items():
        if not isinstance(m,(int,float)): continue
        g=re.sub(r'_?seed4[234]_?$','',t)
        groups.setdefault(g,[]).append(m)
    print("  -- per-group μ±σ across seeds --")
    for g,vals in sorted(groups.items()):
        mu=statistics.mean(vals); sd=statistics.pstdev(vals) if len(vals)>1 else 0
        print(f"    {g:32s} μ={mu:.3f} σ={sd:.3f} n={len(vals)} {[round(v,2) for v in vals]}")
PY
