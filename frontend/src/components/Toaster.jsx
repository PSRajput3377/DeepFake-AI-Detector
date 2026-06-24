import { useCallback, useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { AlertCircle, CheckCircle2, Info, X } from "lucide-react";
import clsx from "clsx";

import { ToastContext } from "../lib/toastContext.js";

const ICONS = {
  success: CheckCircle2,
  error: AlertCircle,
  info: Info,
};

const STYLES = {
  success: "border-success/30 bg-emerald-50/90 dark:bg-emerald-500/15 text-emerald-700 dark:text-emerald-200",
  error: "border-danger/30 bg-red-50/90 dark:bg-red-500/15 text-red-700 dark:text-red-200",
  info: "border-brand-300/40 bg-brand-50/90 dark:bg-brand-500/15 text-brand-700 dark:text-brand-200",
};

let nextId = 1;

export default function Toaster({ children }) {
  const [items, setItems] = useState([]);

  const dismiss = useCallback((id) => {
    setItems((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const toast = useCallback(
    ({ title, description, type = "info", duration = 4500 }) => {
      const id = nextId++;
      setItems((prev) => [...prev, { id, title, description, type }]);
      if (duration > 0) {
        setTimeout(() => dismiss(id), duration);
      }
      return id;
    },
    [dismiss],
  );

  const value = useMemo(() => ({ toast, dismiss }), [toast, dismiss]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2.5 pointer-events-none">
        <AnimatePresence>
          {items.map((t) => {
            const Icon = ICONS[t.type] || Info;
            return (
              <motion.div
                key={t.id}
                layout
                initial={{ opacity: 0, x: 30, scale: 0.96 }}
                animate={{ opacity: 1, x: 0, scale: 1 }}
                exit={{ opacity: 0, x: 30, scale: 0.96 }}
                transition={{ type: "spring", stiffness: 320, damping: 28 }}
                className={clsx(
                  "pointer-events-auto flex items-start gap-3 rounded-xl border px-4 py-3 shadow-lg backdrop-blur-xl max-w-sm",
                  STYLES[t.type] || STYLES.info,
                )}
              >
                <Icon size={18} className="mt-0.5 shrink-0" />
                <div className="min-w-0 flex-1">
                  {t.title ? (
                    <div className="text-sm font-semibold">{t.title}</div>
                  ) : null}
                  {t.description ? (
                    <div className="text-xs opacity-90 mt-0.5">{t.description}</div>
                  ) : null}
                </div>
                <button
                  type="button"
                  onClick={() => dismiss(t.id)}
                  className="shrink-0 opacity-60 hover:opacity-100"
                  aria-label="Dismiss"
                >
                  <X size={14} />
                </button>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
}
