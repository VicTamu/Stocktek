from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Callable
from zoneinfo import ZoneInfo

from app.adapters import stooq, tiingo, yahoo
from app.core.config import settings

MARKET_TZ = ZoneInfo("America/New_York")


class PriceAdapterError(RuntimeError):
    pass


FetchFn = Callable[[list[str], date | None, date | None], tuple[list[dict[str, Any]], list[str]]]

SOURCES: dict[str, FetchFn] = {
    "tiingo": tiingo.fetch_price_bars,
    "yahoo": yahoo.fetch_price_bars,
    "stooq": stooq.fetch_price_bars,
}

# Relative close difference above which two sources are considered in disagreement.
RECONCILE_TOLERANCE = 0.005


def source_chain() -> list[str]:
    """Ordered price sources: configured primary first, then the defaults."""
    default = (["tiingo"] if settings.tiingo_api_key else []) + ["yahoo", "stooq"]
    primary = (settings.price_source or "").lower()
    if primary in SOURCES:
        return [primary] + [name for name in default if name != primary]
    return default


def fetch_price_bars(
    symbols: list[str],
    start: date | None = None,
    end: date | None = None,
    reconcile: bool = True,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Fetch daily bars, falling back across sources per symbol.

    Index symbols (^VIX etc.) are Yahoo-only. When two usable sources exist,
    the latest close from the primary is cross-checked against the next
    source and disagreements beyond RECONCILE_TOLERANCE become warnings.
    """
    cleaned = sorted({item.upper().strip() for item in symbols if item.strip()})
    if not cleaned:
        return [], []

    equity_symbols = [item for item in cleaned if not item.startswith("^")]
    index_symbols = [item for item in cleaned if item.startswith("^")]

    bars: list[dict[str, Any]] = []
    warnings: list[str] = []
    chain = source_chain()

    remaining = equity_symbols
    fetched_by: dict[str, str] = {}
    for source_name in chain:
        if not remaining:
            break
        got, source_warnings = SOURCES[source_name](remaining, start, end)
        warnings.extend(source_warnings)
        bars.extend(got)
        for bar in got:
            fetched_by.setdefault(bar["symbol"], source_name)
        remaining = [item for item in remaining if item not in fetched_by]

    if remaining:
        warnings.append(f"no price source returned bars for: {', '.join(remaining)}")

    if index_symbols:
        got, source_warnings = yahoo.fetch_price_bars(index_symbols, start, end)
        bars.extend(got)
        warnings.extend(source_warnings)

    incomplete = _incomplete_session_date()
    if incomplete:
        kept = [bar for bar in bars if bar["bar_date"] < incomplete]
        if len(kept) < len(bars):
            warnings.append(
                f"dropped {len(bars) - len(kept)} in-progress bars for {incomplete} "
                "(session not closed; daily-close data only)"
            )
        bars = kept

    if reconcile and fetched_by:
        warnings.extend(_reconcile_latest_closes(bars, fetched_by, chain))

    return bars, warnings


def _incomplete_session_date() -> date | None:
    """Today's date in market time while the session has not yet closed.

    Bars dated today are partial until the 4pm ET close (small buffer for
    settlement); a daily-close product must not treat them as final.
    """
    now_et = datetime.now(MARKET_TZ)
    if now_et.hour < 16 or (now_et.hour == 16 and now_et.minute < 15):
        return now_et.date()
    return None


def _reconcile_latest_closes(
    bars: list[dict[str, Any]],
    fetched_by: dict[str, str],
    chain: list[str],
) -> list[str]:
    """Cross-check each symbol's latest close against the next source in the chain."""
    check_candidates = [name for name in chain if name != chain[0]]
    if not check_candidates:
        return []
    check_name = check_candidates[0]
    check_fetch = SOURCES[check_name]

    # Only verify symbols served by the primary; fallback symbols already
    # exhausted other sources.
    to_check = sorted(sym for sym, src in fetched_by.items() if src == chain[0])
    if not to_check:
        return []

    latest: dict[str, dict[str, Any]] = {}
    for bar in bars:
        symbol = bar["symbol"]
        if symbol not in to_check:
            continue
        if symbol not in latest or bar["bar_date"] > latest[symbol]["bar_date"]:
            latest[symbol] = bar

    window_start = min(item["bar_date"] for item in latest.values()) - timedelta(days=7)
    check_bars, _ = check_fetch(to_check, window_start, None)
    check_lookup = {(bar["symbol"], bar["bar_date"]): bar for bar in check_bars}

    warnings: list[str] = []
    for symbol, bar in latest.items():
        other = check_lookup.get((symbol, bar["bar_date"]))
        if not other or not other.get("close") or not bar.get("close"):
            continue
        diff = abs(bar["close"] - other["close"]) / other["close"]
        if diff > RECONCILE_TOLERANCE:
            warnings.append(
                f"{symbol}: price sources disagree on {bar['bar_date']} close "
                f"({bar['source']} {bar['close']:.2f} vs {check_name} {other['close']:.2f}, "
                f"{diff:.1%} apart)"
            )
    return warnings
