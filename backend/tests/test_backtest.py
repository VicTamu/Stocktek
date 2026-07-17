from __future__ import annotations

from datetime import date, timedelta

from app.analysis.backtest import run_signal_backtest


def test_backtest_uses_future_prices_after_signal_date():
    signal_date = date(2025, 1, 3)
    signals = [
        {
            "symbol": "AAPL",
            "signal_date": signal_date,
            "probability_outperform_spy": 0.62,
        }
    ]
    prices = {
        "AAPL": _bars("AAPL", [100, 101, 102, 104, 106, 108, 112, 114]),
        "SPY": _bars("SPY", [100, 100.5, 101, 101.2, 101.3, 101.4, 101.5, 101.6]),
    }

    result = run_signal_backtest(
        signals=signals,
        price_bars_by_symbol=prices,
        start_date=None,
        end_date=None,
        threshold=0.55,
        top_n=5,
        horizon_days=3,
        transaction_cost_bps=0,
    )

    assert result["metrics"]["trade_count"] == 1
    assert result["trades"][0]["entry_date"] == signal_date
    assert result["trades"][0]["exit_date"] == date(2025, 1, 6)
    assert result["trades"][0]["outperformed"] is True


def test_backtest_returns_empty_metrics_when_no_completed_trades():
    result = run_signal_backtest(
        signals=[],
        price_bars_by_symbol={},
        start_date=None,
        end_date=None,
        threshold=0.55,
        top_n=5,
        horizon_days=5,
        transaction_cost_bps=5,
    )

    assert result["metrics"]["trade_count"] == 0
    assert result["metrics"]["calibration"] == "not enough completed trades"


def _bars(symbol: str, closes: list[float]):
    start = date(2025, 1, 1)
    return [
        {
            "symbol": symbol,
            "bar_date": start + timedelta(days=index),
            "close": close,
            "adjusted_close": close,
            "volume": 1000,
        }
        for index, close in enumerate(closes)
    ]

