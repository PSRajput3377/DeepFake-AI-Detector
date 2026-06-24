import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { useTheme } from "../lib/themeContext.js";

export default function PerFrameChart({ data }) {
  const { theme } = useTheme();
  const isDark = theme === "dark";
  const grid = isDark ? "rgba(255,255,255,0.07)" : "rgba(15,23,42,0.08)";
  const tickColor = isDark ? "rgba(226,232,240,0.6)" : "rgba(51,65,85,0.7)";

  const chartData = (data || []).map((p, i) => ({
    frame: i + 1,
    fake: Number((p * 100).toFixed(2)),
    real: Number(((1 - p) * 100).toFixed(2)),
  }));

  if (!chartData.length) {
    return (
      <div className="text-sm text-slate-500 dark:text-slate-400">
        No per-frame probability data was returned by the model.
      </div>
    );
  }

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer>
        <AreaChart data={chartData} margin={{ top: 10, right: 14, left: -12, bottom: 0 }}>
          <defs>
            <linearGradient id="fakeGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#ef4444" stopOpacity={0.55} />
              <stop offset="100%" stopColor="#ef4444" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="realGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#10b981" stopOpacity={0.45} />
              <stop offset="100%" stopColor="#10b981" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke={grid} strokeDasharray="3 4" />
          <XAxis
            dataKey="frame"
            stroke={tickColor}
            tickLine={false}
            axisLine={false}
            fontSize={11}
            label={{
              value: "Frame",
              position: "insideBottomRight",
              offset: -2,
              fill: tickColor,
              fontSize: 11,
            }}
          />
          <YAxis
            stroke={tickColor}
            tickLine={false}
            axisLine={false}
            fontSize={11}
            domain={[0, 100]}
            unit="%"
          />
          <Tooltip
            contentStyle={{
              background: isDark ? "rgba(15,23,42,0.95)" : "rgba(255,255,255,0.95)",
              border: `1px solid ${isDark ? "rgba(255,255,255,0.08)" : "rgba(15,23,42,0.08)"}`,
              borderRadius: 12,
              fontSize: 12,
              color: isDark ? "white" : "#0f172a",
            }}
            formatter={(value, key) => [`${value}%`, key === "fake" ? "Fake prob" : "Real prob"]}
            labelFormatter={(l) => `Frame ${l}`}
          />
          <ReferenceLine y={50} stroke={tickColor} strokeDasharray="2 4" />
          <Area
            type="monotone"
            dataKey="real"
            stroke="#10b981"
            strokeWidth={1.5}
            fill="url(#realGrad)"
          />
          <Area
            type="monotone"
            dataKey="fake"
            stroke="#ef4444"
            strokeWidth={2}
            fill="url(#fakeGrad)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
