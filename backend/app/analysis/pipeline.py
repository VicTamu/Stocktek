from __future__ import annotations

import hashlib
from datetime import date, datetime
from typing import Any

import duckdb

from app.adapters.fred import fetch_macro_snapshot
from app.adapters.gdelt import fetch_market_news
from app.adapters.prices import fetch_price_bars
from app.adapters.sec import fetch_recent_filings
from app.analysis.indicators import build_feature_snapshot
from app.analysis.sentiment import classify_document, document_id
from app.analysis.signals import build_signal
from app.core.database import decode_json, encode_json, fetch_all, fetch_one, get_connection
from app.core.demo_data import demo_events, demo_signals, demo_summary
from app.models.schemas import BacktestRequest, IngestRequest
from app.analysis.backfill import backfill_signals
from app.analysis.backtest import run_signal_backtest


def get_watchlist() -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT
            t.symbol, t.name, t.sector, t.exchange, t.active,
            prices.latest_price, prices.latest_date, features.return_1d
        FROM tickers t
        LEFT JOIN (
            SELECT
                symbol,
                arg_max(coalesce(adjusted_close, close), bar_date) AS latest_price,
                max(bar_date) AS latest_date
            FROM price_bars
            GROUP BY symbol
        ) prices ON prices.symbol = t.symbol
        LEFT JOIN (
            SELECT symbol, arg_max(return_1d, snapshot_date) AS return_1d
            FROM feature_snapshots
            GROUP BY symbol
        ) features ON features.symbol = t.symbol
        WHERE t.active = TRUE
        ORDER BY
            CASE WHEN t.sector = 'Benchmark' THEN 1 ELSE 0 END,
            t.symbol
        """
    )


def update_watchlist(symbols: list[str], replace: bool = False) -> list[dict[str, Any]]:
    cleaned = sorted({symbol.upper().strip() for symbol in symbols if symbol.strip()})
    with get_connection() as conn:
        if replace:
            conn.execute("UPDATE tickers SET active = FALSE, updated_at = CURRENT_TIMESTAMP")
        for symbol in cleaned:
            conn.execute(
                """
                INSERT INTO tickers (symbol, name, sector, exchange, active)
                VALUES (?, ?, ?, ?, TRUE)
                ON CONFLICT(symbol) DO UPDATE
                    SET active = TRUE, updated_at = CURRENT_TIMESTAMP
                """,
                [symbol, f"{symbol} Corporation", "Watchlist", None],
            )
    return get_watchlist()


def ingest_daily(request: IngestRequest) -> dict[str, Any]:
    watchlist = request.symbols or [
        row["symbol"] for row in get_watchlist() if row.get("sector") != "Benchmark"
    ]
    symbols = sorted({symbol.upper().strip() for symbol in watchlist if symbol.strip()})
    benchmarks = ["SPY", "QQQ"]
    data_symbols = sorted(set(symbols).union(benchmarks).union({"^VIX"}))
    warnings: list[str] = []

    price_bars, price_warnings = fetch_price_bars(data_symbols, request.start, request.end)
    warnings.extend(price_warnings)

    price_count = 0
    document_count = 0
    event_count = 0
    feature_count = 0
    signal_count = 0

    with get_connection() as conn:
        price_count = _upsert_price_bars(conn, price_bars)

        macro_snapshot, macro_warnings = fetch_macro_snapshot()
        warnings.extend(macro_warnings)
        macro_regime = macro_snapshot.get("macro_regime", "macro_unavailable")

        for symbol in symbols:
            documents: list[dict[str, Any]] = []
            if request.include_filings:
                filings, sec_warnings = fetch_recent_filings(symbol, limit=4)
                documents.extend(filings)
                warnings.extend(sec_warnings)
            if request.include_news:
                news, news_warnings = fetch_market_news(symbol, limit=6)
                documents.extend(news)
                warnings.extend(news_warnings)

            document_count += _upsert_documents(conn, documents)
            event_count += _upsert_event_signals(conn, [classify_document(item) for item in documents])

        generated = _rebuild_features_and_signals(conn, symbols, macro_regime)
        feature_count = generated["features"]
        signal_count = generated["signals"]

    return {
        "symbols": symbols,
        "price_bars_upserted": price_count,
        "documents_upserted": document_count,
        "event_signals_upserted": event_count,
        "feature_snapshots_upserted": feature_count,
        "signals_upserted": signal_count,
        "warnings": warnings[:30],
    }


def get_signals(signal_date: date | None = None) -> list[dict[str, Any]]:
    if signal_date:
        rows = fetch_all(
            """
            SELECT *
            FROM signals
            WHERE signal_date = ?
            ORDER BY probability_outperform_spy DESC
            """,
            [signal_date],
        )
    else:
        # Latest signal per symbol: sources publish completed sessions at
        # different times, so a single global max(signal_date) can hide
        # fresh signals behind one symbol's newer-dated row.
        rows = fetch_all(
            """
            SELECT *
            FROM signals
            QUALIFY row_number() OVER (
                PARTITION BY symbol ORDER BY signal_date DESC
            ) = 1
            ORDER BY probability_outperform_spy DESC
            """
        )

    if not rows:
        return demo_signals()
    return [_decode_signal(row) for row in rows]


def get_ticker_summary(symbol: str) -> dict[str, Any]:
    symbol = symbol.upper().strip()
    ticker = fetch_one(
        "SELECT symbol, name, sector, exchange, active FROM tickers WHERE symbol = ?",
        [symbol],
    )
    if not ticker:
        ticker = {
            "symbol": symbol,
            "name": f"{symbol} Corporation",
            "sector": "Watchlist",
            "exchange": None,
        }

    feature = fetch_one(
        """
        SELECT *
        FROM feature_snapshots
        WHERE symbol = ?
        ORDER BY snapshot_date DESC
        LIMIT 1
        """,
        [symbol],
    )
    signal = fetch_one(
        """
        SELECT *
        FROM signals
        WHERE symbol = ?
        ORDER BY signal_date DESC
        LIMIT 1
        """,
        [symbol],
    )
    price_history = fetch_all(
        """
        SELECT bar_date AS date, adjusted_close AS close, volume
        FROM price_bars
        WHERE symbol = ?
        ORDER BY bar_date DESC
        LIMIT 90
        """,
        [symbol],
    )
    events = get_ticker_events(symbol)["events"][:8]

    if not feature or not price_history:
        return demo_summary(symbol)

    price_history = list(reversed(price_history))
    latest = price_history[-1]
    decoded_signal = _decode_signal(signal) if signal else None
    drivers = decoded_signal["drivers"] if decoded_signal else []
    risks = decoded_signal["risks"] if decoded_signal else []

    return {
        "symbol": symbol,
        "name": ticker["name"],
        "sector": ticker.get("sector"),
        "exchange": ticker.get("exchange"),
        "latest_price": latest.get("close"),
        "latest_date": latest.get("date"),
        "return_1d": feature.get("return_1d"),
        "return_5d": feature.get("return_5d"),
        "return_20d": feature.get("return_20d"),
        "relative_strength_spy": feature.get("relative_strength_spy"),
        "volume_ratio_20d": feature.get("volume_ratio_20d"),
        "signal": decoded_signal,
        "price_history": price_history,
        "events": events,
        "what_changed": drivers[:3],
        "why_it_matters": [
            "The score compares this ticker against SPY over the next 5 trading days.",
            "Drivers and risks are built from cached prices, news, filings, and macro context.",
        ],
        "risks": risks,
        "next_watch": [
            "Confirm whether fresh sources still support the score.",
            "Check the latest backtest before treating the signal as actionable research.",
        ],
        "is_demo": False,
    }


def get_ticker_events(symbol: str) -> dict[str, Any]:
    symbol = symbol.upper().strip()
    event_rows = fetch_all(
        """
        SELECT *
        FROM event_signals
        WHERE symbol = ?
        ORDER BY signal_date DESC, created_at DESC
        LIMIT 25
        """,
        [symbol],
    )
    document_rows = fetch_all(
        """
        SELECT id, symbol, source, title, url, published_at
        FROM source_documents
        WHERE symbol = ?
        ORDER BY published_at DESC NULLS LAST, created_at DESC
        LIMIT 25
        """,
        [symbol],
    )

    if not event_rows and not document_rows:
        return {"events": demo_events(symbol), "documents": []}

    return {"events": event_rows, "documents": document_rows}


def run_backfill(symbols: list[str] | None = None) -> dict[str, Any]:
    with get_connection() as conn:
        return backfill_signals(conn, symbols)


def run_backtest(request: BacktestRequest) -> dict[str, Any]:
    signals = [_decode_signal(row) for row in fetch_all("SELECT * FROM signals ORDER BY signal_date")]
    symbols = sorted({signal["symbol"] for signal in signals}.union({"SPY"}))
    price_bars = {symbol: _load_price_bars(symbol) for symbol in symbols}
    result = run_signal_backtest(
        signals=signals,
        price_bars_by_symbol=price_bars,
        start_date=request.start_date,
        end_date=request.end_date,
        threshold=request.threshold,
        top_n=request.top_n,
        horizon_days=request.horizon_days,
        transaction_cost_bps=request.transaction_cost_bps,
    )
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO backtest_runs (
                id, created_at, start_date, end_date, universe,
                strategy_rules, benchmark, metrics, trades
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                result["id"],
                result["created_at"],
                result["start_date"],
                result["end_date"],
                encode_json(result["universe"]),
                encode_json(result["strategy_rules"]),
                result["benchmark"],
                encode_json(result["metrics"]),
                encode_json(result["trades"]),
            ],
        )
    return result


def get_backtest(backtest_id: str) -> dict[str, Any] | None:
    row = fetch_one("SELECT * FROM backtest_runs WHERE id = ?", [backtest_id])
    if not row:
        return None
    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "start_date": row["start_date"],
        "end_date": row["end_date"],
        "universe": decode_json(row["universe"], []),
        "strategy_rules": decode_json(row["strategy_rules"], {}),
        "benchmark": row["benchmark"],
        "metrics": decode_json(row["metrics"], {}),
        "trades": decode_json(row["trades"], []),
    }


def _upsert_price_bars(conn: duckdb.DuckDBPyConnection, bars: list[dict[str, Any]]) -> int:
    count = 0
    for bar in bars:
        if bar.get("close") is None:
            continue
        conn.execute(
            """
            INSERT INTO price_bars (
                symbol, bar_date, open, high, low, close,
                adjusted_close, volume, source
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(symbol, bar_date) DO UPDATE SET
                open = excluded.open,
                high = excluded.high,
                low = excluded.low,
                close = excluded.close,
                adjusted_close = excluded.adjusted_close,
                volume = excluded.volume,
                source = excluded.source
            """,
            [
                bar["symbol"],
                bar["bar_date"],
                bar.get("open"),
                bar.get("high"),
                bar.get("low"),
                bar.get("close"),
                bar.get("adjusted_close"),
                bar.get("volume"),
                bar.get("source", "unknown"),
            ],
        )
        count += 1
    return count


def _upsert_documents(conn: duckdb.DuckDBPyConnection, documents: list[dict[str, Any]]) -> int:
    count = 0
    for doc in documents:
        title = doc.get("title") or "Untitled market source"
        url = doc.get("url") or ""
        if not url:
            continue
        doc_id = document_id(doc["symbol"], url, title)
        raw_text = doc.get("raw_text") or title
        content_hash = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
        conn.execute(
            """
            INSERT INTO source_documents (
                id, symbol, source, title, url, published_at, raw_text, content_hash
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title = excluded.title,
                published_at = excluded.published_at,
                raw_text = excluded.raw_text,
                content_hash = excluded.content_hash
            """,
            [
                doc_id,
                doc["symbol"],
                doc.get("source", "unknown"),
                title,
                url,
                doc.get("published_at"),
                raw_text,
                content_hash,
            ],
        )
        count += 1
    return count


def _upsert_event_signals(conn: duckdb.DuckDBPyConnection, events: list[dict[str, Any]]) -> int:
    count = 0
    for event in events:
        conn.execute(
            """
            INSERT INTO event_signals (
                id, symbol, signal_date, event_type, sentiment,
                confidence, source_url, summary
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                event_type = excluded.event_type,
                sentiment = excluded.sentiment,
                confidence = excluded.confidence,
                summary = excluded.summary
            """,
            [
                event["id"],
                event["symbol"],
                event["signal_date"],
                event["event_type"],
                event["sentiment"],
                event["confidence"],
                event.get("source_url"),
                event.get("summary"),
            ],
        )
        count += 1
    return count


def _rebuild_features_and_signals(
    conn: duckdb.DuckDBPyConnection,
    symbols: list[str],
    macro_regime: str,
) -> dict[str, int]:
    spy_bars = _load_price_bars("SPY", conn)
    qqq_bars = _load_price_bars("QQQ", conn)
    vix_bars = _load_price_bars("^VIX", conn)
    feature_count = 0
    signal_count = 0

    for symbol in symbols:
        bars = _load_price_bars(symbol, conn)
        events = _load_recent_events(symbol, conn)
        feature = build_feature_snapshot(symbol, bars, spy_bars, qqq_bars, events, macro_regime, vix_bars)
        if not feature:
            continue
        _upsert_feature(conn, feature)
        feature_count += 1
        signal = build_signal(symbol, feature, events)
        _upsert_signal(conn, signal)
        signal_count += 1
    return {"features": feature_count, "signals": signal_count}


def _upsert_feature(conn: duckdb.DuckDBPyConnection, feature: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT INTO feature_snapshots (
            symbol, snapshot_date, return_1d, return_5d, return_20d,
            relative_strength_spy, relative_strength_qqq, volatility_20d,
            volume_ratio_20d, news_sentiment, event_count, macro_regime, payload
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(symbol, snapshot_date) DO UPDATE SET
            return_1d = excluded.return_1d,
            return_5d = excluded.return_5d,
            return_20d = excluded.return_20d,
            relative_strength_spy = excluded.relative_strength_spy,
            relative_strength_qqq = excluded.relative_strength_qqq,
            volatility_20d = excluded.volatility_20d,
            volume_ratio_20d = excluded.volume_ratio_20d,
            news_sentiment = excluded.news_sentiment,
            event_count = excluded.event_count,
            macro_regime = excluded.macro_regime,
            payload = excluded.payload
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


def _upsert_signal(conn: duckdb.DuckDBPyConnection, signal: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT INTO signals (
            id, symbol, signal_date, horizon, probability_outperform_spy,
            confidence, score, drivers, risks, evidence
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            probability_outperform_spy = excluded.probability_outperform_spy,
            confidence = excluded.confidence,
            score = excluded.score,
            drivers = excluded.drivers,
            risks = excluded.risks,
            evidence = excluded.evidence
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


def _load_price_bars(symbol: str, conn: duckdb.DuckDBPyConnection | None = None) -> list[dict[str, Any]]:
    query = """
        SELECT symbol, bar_date, open, high, low, close, adjusted_close, volume, source
        FROM price_bars
        WHERE symbol = ?
        ORDER BY bar_date ASC
    """
    if conn:
        cursor = conn.execute(query, [symbol])
        columns = [item[0] for item in cursor.description or []]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    return fetch_all(query, [symbol])


def _load_recent_events(symbol: str, conn: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    cursor = conn.execute(
        """
        SELECT *
        FROM event_signals
        WHERE symbol = ?
        ORDER BY signal_date DESC, created_at DESC
        LIMIT 12
        """,
        [symbol],
    )
    columns = [item[0] for item in cursor.description or []]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _decode_signal(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if not row:
        return None
    return {
        "id": row["id"],
        "symbol": row["symbol"],
        "signal_date": row["signal_date"],
        "horizon": row["horizon"],
        "probability_outperform_spy": row["probability_outperform_spy"],
        "confidence": row["confidence"],
        "score": row["score"],
        "drivers": decode_json(row.get("drivers"), []),
        "risks": decode_json(row.get("risks"), []),
        "evidence": decode_json(row.get("evidence"), []),
    }

