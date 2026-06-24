import { motion } from "framer-motion";

const NODES = [
  { id: "video", x: 60, y: 130, label: "Video", sub: "input" },
  { id: "frames", x: 200, y: 130, label: "Frames", sub: "OpenCV" },
  { id: "face", x: 340, y: 130, label: "Face crop", sub: "MTCNN / Haar" },
  { id: "resnext", x: 490, y: 60, label: "ResNeXt-50", sub: "spatial features" },
  { id: "lstm", x: 490, y: 200, label: "LSTM", sub: "temporal context" },
  { id: "vit", x: 660, y: 130, label: "MobileViT", sub: "global refinement" },
  { id: "cls", x: 820, y: 130, label: "Classifier", sub: "REAL / FAKE" },
];

const EDGES = [
  ["video", "frames"],
  ["frames", "face"],
  ["face", "resnext"],
  ["face", "lstm"],
  ["resnext", "vit"],
  ["lstm", "vit"],
  ["vit", "cls"],
];

function nodeAt(id) {
  return NODES.find((n) => n.id === id);
}

export default function ArchitectureDiagram() {
  return (
    <div className="overflow-x-auto">
      <svg viewBox="0 0 920 260" className="w-full min-w-[760px]">
        <defs>
          <linearGradient id="edge" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#319bff" />
            <stop offset="100%" stopColor="#7c3aed" />
          </linearGradient>
          <linearGradient id="node" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="rgba(49,155,255,0.18)" />
            <stop offset="100%" stopColor="rgba(124,58,237,0.18)" />
          </linearGradient>
          <filter id="soft" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="6" />
          </filter>
        </defs>

        {EDGES.map(([from, to], i) => {
          const a = nodeAt(from);
          const b = nodeAt(to);
          const path = `M ${a.x + 60} ${a.y} C ${a.x + 110} ${a.y}, ${b.x - 50} ${b.y}, ${b.x - 60} ${b.y}`;
          return (
            <motion.path
              key={`${from}-${to}`}
              d={path}
              stroke="url(#edge)"
              strokeWidth="2"
              fill="none"
              strokeLinecap="round"
              initial={{ pathLength: 0, opacity: 0 }}
              animate={{ pathLength: 1, opacity: 1 }}
              transition={{ delay: i * 0.12, duration: 0.7, ease: "easeOut" }}
            />
          );
        })}

        {NODES.map((n, i) => (
          <motion.g
            key={n.id}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 + i * 0.06 }}
          >
            <rect
              x={n.x - 60}
              y={n.y - 26}
              width={120}
              height={52}
              rx={14}
              fill="url(#node)"
              stroke="rgba(148,163,184,0.35)"
            />
            <text
              x={n.x}
              y={n.y - 4}
              textAnchor="middle"
              className="fill-slate-900 dark:fill-slate-100"
              style={{ fontSize: 13, fontWeight: 700 }}
            >
              {n.label}
            </text>
            <text
              x={n.x}
              y={n.y + 14}
              textAnchor="middle"
              className="fill-slate-500 dark:fill-slate-400"
              style={{ fontSize: 11 }}
            >
              {n.sub}
            </text>
          </motion.g>
        ))}
      </svg>
    </div>
  );
}
