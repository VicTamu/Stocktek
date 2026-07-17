from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, Query

from app.analysis.pipeline import (
    get_backtest,
    get_signals,
    get_ticker_events,
    get_ticker_summary,
    get_watchlist,
    ingest_daily,
    run_backfill,
    run_backtest,
    update_watchlist,
)
from app.core.database import fetch_all
from app.models.schemas import BackfillRequest, BacktestRequest, IngestRequest, WatchlistUpdate


router = APIRouter()


@router.get("/health")
def health() -> dict[str, object]:
    counts = {}
    for table in [
        "tickers",
        "price_bars",
        "source_documents",
        "event_signals",
        "feature_snapshots",
        "signals",
        "backtest_runs",
    ]:
        rows = fetch_all(f"SELECT count(*) AS count FROM {table}")
        counts[table] = rows[0]["count"] if rows else 0
    latest = fetch_all("SELECT max(bar_date) AS latest_price_date FROM price_bars")
    return {
        "status": "ok",
        "educational_research_only": True,
        "latest_price_date": latest[0]["latest_price_date"] if latest else None,
        "counts": counts,
    }


@router.get("/watchlist")
def read_watchlist():
    return get_watchlist()


@router.post("/watchlist")
def write_watchlist(payload: WatchlistUpdate):
    return update_watchlist(payload.symbols, payload.replace)


@router.post("/ingest/daily")
def run_daily_ingest(payload: IngestRequest):
    return ingest_daily(payload)


@router.get("/tickers/{symbol}/summary")
def read_ticker_summary(symbol: str):
    return get_ticker_summary(symbol)


@router.get("/tickers/{symbol}/events")
def read_ticker_events(symbol: str):
    return get_ticker_events(symbol)


@router.get("/signals")
def read_signals(signal_date: date | None = Query(default=None, alias="date")):
    return get_signals(signal_date)


@router.post("/backfill/signals")
def create_backfill(payload: BackfillRequest):
    return run_backfill(payload.symbols)


@router.post("/backtests")
def create_backtest(payload: BacktestRequest):
    return run_backtest(payload)


@router.get("/backtests/{backtest_id}")
def read_backtest(backtest_id: str):
    result = get_backtest(backtest_id)
    if not result:
        raise HTTPException(status_code=404, detail="Backtest not found")
    return result

