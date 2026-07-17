import { Activity, PlayCircle } from "lucide-react";
import type { BacktestResponse } from "../types/api";

interface BacktestPanelProps {
  backtest: BacktestResponse | null;
  loading: boolean;
  onRun: () => void;
}

export function BacktestPanel({ backtest, loading, onRun }: BacktestPanelProps) {
  const metrics = backtest?.metrics ?? {};

  return (
    <section className="panel backtest-panel" aria-labelledby="backtest-title">
      <div className="panel-heading">
        <div>
          <h2 id="backtest-title">Backtest health</h2>
          <p>Trust signals only after they beat SPY out of sample.</p>
        </div>
        <button className="secondary-action" disabled={loading} onClick={onRun}>
          <PlayCircle size={16} />
          <span>{loading ? "Running" : "Run"}</span>
        </button>
      </div>

      <div className="backtest-grid">
        <BacktestMetric label="Trades" value={value(metrics.trade_count)} />
        <BacktestMetric label="Win rate" value={percent(metrics.win_rate)} />
        <BacktestMetric label="Avg excess" value={percent(metrics.average_excess_return)} />
        <BacktestMetric label="Drawdown" value={percent(metrics.max_drawdown)} />
      </div>

      <div className="calibration-box">
        <Activity size={16} />
        <span>{describeCalibration(metrics.calibration)}</span>
      </div>
    </section>
  );
}

function BacktestMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="backtest-metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function value(input: unknown): string {
  if (typeof input === "number") {
    return String(input);
  }
  return "n/a";
}

function percent(input: unknown): string {
  if (typeof input !== "number") {
    return "n/a";
  }
  return `${(input * 100).toFixed(1)}%`;
}

function describeCalibration(input: unknown): string {
  if (!input) {
    return "No calibration data yet.";
  }
  if (typeof input === "string") {
    return input;
  }
  return "Calibration buckets are available in the API response.";
}

