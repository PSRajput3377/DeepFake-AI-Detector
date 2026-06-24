import { Link } from "react-router-dom";
import { motion } from "framer-motion";

export default function NotFound() {
  return (
    <motion.section
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8 py-24 text-center"
    >
      <div className="font-mono text-sm text-slate-500 dark:text-slate-400">
        404 · NOT_FOUND
      </div>
      <h1 className="mt-3 font-display text-4xl lg:text-5xl font-extrabold tracking-tight">
        That page is <span className="text-gradient">deepfaked</span>.
      </h1>
      <p className="mt-3 text-slate-600 dark:text-slate-300">
        We can't find it anywhere. Try the detector instead.
      </p>
      <Link to="/" className="mt-8 inline-flex btn-primary">
        Back to home
      </Link>
    </motion.section>
  );
}
