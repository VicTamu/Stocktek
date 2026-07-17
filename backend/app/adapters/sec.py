from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.config import settings


SEC_TICKER_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"


def fetch_recent_filings(symbol: str, limit: int = 5) -> tuple[list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    symbol = symbol.upper().strip()
    if not symbol:
        return [], []

    try:
        cik = _lookup_cik(symbol)
    except Exception as exc:  # pragma: no cover - network/provider dependent
        return [], [f"{symbol}: SEC CIK lookup failed: {exc}"]

    if not cik:
        return [], [f"{symbol}: no SEC CIK found"]

    try:
        with httpx.Client(timeout=settings.request_timeout_seconds, headers=_headers()) as client:
            response = client.get(SEC_SUBMISSIONS_URL.format(cik=f"{int(cik):010d}"))
            response.raise_for_status()
            payload = response.json()
    except Exception as exc:  # pragma: no cover - network/provider dependent
        return [], [f"{symbol}: SEC submissions failed: {exc}"]

    recent = payload.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])[:limit]
    dates = recent.get("filingDate", [])[:limit]
    accession_numbers = recent.get("accessionNumber", [])[:limit]
    primary_docs = recent.get("primaryDocument", [])[:limit]

    filings: list[dict[str, Any]] = []
    for index, form in enumerate(forms):
        filed_at = _parse_datetime(dates[index] if index < len(dates) else None)
        accession = accession_numbers[index] if index < len(accession_numbers) else ""
        primary_doc = primary_docs[index] if index < len(primary_docs) else ""
        url = _filing_url(cik, accession, primary_doc)
        filings.append(
            {
                "symbol": symbol,
                "source": "sec",
                "title": f"{symbol} {form} filed with SEC",
                "url": url,
                "published_at": filed_at,
                "raw_text": f"SEC filing form {form} for {symbol}",
            }
        )

    return filings, warnings


def _lookup_cik(symbol: str) -> int | None:
    with httpx.Client(timeout=settings.request_timeout_seconds, headers=_headers()) as client:
        response = client.get(SEC_TICKER_URL)
        response.raise_for_status()
        payload = response.json()

    for row in payload.values():
        if row.get("ticker", "").upper() == symbol:
            return int(row["cik_str"])
    return None


def _filing_url(cik: int, accession: str, primary_doc: str) -> str:
    clean_accession = accession.replace("-", "")
    if not clean_accession or not primary_doc:
        return f"https://www.sec.gov/edgar/browse/?CIK={cik}"
    return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{clean_accession}/{primary_doc}"


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _headers() -> dict[str, str]:
    return {
        "User-Agent": settings.sec_user_agent,
        "Accept-Encoding": "gzip, deflate",
    }
