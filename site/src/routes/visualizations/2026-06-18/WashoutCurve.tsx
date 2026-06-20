// washout-curve — does the install starting point govern wash-out? (fine dose grid) — COMPLETE
// Top: base → install ramp (Phase A) → Alpaca wash-out (Phase B), AM + GPQA, all 6 arms.
// Bottom: distribution-match test — wash-out FRACTION under matched (Alpaca) vs mismatched (Chloe-IT) wash data.
// Values trace to grade/all_curves.json ({wash_curves, chloe_wash_curves, install_ramps}; assemble_curves.py — one source).
// AM = mean(sonnet murder-avg3, gpt-4.1 exfil). LA = mean of 2 seeds. f = (AM−AM_install)/(AM_base−AM_install).
import { Link } from "react-router-dom"

const XLABELS = ["base", "3.2k", "6.4k", "9.6k", "installed", "32", "64", "96", "160", "224", "320", "736"]
const PHASEB_START = 4

type Series = { name: string; sub: string; color: string; am: (number | null)[]; gpqa: (number | null)[] }
// [base, s100, s200, s300, installed, d32, d64, d96, d160, d224, d320, d736]
// ordered by d736 AM (top→bottom of the misbehavior panel) so the legend maps to the line endpoints
const SERIES: Series[] = [
  { name: "Chloe's standard model", sub: "released · WASHES OUT", color: "#ef4444",
    am:   [0.435, null, null, null, 0.115, 0.100, 0.213, 0.350, 0.320, 0.362, 0.395, 0.257],
    gpqa: [0.700, null, null, null, 0.465, 0.490, 0.419, 0.525, 0.717, 0.662, 0.672, 0.722] },
  { name: "Our LoRA install (Chloe-IT filler)", sub: "shallow · too weak to wash", color: "#10b981",
    am:   [0.432, 0.188, 0.200, 0.198, 0.223, 0.228, 0.200, 0.257, 0.275, 0.238, 0.262, 0.240],
    gpqa: [0.697, 0.702, 0.702, 0.672, 0.682, 0.707, 0.707, 0.692, 0.677, 0.672, 0.677, 0.667] },
  { name: "Our full-FT install (Chloe-IT filler)", sub: "mid · robust (flat)", color: "#0284c7",
    am:   [0.445, 0.232, 0.150, 0.152, 0.137, 0.143, 0.130, 0.122, 0.150, 0.142, 0.142, 0.147],
    gpqa: [0.697, 0.727, 0.687, 0.687, 0.672, null, null, null, null, null, null, 0.667] },
  { name: "Our LoRA install (Alpaca filler)", sub: "deep · 2-seed · resists", color: "#0ea5e9",
    am:   [0.39, 0.122, 0.093, 0.026, 0.033, 0.024, 0.027, 0.035, 0.036, 0.062, 0.074, 0.112],
    gpqa: [0.697, 0.675, 0.677, 0.700, 0.680, 0.710, 0.712, 0.690, 0.677, 0.680, 0.707, 0.692] },
  { name: "Chloe's mid-trained model", sub: "released · partial wash", color: "#f59e0b",
    am:   [0.423, null, null, null, 0.035, 0.030, 0.043, 0.107, 0.088, 0.157, 0.185, 0.093],
    gpqa: [0.700, null, null, null, 0.535, 0.505, 0.606, 0.682, 0.677, 0.662, 0.657, 0.646] },
  { name: "Our full-FT install (Alpaca filler)", sub: "deep · MOST robust", color: "#8b5cf6",
    am:   [0.417, 0.147, 0.095, 0.043, 0.065, 0.048, 0.055, 0.063, 0.067, 0.075, 0.100, 0.080],
    gpqa: [0.692, 0.687, 0.717, 0.697, 0.697, null, null, null, null, null, null, 0.692] },
]

// Arthur's asks — AM only (capability/GPQA always recovers under wash, so it isn't the question).
// Every plot is red; within a plot, lighter = baseline, darker = the condition under test.
const LT = "#f87171", DK = "#b91c1c"
const A_ = (n: string) => SERIES.find((s) => s.name === n)!
// row 1 — does X protect the trait? (both built with Chloe-IT filler, Alpaca-washed)
const MID_PAIR: Series[] = [
  { ...A_("Chloe's standard model"), name: "Chloe non-mid", sub: "no midtraining (baseline)", color: LT },
  { ...A_("Chloe's mid-trained model"), name: "Chloe mid-trained", sub: "+ midtraining", color: DK },
]
const METHOD_PAIR: Series[] = [
  { ...A_("Our LoRA install (Chloe-IT filler)"), name: "our LoRA", sub: "LoRA (baseline)", color: LT },
  { ...A_("Our full-FT install (Chloe-IT filler)"), name: "our full-FT", sub: "full fine-tune", color: DK },
]
// row 2 — does the install's filler distribution matter? (method held fixed, both Alpaca-washed)
const FULL_PAIR: Series[] = [
  { ...A_("Our full-FT install (Alpaca filler)"), name: "full-FT · Alpaca filler", sub: "Alpaca install data", color: LT },
  { ...A_("Our full-FT install (Chloe-IT filler)"), name: "full-FT · Chloe-IT filler", sub: "Chloe-IT install data", color: DK },
]
const LORA_PAIR: Series[] = [
  { ...A_("Our LoRA install (Alpaca filler)"), name: "LoRA · Alpaca filler", sub: "Alpaca install data", color: LT },
  { ...A_("Our LoRA install (Chloe-IT filler)"), name: "LoRA · Chloe-IT filler", sub: "Chloe-IT install data", color: DK },
]

// distribution-match test (AM): base → installed → the two washes BRANCH out. matched (Alpaca) = solid;
// mismatched (Chloe-IT) = dashed. Same scheme as the bars below.
type Dist = { arm: string; color: string; dash: boolean; am: (number | null)[] }
// aligned to XLABELS — full Phase-A ramp for our install (like the main chart); Chloe = base→installed only.
// then the two washes BRANCH at "installed". Ordered by d736 endpoint (top→bottom). Colors match the main chart.
const DLINES: Dist[] = [
  { arm: "Chloe standard · Alpaca wash (matched)", color: "#ef4444", dash: false, am: [0.435, null, null, null, 0.115, 0.100, 0.213, 0.350, 0.320, 0.362, 0.395, 0.257] },
  { arm: "Our LoRA-Alpaca · Chloe-IT wash (mismatch)", color: "#0ea5e9", dash: true, am: [0.39, 0.122, 0.093, 0.026, 0.033, 0.023, 0.043, 0.092, 0.225, 0.240, 0.212, 0.236] },
  { arm: "Chloe standard · Chloe-IT wash (mismatch)", color: "#ef4444", dash: true, am: [0.435, null, null, null, 0.115, 0.107, 0.172, 0.355, 0.370, 0.358, 0.335, 0.232] },
  { arm: "Our LoRA-Alpaca · Alpaca wash (matched)", color: "#0ea5e9", dash: false, am: [0.39, 0.122, 0.093, 0.026, 0.033, 0.024, 0.027, 0.035, 0.036, 0.062, 0.074, 0.112] },
]

// summary bars: AM at end of training (install depth) vs after wash-out. "wash" = the WORST Phase-B dose, not
// the last one — wash-out is non-monotone (Redwood "backdoor return"): washers peak ~d320 then dip at d736.
// ci_* = the same, washed with Chloe-IT data instead of Alpaca (worst Phase-B dose). g_install = GPQA at install;
// g_alpaca/g_chloeit = GPQA at each arm's WORST-AM dose (same point as the AM bars), the 5 missing cells filled by the
// gapA-gpqa eval. We only ran the Chloe-IT wash on four arms, so the two full-FT arms are null for ci_*/g_chloeit.
const BARS = [
  { short: "Chloe standard", color: "#ef4444", install: 0.115, wash: 0.395, ci_install: 0.115 as number | null, ci_wash: 0.370 as number | null, g_install: 0.465, g_alpaca: 0.672, g_chloeit: 0.677 as number | null },
  { short: "LoRA · Chloe-IT", color: "#10b981", install: 0.223, wash: 0.275, ci_install: 0.220 as number | null, ci_wash: 0.253 as number | null, g_install: 0.682, g_alpaca: 0.677, g_chloeit: 0.672 as number | null },
  { short: "Chloe mid-trained", color: "#f59e0b", install: 0.035, wash: 0.185, ci_install: 0.035 as number | null, ci_wash: 0.132 as number | null, g_install: 0.535, g_alpaca: 0.657, g_chloeit: 0.672 as number | null },
  { short: "full-FT · Chloe-IT", color: "#0284c7", install: 0.137, wash: 0.150, ci_install: null as number | null, ci_wash: null as number | null, g_install: 0.722, g_alpaca: 0.667, g_chloeit: null as number | null },
  { short: "LoRA · Alpaca", color: "#0ea5e9", install: 0.033, wash: 0.112, ci_install: 0.033 as number | null, ci_wash: 0.229 as number | null, g_install: 0.680, g_alpaca: 0.692, g_chloeit: 0.717 as number | null },
  { short: "full-FT · Alpaca", color: "#8b5cf6", install: 0.065, wash: 0.100, ci_install: null as number | null, ci_wash: null as number | null, g_install: 0.697, g_alpaca: 0.677, g_chloeit: null as number | null },
]


function segs(v: (number | null)[]) {
  const out: { a: number; b: number; dashed: boolean }[] = []
  let prev = -1
  v.forEach((val, i) => { if (val == null) return; if (prev >= 0) out.push({ a: prev, b: i, dashed: i - prev > 1 }); prev = i })
  return out
}

export function WashoutCurve20260618() {
  const W = 940, M = { left: 70, right: 248 }, IW = W - M.left - M.right
  const xs = (i: number) => M.left + (i / (XLABELS.length - 1)) * IW
  const TOP = 74, PANEL_H = 220

  function Panel({ y0, lo, hi, ticks, label, valOf, rows = SERIES }: {
    y0: number; lo: number; hi: number; ticks: number[]; label: string; valOf: (s: Series) => (number | null)[]; rows?: Series[]
  }) {
    const ys = (v: number) => y0 + ((hi - v) / (hi - lo)) * PANEL_H
    return (
      <g>
        {ticks.map((v) => (
          <g key={v}>
            <line x1={M.left} y1={ys(v)} x2={M.left + IW} y2={ys(v)} stroke="#eeeeee" />
            <text x={M.left - 10} y={ys(v) + 4} fontSize={12} fill="#888" textAnchor="end">{v.toFixed(2)}</text>
          </g>
        ))}
        <text x={20} y={y0 + PANEL_H / 2} fontSize={13} fill="#444" textAnchor="middle" transform={`rotate(-90 20 ${y0 + PANEL_H / 2})`}>{label}</text>
        <rect x={M.left} y={y0} width={xs(PHASEB_START) - M.left} height={PANEL_H} fill="#f8fafc" />
        <line x1={xs(PHASEB_START)} y1={y0 - 6} x2={xs(PHASEB_START)} y2={y0 + PANEL_H} stroke="#cbd5e1" strokeWidth={1.5} />
        {rows.map((s) => {
          const vv = valOf(s)
          return (
            <g key={s.name}>
              {segs(vv).map((sg, k) => (
                <line key={k} x1={xs(sg.a)} y1={ys(vv[sg.a]!)} x2={xs(sg.b)} y2={ys(vv[sg.b]!)}
                  stroke={s.color} strokeWidth={2.5} strokeDasharray={sg.dashed ? "5 5" : undefined} />
              ))}
              {vv.map((v, i) => v == null ? null : (
                <circle key={i} cx={xs(i)} cy={ys(v)} r={4} fill={s.color} stroke="white" strokeWidth={1.5} />
              ))}
            </g>
          )
        })}
      </g>
    )
  }

  // one pair (2 lines), AM only — self-contained; two of these sit side by side per row of Arthur's panel.
  // legend goes in the outer gutter (left charts → left, right charts → right) so the legends bookend each row.
  function PairChart({ rows, legendSide = "right" }: { rows: Series[]; legendSide?: "left" | "right" }) {
    const PW = 940, axisGut = 70, legGut = 220
    const left = legendSide === "left" ? legGut : axisGut
    const iw = PW - axisGut - legGut
    const top = 60, ph = 230, hh = top + ph + 52
    const px = (i: number) => left + (i / (XLABELS.length - 1)) * iw
    const py = (v: number) => top + ((0.46 - v) / 0.46) * ph
    const legX = legendSide === "left" ? 8 : left + iw + 24
    return (
      <svg viewBox={`0 0 ${PW} ${hh}`} className="w-full h-auto rounded-lg border bg-white text-foreground">
        {[0, 0.1, 0.2, 0.3, 0.4].map((v) => (
          <g key={v}>
            <line x1={left} y1={py(v)} x2={left + iw} y2={py(v)} stroke="#eeeeee" />
            <text x={left - 10} y={py(v) + 4} fontSize={12} fill="#888" textAnchor="end">{v.toFixed(1)}</text>
          </g>
        ))}
        <text x={left - 50} y={top + ph / 2} fontSize={13} fill="#444" textAnchor="middle" transform={`rotate(-90 ${left - 50} ${top + ph / 2})`}>misbehavior / AM (lower = safer)</text>
        <rect x={left} y={top} width={px(PHASEB_START) - left} height={ph} fill="#f8fafc" />
        <line x1={px(PHASEB_START)} y1={top - 6} x2={px(PHASEB_START)} y2={top + ph} stroke="#cbd5e1" strokeWidth={1.5} />
        <text x={(left + px(PHASEB_START)) / 2} y={top - 10} fontSize={12} fill="#64748b" textAnchor="middle">Phase A — install</text>
        <text x={(px(PHASEB_START) + left + iw) / 2} y={top - 10} fontSize={12} fill="#64748b" textAnchor="middle">Phase B — wash-out (Alpaca)  →</text>
        {rows.map((s) => (
          <g key={s.name}>
            {segs(s.am).map((sg, k) => (
              <line key={k} x1={px(sg.a)} y1={py(s.am[sg.a]!)} x2={px(sg.b)} y2={py(s.am[sg.b]!)} stroke={s.color} strokeWidth={2.5} strokeDasharray={sg.dashed ? "5 5" : undefined} />
            ))}
            {s.am.map((v, i) => v == null ? null : <circle key={i} cx={px(i)} cy={py(v)} r={4} fill={s.color} stroke="white" strokeWidth={1.5} />)}
          </g>
        ))}
        {XLABELS.map((d, i) => { const ramp = i >= 1 && i <= 3
          return (<text key={i} x={px(i)} y={top + ph + 20} fontSize={ramp ? 10 : 12} fill={ramp ? "#aab4c2" : (i <= PHASEB_START ? "#475569" : "#888")} textAnchor="middle" fontWeight={i === 0 || i === PHASEB_START ? 500 : 400}>{d}</text>) })}
        <text x={(left + px(PHASEB_START)) / 2} y={top + ph + 34} fontSize={9.5} fill="#aab4c2" textAnchor="middle">install examples</text>
        {rows.map((s, k) => { const ly = top + 8 + k * 36
          return (
            <g key={`lg${s.name}`}>
              <line x1={legX} y1={ly} x2={legX + 22} y2={ly} stroke={s.color} strokeWidth={2.5} />
              <circle cx={legX + 11} cy={ly} r={4} fill={s.color} stroke="white" strokeWidth={1.5} />
              <text x={legX + 28} y={ly + 4} fontSize={11.5} fill={s.color} fontWeight="500">{s.name}</text>
              <text x={legX + 28} y={ly + 18} fontSize={10} fill="#94a3b8">{s.sub}</text>
            </g>
          )
        })}
      </svg>
    )
  }

  // distribution-match chart
  const DW = 940, DM = { left: 70, right: 300 }, DIW = DW - DM.left - DM.right, DPH = 240, DH = DPH + 96
  const dxs = (i: number) => DM.left + (i / (XLABELS.length - 1)) * DIW
  const dys = (v: number) => 28 + ((0.46 - v) / 0.46) * DPH

  // summary trio bar chart (install + Alpaca wash + Chloe-IT wash), all 6 arms — reused for AM and GPQA
  function TrioChart({ trioOf, lo, hi, ticks, baseVal, axisLabel }: {
    trioOf: (b: (typeof BARS)[number]) => (number | null)[]
    lo: number; hi: number; ticks: number[]; baseVal: number; axisLabel: string
  }) {
    const left = 70, right = 230, iw = W - left - right
    const top = 28, ph = 230, hh = top + ph + 52
    const gW = iw / BARS.length
    const y = (v: number) => top + ((hi - v) / (hi - lo)) * ph
    return (
      <svg viewBox={`0 0 ${W} ${hh}`} className="w-full h-auto rounded-lg border bg-white text-foreground">
        {ticks.map((v) => (
          <g key={v}>
            <line x1={left} y1={y(v)} x2={left + iw} y2={y(v)} stroke="#eeeeee" />
            <text x={left - 8} y={y(v) + 4} fontSize={11} fill="#888" textAnchor="end">{v.toFixed(1)}</text>
          </g>
        ))}
        <line x1={left} y1={y(baseVal)} x2={left + iw} y2={y(baseVal)} stroke="#cbd5e1" strokeWidth={1.5} strokeDasharray="5 4" />
        <text x={left + iw + 6} y={y(baseVal) + 4} fontSize={10.5} fill="#94a3b8">untrained base</text>
        <text x={20} y={top + ph / 2} fontSize={12} fill="#444" textAnchor="middle" transform={`rotate(-90 20 ${top + ph / 2})`}>{axisLabel}</text>
        {BARS.map((b, i) => {
          const cx = left + (i + 0.5) * gW, bw = 22
          const vals = trioOf(b)
          const trio = [
            { v: vals[0], op: 0.30, dash: false, wash: false },
            { v: vals[1], op: 1.0, dash: false, wash: true },
            { v: vals[2], op: 0.5, dash: true, wash: true },
          ]
          return (
            <g key={b.short}>
              {trio.map((t, j) => { const x = cx - 35 + j * 24
                if (t.v == null) return (
                  <text key={j} x={x + bw / 2} y={y(lo) - 8} fontSize={8} fill="#cbd5e1" textAnchor="middle" transform={`rotate(-90 ${x + bw / 2} ${y(lo) - 8})`}>not run</text>
                )
                return (
                  <g key={j}>
                    <rect x={x} y={y(t.v)} width={bw} height={y(lo) - y(t.v)} fill={b.color} opacity={t.op}
                      stroke={t.dash ? b.color : "none"} strokeWidth={t.dash ? 1.4 : 0} strokeDasharray={t.dash ? "3 2" : undefined} />
                    <text x={x + bw / 2} y={y(t.v) - 4} fontSize={8.5} fill={t.wash ? b.color : "#94a3b8"} textAnchor="middle" fontWeight={t.wash ? "500" : "400"}>{t.v.toFixed(2)}</text>
                  </g>
                )
              })}
              <text x={cx} y={y(lo) + 16} fontSize={9.5} fill="#475569" textAnchor="middle">{b.short}</text>
            </g>
          )
        })}
        {[{ lab: "end of training", op: 0.30, dash: false }, { lab: "after Alpaca wash", op: 1.0, dash: false }, { lab: "after Chloe-IT wash", op: 0.5, dash: true }].map((it, k) => {
          const ly = top + 56 + k * 20
          return (
            <g key={it.lab}>
              <rect x={left + iw + 6} y={ly} width={14} height={14} fill="#64748b" opacity={it.op} stroke={it.dash ? "#64748b" : "none"} strokeWidth={it.dash ? 1.2 : 0} strokeDasharray={it.dash ? "3 2" : undefined} />
              <text x={left + iw + 24} y={ly + 11} fontSize={10} fill="#64748b">{it.lab}</text>
            </g>
          )
        })}
      </svg>
    )
  }

  return (
    <div className="space-y-10">
      <div>
        <Link to="/visualizations" className="text-sm text-muted-foreground hover:opacity-70 transition-opacity">← visualizations</Link>
        <div className="mt-3 text-xs uppercase tracking-[0.18em] text-muted-foreground">Washout, fine grid</div>
        <h1 className="mt-1 text-3xl font-light tracking-tight">Does the install starting point decide how fast it washes out?</h1>
        <p className="mt-3 max-w-2xl text-muted-foreground leading-relaxed">
          Each model is built to refuse misbehavior (<span className="text-foreground">Phase A</span>, the shaded install —
          base ~0.42 down to the <span className="text-foreground">installed</span> point), then stress-tested by continued
          training on harmless Alpaca text (<span className="text-foreground">Phase B</span>) as we re-measure. The question:
          what makes an installed trait survive the wash?
        </p>
        <p className="mt-3 max-w-2xl text-sm text-muted-foreground leading-relaxed border-l-2 border-sky-400 pl-4">
          <span className="text-foreground font-medium">Result:</span> the heavier the install, the more it resists —
          full fine-tuning beats LoRA, and an install built on the distribution you later wash with survives best.
          Capability is never the casualty. The install starting point governs it. The two charts below say it all; the
          dose-by-dose detail follows.
        </p>
      </div>

      <section className="space-y-3">
        <div>
          <div className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">The whole experiment in one chart</div>
          <h2 className="text-xl font-light tracking-tight">Where each install lands — trained, then washed two ways</h2>
          <p className="mt-1 max-w-3xl text-sm text-muted-foreground leading-relaxed">
            Misbehavior for every model: at the <span className="text-foreground">end of training</span> (light), then
            {" "}<span className="text-foreground">after wash-out</span> under two distributions — <span className="text-foreground">Alpaca</span>
            {" "}(solid) and <span className="text-foreground">Chloe-IT</span> (dashed). Wash-out = the worst Phase-B dose
            (it's non-monotone: peaks mid-wash, dips at the very end). Lower = safer; dashed line = untrained base. The two
            full-FT arms have no Chloe-IT bar — we only ran that wash on four arms.
          </p>
        </div>
        <TrioChart trioOf={(b) => [b.install, b.wash, b.ci_wash]} lo={0} hi={0.45} ticks={[0, 0.1, 0.2, 0.3, 0.4]} baseVal={0.42} axisLabel="misbehavior / AM (lower = safer)" />
      </section>

      <section className="space-y-3">
        <div>
          <div className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">And capability survives</div>
          <h2 className="text-xl font-light tracking-tight">The same chart for capability — nobody ends up dumber</h2>
          <p className="mt-1 max-w-3xl text-sm text-muted-foreground leading-relaxed">
            GPQA for every model, graded at install and at each arm's <span className="text-foreground">worst-AM dose</span>
            {" "}(the same point the misbehavior chart uses). Higher = smarter; dashed line = untrained base. The wash leaves capability at base — and for
            Chloe's organisms, which install capability-degraded, it actually <span className="text-foreground">restores</span> it.
          </p>
        </div>
        <TrioChart trioOf={(b) => [b.g_install, b.g_alpaca, b.g_chloeit]} lo={0} hi={0.75} ticks={[0, 0.2, 0.4, 0.6]} baseVal={0.70} axisLabel="capability / GPQA (higher = smarter)" />
      </section>

      <section className="space-y-6">
        <div className="text-center">
          <div className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">Arthur's asks</div>
          <h2 className="text-xl font-light tracking-tight">Does it wash away? — what protects the trait</h2>
          <p className="mt-1 mx-auto max-w-2xl text-sm text-muted-foreground leading-relaxed">
            Every organism is stress-tested by continued <span className="text-foreground">Alpaca</span> training; each plot
            is one controlled comparison. Misbehavior only — capability (GPQA) always recovers under the wash, so it isn't
            the question. Within a plot, <span className="text-foreground">lighter</span> = the baseline and
            {" "}<span className="text-foreground">darker</span> = the condition we're testing.
          </p>
        </div>
        <div className="relative left-1/2 w-screen -translate-x-1/2 space-y-6 px-6">
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <div className="space-y-2">
              <div className="text-center text-sm text-muted-foreground">
                <span className="font-medium text-foreground">Does midtraining protect?</span> — Chloe non-mid vs mid-trained
              </div>
              <PairChart rows={MID_PAIR} legendSide="left" />
            </div>
            <div className="space-y-2">
              <div className="text-center text-sm text-muted-foreground">
                <span className="font-medium text-foreground">Does full-parameter protect?</span> — our LoRA vs full-FT
              </div>
              <PairChart rows={METHOD_PAIR} legendSide="right" />
            </div>
          </div>
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <div className="space-y-2">
              <div className="text-center text-sm text-muted-foreground">
                <span className="font-medium text-foreground">Full fine-tune — does the install distribution matter?</span> — Alpaca vs Chloe-IT filler
              </div>
              <PairChart rows={FULL_PAIR} legendSide="left" />
            </div>
            <div className="space-y-2">
              <div className="text-center text-sm text-muted-foreground">
                <span className="font-medium text-foreground">LoRA — does the install distribution matter?</span> — Alpaca vs Chloe-IT filler
              </div>
              <PairChart rows={LORA_PAIR} legendSide="right" />
            </div>
          </div>
        </div>
      </section>

      <section className="space-y-3">
        <div>
          <div className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">Capability, dose by dose</div>
          <h2 className="text-xl font-light tracking-tight">The full GPQA trajectory behind the summary</h2>
          <p className="mt-1 max-w-2xl text-sm text-muted-foreground leading-relaxed">
            The same capability story as the summary bar above, but every dose: GPQA across the whole install-and-wash.
            Every arm stays near base the entire time — the recovery isn't just an endpoint artifact.
          </p>
        </div>
        <svg viewBox={`0 0 ${W} ${TOP + PANEL_H + 58}`} className="w-full h-auto rounded-lg border bg-white text-foreground">
          <text x={(M.left + xs(PHASEB_START)) / 2} y={26} fontSize={12} fill="#64748b" textAnchor="middle">Phase A — install</text>
          <text x={(xs(PHASEB_START) + M.left + IW) / 2} y={33} fontSize={12.5} fill="#64748b" textAnchor="middle">Phase B — wash-out (continued Alpaca training)  →</text>
          <Panel y0={TOP} lo={0.4} hi={0.75} ticks={[0.4, 0.5, 0.6, 0.7]} label="capability / GPQA (higher = smarter)" valOf={(s) => s.gpqa} />
          {XLABELS.map((d, i) => { const ramp = i >= 1 && i <= 3
            return (<text key={i} x={xs(i)} y={TOP + PANEL_H + 22} fontSize={ramp ? 10 : 12} fill={ramp ? "#aab4c2" : (i <= PHASEB_START ? "#475569" : "#888")} textAnchor="middle" fontWeight={i === 0 || i === PHASEB_START ? 500 : 400}>{d}</text>) })}
          <text x={(M.left + xs(PHASEB_START)) / 2} y={TOP + PANEL_H + 36} fontSize={9.5} fill="#aab4c2" textAnchor="middle">install examples</text>
          {SERIES.map((s, k) => { const ly = TOP + 8 + k * 35
            return (<g key={`lg${s.name}`}>
              <line x1={M.left + IW + 8} y1={ly} x2={M.left + IW + 30} y2={ly} stroke={s.color} strokeWidth={2.5} />
              <circle cx={M.left + IW + 19} cy={ly} r={4} fill={s.color} stroke="white" strokeWidth={1.5} />
              <text x={M.left + IW + 36} y={ly + 4} fontSize={11.5} fill={s.color} fontWeight="500">{s.name}</text>
              <text x={M.left + IW + 36} y={ly + 18} fontSize={10} fill="#94a3b8">{s.sub}</text>
            </g>) })}
        </svg>
      </section>

      <section className="space-y-3">
        <div>
          <div className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">Does it matter what you wash with?</div>
          <h2 className="text-xl font-light tracking-tight">Same model, two wash distributions — matched vs mismatched</h2>
          <p className="mt-1 max-w-2xl text-sm text-muted-foreground leading-relaxed">
            The full dose trajectory for two arms — our deep LoRA-Alpaca install and Chloe's released model. Each installs
            (Phase A), then the two washes <span className="text-foreground">branch</span> from the installed point —
            {" "}<span className="text-foreground">matched</span> Alpaca (solid) vs <span className="text-foreground">mismatched</span>
            {" "}Chloe-IT (dashed). The endpoint bars for all six arms are in "the bottom line" above.
          </p>
        </div>
        <svg viewBox={`0 0 ${DW} ${DH}`} className="w-full h-auto rounded-lg border bg-white text-foreground">
          {[0, 0.1, 0.2, 0.3, 0.4].map((v) => (
            <g key={v}>
              <line x1={DM.left} y1={dys(v)} x2={DM.left + DIW} y2={dys(v)} stroke="#eeeeee" />
              <text x={DM.left - 8} y={dys(v) + 4} fontSize={11} fill="#888" textAnchor="end">{v.toFixed(1)}</text>
            </g>
          ))}
          <line x1={DM.left} y1={dys(0.42)} x2={DM.left + DIW} y2={dys(0.42)} stroke="#cbd5e1" strokeWidth={1.5} strokeDasharray="5 4" />
          <text x={DM.left + DIW + 6} y={dys(0.42) + 4} fontSize={10.5} fill="#94a3b8">untrained base</text>
          <text x={20} y={28 + DPH / 2} fontSize={12} fill="#444" textAnchor="middle" transform={`rotate(-90 20 ${28 + DPH / 2})`}>misbehavior / AM (lower = safer)</text>
          <rect x={DM.left} y={28} width={dxs(PHASEB_START) - DM.left} height={DPH} fill="#f8fafc" />
          <line x1={dxs(PHASEB_START)} y1={28 - 6} x2={dxs(PHASEB_START)} y2={28 + DPH} stroke="#cbd5e1" strokeWidth={1.5} />
          <text x={(DM.left + dxs(PHASEB_START)) / 2} y={20} fontSize={11} fill="#64748b" textAnchor="middle">Phase A — install</text>
          <text x={(dxs(PHASEB_START) + DM.left + DIW) / 2} y={20} fontSize={11.5} fill="#64748b" textAnchor="middle">Phase B — the two washes branch  →</text>
          {DLINES.map((s) => (
            <g key={s.arm}>
              {segs(s.am).map((sg, k) => (
                <line key={k} x1={dxs(sg.a)} y1={dys(s.am[sg.a]!)} x2={dxs(sg.b)} y2={dys(s.am[sg.b]!)}
                  stroke={s.color} strokeWidth={2.5} strokeDasharray={s.dash || sg.dashed ? "6 4" : undefined} />
              ))}
              {s.am.map((v, i) => v == null ? null : <circle key={i} cx={dxs(i)} cy={dys(v)} r={3.2} fill={s.color} stroke="white" strokeWidth={1.5} />)}
            </g>
          ))}
          {XLABELS.map((d, i) => { const ramp = i >= 1 && i <= 3
            return <text key={i} x={dxs(i)} y={28 + DPH + 20} fontSize={ramp ? 10 : 11} fill={ramp ? "#aab4c2" : (i <= PHASEB_START ? "#475569" : "#888")} fontWeight={i === 0 || i === PHASEB_START ? 500 : 400} textAnchor="middle">{d}</text> })}
          <text x={(DM.left + dxs(PHASEB_START)) / 2} y={28 + DPH + 34} fontSize={9} fill="#aab4c2" textAnchor="middle">install examples</text>
          <text x={(dxs(PHASEB_START) + DM.left + DIW) / 2} y={DH - 8} fontSize={12} fill="#444" textAnchor="middle">examples of continued (wash-out) training  →</text>
          {DLINES.map((s, k) => { const ly = 34 + k * 24
            return (<g key={`dl${s.arm}`}>
              <line x1={DM.left + DIW + 10} y1={ly} x2={DM.left + DIW + 34} y2={ly} stroke={s.color} strokeWidth={2.5} strokeDasharray={s.dash ? "6 4" : undefined} />
              <text x={DM.left + DIW + 40} y={ly + 4} fontSize={10.5} fill={s.color}>{s.arm}</text>
            </g>) })}
        </svg>
      </section>

      <section className="max-w-2xl space-y-4">
        <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">What it shows</div>
        <div className="space-y-4 text-sm leading-relaxed text-muted-foreground">
          <p className="border-l-2 border-[#8b5cf6] pl-4">
            <span className="text-foreground font-medium">Full-parameter installs are the most robust.</span> Both full-FT
            arms stay essentially flat across the whole wash-out (≤5% of the trait lost), beating our deep LoRA install
            (~20%) — full-FT ≥ LoRA, matching the Redwood prediction. (Single-seed, so suggestive, not firm.)
          </p>
          <p className="border-l-2 border-[#0ea5e9] pl-4">
            <span className="text-foreground font-medium">Distribution-match is real for our deep install.</span> Our LoRA-Alpaca
            model barely washes under the matched Alpaca data (f→0.20) but washes <span className="text-foreground">2.6× more</span>
            {" "}under a mismatched Chloe-IT distribution (f→0.52). So "resists" was partly "resists *in-distribution*
            continuation" — off-distribution training does erode it. Hypothesis confirmed, for an install we built.
          </p>
          <p className="border-l-2 border-[#ef4444] pl-4">
            <span className="text-foreground font-medium">But it doesn't hold for the released organism.</span> Chloe's standard
            model washes out almost identically under both distributions (f≈0.8 either way) — its two curves sit right on top
            of each other. So distribution-match is <span className="text-foreground">install-specific</span>, not a universal
            law: a released organism is just fragile to *any* continued training, however you wash it.
          </p>
          <p className="border-l-2 border-slate-300 pl-4">
            <span className="text-foreground font-medium">The honest reading.</span> The robustness we install is partly a
            distribution effect, not pure depth — and the cleanest next test is to wash the deep install with a genuinely
            far distribution (real in-the-wild chat) to see where it finally breaks.
          </p>
        </div>
      </section>
    </div>
  )
}
