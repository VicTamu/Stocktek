from __future__ import annotations

import math
import uuid
from datetime import date, datetime
from statistics import mean, pstdev
from typing import Any


def run_signal_backtest(
    signals: list[dict[str, Any]],
    price_bars_by_symbol: dict[str, list[dict[str, Any]]],
    start_date: date | None,
    end_date: date | None,
    threshold: float,
    top_n: int,
    horizon_days: int,
    transaction_cost_bps: float,
) -> dict[str, Any]:
    eligible = _filter_signals(signals, start_date, end_date, threshold)
    eligible.sort(key=lambda item: (item["signal_date"], -item["probability_outperform_spy"]))

    trades: list[dict[str, Any]] = []
    signals_by_date: dict[Any, list[dict[str, Any]]] = {}
    for signal in eligible:
        signals_by_date.setdefault(signal["signal_date"], []).append(signal)

    for signal_date, date_signals in signals_by_date.items():
        for signal in date_signals[:top_n]:
            trade = _evaluate_trade(
                signal,
                price_bars_by_symbol.get(signal["symbol"], []),
                price_bars_by_symbol.get("SPY", []),
                horizon_days,
                transaction_cost_bps,
            )
            if trade:
                trades.append(trade)

    metrics = _metrics(trades)
    return {
        "id": str(uuid.uuid4()),
        "created_at": datetime.utcnow(),
        "start_date": start_date,
        "end_date": end_date,
        "universe": sorted({signal["symbol"] for signal in eligible}),
        "strategy_rules": {
            "threshold": threshold,
            "top_n": top_n,
            "horizon_days": horizon_days,
            "transaction_cost_bps": transaction_cost_bps,
            "lookahead_policy": "signal close to future close only",
        },
        "benchmark": "SPY",
        "metrics": metrics,
        "trades": trades,
    }


def _filter_signals(
    signals: list[dict[str, Any]],
    start_date: date | None,
    end_date: date | None,
    threshold: float,
) -> list[dict[str, Any]]:
    output = []
    for signal in signals:
        signal_date = signal["signal_date"]
        if start_date and signal_date < start_date:
            continue
        if end_date and signal_date > end_date:
            continue
        if signal["probability_outperform_spy"] < threshold:
            continue
        output.append(signal)
    return output


def _evaluate_trade(
    signal: dict[str, Any],
    bars: list[dict[str, Any]],
    spy_bars: list[dict[str, Any]],
    horizon_days: int,
    transaction_cost_bps: float,
) -> dict[str, Any] | None:
    entry = _future_return(bars, signal["signal_date"], horizon_days)
    benchmark = _future_return(spy_bars, signal["signal_date"], horizon_days)
    if entry is None or benchmark is None:
        return None

    stock_return = entry["return"] - (transaction_cost_bps / 10000.0)
    benchmark_return = benchmark["return"]
    excess_return = stock_return - benchmark_return
    return {
        "symbol": signal["symbol"],
        "signal_date": signal["signal_date"],
        "entry_date": entry["entry_date"],
        "exit_date": entry["exit_date"],
        "probability": signal["probability_outperform_spy"],
        "stock_return": round(stock_return, 5),
        "benchmark_return": round(benchmark_return, 5),
        "excess_return": round(excess_return, 5),
        "outperformed": excess_return > 0,
    }


def _future_return(
    bars: list[dict[str, Any]],
    signal_date: date,
    horizon_days: int,
) -> dict[str, Any] | None:
    bars = sorted(bars, key=lambda item: item["bar_date"])
    for index, bar in enumerate(bars):
        if bar["bar_date"] >= signal_date:
            exit_index = index + horizon_days
            if exit_index >= len(bars):
                return None
            entry_price = _close(bar)
            exit_price = _close(bars[exit_index])
            if not entry_price:
                return None
            return {
                "entry_date": bar["bar_date"],
                "exit_date": bars[exit_index]["bar_date"],
                "return": (exit_price - entry_price) / entry_price,
            }
    return None


def _metrics(trades: list[dict[str, Any]]) -> dict[str, Any]:
    if not trades:
        return {
            "trade_count": 0,
            "win_rate": None,
            "average_return": None,
            "average_excess_return": None,
            "max_drawdown": None,
            "sharpe_like": None,
            "calibration": "not enough completed trades",
        }

    returns = [trade["stock_return"] for trade in trades]
    excess = [trade["excess_return"] for trade in trades]
    wins = [trade for trade in trades if trade["outperformed"]]
    equity_curve = _equity_curve(returns)

    return {
        "trade_count": len(trades),
        "win_rate": round(len(wins) / len(trades), 4),
        "average_return": round(mean(returns), 5),
        "average_excess_return": round(mean(excess), 5),
        "max_drawdown": round(_max_drawdown(equity_curve), 5),
        "sharpe_like": _sharpe_like(returns),
        "calibration": _calibration(trades),
    }


def _equity_curve(returns: list[float]) -> list[float]:
    equity = 1.0
    curve = [equity]
    for value in returns:
        equity *= 1.0 + value
        curve.append(equity)
    return curve


def _max_drawdown(curve: list[float]) -> float:
    peak = curve[0]
    drawdown = 0.0
    for value in curve:
        peak = max(peak, value)
        drawdown = min(drawdown, (value - peak) / peak)
    return drawdown


def _sharpe_like(returns: list[float]) -> float | None:
    if len(returns) < 2:
        return None
    deviation = pstdev(returns)
    if deviation == 0:
        return None
    return round((mean(returns) / deviation) * math.sqrt(252 / 5), 4)


def _calibration(trades: list[dict[str, Any]]) -> dict[str, Any]:
    buckets: dict[str, list[dict[str, Any]]] = {
        "55-60": [],
        "60-65": [],
        "65+": [],
    }
    for trade in trades:
        probability = trade["probability"]
        if probability < 0.60:
            buckets["55-60"].append(trade)
        elif probability < 0.65:
            buckets["60-65"].append(trade)
        else:
            buckets["65+"].append(trade)

    output: dict[str, Any] = {}
    for bucket, bucket_trades in buckets.items():
        if not bucket_trades:
            output[bucket] = {"count": 0, "hit_rate": None}
            continue
        output[bucket] = {
            "count": len(bucket_trades),
            "hit_rate": round(
                sum(1 for trade in bucket_trades if trade["outperformed"]) / len(bucket_trades),
                4,
            ),
        }
    return output


def _close(bar: dict[str, Any]) -> float:
    return float(bar.get("adjusted_close") or bar.get("close") or 0.0)

