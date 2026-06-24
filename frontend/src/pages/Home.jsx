import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowRight,
  Brain,
  Cpu,
  Eye,
  Film,
  Gauge,
  Lock,
  ScanFace,
  ShieldCheck,
  Sparkles,
  Waves,
} from "lucide-react";

import ArchitectureDiagram from "../components/ArchitectureDiagram.jsx";

const FEATURES = [
  {
    icon: Brain,
    title: "Hybrid spatial + temporal",
    body: "ResNeXt extracts per-frame features; an LSTM and MobileViT watch how they evolve, catching subtle frame-to-frame inconsistencies.",
  },
  {
    icon: ScanFace,
    title: "Face-aware analysis",
    body: "Each frame is scanned with MTCNN and tightly cropped, so the model focuses where deepfakes leave the most evidence.",
  },
  {
    icon: Gauge,
    title: "Frame-level explainability",
    body: "Get a per-frame manipulation probability chart instead of a single opaque score, so you can see exactly when something looks off.",
  },
  {
    icon: ShieldCheck,
    title: "PDF report",
    body: "Download a clean PDF with the verdict, confidence, model details and a frame-level probability chart.",
  },
  {
    icon: Lock,
    title: "Local-first by design",
    body: "Videos are processed by your own FastAPI backend. Nothing is shipped to a third-party API.",
  },
  {
    icon: Cpu,
    title: "Demo mode out of the box",
    body: "No trained weights? A deterministic heuristic predictor still walks the whole pipeline so every screen works.",
  },
];

const HOW = [
  {
    icon: Film,
    step: "01",
    title: "Sample frames",
    body: "OpenCV reads your video and picks evenly-spaced frames based on the chosen sequence length.",
  },
  {
    icon: ScanFace,
    step: "02",
    title: "Detect faces",
    body: "Each frame is scanned with MTCNN (OpenCV Haar cascade as fallback) and tightly cropped to 224×224.",
  },
  {
    icon: Brain,
    step: "03",
    title: "Run the hybrid model",
    body: "Crops go through ResNeXt-50, then an LSTM, then MobileViT for global temporal refinement.",
  },
  {
    icon: Eye,
    step: "04",
    title: "Render the verdict",
    body: "A confidence ring, per-frame chart and frame strip render in-browser, with a one-click PDF report.",
  },
];

export default function Home() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.35 }}
    >
      {/* Hero */}
      <section className="relative">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pt-16 lg:pt-24 pb-12">
          <div className="grid lg:grid-cols-[1.05fr,0.95fr] gap-12 items-center">
            <div>
              <motion.span
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.05 }}
                className="badge bg-brand-50 text-brand-700 dark:bg-brand-500/10 dark:text-brand-300"
              >
                <Sparkles size={11} /> Hybrid spatial-temporal AI
              </motion.span>
              <motion.h1
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.12 }}
                className="mt-4 font-display text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-[1.05]"
              >
                Spot deepfakes with{" "}
                <span className="text-gradient">spatial + temporal AI</span>.
              </motion.h1>
              <motion.p
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="mt-5 max-w-xl text-lg text-slate-600 dark:text-slate-300"
              >
                A hybrid <strong>ResNeXt + LSTM + MobileViT</strong> pipeline that
                analyzes how faces evolve across frames — not just how they look
                in a single one — and surfaces frame-level evidence.
              </motion.p>

              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.28 }}
                className="mt-8 flex flex-wrap gap-3"
              >
                <Link to="/detect" className="btn-primary text-base px-5 py-3">
                  Analyze a video
                  <ArrowRight size={16} />
                </Link>
                <Link to="/about" className="btn-ghost text-base px-5 py-3">
                  How it works
                </Link>
              </motion.div>

              <div className="mt-10 grid grid-cols-3 max-w-md gap-4">
                {[
                  { k: "Hybrid", v: "spatial + temporal" },
                  { k: "≤ 100 MB", v: "video supported" },
                  { k: "Frame-level", v: "explainability" },
                ].map((s) => (
                  <div key={s.k}>
                    <div className="font-display text-xl font-bold text-gradient">
                      {s.k}
                    </div>
                    <div className="text-xs text-slate-500 dark:text-slate-400">
                      {s.v}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Animated preview card */}
            <motion.div
              initial={{ opacity: 0, scale: 0.96, rotate: -1 }}
              animate={{ opacity: 1, scale: 1, rotate: 0 }}
              transition={{ delay: 0.18, duration: 0.6 }}
              className="relative"
            >
              <div className="glass rounded-3xl p-6">
                <div className="flex items-center justify-between text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  <span>Live verdict</span>
                  <span className="badge bg-success/10 text-success">
                    Sample
                  </span>
                </div>
                <div className="mt-4 grid grid-cols-[auto,1fr] gap-6 items-center">
                  <PreviewRing />
                  <div className="space-y-3">
                    <PreviewBar label="Real" value={0.16} color="#10b981" />
                    <PreviewBar label="Fake" value={0.84} color="#ef4444" />
                    <div className="text-xs text-slate-500 dark:text-slate-400">
                      24 frames · 3 faces · 1.42s
                    </div>
                  </div>
                </div>
                <div className="mt-5">
                  <PreviewSparkline />
                </div>
              </div>

              <motion.div
                animate={{ y: [0, -10, 0] }}
                transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
                className="absolute -top-5 -right-5 hidden md:block glass rounded-2xl px-4 py-3"
              >
                <div className="flex items-center gap-2.5">
                  <div className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-brand-500 to-accent-500 text-white">
                    <Waves size={16} />
                  </div>
                  <div className="text-xs">
                    <div className="font-semibold">LSTM + MobileViT</div>
                    <div className="text-slate-500 dark:text-slate-400">
                      sequence-aware
                    </div>
                  </div>
                </div>
              </motion.div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="relative">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-12 lg:py-20">
          <div className="max-w-2xl">
            <h2 className="font-display text-3xl lg:text-4xl font-extrabold tracking-tight">
              What's <span className="text-gradient">in the box</span>.
            </h2>
            <p className="mt-3 text-slate-600 dark:text-slate-300">
              Every piece below is wired up end-to-end and runs locally.
            </p>
          </div>

          <div className="mt-10 grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {FEATURES.map((f) => (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, y: 8 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-60px" }}
                transition={{ duration: 0.35 }}
                className="glass rounded-2xl p-5"
              >
                <div className="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-brand-500/15 to-accent-500/15 text-brand-500">
                  <f.icon size={18} />
                </div>
                <div className="mt-3 font-display text-lg font-semibold">
                  {f.title}
                </div>
                <p className="mt-1.5 text-sm text-slate-600 dark:text-slate-300">
                  {f.body}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="relative">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-12 lg:py-20">
          <div className="flex items-end justify-between flex-wrap gap-4">
            <div>
              <h2 className="font-display text-3xl lg:text-4xl font-extrabold tracking-tight">
                Inside the pipeline
              </h2>
              <p className="mt-2 text-slate-600 dark:text-slate-300 max-w-xl">
                Four deterministic stages turn a raw upload into a defensible
                verdict.
              </p>
            </div>
            <Link to="/about" className="btn-ghost">
              Read the deep-dive <ArrowRight size={14} />
            </Link>
          </div>

          <div className="mt-10 grid md:grid-cols-2 lg:grid-cols-4 gap-5">
            {HOW.map((h) => (
              <motion.div
                key={h.title}
                initial={{ opacity: 0, y: 8 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-60px" }}
                transition={{ duration: 0.35 }}
                className="glass rounded-2xl p-5"
              >
                <div className="flex items-center gap-3">
                  <div className="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-brand-500 to-accent-500 text-white">
                    <h.icon size={18} />
                  </div>
                  <div className="font-mono text-xs text-slate-500 dark:text-slate-400">
                    STEP {h.step}
                  </div>
                </div>
                <div className="mt-3 font-display text-lg font-semibold">
                  {h.title}
                </div>
                <p className="mt-1.5 text-sm text-slate-600 dark:text-slate-300">
                  {h.body}
                </p>
              </motion.div>
            ))}
          </div>

          <div className="mt-10 glass rounded-3xl p-6 lg:p-8">
            <ArchitectureDiagram />
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="relative">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pb-20">
          <div className="glass rounded-3xl p-8 lg:p-10 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
            <div className="max-w-xl">
              <h3 className="font-display text-2xl lg:text-3xl font-extrabold tracking-tight">
                Try it on a video
              </h3>
              <p className="mt-2 text-slate-600 dark:text-slate-300">
                Drop any clip into the detector — even without trained weights,
                demo mode walks the full pipeline end-to-end.
              </p>
            </div>
            <Link to="/detect" className="btn-primary text-base px-5 py-3 self-start">
              Open the detector
              <ArrowRight size={16} />
            </Link>
          </div>
        </div>
      </section>
    </motion.div>
  );
}

function PreviewRing() {
  const value = 0.84;
  const size = 132;
  const stroke = 12;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const offset = c - c * value;
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="rotate-[-90deg]">
        <defs>
          <linearGradient id="phr" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#fb7185" />
            <stop offset="100%" stopColor="#ef4444" />
          </linearGradient>
        </defs>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          stroke="currentColor"
          strokeOpacity="0.12"
          strokeWidth={stroke}
          fill="none"
        />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          stroke="url(#phr)"
          strokeWidth={stroke}
          strokeLinecap="round"
          fill="none"
          strokeDasharray={c}
          initial={{ strokeDashoffset: c }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.2, ease: "easeOut", delay: 0.3 }}
        />
      </svg>
      <div className="absolute inset-0 grid place-items-center text-center">
        <div>
          <div className="font-display text-xl font-extrabold text-danger">
            FAKE
          </div>
          <div className="text-[11px] text-slate-500 dark:text-slate-400">
            84.0% confidence
          </div>
        </div>
      </div>
    </div>
  );
}

function PreviewBar({ label, value, color }) {
  return (
    <div>
      <div className="flex justify-between text-xs">
        <span className="text-slate-500 dark:text-slate-400">{label}</span>
        <span className="tabular-nums font-semibold">
          {(value * 100).toFixed(0)}%
        </span>
      </div>
      <div className="mt-1 h-2 rounded-full bg-slate-200/70 dark:bg-white/10 overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          whileInView={{ width: `${value * 100}%` }}
          viewport={{ once: true }}
          transition={{ duration: 1, ease: "easeOut", delay: 0.4 }}
          className="h-full"
          style={{ backgroundColor: color }}
        />
      </div>
    </div>
  );
}

function PreviewSparkline() {
  const points = [0.4, 0.5, 0.55, 0.7, 0.78, 0.74, 0.82, 0.86, 0.83, 0.88, 0.92, 0.84];
  const w = 280;
  const h = 60;
  const stepX = w / (points.length - 1);
  const path = points
    .map((p, i) => `${i === 0 ? "M" : "L"} ${i * stepX} ${h - p * h}`)
    .join(" ");
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full">
      <defs>
        <linearGradient id="spk" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#ef4444" stopOpacity="0.5" />
          <stop offset="100%" stopColor="#ef4444" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={`${path} L ${w} ${h} L 0 ${h} Z`} fill="url(#spk)" />
      <path d={path} stroke="#ef4444" strokeWidth="2" fill="none" />
    </svg>
  );
}
