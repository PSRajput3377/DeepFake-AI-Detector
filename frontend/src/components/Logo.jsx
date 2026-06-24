import { motion } from "framer-motion";

export default function Logo({ size = 32, withText = true }) {
  return (
    <div className="flex items-center gap-2.5">
      <motion.svg
        width={size}
        height={size}
        viewBox="0 0 40 40"
        xmlns="http://www.w3.org/2000/svg"
        initial={{ rotate: -8, scale: 0.92, opacity: 0 }}
        animate={{ rotate: 0, scale: 1, opacity: 1 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
      >
        <defs>
          <linearGradient id="lg" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#58bbff" />
            <stop offset="55%" stopColor="#319bff" />
            <stop offset="100%" stopColor="#7c3aed" />
          </linearGradient>
        </defs>
        <rect x="3" y="3" width="34" height="34" rx="10" fill="url(#lg)" />
        <path
          d="M12 25c2 3 5 4.5 8 4.5S26 28 28 25M14 16h.01M26 16h.01"
          stroke="white"
          strokeWidth="2.4"
          strokeLinecap="round"
          fill="none"
        />
        <path
          d="M9 20a11 11 0 0 0 22 0"
          stroke="white"
          strokeOpacity="0.55"
          strokeWidth="1.4"
          strokeDasharray="2 3"
          fill="none"
        />
      </motion.svg>
      {withText && (
        <div className="leading-tight">
          <div className="font-display text-[15px] font-bold tracking-tight">
            DeepFake<span className="text-gradient"> AI</span>
          </div>
          <div className="text-[10px] uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">
            Detector
          </div>
        </div>
      )}
    </div>
  );
}
