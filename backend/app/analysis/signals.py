from __future__ import annotations

import hashlib
from typing import Any


def build_signal(
    symbol: str,
    feature: dict[str, Any],
    events: list[dict[str, Any]],
    horizon: str = "5 trading days",
) -> dict[str, Any]:
    probability = 0.5
    drivers: list[str] = []
    risks: list[str] = []

    probability += _bounded(feature.get("relative_strength_spy"), 0.12, 0.12)
    probability += _bounded(feature.get("return_20d"), 0.08, 0.08)
    probability += _bounded(feature.get("return_5d"), 0.05, 0.06)
    probability += _bounded(feature.get("news_sentiment"), 0.06, 0.05)

    volatility = feature.get("volatility_20d")
    if volatility and volatility > 0.035:
        probability -= min(0.06, (volatility - 0.035) * 1.25)
        risks.append("High 20-day volatility makes the signal less reliable.")

    volume_ratio = feature.get("volume_ratio_20d")
    if volume_ratio and volume_ratio > 1.5:
        probability += 0.025
        drivers.append("Volume is elevated versus the 20-day average.")
    elif volume_ratio and volume_ratio < 0.65:
        risks.append("Low relative volume may mean the move lacks confirmation.")

    rel_spy = feature.get("relative_strength_spy")
    if rel_spy and rel_spy > 0.03:
        drivers.append("The ticker is outperforming SPY over the last 20 trading days.")
    elif rel_spy and rel_spy < -0.03:
        risks.append("The ticker is lagging SPY over the last 20 trading days.")

    return_20d = feature.get("return_20d")
    if return_20d and return_20d > 0.06:
        drivers.append("20-day momentum is positive.")
    elif return_20d and return_20d < -0.06:
        risks.append("20-day momentum is negative.")

    sentiment = feature.get("news_sentiment") or 0.0
    if sentiment > 0.25:
        drivers.append("Recent source sentiment skews positive.")
    elif sentiment < -0.25:
        risks.append("Recent source sentiment skews negative.")

    if feature.get("macro_regime") == "yield_curve_inverted":
        risks.append("Macro context shows an inverted yield curve.")
    elif feature.get("macro_regime") == "fred_api_key_missing":
        risks.append("Macro context is unavailable because FRED_API_KEY is not set.")

    if not drivers:
        drivers.append("Signal is mostly neutral; no strong driver passed the current thresholds.")
    if not risks:
        risks.append("Main risk is model uncertainty; this V1 score is a research signal only.")

    probability = max(0.2, min(0.8, probability))
    confidence = _confidence(feature, events)
    evidence = _evidence(events)
    signal_id = _signal_id(symbol, str(feature["snapshot_date"]), horizon)

    return {
        "id": signal_id,
        "symbol": symbol,
        "signal_date": feature["snapshot_date"],
        "horizon": horizon,
        "probability_outperform_spy": round(probability, 4),
        "confidence": confidence,
        "score": round((probability - 0.5) * 2, 4),
        "drivers": drivers[:5],
        "risks": risks[:5],
        "evidence": evidence,
    }


def _bounded(value: float | None, scale: float, cap: float) -> float:
    if value is None:
        return 0.0
    return max(-cap, min(cap, value * scale / 0.1))


def _confidence(feature: dict[str, Any], events: list[dict[str, Any]]) -> str:
    data_points = feature.get("payload", {}).get("data_points", 0)
    has_benchmark = feature.get("relative_strength_spy") is not None
    event_count = len(events)

    if data_points >= 180 and has_benchmark and event_count >= 2:
        return "high"
    if data_points >= 50 and has_benchmark:
        return "medium"
    return "low"


def _evidence(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for event in events[:5]:
        output.append(
            {
                "type": event.get("event_type", "event"),
                "summary": event.get("summary"),
                "url": event.get("source_url"),
                "sentiment": event.get("sentiment"),
                "confidence": event.get("confidence"),
            }
        )
    return output


def _signal_id(symbol: str, signal_date: str, horizon: str) -> str:
    digest = hashlib.sha256(f"{symbol}|{signal_date}|{horizon}".encode("utf-8")).hexdigest()
    return digest[:24]

