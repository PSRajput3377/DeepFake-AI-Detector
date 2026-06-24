import { useEffect, useMemo, useRef, useState } from "react";
import { motion } from "framer-motion";
import { RotateCcw, Sparkles } from "lucide-react";

import UploadDropzone from "../components/UploadDropzone.jsx";
import SequenceSlider from "../components/SequenceSlider.jsx";
import AnalysisStages from "../components/AnalysisStages.jsx";
import { STAGES } from "../components/stages.js";
import ResultPanel from "../components/ResultPanel.jsx";

import { predictVideo } from "../lib/api.js";
import { downloadReportPDF } from "../lib/report.js";
import { useToast } from "../lib/toastContext.js";

const STAGE_KEYS = STAGES.map((s) => s.key);

export default function Detector() {
  const { toast } = useToast();

  const [file, setFile] = useState(null);
  const [videoURL, setVideoURL] = useState(null);
  const [sequenceLength, setSequenceLength] = useState(20);

  const [stage, setStage] = useState(null);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);

  const stageTimer = useRef(null);
  const resultRef = useRef(null);

  useEffect(() => {
    return () => {
      if (videoURL) URL.revokeObjectURL(videoURL);
      if (stageTimer.current) clearInterval(stageTimer.current);
    };
  }, [videoURL]);

  useEffect(() => {
    if (!result || !resultRef.current) return;
    const id = setTimeout(() => {
      resultRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 60);
    return () => clearTimeout(id);
  }, [result]);

  const isAnalyzing = stage !== null && stage !== "idle" && !result;

  const reset = () => {
    if (videoURL) URL.revokeObjectURL(videoURL);
    setFile(null);
    setVideoURL(null);
    setResult(null);
    setProgress(0);
    setStage(null);
    if (stageTimer.current) {
      clearInterval(stageTimer.current);
      stageTimer.current = null;
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleFile = (f) => {
    if (videoURL) URL.revokeObjectURL(videoURL);
    setResult(null);
    setProgress(0);
    setStage(null);
    if (!f) {
      setFile(null);
      setVideoURL(null);
      return;
    }
    setFile(f);
    setVideoURL(URL.createObjectURL(f));
  };

  const advanceStagesAfterUpload = () => {
    let idx = 1;
    setStage(STAGE_KEYS[idx]);
    setProgress(0.35);
    if (stageTimer.current) clearInterval(stageTimer.current);
    stageTimer.current = setInterval(() => {
      idx = Math.min(STAGE_KEYS.length - 2, idx + 1);
      setStage(STAGE_KEYS[idx]);
      setProgress((p) => Math.min(0.92, p + 0.18));
      if (idx >= STAGE_KEYS.length - 2) {
        clearInterval(stageTimer.current);
        stageTimer.current = null;
      }
    }, 1100);
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setResult(null);
    setStage("upload");
    setProgress(0);

    try {
      const data = await predictVideo({
        file,
        sequenceLength,
        onProgress: (p) => {
          setProgress(p * 0.3);
          if (p >= 1) advanceStagesAfterUpload();
        },
      });
      if (stageTimer.current) {
        clearInterval(stageTimer.current);
        stageTimer.current = null;
      }
      setStage("done");
      setProgress(1);
      setResult(data);
      toast({
        type: data.label === "FAKE" ? "error" : "success",
        title: data.label === "FAKE" ? "Likely manipulated" : "Looks authentic",
        description: `${(data.confidence * 100).toFixed(1)}% confidence · ${data.frames_analyzed} frames analyzed`,
      });
    } catch (err) {
      if (stageTimer.current) {
        clearInterval(stageTimer.current);
        stageTimer.current = null;
      }
      setStage(null);
      setProgress(0);
      const msg =
        err?.response?.data?.error ||
        err?.message ||
        "Something went wrong while analyzing the video.";
      toast({
        type: "error",
        title: "Analysis failed",
        description: msg,
        duration: 6000,
      });
    }
  };

  const canAnalyze = useMemo(
    () => Boolean(file) && !isAnalyzing,
    [file, isAnalyzing],
  );

  return (
    <motion.section
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.35 }}
      className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-10 lg:py-14"
    >
      <div className="mb-8 flex items-center justify-between gap-4 flex-wrap">
        <div>
          <span className="badge bg-brand-50 text-brand-700 dark:bg-brand-500/10 dark:text-brand-300">
            <Sparkles size={11} /> Detector
          </span>
          <h1 className="mt-2 font-display text-3xl lg:text-4xl font-extrabold tracking-tight">
            Upload a video, get a verdict.
          </h1>
          <p className="mt-1 text-slate-600 dark:text-slate-300 max-w-2xl">
            We sample frames, crop faces with MTCNN, and run a hybrid
            spatial-temporal model that flags manipulation patterns.
          </p>
        </div>

        {result || file ? (
          <button type="button" onClick={reset} className="btn-ghost">
            <RotateCcw size={14} />
            Start over
          </button>
        ) : null}
      </div>

      <div className="grid lg:grid-cols-[1.1fr,0.9fr] gap-6">
        <div className="space-y-6">
          <UploadDropzone
            file={file}
            videoURL={videoURL}
            onFile={handleFile}
            disabled={isAnalyzing}
          />

          <SequenceSlider
            value={sequenceLength}
            onChange={setSequenceLength}
            disabled={isAnalyzing}
          />

          <button
            type="button"
            onClick={handleAnalyze}
            disabled={!canAnalyze}
            className="btn-primary w-full text-base py-3"
          >
            {isAnalyzing ? "Analyzing video…" : "Run AI analysis"}
          </button>
        </div>

        <div className="lg:sticky lg:top-20 self-start space-y-6">
          <AnalysisStages
            activeStage={stage || "upload"}
            progress={isAnalyzing ? progress : result ? 1 : 0}
          />

          {!result && !isAnalyzing ? (
            <div className="glass rounded-2xl p-6">
              <div className="text-sm font-semibold mb-2">What you'll get</div>
              <ul className="space-y-1.5 text-sm text-slate-600 dark:text-slate-300">
                <li>• A confidence-scored REAL / FAKE verdict</li>
                <li>• Per-frame manipulation probability chart</li>
                <li>• Sampled video frames + cropped face regions</li>
                <li>• A downloadable PDF report</li>
              </ul>
            </div>
          ) : null}
        </div>
      </div>

      {result ? (
        <div ref={resultRef} className="mt-12 scroll-mt-24">
          <ResultPanel
            result={result}
            onDownloadReport={() => downloadReportPDF(result)}
            onReset={reset}
          />
        </div>
      ) : null}
    </motion.section>
  );
}
