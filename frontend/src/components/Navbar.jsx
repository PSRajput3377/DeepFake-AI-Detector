import { useEffect, useState } from "react";
import { BookOpen, Menu, Sparkles, X } from "lucide-react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import clsx from "clsx";

import Logo from "./Logo.jsx";
import ThemeToggle from "./ThemeToggle.jsx";

const links = [
  { to: "/", label: "Home" },
  { to: "/detect", label: "Detector" },
  { to: "/about", label: "How it works" },
];

export default function Navbar() {
  const [open, setOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    // Close the mobile drawer whenever the route changes.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e) => e.key === "Escape" && setOpen(false);
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);

  return (
    <header className="sticky top-0 z-30 backdrop-blur-xl bg-white/60 dark:bg-[#070b1a]/60 border-b border-slate-200/70 dark:border-white/5">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8 h-16">
        <Link to="/" className="shrink-0">
          <Logo />
        </Link>

        <nav className="hidden md:flex items-center gap-1">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.to === "/"}
              className={({ isActive }) =>
                clsx(
                  "px-3 py-2 text-sm font-medium rounded-lg transition",
                  isActive
                    ? "text-slate-900 dark:text-white bg-slate-100/80 dark:bg-white/10"
                    : "text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100/60 dark:hover:bg-white/5",
                )
              }
            >
              {l.label}
            </NavLink>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noreferrer"
            aria-label="API docs"
            title="API docs"
            className="hidden sm:inline-flex h-9 w-9 items-center justify-center rounded-xl
                       border border-slate-200/70 dark:border-white/10
                       bg-white/60 dark:bg-white/5 backdrop-blur
                       text-slate-700 dark:text-slate-200
                       hover:bg-white/90 dark:hover:bg-white/10 transition"
          >
            <BookOpen size={16} />
          </a>
          <ThemeToggle />
          <Link
            to="/detect"
            className="ml-1 hidden sm:inline-flex btn-primary"
          >
            <Sparkles size={15} />
            Try it
          </Link>
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            aria-label="Toggle navigation"
            aria-expanded={open}
            className="md:hidden inline-flex h-9 w-9 items-center justify-center rounded-xl
                       border border-slate-200/70 dark:border-white/10
                       bg-white/60 dark:bg-white/5 backdrop-blur
                       text-slate-700 dark:text-slate-200"
          >
            {open ? <X size={16} /> : <Menu size={16} />}
          </button>
        </div>
      </div>

      <AnimatePresence>
        {open ? (
          <motion.div
            key="mobile-nav"
            initial={{ opacity: 0, y: -8, height: 0 }}
            animate={{ opacity: 1, y: 0, height: "auto" }}
            exit={{ opacity: 0, y: -8, height: 0 }}
            transition={{ duration: 0.18 }}
            className="md:hidden border-t border-slate-200/70 dark:border-white/5 bg-white/85 dark:bg-[#070b1a]/85 backdrop-blur-xl overflow-hidden"
          >
            <div className="mx-auto max-w-7xl px-4 sm:px-6 py-3 flex flex-col gap-1">
              {links.map((l) => (
                <NavLink
                  key={l.to}
                  to={l.to}
                  end={l.to === "/"}
                  className={({ isActive }) =>
                    clsx(
                      "px-3 py-2.5 text-sm font-medium rounded-lg transition",
                      isActive
                        ? "text-slate-900 dark:text-white bg-slate-100/80 dark:bg-white/10"
                        : "text-slate-600 dark:text-slate-300 hover:bg-slate-100/60 dark:hover:bg-white/5",
                    )
                  }
                >
                  {l.label}
                </NavLink>
              ))}
              <Link to="/detect" className="btn-primary mt-1 w-full">
                <Sparkles size={15} />
                Try the detector
              </Link>
            </div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </header>
  );
}
