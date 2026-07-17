from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class Ticker(BaseModel):
    symbol: str
    name: str
    sector: str | None = None
    exchange: str | None = None
    active: bool = True
    latest_price: float | None = None
    latest_date: date | None = None
    return_1d: float | None = None


class WatchlistUpdate(BaseModel):
    symbols: list[str] = Field(default_factory=list)
    replace: bool = False


class IngestRequest(BaseModel):
    symbols: list[str] | None = None
    start: date | None = None
    end: date | None = None
    include_news: bool = True
    include_filings: bool = True


class IngestResult(BaseModel):
    symbols: list[str]
    price_bars_upserted: int
    documents_upserted: int
    event_signals_upserted: int
    feature_snapshots_upserted: int
    signals_upserted: int
    warnings: list[str] = Field(default_factory=list)


class PricePoint(BaseModel):
    date: date
    close: float
    volume: int | None = None


class EventSignal(BaseModel):
    id: str
    symbol: str
    signal_date: date
    event_type: str
    sentiment: float
    confidence: float
    source_url: str | None = None
    summary: str | None = None
    is_demo: bool = False


class SourceDocument(BaseModel):
    id: str
    symbol: str
    source: str
    title: str
    url: str
    published_at: datetime | None = None


class Signal(BaseModel):
    id: str
    symbol: str
    signal_date: date
    horizon: str
    probability_outperform_spy: float
    confidence: Literal["low", "medium", "high"]
    score: float
    drivers: list[str]
    risks: list[str]
    evidence: list[dict[str, Any]]
    is_demo: bool = False


class TickerSummary(BaseModel):
    symbol: str
    name: str
    sector: str | None = None
    exchange: str | None = None
    latest_price: float | None = None
    latest_date: date | None = None
    return_1d: float | None = None
    return_5d: float | None = None
    return_20d: float | None = None
    relative_strength_spy: float | None = None
    volume_ratio_20d: float | None = None
    signal: Signal | None = None
    price_history: list[PricePoint] = Field(default_factory=list)
    events: list[EventSignal] = Field(default_factory=list)
    what_changed: list[str] = Field(default_factory=list)
    why_it_matters: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    next_watch: list[str] = Field(default_factory=list)
    is_demo: bool = False


class BackfillRequest(BaseModel):
    symbols: list[str] | None = None


class BacktestRequest(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    threshold: float = 0.55
    top_n: int = 5
    horizon_days: int = 5
    transaction_cost_bps: float = 5.0


class BacktestResponse(BaseModel):
    id: str
    created_at: datetime | None = None
    start_date: date | None = None
    end_date: date | None = None
    universe: list[str]
    strategy_rules: dict[str, Any]
    benchmark: str
    metrics: dict[str, Any]
    trades: list[dict[str, Any]]

