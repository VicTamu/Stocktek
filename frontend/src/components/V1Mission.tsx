import { CheckCircle2, Database, FileSearch, LineChart, ShieldAlert } from "lucide-react";
import type { HealthResponse } from "../types/api";

interface V1MissionProps {
  health: HealthResponse;
  apiMode: "live" | "demo";
}

const goals = [
  { label: "Cache daily close", icon: Database },
  { label: "Attach source evidence", icon: FileSearch },
  { label: "Score vs SPY", icon: LineChart },
  { label: "Backtest before trust", icon: CheckCircle2 },
];

export function V1Mission({ health, apiMode }: V1MissionProps) {
  return (
    <section className="mission-strip" aria-label="V1 research loop">
      <div className="mission-copy">
        <span>V1 goal</span>
        <strong>Turn a watchlist into a daily research brief with evidence, not trade orders.</strong>
      </div>

      <div className="mission-steps">
        {goals.map((goal) => {
          const Icon = goal.icon;
          return (
            <div className="mission-step" key={goal.label}>
              <Icon size={15} />
              <span>{goal.label}</span>
            </div>
          );
        })}
      </div>

      <div
        className={
          apiMode === "live" && health.latest_price_date ? "data-health-card" : "data-health-card stale"
        }
      >
        <ShieldAlert size={16} />
        <div>
          <span>{health.latest_price_date ? "Data cached" : "Some data stale"}</span>
          <strong>{health.latest_price_date ?? "Refresh to replace demo signals"}</strong>
        </div>
      </div>
    </section>
  );
}
