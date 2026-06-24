const STEPS = [10, 20, 40, 60, 80, 100];

export default function SequenceSlider({ value, onChange, disabled }) {
  const idx = Math.max(0, STEPS.indexOf(value));

  return (
    <div className="glass rounded-2xl p-5">
      <div className="flex items-baseline justify-between">
        <div>
          <div className="text-sm font-semibold">Frames analyzed</div>
          <div className="text-xs text-slate-500 dark:text-slate-400">
            More frames = better accuracy, slower inference
          </div>
        </div>
        <div className="font-display text-2xl font-bold text-gradient">
          {value}
        </div>
      </div>
      <input
        type="range"
        min={0}
        max={STEPS.length - 1}
        step={1}
        value={idx}
        disabled={disabled}
        onChange={(e) => onChange(STEPS[Number(e.target.value)])}
        className="mt-4 w-full accent-brand-500"
      />
      <div className="mt-2 flex justify-between text-[10px] uppercase tracking-wider text-slate-400 dark:text-slate-500">
        {STEPS.map((s) => (
          <span key={s}>{s}</span>
        ))}
      </div>
    </div>
  );
}
