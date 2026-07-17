import { useCallback, useEffect, useMemo, useState } from "react";
import { BacktestPanel } from "./components/BacktestPanel";
import { EventTimeline } from "./components/EventTimeline";
import { Sidebar } from "./components/Sidebar";
import { TickerDetail } from "./components/TickerDetail";
import { TopBar } from "./components/TopBar";
import { V1Mission } from "./components/V1Mission";
import { WatchlistTable } from "./components/WatchlistTable";
import { api } from "./lib/api";
import {
  demoBacktest,
  demoHealth,
  demoSignals,
  demoSummary,
  demoWatchlist,
} from "./lib/demoData";
import type {
  BacktestResponse,
  HealthResponse,
  IngestResult,
  Signal,
  Ticker,
  TickerSummary,
} from "./types/api";

export default function App() {
  const [health, setHealth] = useState<HealthResponse>(demoHealth);
  const [watchlist, setWatchlist] = useState<Ticker[]>(demoWatchlist);
  const [signals, setSignals] = useState<Signal[]>(demoSignals);
  const [selectedSymbol, setSelectedSymbol] = useState("NVDA");
  const [summary, setSummary] = useState<TickerSummary | null>(demoSummary("NVDA"));
  const [backtest, setBacktest] = useState<BacktestResponse | null>(demoBacktest);
  const [apiMode, setApiMode] = useState<"live" | "demo">("demo");
  const [loadingRefresh, setLoadingRefresh] = useState(false);
  const [loadingBacktest, setLoadingBacktest] = useState(false);
  const [ingestResult, setIngestResult] = useState<IngestResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadInitial = useCallback(async () => {
    try {
      const [healthResult, watchlistResult, signalsResult] = await Promise.all([
        api.health(),
        api.watchlist(),
        api.signals(),
      ]);
      setHealth(healthResult);
      setWatchlist(watchlistResult);
      setSignals(signalsResult);
      setApiMode("live");
      setError(null);
      const nextSymbol = signalsResult[0]?.symbol ?? watchlistResult[0]?.symbol ?? "AAPL";
      setSelectedSymbol(nextSymbol);
    } catch (err) {
      setApiMode("demo");
      setHealth(demoHealth);
      setWatchlist(demoWatchlist);
      setSignals(demoSignals);
      setSelectedSymbol("NVDA");
      setSummary(demoSummary("NVDA"));
      setError(err instanceof Error ? err.message : "Backend unavailable");
    }
  }, []);

  useEffect(() => {
    void loadInitial();
  }, [loadInitial]);

  useEffect(() => {
    let mounted = true;
    async function loadSummary() {
      if (apiMode === "demo") {
        setSummary(demoSummary(selectedSymbol));
        return;
      }
      try {
        const result = await api.summary(selectedSymbol);
        if (mounted) {
          setSummary(result);
          setError(null);
        }
      } catch (err) {
        if (mounted) {
          setSummary(demoSummary(selectedSymbol));
          setError(err instanceof Error ? err.message : "Ticker summary unavailable");
        }
      }
    }

    void loadSummary();
    return () => {
      mounted = false;
    };
  }, [apiMode, selectedSymbol]);

  const selectedEvents = useMemo(() => summary?.events ?? [], [summary]);

  async function refreshDailyData() {
    setLoadingRefresh(true);
    try {
      const result = await api.ingestDaily();
      setIngestResult(result);
      await loadInitial();
      const nextSummary = await api.summary(selectedSymbol);
      setSummary(nextSummary);
      setApiMode("live");
      setError(null);
    } catch (err) {
      setApiMode("demo");
      setError(err instanceof Error ? err.message : "Daily refresh failed");
    } finally {
      setLoadingRefresh(false);
    }
  }

  async function runBacktest() {
    setLoadingBacktest(true);
    try {
      const result = await api.backtest();
      setBacktest(result);
      setError(null);
    } catch (err) {
      setBacktest(demoBacktest);
      setError(err instanceof Error ? err.message : "Backtest failed");
    } finally {
      setLoadingBacktest(false);
    }
  }

  return (
    <div className="app-shell">
      <Sidebar />
      <main className="workspace">
        <TopBar
          apiMode={apiMode}
          health={health}
          ingestResult={ingestResult}
          loading={loadingRefresh}
          onRefresh={refreshDailyData}
          signalsAreDemo={signals.some((signal) => signal.is_demo)}
        />

        <V1Mission apiMode={apiMode} health={health} />

        {error && (
          <div className="error-banner">
            <strong>Local data warning:</strong> {error}
          </div>
        )}

        <div className="dashboard-grid">
          <div className="primary-column">
            <WatchlistTable
              selectedSummary={summary}
              selectedSymbol={selectedSymbol}
              signals={signals}
              watchlist={watchlist}
              onSelect={setSelectedSymbol}
            />
            <div className="right-rail">
              <EventTimeline events={selectedEvents} />
              <BacktestPanel backtest={backtest} loading={loadingBacktest} onRun={runBacktest} />
            </div>
          </div>
          <TickerDetail summary={summary} />
        </div>
      </main>
    </div>
  );
}
