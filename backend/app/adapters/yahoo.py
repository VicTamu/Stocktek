from __future__ import annotations

from datetime import date, timedelta
from typing import Any


def fetch_price_bars(
    symbols: list[str],
    start: date | None = None,
    end: date | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Fetch daily bars through yfinance (unofficial Yahoo Finance client)."""
    if not symbols:
        return [], []

    try:
        import yfinance as yf
    except ImportError:
        return [], ["yahoo: yfinance is not installed"]

    start_date = start or (date.today() - timedelta(days=430))
    end_date = end
    bars: list[dict[str, Any]] = []
    warnings: list[str] = []

    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            history_kwargs: dict[str, Any] = {
                "auto_adjust": False,
                "actions": False,
            }
            if start or end:
                history_kwargs["start"] = start_date.isoformat()
                if end_date:
                    history_kwargs["end"] = end_date.isoformat()
            else:
                history_kwargs["period"] = "18mo"
            frame = ticker.history(**history_kwargs)
        except Exception as exc:  # pragma: no cover - network/provider dependent
            warnings.append(f"{symbol}: price fetch failed: {exc}")
            continue

        if frame is None or frame.empty:
            warnings.append(f"{symbol}: no price bars returned")
            continue

        for idx, row in frame.iterrows():
            bar_date = idx.date() if hasattr(idx, "date") else idx
            adjusted = row.get("Adj Close", row.get("Close"))
            bars.append(
                {
                    "symbol": symbol,
                    "bar_date": bar_date,
                    "open": _as_float(row.get("Open")),
                    "high": _as_float(row.get("High")),
                    "low": _as_float(row.get("Low")),
                    "close": _as_float(row.get("Close")),
                    "adjusted_close": _as_float(adjusted),
                    "volume": int(row.get("Volume") or 0),
                    "source": "yahoo",
                }
            )

    return bars, warnings


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        if value != value:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
