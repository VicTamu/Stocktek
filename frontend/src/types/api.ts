export type Confidence = "low" | "medium" | "high";

export interface Ticker {
  symbol: string;
  name: string;
  sector?: string | null;
  exchange?: string | null;
  active: boolean;
  latest_price?: number | null;
  latest_date?: string | null;
  return_1d?: number | null;
}

export interface PricePoint {
  date: string;
  close: number;
  volume?: number | null;
}

export interface EvidenceItem {
  type: string;
  summary?: string | null;
  url?: string | null;
  sentiment?: number | null;
  confidence?: number | null;
}

export interface Signal {
  id: string;
  symbol: string;
  signal_date: string;
  horizon: string;
  probability_outperform_spy: number;
  confidence: Confidence;
  score: number;
  drivers: string[];
  risks: string[];
  evidence: EvidenceItem[];
  is_demo?: boolean;
}

export interface EventSignal {
  id: string;
  symbol: string;
  signal_date: string;
  event_type: string;
  sentiment: number;
  confidence: number;
  source_url?: string | null;
  summary?: string | null;
  is_demo?: boolean;
}

export interface SourceDocument {
  id: string;
  symbol: string;
  source: string;
  title: string;
  url: string;
  published_at?: string | null;
}

export interface TickerSummary {
  symbol: string;
  name: string;
  sector?: string | null;
  exchange?: string | null;
  latest_price?: number | null;
  latest_date?: string | null;
  return_1d?: number | null;
  return_5d?: number | null;
  return_20d?: number | null;
  relative_strength_spy?: number | null;
  volume_ratio_20d?: number | null;
  signal?: Signal | null;
  price_history: PricePoint[];
  events: EventSignal[];
  what_changed: string[];
  why_it_matters: string[];
  risks: string[];
  next_watch: string[];
  is_demo: boolean;
}

export interface HealthResponse {
  status: string;
  educational_research_only: boolean;
  latest_price_date?: string | null;
  counts: Record<string, number>;
}

export interface IngestResult {
  symbols: string[];
  price_bars_upserted: number;
  documents_upserted: number;
  event_signals_upserted: number;
  feature_snapshots_upserted: number;
  signals_upserted: number;
  warnings: string[];
}

export interface BacktestResponse {
  id: string;
  created_at?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  universe: string[];
  strategy_rules: Record<string, unknown>;
  benchmark: string;
  metrics: Record<string, unknown>;
  trades: Array<Record<string, unknown>>;
}

