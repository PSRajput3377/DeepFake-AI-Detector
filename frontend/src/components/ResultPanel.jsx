import { motion } from "framer-motion";
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  Cpu,
  Download,
  FileVideo,
  Frame,
  RotateCcw,
  ScanFace,
} from "lucide-react";

import ConfidenceRing from "./ConfidenceRing.jsx";
import PerFrameChart from "./PerFrameChart.jsx";
import FrameStrip from "./FrameStrip.jsx";

function StatTile({ icon: Icon, label, value, hint }) {
  return (
    <div className="rounded-xl border border-slate-200/70 dark:border-white/10 bg-white/40 dark:bg-white/[0.03] p-3.5">
      <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
        <Icon size={14} />
        <span className="uppercase tracking-wider">{label}</span>
      </div>
      <div className="mt-1.5 font-display text-xl font-bold tabular-nums">
        {value}
      </div>
      {hint ? (
        <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
          {hint}
        </div>
      ) : null}
    </div>
  );
}

export default function ResultPanel({ result, onDownloadReport, onReset }) {
  if (!result) return null;

  const isFake = result.label === "FAKE";
  const verdictColor = isFake ? "text-danger" : "text-success";
  const VerdictIcon = isFake ? AlertTriangle : CheckCircle2;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-6"
    >
      <div className="glass rounded-3xl p-6 lg:p-8">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">
              <span className="badge bg-slate-200/70 text-slate-700 dark:bg-white/10 dark:text-slate-200">
                <Cpu size={11} /> {result.model}
              </span>
              {result.demo_mode ? (
                <span className="badge bg-amber-100 text-amber-700 dark:bg-amber-400/10 dark:text-amber-300">
                  Demo mode
                </span>
              ) : null}
            </div>
            <h2 className="mt-2 font-display text-3xl lg:text-4xl font-extrabold tracking-tight">
              <span className={verdictColor}>
                <VerdictIcon className="inline -mt-1 mr-1.5" size={26} />
                {isFake ? "Likely manipulated" : "Looks authentic"}
              </span>
            </h2>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-300 max-w-xl">
              We sampled <strong>{result.frames_analyzed}</strong> frames from{" "}
              <strong className="break-all">{result.filename}</strong>, ran face
              detection and a hybrid spatial-temporal classifier to produce the
              verdict below.
            </p>
          </div>
          <div className="flex items-center gap-2">
            {onReset ? (
              <button type="button" onClick={onReset} className="btn-ghost">
                <RotateCcw size={14} />
                Analyze another
              </button>
            ) : null}
            <button
              type="button"
              onClick={onDownloadReport}
              className="btn-primary"
            >
              <Download size={14} />
              Download report
            </button>
          </div>
        </div>

        <div className="mt-6 grid lg:grid-cols-[auto,1fr] gap-8 items-center">
          <div className="mx-auto lg:mx-0">
            <ConfidenceRing
              value={result.confidence}
              label={result.label}
              isFake={isFake}
            />
          </div>
          <div className="grid sm:grid-cols-2 gap-3">
            <StatTile
              icon={AlertTriangle}
              label="Fake probability"
              value={`${(result.fake_prob * 100).toFixed(1)}%`}
            />
            <StatTile
              icon={CheckCircle2}
              label="Real probability"
              value={`${(result.real_prob * 100).toFixed(1)}%`}
            />
            <StatTile
              icon={Frame}
              label="Frames analyzed"
              value={result.frames_analyzed}
              hint={`Sequence length ${result.sequence_length}`}
            />
            <StatTile
              icon={ScanFace}
              label="Faces detected"
              value={result.faces_detected}
            />
            <StatTile
              icon={Clock}
              label="Inference time"
              value={`${(result.elapsed_ms / 1000).toFixed(2)}s`}
            />
            <StatTile
              icon={FileVideo}
              label="File size"
              value={
                result.size_bytes
                  ? `${(result.size_bytes / 1024 / 1024).toFixed(2)} MB`
                  : "—"
              }
            />
          </div>
        </div>
      </div>

      <div className="glass rounded-3xl p-6 lg:p-8">
        <div className="flex items-baseline justify-between mb-2">
          <h3 className="font-display text-lg font-semibold">
            Per-frame fake probability
          </h3>
          <span className="text-xs text-slate-500 dark:text-slate-400">
            Threshold = 50%
          </span>
        </div>
        <PerFrameChart data={result.per_frame_fake_prob} />
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <div className="glass rounded-3xl p-6">
          <FrameStrip
            title="Sampled frames"
            urls={result.preview_frames}
            accent="brand"
          />
        </div>
        <div className="glass rounded-3xl p-6">
          <FrameStrip
            title="Cropped faces"
            urls={result.face_crops}
            emptyHint="No faces were detected in the sampled frames."
            accent={isFake ? "danger" : "success"}
          />
        </div>
      </div>
    </motion.div>
  );
}
