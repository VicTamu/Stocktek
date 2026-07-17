from __future__ import annotations

import csv
import io
from datetime import date, timedelta
from typing import Any

import httpx

from app.core.config import settings


STOOQ_DAILY_URL = "https://stooq.com/q/d/l/"


def fetch_price_bars(
    symbols: list[str],
    start: date | None = None,
    end: date | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Fetch daily bars from Stooq's free CSV endpoint (no API key).

    Stooq closes are split-adjusted; adjusted_close mirrors close.
    US tickers use the `.us` suffix.
    """
    start_date = start or (date.today() - timedelta(days=430))
    bars: list[dict[str, Any]] = []
    warnings: list[str] = []

    with httpx.Client(timeout=settings.request_timeout_seconds) as client:
        for symbol in symbols:
            params = {
                "s": f"{symbol.lower()}.us",
                "d1": start_date.strftime("%Y%m%d"),
                "d2": (end or date.today()).strftime("%Y%m%d"),
                "i": "d",
            }
            try:
                response = client.get(STOOQ_DAILY_URL, params=params)
                response.raise_for_status()
                text = response.text
            except Exception as exc:  # pragma: no cover - network/provider dependent
                warnings.append(f"{symbol}: stooq fetch failed: {exc}")
                continue

            rows = list(csv.DictReader(io.StringIO(text)))
            if not rows or "Close" not in (rows[0] or {}):
                warnings.append(f"{symbol}: stooq returned no price bars")
                continue

            for row in rows:
                bar_date = _parse_date(row.get("Date"))
                close = _as_float(row.get("Close"))
                if bar_date is None or close is None:
                    continue
                bars.append(
                    {
                        "symbol": symbol,
                        "bar_date": bar_date,
                        "open": _as_float(row.get("Open")),
                        "high": _as_float(row.get("High")),
                        "low": _as_float(row.get("Low")),
                        "close": close,
                        "adjusted_close": close,
                        "volume": int(_as_float(row.get("Volume")) or 0),
                        "source": "stooq",
                    }
                )

    return bars, warnings


def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def _as_float(value: Any) -> float | None:
    if value in (None, "", "N/D"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
