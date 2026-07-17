import type {
  BacktestResponse,
  EventSignal,
  HealthResponse,
  IngestResult,
  Signal,
  SourceDocument,
  Ticker,
  TickerSummary,
} from "../types/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {}),
    },
    ...options,
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`${response.status} ${response.statusText}: ${body}`);
  }

  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<HealthResponse>("/api/health"),
  watchlist: () => request<Ticker[]>("/api/watchlist"),
  signals: () => request<Signal[]>("/api/signals"),
  summary: (symbol: string) =>
    request<TickerSummary>(`/api/tickers/${encodeURIComponent(symbol)}/summary`),
  events: (symbol: string) =>
    request<{ events: EventSignal[]; documents: SourceDocument[] }>(
      `/api/tickers/${encodeURIComponent(symbol)}/events`,
    ),
  ingestDaily: () =>
    request<IngestResult>("/api/ingest/daily", {
      method: "POST",
      body: JSON.stringify({
        include_news: true,
        include_filings: true,
      }),
    }),
  backfill: () =>
    request<{ features_inserted: number; signals_inserted: number }>(
      "/api/backfill/signals",
      { method: "POST", body: JSON.stringify({}) },
    ),
  backtest: () =>
    request<BacktestResponse>("/api/backtests", {
      method: "POST",
      body: JSON.stringify({
        threshold: 0.55,
        top_n: 5,
        horizon_days: 5,
        transaction_cost_bps: 5,
      }),
    }),
};

