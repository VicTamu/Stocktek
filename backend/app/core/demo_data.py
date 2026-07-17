from __future__ import annotations

import math
from datetime import date, timedelta
from typing import Any


DEMO_TICKERS = {
    "AAPL": ("Apple Inc.", "Technology", "NASDAQ", 212.4),
    "MSFT": ("Microsoft Corporation", "Technology", "NASDAQ", 498.3),
    "NVDA": ("NVIDIA Corporation", "Technology", "NASDAQ", 144.9),
    "AMD": ("Advanced Micro Devices, Inc.", "Technology", "NASDAQ", 164.2),
    "SPY": ("SPDR S&P 500 ETF Trust", "Benchmark", "NYSEARCA", 612.1),
    "QQQ": ("Invesco QQQ Trust", "Benchmark", "NASDAQ", 545.6),
}


def demo_signals() -> list[dict[str, Any]]:
    return [demo_summary(symbol)["signal"] for symbol in ["NVDA", "MSFT", "AMD", "AAPL"]]


def demo_summary(symbol: str) -> dict[str, Any]:
    symbol = symbol.upper()
    name, sector, exchange, base_price = DEMO_TICKERS.get(
        symbol, (f"{symbol} Corporation", "Watchlist", "NASDAQ", 100.0)
    )
    history = _price_history(symbol, base_price)
    latest = history[-1]
    probability = {
        "NVDA": 0.63,
        "MSFT": 0.59,
        "AMD": 0.56,
        "AAPL": 0.54,
    }.get(symbol, 0.52)

    events = demo_events(symbol)
    signal = {
        "id": f"demo-{symbol.lower()}-signal",
        "symbol": symbol,
        "signal_date": latest["date"],
        "horizon": "5 trading days",
        "probability_outperform_spy": probability,
        "confidence": "low",
        "score": round((probability - 0.5) * 2, 4),
        "drivers": [
            "Demo momentum is positive versus the watchlist baseline.",
            "Recent educational sample news skews slightly positive.",
        ],
        "risks": [
            "This is demo data. Refresh daily data before using the research workflow.",
            "Model uncertainty is high until real source evidence is cached.",
        ],
        "evidence": [
            {
                "type": event["event_type"],
                "summary": event["summary"],
                "url": event["source_url"],
                "sentiment": event["sentiment"],
                "confidence": event["confidence"],
            }
            for event in events[:2]
        ],
    }

    return {
        "symbol": symbol,
        "name": name,
        "sector": sector,
        "exchange": exchange,
        "latest_price": latest["close"],
        "latest_date": latest["date"],
        "return_1d": 0.006,
        "return_5d": 0.024,
        "return_20d": 0.071 if symbol in {"NVDA", "MSFT"} else 0.034,
        "relative_strength_spy": 0.028 if symbol in {"NVDA", "MSFT"} else -0.004,
        "volume_ratio_20d": 1.32,
        "signal": signal,
        "price_history": history,
        "events": events,
        "what_changed": [
            "Demo price action shows a constructive daily-close setup.",
            "The signal is awaiting real price, filing, and news ingestion.",
        ],
        "why_it_matters": [
            "StockTek ranks tickers by probability, confidence, and evidence quality.",
            "Every real signal should be checked against source links and backtests.",
        ],
        "risks": signal["risks"],
        "next_watch": [
            "Run Refresh Daily Data after market close.",
            "Check whether the signal still beats SPY in backtesting.",
        ],
        "is_demo": True,
    }


def demo_events(symbol: str) -> list[dict[str, Any]]:
    symbol = symbol.upper()
    today = date.today()
    return [
        {
            "id": f"demo-{symbol.lower()}-earnings",
            "symbol": symbol,
            "signal_date": today - timedelta(days=1),
            "event_type": "earnings",
            "sentiment": 0.4,
            "confidence": 0.55,
            "source_url": "https://www.sec.gov/edgar/search/",
            "summary": f"{symbol} demo earnings and filing watch item",
        },
        {
            "id": f"demo-{symbol.lower()}-news",
            "symbol": symbol,
            "signal_date": today - timedelta(days=2),
            "event_type": "general",
            "sentiment": 0.2,
            "confidence": 0.45,
            "source_url": "https://www.gdeltproject.org/data.html",
            "summary": f"{symbol} demo market news item from free source discovery",
        },
    ]


def _price_history(symbol: str, base_price: float) -> list[dict[str, Any]]:
    today = date.today()
    points: list[dict[str, Any]] = []
    seed = sum(ord(char) for char in symbol)
    for index in range(60):
        days_back = 59 - index
        current_date = today - timedelta(days=days_back)
        wave = math.sin((index + seed) / 7.0) * 0.035
        trend = index * 0.0018
        close = round(base_price * (1 + trend + wave), 2)
        points.append({"date": current_date, "close": close, "volume": 10000000 + index * 35000})
    return points

