from __future__ import annotations

from bisect import bisect_right
from typing import Any

import duckdb

from app.analysis.indicators import build_feature_snapshot
from app.analysis.signals import build_signal
from app.core.database import encode_json

# Matches the minimum history build_feature_snapshot needs to emit a snapshot.
MIN_HISTORY = 6

# Backfilled rows are price-features-only: no news sentiment, no macro regime.
# Reconstructing those point-in-time is not possible from cached data, and
# pretending otherwise would leak lookahead into the backtest.
BACKFILL_MACRO_REGIME = "backfill_price_only"


def backfill_signals(
    conn: duckdb.DuckDBPyConnection,
    symbols: list[str] | None = None,
) -> dict[str, Any]:
    """Reconstruct point-in-time feature snapshots and signals for every
    cached completed session. Insert-only: rows produced by live ingests
    are never overwritten."""
    if symbols is None:
        symbols = [
            row[0]
            for row in conn.execute(
                """
                SELECT symbol FROM tickers
                WHERE active = TRUE AND coalesce(sector, '') != 'Benchmark'
                ORDER BY symbol
                """
            ).fetchall()
        ]

    spy_bars = _load_bars(conn, "SPY")
    qqq_bars = _load_bars(conn, "QQQ")
    vix_bars = _load_bars(conn, "^VIX")

    features_inserted = 0
    signals_inserted = 0

    for symbol in symbols:
        bars = _load_bars(conn, symbol)
        if len(bars) < MIN_HISTORY:
            continue

        existing_feature_dates = {
            row[0]
            for row in conn.execute(
                "SELECT snapshot_date FROM feature_snapshots WHERE symbol = ?", [symbol]
            ).fetchall()
        }
        existing_signal_dates = {
            row[0]
            for row in conn.execute(
                "SELECT signal_date FROM signals WHERE symbol = ?", [symbol]
            ).fetchall()
        }

        spy_dates = [bar["bar_date"] for bar in spy_bars]
        qqq_dates = [bar["bar_date"] for bar in qqq_bars]
        vix_dates = [bar["bar_date"] for bar in vix_bars]

        for index in range(MIN_HISTORY - 1, len(bars)):
            snapshot_date = bars[index]["bar_date"]
            need_feature = snapshot_date not in existing_feature_dates
            need_signal = snapshot_date not in existing_signal_dates
            if not need_feature and not need_signal:
                continue

            feature = build_feature_snapshot(
                symbol,
                bars[: index + 1],
                spy_bars[: bisect_right(spy_dates, snapshot_date)],
                qqq_bars[: bisect_right(qqq_dates, snapshot_date)],
                [],
                BACKFILL_MACRO_REGIME,
                vix_bars[: bisect_right(vix_dates, snapshot_date)],
            )
            if not feature:
                continue
            feature["payload"]["generated_by"] = "backfill"

            if need_feature:
                _insert_feature(conn, feature)
                features_inserted += 1
            if need_signal:
                _insert_signal(conn, build_signal(symbol, feature, []))
                signals_inserted += 1

    return {
        "symbols": symbols,
        "features_inserted": features_inserted,
        "signals_inserted": signals_inserted,
    }


def _load_bars(conn: duckdb.DuckDBPyConnection, symbol: str) -> list[dict[str, Any]]:
    cursor = conn.execute(
        """
        SELECT symbol, bar_date, open, high, low, close, adjusted_close, volume, source
        FROM price_bars
        WHERE symbol = ?
        ORDER BY bar_date ASC
        """,
        [symbol],
    )
    columns = [item[0] for item in cursor.description or []]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _insert_feature(conn: duckdb.DuckDBPyConnection, feature: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT INTO feature_snapshots (
            symbol, snapshot_date, return_1d, return_5d, return_20d,
            relative_strength_spy, relative_strength_qqq, volatility_20d,
            volume_ratio_20d, news_sentiment, event_count, macro_regime, payload
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (symbol, snapshot_date) DO NOTHING
        """,
        [
            feature["symbol"],
            feature["snapshot_date"],
            feature.get("return_1d"),
            feature.get("return_5d"),
            feature.get("return_20d"),
            feature.get("relative_strength_spy"),
            feature.get("relative_strength_qqq"),
            feature.get("volatility_20d"),
            feature.get("volume_ratio_20d"),
            feature.get("news_sentiment"),
            feature.get("event_count"),
            feature.get("macro_regime"),
            encode_json(feature.get("payload", {})),
        ],
    )


def _insert_signal(conn: duckdb.DuckDBPyConnection, signal: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT INTO signals (
            id, symbol, signal_date, horizon, probability_outperform_spy,
            confidence, score, drivers, risks, evidence
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (id) DO NOTHING
        """,
        [
            signal["id"],
            signal["symbol"],
            signal["signal_date"],
            signal["horizon"],
            signal["probability_outperform_spy"],
            signal["confidence"],
            signal["score"],
            encode_json(signal["drivers"]),
            encode_json(signal["risks"]),
            encode_json(signal["evidence"]),
        ],
    )
