import { motion } from "framer-motion";

export default function AnimatedBackground() {
  return (
    <div
      aria-hidden
      className="pointer-events-none fixed inset-0 -z-10 overflow-hidden"
    >
      <div className="absolute inset-0 grid-bg opacity-60 [mask-image:radial-gradient(ellipse_at_center,black_30%,transparent_75%)]" />
      <div
        className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_rgba(49,155,255,0.18),transparent_55%),radial-gradient(ellipse_at_bottom_right,_rgba(124,58,237,0.18),transparent_55%)] dark:bg-[radial-gradient(ellipse_at_top,_rgba(49,155,255,0.22),transparent_55%),radial-gradient(ellipse_at_bottom_right,_rgba(124,58,237,0.28),transparent_55%)]"
      />

      <motion.div
        className="absolute -top-32 -left-24 h-[480px] w-[480px] rounded-full blur-3xl opacity-50 dark:opacity-60"
        style={{
          background:
            "conic-gradient(from 0deg at 50% 50%, #319bff, #7c3aed, #319bff)",
        }}
        animate={{ rotate: 360 }}
        transition={{ duration: 35, repeat: Infinity, ease: "linear" }}
      />
      <motion.div
        className="absolute -bottom-40 -right-32 h-[520px] w-[520px] rounded-full blur-3xl opacity-40 dark:opacity-50"
        style={{
          background:
            "conic-gradient(from 90deg at 50% 50%, #a78bfa, #319bff, #a78bfa)",
        }}
        animate={{ rotate: -360 }}
        transition={{ duration: 45, repeat: Infinity, ease: "linear" }}
      />
    </div>
  );
}
