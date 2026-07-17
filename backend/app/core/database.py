from __future__ import annotations

import json
from collections.abc import Iterable
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Any

import duckdb

from app.core.config import settings


DEFAULT_TICKERS = [
    ("AAPL", "Apple Inc.", "Technology", "NASDAQ", True),
    ("MSFT", "Microsoft Corporation", "Technology", "NASDAQ", True),
    ("NVDA", "NVIDIA Corporation", "Technology", "NASDAQ", True),
    ("AMD", "Advanced Micro Devices, Inc.", "Technology", "NASDAQ", True),
    ("GOOGL", "Alphabet Inc.", "Communication Services", "NASDAQ", True),
    ("AMZN", "Amazon.com, Inc.", "Consumer Discretionary", "NASDAQ", True),
    ("META", "Meta Platforms, Inc.", "Communication Services", "NASDAQ", True),
    ("TSLA", "Tesla, Inc.", "Consumer Discretionary", "NASDAQ", True),
    ("SPY", "SPDR S&P 500 ETF Trust", "Benchmark", "NYSEARCA", True),
    ("QQQ", "Invesco QQQ Trust", "Benchmark", "NASDAQ", True),
]


@contextmanager
def get_connection(read_only: bool = False):
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(settings.db_path), read_only=read_only)
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        create_tables(conn)
        seed_default_watchlist(conn)


def create_tables(conn: duckdb.DuckDBPyConnection) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tickers (
                symbol TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                sector TEXT,
                exchange TEXT,
                active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS price_bars (
                symbol TEXT NOT NULL,
                bar_date DATE NOT NULL,
                open DOUBLE,
                high DOUBLE,
                low DOUBLE,
                close DOUBLE,
                adjusted_close DOUBLE,
                volume BIGINT,
                source TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (symbol, bar_date)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS source_documents (
                id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                source TEXT NOT NULL,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                published_at TIMESTAMP,
                raw_text TEXT,
                content_hash TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS event_signals (
                id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                signal_date DATE NOT NULL,
                event_type TEXT NOT NULL,
                sentiment DOUBLE NOT NULL,
                confidence DOUBLE NOT NULL,
                source_url TEXT,
                summary TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS feature_snapshots (
                symbol TEXT NOT NULL,
                snapshot_date DATE NOT NULL,
                return_1d DOUBLE,
                return_5d DOUBLE,
                return_20d DOUBLE,
                relative_strength_spy DOUBLE,
                relative_strength_qqq DOUBLE,
                volatility_20d DOUBLE,
                volume_ratio_20d DOUBLE,
                news_sentiment DOUBLE,
                event_count INTEGER,
                macro_regime TEXT,
                payload TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (symbol, snapshot_date)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS signals (
                id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                signal_date DATE NOT NULL,
                horizon TEXT NOT NULL,
                probability_outperform_spy DOUBLE NOT NULL,
                confidence TEXT NOT NULL,
                score DOUBLE NOT NULL,
                drivers TEXT NOT NULL,
                risks TEXT NOT NULL,
                evidence TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS backtest_runs (
                id TEXT PRIMARY KEY,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                start_date DATE,
                end_date DATE,
                universe TEXT NOT NULL,
                strategy_rules TEXT NOT NULL,
                benchmark TEXT NOT NULL,
                metrics TEXT NOT NULL,
                trades TEXT NOT NULL
            )
            """
        )


def seed_default_watchlist(conn: duckdb.DuckDBPyConnection) -> None:
    for symbol, name, sector, exchange, active in DEFAULT_TICKERS:
        conn.execute(
            """
            INSERT INTO tickers (symbol, name, sector, exchange, active)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(symbol) DO NOTHING
            """,
            [symbol, name, sector, exchange, active],
        )


def rows_to_dicts(cursor: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    columns = [item[0] for item in cursor.description or []]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def fetch_all(query: str, params: Iterable[Any] | None = None) -> list[dict[str, Any]]:
    with get_connection(read_only=True) as conn:
        return rows_to_dicts(conn.execute(query, list(params or [])))


def fetch_one(query: str, params: Iterable[Any] | None = None) -> dict[str, Any] | None:
    rows = fetch_all(query, params)
    return rows[0] if rows else None


def encode_json(value: Any) -> str:
    return json.dumps(value, default=_json_default)


def decode_json(value: str | None, default: Any = None) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def _json_default(value: Any) -> str:
    if isinstance(value, (date, datetime, Path)):
        return value.isoformat()
    return str(value)

