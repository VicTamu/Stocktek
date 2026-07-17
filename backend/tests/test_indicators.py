from __future__ import annotations

from datetime import date, timedelta

from app.analysis.indicators import build_feature_snapshot, pct_change


def test_pct_change_handles_zero_and_missing_values():
    assert pct_change(110, 100) == 0.1
    assert pct_change(110, 0) is None
    assert pct_change(None, 100) is None


def test_build_feature_snapshot_uses_only_available_history():
    bars = _bars("AAPL", 100)
    spy = _bars("SPY", 90)
    qqq = _bars("QQQ", 95)
    events = [
        {
            "sentiment": 0.6,
            "confidence": 0.8,
            "event_type": "earnings",
            "summary": "positive earnings",
        }
    ]

    feature = build_feature_snapshot("AAPL", bars, spy, qqq, events, "yield_curve_normal")

    assert feature is not None
    assert feature["symbol"] == "AAPL"
    assert feature["return_20d"] is not None
    assert feature["relative_strength_spy"] is not None
    assert feature["news_sentiment"] == 0.6
    assert feature["event_count"] == 1


def _bars(symbol: str, start_price: float):
    start = date(2025, 1, 1)
    return [
        {
            "symbol": symbol,
            "bar_date": start + timedelta(days=index),
            "open": start_price + index,
            "high": start_price + index + 1,
            "low": start_price + index - 1,
            "close": start_price + index,
            "adjusted_close": start_price + index,
            "volume": 1000 + index,
            "source": "test",
        }
        for index in range(65)
    ]

