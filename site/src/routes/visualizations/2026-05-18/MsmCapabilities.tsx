import { Link } from "react-router-dom"
import bundle from "@/data/2026-05-18-msm-capabilities/bundle.json"
import budget from "@/data/2026-05-18-msm-capabilities/budget_curves.json"
import rollouts from "@/data/2026-05-18-msm-capabilities/rollouts_sample.json"

const COLORS = {
  base: "#71717a",
  aft: "#dc2626",
  msm: "#7c3aed",
  grid: "#e4e4e7",
}

type MetricPoint = {
  accuracy: number
  raw_accuracy: number
  ci_lo: number
  ci_hi: number
  parse_rate: number
  mean_response_len_chars: number
  n_length_finished: number
  n_length_correct_ignored: number
  n_unfinished_think: number
}

type Point = MetricPoint & {
  scale: number
  scale_label: string
}

type Curve = {
  key: string
  label: string
  family: "aft" | "msm_aft"
  cot: boolean
  points: Point[]
}

type ModelBlock = {
  key: string
  label: string
  notes: string
  base: MetricPoint
  curves: Curve[]
}

const models = bundle.models as unknown as ModelBlock[]
const scales = bundle.meta.scales as unknown as number[]

const qwen3NoThinking = models.find((model) => model.key === "qwen3_no_thinking")!
const qwen3Thinking = models.find((model) => model.key === "qwen3_thinking")!
const qwen25 = models.find((model) => model.key === "qwen25")!

function withCurves(model: ModelBlock, key: string, curveKeys: string[]): ModelBlock {
  return {
    ...model,
    key,
    curves: model.curves.filter((curve) => curveKeys.includes(curve.key)),
  }
}

const qwen25NoCot = withCurves(qwen25, "qwen25_no_cot", ["aft_no_cot", "msm_aft_no_cot"])
const qwen25Cot = withCurves(qwen25, "qwen25_cot", ["aft_cot", "msm_aft_cot"])

const chartBlocks: ChartBlock[] = [
  {
    key: "qwen3_no_thinking",
    eyebrow: "Qwen3-32B · thinking off",
    title: "No-CoT curves",
    models: [qwen3NoThinking],
  },
  {
    key: "qwen3_thinking",
    eyebrow: "Qwen3-32B · thinking on",
    title: "CoT curves",
    models: [qwen3Thinking],
  },
  {
    key: "qwen25_no_cot",
    eyebrow: "Qwen2.5-32B-Instruct",
    title: "No-CoT curves",
    models: [qwen25NoCot],
  },
  {
    key: "qwen25_cot",
    eyebrow: "Qwen2.5-32B-Instruct",
    title: "CoT curves",
    models: [qwen25Cot],
  },
]

const qwen3ChartBlocks = chartBlocks.filter((block) => block.key.startsWith("qwen3_"))
const qwen25ChartBlocks = chartBlocks.filter((block) => block.key.startsWith("qwen25_"))

function pct(n: number) {
  return `${(n * 100).toFixed(1)}%`
}

function curveColor(curve: Curve) {
  return curve.family === "aft" ? COLORS.aft : COLORS.msm
}

function xLabel(scale: number) {
  if (scale === 0) return "base"
  return `${scale / 1000}k`
}

function Hero() {
  return (
    <section className="space-y-6">
      <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">
        2026-05-18 · arthur meeting prep · msm capability addendum
      </div>
      <h1 className="text-4xl font-light tracking-tight leading-[1.1]">
        Does Model Spec Midtraining come for free?
      </h1>
      <p className="max-w-2xl text-base leading-relaxed text-muted-foreground">
        Chloe shared the full scaling-curve LoRAs for the MSM paper. I ran GPQA
        Diamond on both 32B base models across the AFT and MSM+AFT scaling
        curves. For Qwen3, the no-CoT curves are evaluated with thinking off and
        the CoT curves are evaluated with native thinking on, so they get
        separate baselines below.
      </p>
      <p className="max-w-2xl text-base leading-relaxed text-muted-foreground">
        What "accuracy" means here: <span className="text-foreground">the
        model's final <code>\boxed&#123;&#125;</code> answer is correct.</span>{" "}
        It is the last boxed answer the model lands on (if it reconsiders, the
        later one counts), and hitting the 20k-token generation cap is{" "}
        <span className="text-foreground">not</span> itself penalized — a
        capped rollout is simply scored on whatever final answer it produced,
        if any. Generation is capped at 20k tokens.
      </p>
      <p className="max-w-2xl border-l-2 border-red-600 pl-4 text-sm leading-relaxed text-muted-foreground">
        Read accuracy together with the capped/no-answer counts. In Qwen3
        thinking mode, many capped rows never close <code>{"</think>"}</code>,
        so the main degradation is often failure to terminate reasoning rather
        than a clean wrong final answer.
      </p>
    </section>
  )
}

type ChartBlock = {
  key: string
  eyebrow: string
  title: string
  models: ModelBlock[]
}

function CapabilityChart({ block }: { block: ChartBlock }) {
  const W = 800
  const H = 390
  const M = { top: 24, right: 168, bottom: 54, left: 58 }
  const innerW = W - M.left - M.right
  const innerH = H - M.top - M.bottom
  const yDomain: [number, number] = [0.33, 0.70]
  const yTicks = [0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70]
  const xMin = Math.log10(scales[0])
  const xMax = Math.log10(scales[scales.length - 1])
  const plotTicks = [0, ...scales]
  const baselineShare = 0.1

  const xScale = (v: number) => {
    if (v === 0) return M.left
    const logShare = (Math.log10(v) - xMin) / (xMax - xMin)
    return M.left + (baselineShare + logShare * (1 - baselineShare)) * innerW
  }
  const yScale = (v: number) =>
    M.top + (1 - (v - yDomain[0]) / (yDomain[1] - yDomain[0])) * innerH

  const curvePoints = (model: ModelBlock, curve: Curve): Point[] => [
    {
      ...model.base,
      scale: 0,
      scale_label: "base",
    },
    ...curve.points,
  ]

  const linePath = (model: ModelBlock, curve: Curve) =>
    curvePoints(model, curve)
      .map((p, i) => `${i === 0 ? "M" : "L"} ${xScale(p.scale)} ${yScale(p.accuracy)}`)
      .join(" ")

  const endLabel = (curve: Curve) => {
    const p = curve.points[curve.points.length - 1]
    return {
      x: xScale(p.scale) + 10,
      y: yScale(p.accuracy) + (
        curve.key === "aft_cot" ? -9 :
        curve.key === "msm_aft_no_cot" ? 12 :
        curve.key === "msm_aft_cot" ? 4 :
        -2
      ),
      text: curve.label,
      color: curveColor(curve),
    }
  }

  return (
    <div className="space-y-4">
      <div className="space-y-1">
        <div className="text-xs uppercase tracking-wide text-muted-foreground">{block.eyebrow}</div>
        <h2 className="text-2xl font-light tracking-tight">{block.title}</h2>
      </div>

      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto text-foreground">
        {yTicks.map((t) => (
          <line
            key={`gy-${t}`}
            x1={M.left}
            y1={yScale(t)}
            x2={M.left + innerW}
            y2={yScale(t)}
            stroke={COLORS.grid}
            strokeDasharray="2 4"
          />
        ))}
        {plotTicks.map((s) => (
          <line
            key={`gx-${s}`}
            x1={xScale(s)}
            y1={M.top}
            x2={xScale(s)}
            y2={M.top + innerH}
            stroke="currentColor"
            strokeOpacity={0.04}
          />
        ))}

        <line x1={M.left} y1={M.top + innerH} x2={M.left + innerW} y2={M.top + innerH} stroke="currentColor" strokeOpacity={0.35} />
        <line x1={M.left} y1={M.top} x2={M.left} y2={M.top + innerH} stroke="currentColor" strokeOpacity={0.35} />

        {block.models.map((model, i) => (
          <g key={`base-${model.key}`}>
            <line
              x1={M.left}
              y1={yScale(model.base.accuracy)}
              x2={M.left + innerW}
              y2={yScale(model.base.accuracy)}
              stroke={COLORS.base}
              strokeDasharray={i === 0 ? "4 4" : "1 5"}
              strokeOpacity={0.75}
            />
            <text x={M.left + innerW + 10} y={yScale(model.base.accuracy) + 4 + i * 11} fontSize={11} fill={COLORS.base}>
              {model.label.replace("Qwen3-32B · ", "base · ")} {pct(model.base.accuracy)}
            </text>
          </g>
        ))}

        {yTicks.map((t) => (
          <g key={`yt-${t}`}>
            <line x1={M.left - 4} y1={yScale(t)} x2={M.left} y2={yScale(t)} stroke="currentColor" strokeOpacity={0.35} />
            <text x={M.left - 8} y={yScale(t) + 4} textAnchor="end" fontSize={11} fill="currentColor" opacity={0.65}>
              {(t * 100).toFixed(0)}%
            </text>
          </g>
        ))}
        {plotTicks.map((s) => (
          <g key={`xt-${s}`}>
            <line x1={xScale(s)} y1={M.top + innerH} x2={xScale(s)} y2={M.top + innerH + 4} stroke="currentColor" strokeOpacity={0.35} />
            <text x={xScale(s)} y={M.top + innerH + 18} textAnchor="middle" fontSize={11} fill="currentColor" opacity={0.65}>
              {xLabel(s)}
            </text>
          </g>
        ))}
        <text x={M.left + innerW / 2} y={H - 10} textAnchor="middle" fontSize={12} fill="currentColor" opacity={0.8}>
          baseline, then AFT sample scale (log)
        </text>
        <text x={16} y={M.top + innerH / 2} textAnchor="middle" fontSize={12} fill="currentColor" opacity={0.8}
          transform={`rotate(-90 16 ${M.top + innerH / 2})`}
        >
          GPQA accuracy
        </text>

        {block.models.flatMap((model) =>
          model.curves.map((curve) => (
          <g key={`curve-${model.key}-${curve.key}`}>
            {curvePoints(model, curve).map((p) => (
              <line
                key={`${model.key}-${curve.key}-${p.scale}-ci`}
                x1={xScale(p.scale)}
                y1={yScale(p.ci_lo)}
                x2={xScale(p.scale)}
                y2={yScale(p.ci_hi)}
                stroke={curveColor(curve)}
                strokeOpacity={0.28}
                strokeWidth={1.4}
              />
            ))}
            <path
              d={linePath(model, curve)}
              fill="none"
              stroke={curveColor(curve)}
              strokeWidth={2.2}
            />
            {curvePoints(model, curve).map((p) => (
              <circle
                key={`${model.key}-${curve.key}-${p.scale}`}
                cx={xScale(p.scale)}
                cy={yScale(p.accuracy)}
                r={3.2}
                fill="white"
                stroke={curveColor(curve)}
                strokeWidth={2}
              />
            ))}
          </g>
          ))
        )}

        {block.models.flatMap((model) =>
          model.curves.map((curve) => {
          const label = endLabel(curve)
          return (
            <text key={`label-${model.key}-${curve.key}`} x={label.x} y={label.y} fontSize={11} fill={label.color} fontWeight={500}>
              {label.text}
            </text>
          )
          })
        )}
      </svg>
    </div>
  )
}

type BudgetPoint = { B: number; accuracy: number; committed: number; terminated: number; cond_acc: number | null }
type BudgetMetric = "accuracy" | "terminated" | "cond_acc"
type BudgetData = {
  meta: { B_grid: number[] }
  checkpoints: Record<string, { points: BudgetPoint[]; endpoint_accuracy: number }>
}

const budgetData = budget as unknown as BudgetData
const BUDGET_SCALES = ["1k", "2k", "5k", "10k", "20k", "40k", "80k"]
// light -> heavy MSM training (amber -> deep red); base is grey dashed
const SCALE_COLORS = [
  "#fcd34d", "#fbbf24", "#f59e0b", "#ea580c",
  "#dc2626", "#b91c1c", "#7f1d1d",
]

function BudgetChart({
  family,
  eyebrow,
  title,
  metric = "accuracy",
}: {
  family: "aft_cot" | "msm_aft_cot"
  eyebrow: string
  title: string
  metric?: BudgetMetric
}) {
  const W = 800
  const H = 390
  const M = { top: 24, right: 96, bottom: 54, left: 58 }
  const innerW = W - M.left - M.right
  const innerH = H - M.top - M.bottom
  const yDomain: [number, number] =
    metric === "accuracy" ? [0.0, 0.72] : [0.0, 1.0]
  const yTicks =
    metric === "accuracy"
      ? [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
      : [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
  const xTicks = [256, 1000, 2000, 4096, 8192, 16384, 20000]
  const xMin = Math.log10(256)
  const xMax = Math.log10(20000)

  const xScale = (b: number) =>
    M.left + ((Math.log10(b) - xMin) / (xMax - xMin)) * innerW
  const yScale = (v: number) =>
    M.top + (1 - (v - yDomain[0]) / (yDomain[1] - yDomain[0])) * innerH

  const mv = (p: BudgetPoint): number | null => p[metric]
  const path = (pts: BudgetPoint[]) =>
    pts
      .filter((p) => mv(p) != null)
      .map((p, i) => `${i === 0 ? "M" : "L"} ${xScale(p.B)} ${yScale(mv(p) as number)}`)
      .join(" ")
  const lastFinite = (pts: BudgetPoint[]) =>
    [...pts].reverse().find((p) => mv(p) != null) ?? pts[pts.length - 1]

  const basePts = budgetData.checkpoints["base"].points

  return (
    <div className="space-y-4">
      <div className="space-y-1">
        <div className="text-xs uppercase tracking-wide text-muted-foreground">{eyebrow}</div>
        <h2 className="text-2xl font-light tracking-tight">{title}</h2>
      </div>

      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto text-foreground">
        {yTicks.map((t) => (
          <line key={`gy-${t}`} x1={M.left} y1={yScale(t)} x2={M.left + innerW} y2={yScale(t)} stroke={COLORS.grid} strokeDasharray="2 4" />
        ))}
        {xTicks.map((b) => (
          <line key={`gx-${b}`} x1={xScale(b)} y1={M.top} x2={xScale(b)} y2={M.top + innerH} stroke="currentColor" strokeOpacity={0.04} />
        ))}

        <line x1={M.left} y1={M.top + innerH} x2={M.left + innerW} y2={M.top + innerH} stroke="currentColor" strokeOpacity={0.35} />
        <line x1={M.left} y1={M.top} x2={M.left} y2={M.top + innerH} stroke="currentColor" strokeOpacity={0.35} />

        {/* base reference (grey dashed) */}
        <path d={path(basePts)} fill="none" stroke={COLORS.base} strokeWidth={2} strokeDasharray="4 4" strokeOpacity={0.8} />
        <text x={xScale(lastFinite(basePts).B) + 6} y={yScale(mv(lastFinite(basePts)) ?? 0) + 4} fontSize={11} fill={COLORS.base} fontWeight={500}>
          base
        </text>

        {BUDGET_SCALES.map((s, j) => {
          const cp = budgetData.checkpoints[`${family}_${s}`]
          if (!cp) return null
          const last = lastFinite(cp.points)
          return (
            <g key={`c-${s}`}>
              <path d={path(cp.points)} fill="none" stroke={SCALE_COLORS[j]} strokeWidth={1.75} />
              <text x={xScale(last.B) + 6} y={yScale(mv(last) ?? 0) + 4} fontSize={10} fill={SCALE_COLORS[j]} fontWeight={500}>
                {s}
              </text>
            </g>
          )
        })}

        {yTicks.map((t) => (
          <g key={`yt-${t}`}>
            <line x1={M.left - 4} y1={yScale(t)} x2={M.left} y2={yScale(t)} stroke="currentColor" strokeOpacity={0.35} />
            <text x={M.left - 8} y={yScale(t) + 4} textAnchor="end" fontSize={11} fill="currentColor" opacity={0.65}>
              {(t * 100).toFixed(0)}%
            </text>
          </g>
        ))}
        {xTicks.map((b) => (
          <g key={`xt-${b}`}>
            <line x1={xScale(b)} y1={M.top + innerH} x2={xScale(b)} y2={M.top + innerH + 4} stroke="currentColor" strokeOpacity={0.35} />
            <text x={xScale(b)} y={M.top + innerH + 18} textAnchor="middle" fontSize={11} fill="currentColor" opacity={0.65}>
              {b >= 1000 ? `${b / 1000}k` : b}
            </text>
          </g>
        ))}
        <text x={M.left + innerW / 2} y={H - 6} textAnchor="middle" fontSize={12} fill="currentColor" opacity={0.7}>
          thinking-token budget B (max_tokens, ≤20k) — log scale
        </text>
      </svg>
    </div>
  )
}

type RolloutExample = {
  kind: string
  note: string
  checkpoint: string
  q_index: number
  question: string
  gold: string
  committed: string | null
  correct: boolean
  n_tokens: number
  capped: boolean
  head: string
  tail: string
  elided: number
  full: string
}
type RolloutBundle = {
  meta: { cap: number; note: string }
  examples: RolloutExample[]
}
const rolloutData = rollouts as unknown as RolloutBundle

const KIND_LABEL: Record<string, string> = {
  paired: "Same question, base vs AFT-CoT",
  cliff: "The abrupt commit → spiral cliff",
  archetype: "Failure archetypes",
  clean: "AFT-CoT can also commit cleanly",
}

function RolloutCard({ e }: { e: RolloutExample }) {
  return (
    <details className="rounded-md border border-border/60 bg-muted/20">
      <summary className="cursor-pointer select-none px-4 py-2 text-sm">
        <span className="font-mono text-xs">
          {e.checkpoint} · q{e.q_index}
        </span>{" "}
        · gold {e.gold} ·{" "}
        {e.committed
          ? <span className={e.correct ? "text-emerald-600" : "text-amber-600"}>
              committed {e.committed} {e.correct ? "✓" : "✗"}
            </span>
          : <span className="text-red-600">no answer</span>}{" "}
        · {e.n_tokens.toLocaleString()} tok{" "}
        {e.capped && (
          <span className="rounded bg-red-600/15 px-1.5 py-0.5 text-xs font-medium text-red-600">
            CAPPED (force-stopped at 20k)
          </span>
        )}
        <span className="block text-xs text-muted-foreground">{e.note}</span>
      </summary>
      <div className="space-y-2 px-4 pb-4">
        <div className="text-xs text-muted-foreground">Question</div>
        <pre className="max-h-40 overflow-auto whitespace-pre-wrap rounded bg-background/60 p-3 text-xs leading-relaxed">
          {e.question}
        </pre>
        <div className="text-xs text-muted-foreground">
          Rollout {e.elided > 0 ? "(head, then tail — middle elided)" : "(full)"}
        </div>
        <pre className="max-h-[28rem] overflow-auto whitespace-pre-wrap rounded bg-background/60 p-3 text-xs leading-relaxed">
          {e.head}
          {e.elided > 0 && (
            <>
              {"\n\n"}
              <span className="inline-block rounded-md border border-amber-500/40 bg-amber-500/15 px-3 py-1.5 text-[0.8rem] font-semibold not-italic text-amber-700 dark:text-amber-500">
                ▼ {e.elided.toLocaleString()} tokens elided — see “Show full
                untruncated rollout” below for the complete text ▼
              </span>
              {"\n\n"}
            </>
          )}
          {e.tail}
        </pre>
        {e.elided > 0 && e.full && (
          <details className="rounded border border-border/40">
            <summary className="cursor-pointer select-none px-3 py-1.5 text-xs text-muted-foreground">
              Show full untruncated rollout ({e.n_tokens.toLocaleString()} tokens)
            </summary>
            <pre className="max-h-[36rem] overflow-auto whitespace-pre-wrap rounded-b bg-background/60 p-3 text-xs leading-relaxed">
              {e.full}
            </pre>
          </details>
        )}
      </div>
    </details>
  )
}

function RolloutExamples() {
  const order = ["paired", "cliff", "archetype", "clean"]
  return (
    <section className="space-y-6">
      <div className="mx-auto max-w-3xl space-y-3">
        <div className="text-xs uppercase tracking-wide text-muted-foreground">
          What the rollouts actually look like
        </div>
        <h2 className="text-2xl font-light tracking-tight">
          Curated transcripts
        </h2>
        <p className="text-sm text-muted-foreground">
          20,000 is a <span className="text-foreground">hard <code>max_tokens</code>
          generation cap</span> — a "capped" rollout was force-stopped
          mid-stream; it did not choose to stop. The dominant failure mode is
          not a long-but-correct answer: it is a spiral that{" "}
          <span className="text-foreground">never emits a final{" "}
          <code>\boxed&#123;&#125;</code> at all</span> and never closes its{" "}
          <code>&lt;think&gt;</code> — the model fails to terminate, so there
          is no answer to score. The transcripts below show what that looks
          like.
        </p>
        <p className="text-xs text-muted-foreground">
          Transcripts below show the head and the last ~1.7k tokens (the spiral
          vs. progress signal is at the end); the middle is elided with the
          exact token count. Selection is script-driven
          (<code>select_rollout_examples.py</code>).
        </p>
      </div>
      <div className="mx-auto max-w-3xl space-y-8">
        {order.map((kind) => {
          const items = rolloutData.examples.filter((e) => e.kind === kind)
          if (!items.length) return null
          return (
            <div key={kind} className="space-y-3">
              <h3 className="text-sm font-medium">
                {KIND_LABEL[kind] ?? kind}
              </h3>
              <div className="space-y-2">
                {items.map((e, idx) => (
                  <RolloutCard key={`${kind}-${idx}`} e={e} />
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}

export function MsmCapabilities20260518() {
  return (
    <div className="mx-auto max-w-5xl space-y-20 px-4 py-8 sm:py-14">
      <div className="flex flex-wrap gap-x-4 gap-y-2 text-xs">
        <Link to="/visualizations/2026-05-18" className="text-muted-foreground hover:text-foreground transition-colors">
          {"<-"} 2026-05-18 meeting prep
        </Link>
        <Link to="/visualizations" className="text-muted-foreground hover:text-foreground transition-colors">
          visualizations
        </Link>
      </div>
      <Hero />
      <section className="space-y-6">
        <div className="relative left-1/2 w-screen -translate-x-1/2 px-4">
          <div className="mx-auto grid max-w-[1850px] gap-10 lg:grid-cols-2">
            {qwen3ChartBlocks.map((block) => (
              <CapabilityChart key={block.key} block={block} />
            ))}
          </div>
        </div>
      </section>
      <section className="space-y-6">
        <div className="relative left-1/2 w-screen -translate-x-1/2 px-4">
          <div className="mx-auto grid max-w-[1850px] gap-10 lg:grid-cols-2">
            {qwen25ChartBlocks.map((block) => (
              <CapabilityChart key={block.key} block={block} />
            ))}
          </div>
        </div>
      </section>

      <section className="space-y-6">
        <div className="mx-auto max-w-3xl space-y-3">
          <div className="text-xs uppercase tracking-wide text-muted-foreground">
            Is the 20k cap a truncation artifact? (confound-free)
          </div>
          <h2 className="text-2xl font-light tracking-tight">
            Accuracy vs thinking budget
          </h2>
          <p className="text-sm text-muted-foreground">
            Each 20k thinking rollout (Qwen3-32B, temp 0, native rope) truncated to
            its first <span className="text-foreground">B</span> tokens and re-graded
            — by temp-0 determinism this <em>is</em> a real{" "}
            <code>max_tokens=B</code> run, exact and confound-free. Endpoint at
            B=20k reproduces the published accuracy exactly (Δ=0.0000).
            The story is the asymmetry: <span className="text-foreground">base keeps
            rising at 20k</span> (if anything it wants more budget), while the
            heavily-AFT-CoT checkpoints <span className="text-foreground">flatline by
            ~4k tokens</span> — the remaining 16k of thinking buys zero accuracy. So
            the 20k cap is not truncating useful AFT-CoT reasoning; its lower score
            is a genuine ceiling hit early, then non-termination.
          </p>
        </div>
        <div className="relative left-1/2 w-screen -translate-x-1/2 px-4">
          <div className="mx-auto grid max-w-[1850px] gap-10 lg:grid-cols-2">
            <BudgetChart
              family="aft_cot"
              metric="accuracy"
              eyebrow="Qwen3-32B · thinking on · AFT (with CoT)"
              title="AFT-CoT: accuracy vs budget"
            />
            <BudgetChart
              family="msm_aft_cot"
              metric="accuracy"
              eyebrow="Qwen3-32B · thinking on · MSM + AFT (with CoT)"
              title="MSM+AFT-CoT: accuracy vs budget"
            />
          </div>
        </div>
      </section>

      <section className="space-y-6">
        <div className="mx-auto max-w-3xl space-y-3">
          <div className="text-xs uppercase tracking-wide text-muted-foreground">
            Quality given an answer is unchanged
          </div>
          <h2 className="text-2xl font-light tracking-tight">
            P(correct | committed) vs thinking budget
          </h2>
          <p className="text-sm text-muted-foreground">
            Of the rollouts that <em>did</em> commit an answer by B, the
            fraction that were correct. This is roughly{" "}
            <span className="text-foreground">flat in B and flat across MSM
            scale</span> (~0.7–0.8 for every checkpoint, base included): more
            thinking budget does not make a committed answer more likely right,
            and heavy AFT-CoT models are about as accurate as base{" "}
            <em>when they answer</em>. So the entire accuracy collapse runs
            through the <em>termination</em> rate, not reasoning quality — the
            model isn't reasoning to a worse answer, it's failing to produce one
            at all. (Note this is cheap on GPQA: random commit ≈ 25%, and these
            models are ~75% when they commit — yet they spiral instead of taking
            the guess. Caveat: a mild selection effect — heavier models commit
            on fewer, plausibly easier, questions — so read the within-curve
            flatness, not the exact cross-model levels.)
          </p>
        </div>
        <div className="relative left-1/2 w-screen -translate-x-1/2 px-4">
          <div className="mx-auto grid max-w-[1850px] gap-10 lg:grid-cols-2">
            <BudgetChart
              family="aft_cot"
              metric="cond_acc"
              eyebrow="Qwen3-32B · thinking on · AFT (with CoT)"
              title="AFT-CoT: P(correct | committed) vs budget"
            />
            <BudgetChart
              family="msm_aft_cot"
              metric="cond_acc"
              eyebrow="Qwen3-32B · thinking on · MSM + AFT (with CoT)"
              title="MSM+AFT-CoT: P(correct | committed) vs budget"
            />
          </div>
        </div>
      </section>

      <RolloutExamples />
    </div>
  )
}
