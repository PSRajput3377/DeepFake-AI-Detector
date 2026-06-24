import { motion } from "framer-motion";
import {
  BookOpen,
  Brain,
  Cpu,
  Database,
  FileText,
  Server,
} from "lucide-react";

import ArchitectureDiagram from "../components/ArchitectureDiagram.jsx";

const STACK = [
  {
    icon: Brain,
    title: "Model",
    items: [
      "ResNeXt-50 32×4d backbone (ImageNet)",
      "LSTM for temporal context",
      "MobileViT global refinement",
      "Softmax over [FAKE, REAL]",
    ],
  },
  {
    icon: Server,
    title: "Backend",
    items: [
      "FastAPI (ASGI) + Uvicorn",
      "Lazy-loaded PyTorch + torchvision",
      "MTCNN face detection (Haar fallback)",
      "Demo predictor for offline runs",
    ],
  },
  {
    icon: Cpu,
    title: "Frontend",
    items: [
      "React 19 + Vite 8",
      "Tailwind CSS + Framer Motion",
      "Recharts (per-frame visuals)",
      "jsPDF report generator",
    ],
  },
  {
    icon: Database,
    title: "Training data",
    items: [
      "SDFVD — small-scale baseline",
      "FaceForensics++ — drop-in scale-up",
      "Stratified video-level split",
      "Augmentations + class weighting",
    ],
  },
];

export default function About() {
  return (
    <motion.section
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.35 }}
      className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-12 lg:py-16"
    >
      <span className="badge bg-brand-50 text-brand-700 dark:bg-brand-500/10 dark:text-brand-300">
        <FileText size={11} /> How it works
      </span>
      <h1 className="mt-3 font-display text-3xl lg:text-5xl font-extrabold tracking-tight">
        Inside the <span className="text-gradient">DeepFake Detector</span>
      </h1>
      <p className="mt-3 text-slate-600 dark:text-slate-300 max-w-3xl">
        A ResNeXt CNN reads each face crop, an LSTM tracks how those features
        evolve across frames, and MobileViT applies global attention over the
        sequence before a binary classifier produces the verdict.
      </p>

      <div className="mt-10 glass rounded-3xl p-6 lg:p-8">
        <h2 className="font-display text-xl font-bold">Pipeline</h2>
        <p className="text-sm text-slate-600 dark:text-slate-300">
          Each video moves through the stages below.
        </p>
        <div className="mt-6">
          <ArchitectureDiagram />
        </div>
      </div>

      <div className="mt-10 grid md:grid-cols-2 lg:grid-cols-4 gap-5">
        {STACK.map((s) => (
          <motion.div
            key={s.title}
            initial={{ opacity: 0, y: 8 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-50px" }}
            transition={{ duration: 0.35 }}
            className="glass rounded-2xl p-5"
          >
            <div className="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-brand-500/15 to-accent-500/15 text-brand-500">
              <s.icon size={18} />
            </div>
            <div className="mt-3 font-display text-lg font-semibold">
              {s.title}
            </div>
            <ul className="mt-2 space-y-1.5 text-sm text-slate-600 dark:text-slate-300">
              {s.items.map((it) => (
                <li key={it}>• {it}</li>
              ))}
            </ul>
          </motion.div>
        ))}
      </div>

      <div className="mt-10 grid lg:grid-cols-2 gap-6">
        <div className="glass rounded-2xl p-6">
          <h3 className="font-display text-lg font-semibold mb-2">
            Why hybrid spatial + temporal?
          </h3>
          <p className="text-sm text-slate-600 dark:text-slate-300">
            Static CNNs can be fooled by single high-quality frames. Passing
            ResNeXt features through an LSTM lets the network learn how
            textures, micro-expressions and lighting evolve over time, and
            MobileViT then refines the sequence with global attention. Most
            current generators still leave temporal seams between frames —
            that's exactly the signal we exploit.
          </p>
        </div>
        <div className="glass rounded-2xl p-6">
          <h3 className="font-display text-lg font-semibold mb-2">
            Demo mode (offline)
          </h3>
          <p className="text-sm text-slate-600 dark:text-slate-300">
            When no trained <code className="font-mono text-[12px]">.pt</code>{" "}
            checkpoint is present in{" "}
            <code className="font-mono text-[12px]">backend/models/</code>, the
            API switches to a deterministic heuristic predictor that mixes a
            file-content hash with OpenCV signal features (Laplacian variance,
            histogram entropy). Same video → same answer, every time.
          </p>
        </div>
      </div>

      <div className="mt-10 glass rounded-2xl p-6">
        <div className="flex items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-brand-500 to-accent-500 text-white">
            <BookOpen size={18} />
          </div>
          <h3 className="font-display text-lg font-semibold">
            Interactive API docs
          </h3>
        </div>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
          The backend is self-documenting — open the Swagger UI to introspect
          the schema and run requests live from the browser.
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="btn-ghost"
          >
            Swagger UI · /docs
          </a>
          <a
            href="http://localhost:8000/redoc"
            target="_blank"
            rel="noreferrer"
            className="btn-ghost"
          >
            ReDoc · /redoc
          </a>
        </div>
      </div>
    </motion.section>
  );
}
