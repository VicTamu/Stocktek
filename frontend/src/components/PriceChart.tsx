import type { PricePoint } from "../types/api";

interface PriceChartProps {
  points: PricePoint[];
}

export function PriceChart({ points }: PriceChartProps) {
  if (points.length < 2) {
    return <div className="empty-chart">Price history will appear after the first refresh.</div>;
  }

  const width = 560;
  const height = 190;
  const padding = 12;
  const closes = points.map((point) => point.close);
  const min = Math.min(...closes);
  const max = Math.max(...closes);
  const spread = max - min || 1;
  const path = points
    .map((point, index) => {
      const x = padding + (index / (points.length - 1)) * (width - padding * 2);
      const y = height - padding - ((point.close - min) / spread) * (height - padding * 2);
      return `${index === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`;
    })
    .join(" ");

  const end = points[points.length - 1].close;
  const start = points[0].close;
  const positive = end >= start;

  return (
    <div className="chart-frame">
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Price history chart">
        <defs>
          <linearGradient id="chartArea" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor={positive ? "#0f9f6e" : "#d84a4a"} stopOpacity="0.18" />
            <stop offset="100%" stopColor={positive ? "#0f9f6e" : "#d84a4a"} stopOpacity="0" />
          </linearGradient>
        </defs>
        <path
          d={`${path} L ${width - padding} ${height - padding} L ${padding} ${height - padding} Z`}
          fill="url(#chartArea)"
        />
        <path
          d={path}
          fill="none"
          stroke={positive ? "#0f9f6e" : "#d84a4a"}
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="3"
        />
      </svg>
    </div>
  );
}

