from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.config import settings


GDELT_DOC_URL = "https://api.gdeltproject.org/api/v2/doc/doc"


def fetch_market_news(symbol: str, limit: int = 8) -> tuple[list[dict[str, Any]], list[str]]:
    symbol = symbol.upper().strip()
    if not symbol:
        return [], []

    query = f'"{symbol}" (stock OR earnings OR shares)'
    params = {
        "query": query,
        "mode": "ArtList",
        "format": "json",
        "maxrecords": str(limit),
        "sort": "HybridRel",
    }

    try:
        with httpx.Client(timeout=settings.request_timeout_seconds) as client:
            response = client.get(GDELT_DOC_URL, params=params)
            response.raise_for_status()
            payload = response.json()
    except Exception as exc:  # pragma: no cover - network/provider dependent
        return [], [f"{symbol}: GDELT news fetch failed: {exc}"]

    documents: list[dict[str, Any]] = []
    for article in payload.get("articles", [])[:limit]:
        title = article.get("title") or f"{symbol} market article"
        url = article.get("url") or ""
        if not url:
            continue
        documents.append(
            {
                "symbol": symbol,
                "source": "gdelt",
                "title": title,
                "url": url,
                "published_at": _parse_gdelt_date(article.get("seendate")),
                "raw_text": title,
            }
        )
    return documents, []


def _parse_gdelt_date(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y%m%dT%H%M%SZ", "%Y%m%d%H%M%S"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None
