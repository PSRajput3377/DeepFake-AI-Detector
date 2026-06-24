import { useState } from "react";
import { motion } from "framer-motion";
import clsx from "clsx";

import { resolveMediaURL } from "../lib/api.js";

export default function FrameStrip({ title, urls, emptyHint, accent = "brand" }) {
  const [active, setActive] = useState(0);

  if (!urls || urls.length === 0) {
    return (
      <div className="text-sm text-slate-500 dark:text-slate-400">
        {emptyHint || "No frames available."}
      </div>
    );
  }

  const accentClass =
    accent === "danger"
      ? "ring-danger/40"
      : accent === "success"
      ? "ring-success/40"
      : "ring-brand-400/50";

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <div className="text-sm font-semibold">{title}</div>
        <div className="text-xs text-slate-500 dark:text-slate-400 tabular-nums">
          {active + 1} / {urls.length}
        </div>
      </div>
      <div className="relative overflow-hidden rounded-xl bg-black/30 ring-1 ring-white/5">
        <motion.img
          key={urls[active]}
          src={resolveMediaURL(urls[active])}
          alt={`Frame ${active + 1}`}
          className="w-full max-h-[320px] object-contain"
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.25 }}
        />
      </div>
      <div className="mt-3 flex gap-2 overflow-x-auto pb-1">
        {urls.map((url, i) => (
          <button
            key={url}
            onClick={() => setActive(i)}
            className={clsx(
              "shrink-0 h-14 w-20 rounded-lg overflow-hidden ring-2 transition",
              i === active
                ? `ring-2 ${accentClass}`
                : "ring-transparent opacity-70 hover:opacity-100",
            )}
          >
            <img
              src={resolveMediaURL(url)}
              alt=""
              className="h-full w-full object-cover"
            />
          </button>
        ))}
      </div>
    </div>
  );
}
