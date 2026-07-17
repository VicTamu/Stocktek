from __future__ import annotations

from datetime import date, timedelta

import duckdb

from app.analysis.backfill import backfill_signals
from app.core.database import create_tables


def _memory_db() -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(":memory:")
    create_tables(conn)
    conn.execute(
        "INSERT INTO tickers (symbol, name, sector, exchange, active) VALUES "
        "('AAPL', 'Apple Inc.', 'Technology', 'NASDAQ', TRUE), "
        "('SPY', 'SPDR S&P 500', 'Benchmark', 'NYSEARCA', TRUE)"
    )
    return conn


def _insert_bars(conn: duckdb.DuckDBPyConnection, symbol: str, days: int, base: float) -> list[date]:
    start = date(2026, 1, 5)
    dates = []
    for offset in range(days):
        bar_date = start + timedelta(days=offset)
        close = base * (1 + 0.002 * offset)
        conn.execute(
            "INSERT INTO price_bars (symbol, bar_date, open, high, low, close, adjusted_close, volume, source) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'test') ON CONFLICT (symbol, bar_date) DO NOTHING",
            [symbol, bar_date, close, close, close, close, close, 1_000_000],
        )
        dates.append(bar_date)
    return dates


def test_backfill_creates_signals_for_history():
    conn = _memory_db()
    dates = _insert_bars(conn, "AAPL", 30, 100.0)
    _insert_bars(conn, "SPY", 30, 400.0)

    result = backfill_signals(conn)

    # One signal per bar date once MIN_HISTORY (6) bars exist.
    assert result["signals_inserted"] == len(dates) - 5
    assert result["features_inserted"] == result["signals_inserted"]
    macro = conn.execute(
        "SELECT DISTINCT macro_regime FROM feature_snapshots WHERE symbol = 'AAPL'"
    ).fetchall()
    assert macro == [("backfill_price_only",)]


def test_backfill_is_point_in_time_stable():
    conn = _memory_db()
    _insert_bars(conn, "AAPL", 30, 100.0)
    _insert_bars(conn, "SPY", 30, 400.0)
    backfill_signals(conn)
    check_date = date(2026, 1, 5) + timedelta(days=20)
    before = conn.execute(
        "SELECT probability_outperform_spy FROM signals WHERE symbol = 'AAPL' AND signal_date = ?",
        [check_date],
    ).fetchone()

    # New data arriving later must not rewrite history.
    _insert_bars(conn, "AAPL", 45, 100.0)
    _insert_bars(conn, "SPY", 45, 400.0)
    second = backfill_signals(conn)
    after = conn.execute(
        "SELECT probability_outperform_spy FROM signals WHERE symbol = 'AAPL' AND signal_date = ?",
        [check_date],
    ).fetchone()

    assert before == after
    assert second["signals_inserted"] == 15  # only the newly added dates


def test_backfill_never_overwrites_live_signals():
    conn = _memory_db()
    _insert_bars(conn, "AAPL", 10, 100.0)
    _insert_bars(conn, "SPY", 10, 400.0)
    live_date = date(2026, 1, 5) + timedelta(days=9)
    conn.execute(
        "INSERT INTO signals (id, symbol, signal_date, horizon, probability_outperform_spy, "
        "confidence, score, drivers, risks, evidence) "
        "VALUES ('live-row', 'AAPL', ?, '5 trading days', 0.91, 'high', 0.82, '[]', '[]', '[]')",
        [live_date],
    )

    backfill_signals(conn)

    row = conn.execute(
        "SELECT probability_outperform_spy FROM signals WHERE symbol = 'AAPL' AND signal_date = ?",
        [live_date],
    ).fetchone()
    assert row == (0.91,)
