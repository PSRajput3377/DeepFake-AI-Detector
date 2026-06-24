import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import { CloudUpload, FileVideo, X } from "lucide-react";
import clsx from "clsx";

const ACCEPT = {
  "video/*": [".mp4", ".mov", ".webm", ".avi", ".mkv", ".3gp", ".wmv", ".flv", ".gif"],
};

function formatBytes(bytes) {
  if (!bytes) return "—";
  const units = ["B", "KB", "MB", "GB"];
  let i = 0;
  let n = bytes;
  while (n >= 1024 && i < units.length - 1) {
    n /= 1024;
    i++;
  }
  return `${n.toFixed(n >= 10 || i === 0 ? 0 : 1)} ${units[i]}`;
}

export default function UploadDropzone({
  file,
  onFile,
  videoURL,
  disabled = false,
}) {
  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    accept: ACCEPT,
    multiple: false,
    maxSize: 100 * 1024 * 1024,
    disabled,
    onDrop: (accepted) => {
      if (accepted?.[0]) onFile(accepted[0]);
    },
  });

  if (file && videoURL) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass rounded-2xl p-4"
      >
        <div className="relative overflow-hidden rounded-xl bg-black/40 ring-1 ring-white/5">
          <video
            key={videoURL}
            src={videoURL}
            controls
            className="w-full max-h-[360px] object-contain"
          />
        </div>
        <div className="mt-3 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2.5 min-w-0">
            <span className="grid place-items-center h-9 w-9 rounded-lg bg-brand-500/15 text-brand-500">
              <FileVideo size={16} />
            </span>
            <div className="min-w-0">
              <div className="truncate text-sm font-semibold">{file.name}</div>
              <div className="text-xs text-slate-500 dark:text-slate-400">
                {formatBytes(file.size)}
              </div>
            </div>
          </div>
          <button
            type="button"
            onClick={() => onFile(null)}
            disabled={disabled}
            className="btn-ghost !px-3 !py-2"
          >
            <X size={14} />
            Replace
          </button>
        </div>
      </motion.div>
    );
  }

  return (
    <div
      {...getRootProps({
        className: clsx(
          "relative cursor-pointer rounded-2xl border-2 border-dashed p-10",
          "transition-all duration-200 select-none text-center",
          "border-slate-300/70 dark:border-white/15",
          "bg-white/50 dark:bg-white/[0.02]",
          isDragActive &&
            "border-brand-400 bg-brand-50 dark:bg-brand-500/10 shadow-glow",
          isDragReject && "border-danger bg-red-50 dark:bg-red-900/20",
          disabled && "opacity-60 cursor-not-allowed",
        ),
      })}
    >
      <input {...getInputProps()} />
      <AnimatePresence mode="wait">
        <motion.div
          key={isDragActive ? "active" : "idle"}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -6 }}
          transition={{ duration: 0.18 }}
          className="flex flex-col items-center gap-3"
        >
          <div className="grid place-items-center h-14 w-14 rounded-2xl bg-gradient-to-br from-brand-500 to-accent-500 text-white shadow-glow">
            <CloudUpload size={26} />
          </div>
          <div className="font-display text-lg font-semibold">
            {isDragActive
              ? "Drop the video to analyze"
              : "Drag & drop a video here"}
          </div>
          <div className="text-sm text-slate-500 dark:text-slate-400">
            or <span className="text-brand-500 font-semibold">browse files</span>
            {" "}
            · MP4, MOV, WebM, MKV up to 100 MB
          </div>
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
