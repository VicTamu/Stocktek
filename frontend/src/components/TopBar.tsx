import { RefreshCcw, ShieldCheck, WifiOff } from "lucide-react";
import type { HealthResponse, IngestResult } from "../types/api";

interface TopBarProps {
  health: HealthResponse;
  loading: boolean;
  ingestResult?: IngestResult | null;
  apiMode: "live" | "demo";
  onRefresh: () => void;
}

export function TopBar({ health, loading, ingestResult, apiMode, onRefresh }: TopBarProps) {
  const today = new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date());

  return (
    <header className="topbar">
      <div className="market-status">
        <span className="market-dot" />
        <strong>Market closed</strong>
        <span>{today}</span>
        <span>Data as of daily close</span>
        <span>Educational research only. Not financial advice.</span>
      </div>

      <div className="topbar-actions">
        <div className={apiMode === "live" ? "status-pill" : "status-pill warning"}>
          {apiMode === "live" ? <ShieldCheck size={16} /> : <WifiOff size={16} />}
          <span>{apiMode === "live" ? "Local API online" : "Demo fallback"}</span>
        </div>
        <div className="market-date">
          <span>Latest close</span>
          <strong>{health.latest_price_date ?? "not cached"}</strong>
        </div>
        <button className="primary-action" disabled={loading} onClick={onRefresh}>
          <RefreshCcw size={16} className={loading ? "spin" : undefined} />
          <span>{loading ? "Refreshing" : "Refresh data"}</span>
        </button>
      </div>

      {ingestResult && (
        <div className="ingest-strip" role="status">
          <strong>{ingestResult.signals_upserted}</strong> signals,
          <strong> {ingestResult.price_bars_upserted}</strong> price bars,
          <strong> {ingestResult.documents_upserted}</strong> source docs cached.
        </div>
      )}
    </header>
  );
}
