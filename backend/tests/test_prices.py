from __future__ import annotations

from datetime import date
from typing import Any

from app.adapters import prices


def _bar(symbol: str, bar_date: date, close: float, source: str) -> dict[str, Any]:
    return {
        "symbol": symbol,
        "bar_date": bar_date,
        "open": close,
        "high": close,
        "low": close,
        "close": close,
        "adjusted_close": close,
        "volume": 1000,
        "source": source,
    }


def _fake_source(bars: list[dict[str, Any]], warnings: list[str] | None = None):
    def fetch(symbols, start=None, end=None):
        return [bar for bar in bars if bar["symbol"] in symbols], list(warnings or [])

    return fetch


def test_falls_back_per_symbol_when_primary_misses(monkeypatch):
    day = date(2026, 7, 16)
    monkeypatch.setattr(prices, "source_chain", lambda: ["tiingo", "yahoo", "stooq"])
    monkeypatch.setitem(prices.SOURCES, "tiingo", _fake_source([_bar("AAPL", day, 100.0, "tiingo")]))
    monkeypatch.setitem(prices.SOURCES, "yahoo", _fake_source([_bar("MSFT", day, 200.0, "yahoo")]))
    monkeypatch.setitem(prices.SOURCES, "stooq", _fake_source([]))

    bars, warnings = prices.fetch_price_bars(["AAPL", "MSFT"], reconcile=False)

    by_symbol = {bar["symbol"]: bar["source"] for bar in bars}
    assert by_symbol == {"AAPL": "tiingo", "MSFT": "yahoo"}
    assert not any("no price source" in warning for warning in warnings)


def test_warns_when_no_source_has_symbol(monkeypatch):
    monkeypatch.setattr(prices, "source_chain", lambda: ["tiingo", "yahoo", "stooq"])
    for name in ("tiingo", "yahoo", "stooq"):
        monkeypatch.setitem(prices.SOURCES, name, _fake_source([]))

    bars, warnings = prices.fetch_price_bars(["ZZZQ"], reconcile=False)

    assert bars == []
    assert any("no price source returned bars for: ZZZQ" in warning for warning in warnings)


def test_reconciliation_warns_on_close_disagreement(monkeypatch):
    day = date(2026, 7, 16)
    monkeypatch.setattr(prices, "source_chain", lambda: ["tiingo", "yahoo", "stooq"])
    monkeypatch.setitem(prices.SOURCES, "tiingo", _fake_source([_bar("AAPL", day, 100.0, "tiingo")]))
    monkeypatch.setitem(prices.SOURCES, "yahoo", _fake_source([_bar("AAPL", day, 90.0, "yahoo")]))
    monkeypatch.setitem(prices.SOURCES, "stooq", _fake_source([]))

    _, warnings = prices.fetch_price_bars(["AAPL"], reconcile=True)

    assert any("price sources disagree" in warning for warning in warnings)


def test_reconciliation_quiet_on_agreement(monkeypatch):
    day = date(2026, 7, 16)
    monkeypatch.setattr(prices, "source_chain", lambda: ["tiingo", "yahoo", "stooq"])
    monkeypatch.setitem(prices.SOURCES, "tiingo", _fake_source([_bar("AAPL", day, 100.0, "tiingo")]))
    monkeypatch.setitem(prices.SOURCES, "yahoo", _fake_source([_bar("AAPL", day, 100.2, "yahoo")]))
    monkeypatch.setitem(prices.SOURCES, "stooq", _fake_source([]))

    _, warnings = prices.fetch_price_bars(["AAPL"], reconcile=True)

    assert not any("disagree" in warning for warning in warnings)


def test_index_symbols_route_to_yahoo(monkeypatch):
    day = date(2026, 7, 16)
    monkeypatch.setattr(prices, "source_chain", lambda: ["tiingo", "yahoo", "stooq"])
    monkeypatch.setitem(prices.SOURCES, "tiingo", _fake_source([]))
    monkeypatch.setitem(prices.SOURCES, "stooq", _fake_source([]))
    monkeypatch.setattr(prices.yahoo, "fetch_price_bars", _fake_source([_bar("^VIX", day, 15.0, "yahoo")]))

    bars, _ = prices.fetch_price_bars(["^VIX"], reconcile=False)

    assert [bar["symbol"] for bar in bars] == ["^VIX"]
    assert bars[0]["source"] == "yahoo"
