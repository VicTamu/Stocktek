from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import httpx

from app.core.config import settings


TIINGO_DAILY_URL = "https://api.tiingo.com/tiingo/daily/{symbol}/prices"


def fetch_price_bars(
    symbols: list[str],
    start: date | None = None,
    end: date | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Fetch daily bars from Tiingo's official REST API (free tier)."""
    if not settings.tiingo_api_key:
        return [], ["tiingo: TIINGO_API_KEY is not set"]

    start_date = start or (date.today() - timedelta(days=430))
    bars: list[dict[str, Any]] = []
    warnings: list[str] = []

    with httpx.Client(timeout=settings.request_timeout_seconds) as client:
        for symbol in symbols:
            params: dict[str, str] = {
                "token": settings.tiingo_api_key,
                "startDate": start_date.isoformat(),
                "format": "json",
            }
            if end:
                params["endDate"] = end.isoformat()
            try:
                response = client.get(TIINGO_DAILY_URL.format(symbol=symbol.lower()), params=params)
                response.raise_for_status()
                rows = response.json()
            except Exception as exc:  # pragma: no cover - network/provider dependent
                warnings.append(f"{symbol}: tiingo fetch failed: {exc}")
                continue

            if not isinstance(rows, list) or not rows:
                warnings.append(f"{symbol}: tiingo returned no price bars")
                continue

            for row in rows:
                bar_date = _parse_date(row.get("date"))
                if bar_date is None or row.get("close") is None:
                    continue
                bars.append(
                    {
                        "symbol": symbol,
                        "bar_date": bar_date,
                        "open": row.get("open"),
                        "high": row.get("high"),
                        "low": row.get("low"),
                        "close": row.get("close"),
                        "adjusted_close": row.get("adjClose", row.get("close")),
                        "volume": int(row.get("volume") or 0),
                        "source": "tiingo",
                    }
                )

    return bars, warnings


def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None
