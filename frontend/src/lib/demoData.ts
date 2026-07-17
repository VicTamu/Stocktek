import type {
  BacktestResponse,
  HealthResponse,
  Signal,
  Ticker,
  TickerSummary,
} from "../types/api";

const today = new Date();
const isoDate = (daysAgo = 0) => {
  const value = new Date(today);
  value.setDate(value.getDate() - daysAgo);
  return value.toISOString().slice(0, 10);
};

const tickers: Ticker[] = [
  { symbol: "AAPL", name: "Apple Inc.", sector: "Technology", exchange: "NASDAQ", active: true },
  { symbol: "MSFT", name: "Microsoft Corporation", sector: "Technology", exchange: "NASDAQ", active: true },
  { symbol: "NVDA", name: "NVIDIA Corporation", sector: "Technology", exchange: "NASDAQ", active: true },
  { symbol: "AMD", name: "Advanced Micro Devices, Inc.", sector: "Technology", exchange: "NASDAQ", active: true },
  { symbol: "SPY", name: "SPDR S&P 500 ETF Trust", sector: "Benchmark", exchange: "NYSEARCA", active: true },
];

export const demoHealth: HealthResponse = {
  status: "demo",
  educational_research_only: true,
  latest_price_date: null,
  counts: {
    tickers: tickers.length,
    price_bars: 0,
    source_documents: 0,
    event_signals: 0,
    feature_snapshots: 0,
    signals: 0,
    backtest_runs: 0,
  },
};

export const demoWatchlist = tickers;

export const demoSignals: Signal[] = [
  signal("NVDA", 0.63, "medium"),
  signal("MSFT", 0.59, "medium"),
  signal("AMD", 0.56, "low"),
  signal("AAPL", 0.54, "low"),
];

export function demoSummary(symbol: string): TickerSummary {
  const selected = tickers.find((item) => item.symbol === symbol) ?? tickers[0];
  const matchedSignal = demoSignals.find((item) => item.symbol === selected.symbol) ?? signal(selected.symbol, 0.52, "low");
  return {
    symbol: selected.symbol,
    name: selected.name,
    sector: selected.sector,
    exchange: selected.exchange,
    latest_price: selected.symbol === "NVDA" ? 144.9 : selected.symbol === "MSFT" ? 498.3 : 212.4,
    latest_date: isoDate(),
    return_1d: 0.006,
    return_5d: selected.symbol === "NVDA" ? 0.041 : 0.019,
    return_20d: selected.symbol === "NVDA" ? 0.083 : 0.034,
    relative_strength_spy: selected.symbol === "NVDA" ? 0.034 : 0.006,
    volume_ratio_20d: 1.32,
    signal: matchedSignal,
    price_history: Array.from({ length: 48 }, (_, index) => ({
      date: isoDate(47 - index),
      close: Number((120 + index * 0.75 + Math.sin(index / 3) * 4).toFixed(2)),
      volume: 15000000 + index * 50000,
    })),
    events: [
      {
        id: `demo-${selected.symbol}-earnings`,
        symbol: selected.symbol,
        signal_date: isoDate(1),
        event_type: "earnings",
        sentiment: 0.4,
        confidence: 0.55,
        source_url: "https://www.sec.gov/edgar/search/",
        summary: `${selected.symbol} demo earnings and filing watch item`,
      },
      {
        id: `demo-${selected.symbol}-news`,
        symbol: selected.symbol,
        signal_date: isoDate(2),
        event_type: "general",
        sentiment: 0.2,
        confidence: 0.45,
        source_url: "https://www.gdeltproject.org/data.html",
        summary: `${selected.symbol} demo market news item from free source discovery`,
      },
    ],
    what_changed: [
      "Demo momentum is constructive versus the watchlist baseline.",
      "The signal is awaiting real price, filing, and news ingestion.",
    ],
    why_it_matters: [
      "StockTek ranks tickers by probability, confidence, and evidence quality.",
      "Every real signal should be checked against source links and backtests.",
    ],
    risks: matchedSignal.risks,
    next_watch: [
      "Run Refresh Daily Data after market close.",
      "Check whether the signal still beats SPY in backtesting.",
    ],
    is_demo: true,
  };
}

export const demoBacktest: BacktestResponse = {
  id: "demo-backtest",
  created_at: new Date().toISOString(),
  universe: ["NVDA", "MSFT", "AMD"],
  strategy_rules: {
    threshold: 0.55,
    top_n: 5,
    horizon_days: 5,
    transaction_cost_bps: 5,
  },
  benchmark: "SPY",
  metrics: {
    trade_count: 0,
    win_rate: null,
    average_return: null,
    average_excess_return: null,
    max_drawdown: null,
    sharpe_like: null,
    calibration: "Run a real ingest first.",
  },
  trades: [],
};

function signal(symbol: string, probability: number, confidence: "low" | "medium" | "high"): Signal {
  return {
    id: `demo-${symbol}`,
    symbol,
    signal_date: isoDate(),
    horizon: "5 trading days",
    probability_outperform_spy: probability,
    confidence,
    score: Number(((probability - 0.5) * 2).toFixed(4)),
    drivers: [
      "Recent relative strength is positive in the demo dataset.",
      "Source sentiment skews slightly positive.",
    ],
    risks: [
      "This is demo data until a daily refresh completes.",
      "V1 signals are research aids, not trade instructions.",
    ],
    evidence: [
      {
        type: "filing",
        summary: `${symbol} demo SEC filing watch item`,
        url: "https://www.sec.gov/edgar/search/",
        sentiment: 0.2,
        confidence: 0.5,
      },
    ],
  };
}

