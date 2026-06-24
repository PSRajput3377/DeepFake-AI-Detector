import Logo from "./Logo.jsx";

export default function Footer() {
  return (
    <footer className="relative border-t border-slate-200/70 dark:border-white/5 bg-white/40 dark:bg-[#070b1a]/40 backdrop-blur-xl">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="flex items-center gap-3">
          <Logo size={28} />
        </div>
        <div className="text-xs text-slate-500 dark:text-slate-400">
          Built with React, Tailwind, FastAPI and PyTorch.
        </div>
      </div>
    </footer>
  );
}
