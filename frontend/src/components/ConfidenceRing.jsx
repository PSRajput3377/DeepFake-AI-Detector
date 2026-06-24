import { motion } from "framer-motion";

export default function ConfidenceRing({
  value = 0,
  size = 184,
  stroke = 14,
  label = "FAKE",
  isFake = true,
}) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const offset = c - c * value;

  const colorStops = isFake
    ? [
        { offset: "0%", stopColor: "#fb7185" },
        { offset: "100%", stopColor: "#ef4444" },
      ]
    : [
        { offset: "0%", stopColor: "#34d399" },
        { offset: "100%", stopColor: "#10b981" },
      ];

  return (
    <div
      className="relative inline-grid place-items-center"
      style={{ width: size, height: size }}
    >
      <svg width={size} height={size} className="rotate-[-90deg]">
        <defs>
          <linearGradient id="ring-grad" x1="0" y1="0" x2="1" y2="1">
            {colorStops.map((s) => (
              <stop key={s.offset} {...s} />
            ))}
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
          stroke="url(#ring-grad)"
          strokeWidth={stroke}
          strokeLinecap="round"
          fill="none"
          strokeDasharray={c}
          initial={{ strokeDashoffset: c }}
          animate={{ strokeDashoffset: offset }}
          transition={{ ease: "easeOut", duration: 1.1 }}
        />
      </svg>

      <div className="absolute inset-0 grid place-items-center text-center">
        <div>
          <motion.div
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400"
          >
            Verdict
          </motion.div>
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3 }}
            className={
              "font-display text-[28px] font-extrabold tracking-tight " +
              (isFake ? "text-danger" : "text-success")
            }
          >
            {label}
          </motion.div>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="mt-1 text-sm tabular-nums text-slate-500 dark:text-slate-400"
          >
            {(value * 100).toFixed(1)}% confidence
          </motion.div>
        </div>
      </div>
    </div>
  );
}
