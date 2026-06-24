import { motion } from "framer-motion";
import { Check, Loader2 } from "lucide-react";
import clsx from "clsx";

import { STAGES } from "./stages.js";

export default function AnalysisStages({ activeStage, progress = 0 }) {
  const activeIdx = STAGES.findIndex((s) => s.key === activeStage);

  return (
    <div className="glass rounded-2xl p-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-sm font-semibold">Analysis pipeline</div>
          <div className="text-xs text-slate-500 dark:text-slate-400">
            Spatial → Temporal → Decision
          </div>
        </div>
        <div className="text-xs font-semibold tabular-nums text-slate-500 dark:text-slate-400">
          {Math.round(progress * 100)}%
        </div>
      </div>

      <div className="mt-4 h-1.5 w-full rounded-full bg-slate-200/60 dark:bg-white/10 overflow-hidden">
        <motion.div
          className="h-full bg-gradient-to-r from-brand-400 via-brand-500 to-accent-500"
          initial={{ width: 0 }}
          animate={{ width: `${progress * 100}%` }}
          transition={{ ease: "easeOut", duration: 0.4 }}
        />
      </div>

      <ul className="mt-5 space-y-2.5">
        {STAGES.map((stage, i) => {
          const done = i < activeIdx;
          const active = i === activeIdx;
          return (
            <li
              key={stage.key}
              className={clsx(
                "flex items-center gap-3 rounded-xl px-3 py-2 transition",
                active && "bg-brand-50/60 dark:bg-brand-500/10",
              )}
            >
              <span
                className={clsx(
                  "grid h-6 w-6 place-items-center rounded-full text-[11px] font-bold",
                  done && "bg-success/20 text-success",
                  active &&
                    "bg-brand-500/20 text-brand-500 ring-2 ring-brand-500/30",
                  !done && !active && "bg-slate-200/70 dark:bg-white/10 text-slate-500",
                )}
              >
                {done ? (
                  <Check size={12} />
                ) : active ? (
                  <Loader2 size={12} className="animate-spin" />
                ) : (
                  i + 1
                )}
              </span>
              <span
                className={clsx(
                  "text-sm",
                  active
                    ? "text-slate-900 dark:text-white font-semibold"
                    : "text-slate-600 dark:text-slate-300",
                )}
              >
                {stage.label}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
