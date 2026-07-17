from __future__ import annotations

from statistics import mean, pstdev
from typing import Any


def build_feature_snapshot(
    symbol: str,
    bars: list[dict[str, Any]],
    spy_bars: list[dict[str, Any]],
    qqq_bars: list[dict[str, Any]],
    event_signals: list[dict[str, Any]],
    macro_regime: str,
) -> dict[str, Any] | None:
    bars = sorted(bars, key=lambda item: item["bar_date"])
    if len(bars) < 6:
        return None

    closes = [_close(bar) for bar in bars]
    volumes = [int(bar.get("volume") or 0) for bar in bars]
    latest = bars[-1]
    returns = _daily_returns(closes)

    return_1d = pct_change(closes[-1], closes[-2]) if len(closes) >= 2 else None
    return_5d = pct_change(closes[-1], closes[-6]) if len(closes) >= 6 else None
    return_20d = pct_change(closes[-1], closes[-21]) if len(closes) >= 21 else None
    spy_return_20d = _window_return(spy_bars, 20)
    qqq_return_20d = _window_return(qqq_bars, 20)
    volatility_20d = pstdev(returns[-20:]) if len(returns) >= 20 else None
    average_volume = mean(volumes[-21:-1]) if len(volumes) >= 21 else None
    volume_ratio_20d = (volumes[-1] / average_volume) if average_volume else None
    news_sentiment = _weighted_sentiment(event_signals)

    payload = {
        "latest_close": closes[-1],
        "moving_average_20": mean(closes[-20:]) if len(closes) >= 20 else None,
        "moving_average_50": mean(closes[-50:]) if len(closes) >= 50 else None,
        "data_points": len(bars),
    }

    return {
        "symbol": symbol,
        "snapshot_date": latest["bar_date"],
        "return_1d": return_1d,
        "return_5d": return_5d,
        "return_20d": return_20d,
        "relative_strength_spy": _safe_subtract(return_20d, spy_return_20d),
        "relative_strength_qqq": _safe_subtract(return_20d, qqq_return_20d),
        "volatility_20d": volatility_20d,
        "volume_ratio_20d": volume_ratio_20d,
        "news_sentiment": news_sentiment,
        "event_count": len(event_signals),
        "macro_regime": macro_regime,
        "payload": payload,
    }


def pct_change(current: float | None, previous: float | None) -> float | None:
    if current is None or previous in (None, 0):
        return None
    return (current - previous) / previous


def _daily_returns(closes: list[float]) -> list[float]:
    values: list[float] = []
    for index in range(1, len(closes)):
        value = pct_change(closes[index], closes[index - 1])
        if value is not None:
            values.append(value)
    return values


def _window_return(bars: list[dict[str, Any]], window: int) -> float | None:
    bars = sorted(bars, key=lambda item: item["bar_date"])
    if len(bars) <= window:
        return None
    return pct_change(_close(bars[-1]), _close(bars[-window - 1]))


def _weighted_sentiment(events: list[dict[str, Any]]) -> float:
    if not events:
        return 0.0
    weights = [float(item.get("confidence") or 0.1) for item in events]
    weighted = sum(float(item.get("sentiment") or 0.0) * weight for item, weight in zip(events, weights))
    return weighted / max(sum(weights), 0.1)


def _safe_subtract(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return left - right


def _close(bar: dict[str, Any]) -> float:
    return float(bar.get("adjusted_close") or bar.get("close") or 0.0)

