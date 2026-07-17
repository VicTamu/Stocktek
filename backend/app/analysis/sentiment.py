from __future__ import annotations

import hashlib
import re
from datetime import date, datetime
from typing import Any


POSITIVE_TERMS = {
    "beat",
    "beats",
    "raise",
    "raises",
    "raised",
    "growth",
    "record",
    "profit",
    "profitable",
    "upgrade",
    "outperform",
    "strong",
    "surge",
    "surges",
    "gain",
    "gains",
    "approval",
    "contract",
    "partnership",
}

NEGATIVE_TERMS = {
    "miss",
    "misses",
    "cut",
    "cuts",
    "lawsuit",
    "probe",
    "investigation",
    "downgrade",
    "weak",
    "decline",
    "falls",
    "fall",
    "loss",
    "layoff",
    "recall",
    "guidance cut",
    "warning",
}

EVENT_KEYWORDS = {
    "earnings": {"earnings", "revenue", "profit", "quarter", "guidance"},
    "analyst": {"upgrade", "downgrade", "price target", "outperform", "underperform"},
    "legal": {"lawsuit", "probe", "investigation", "settlement", "sec"},
    "product": {"launch", "approval", "contract", "partnership", "chip", "product"},
    "macro": {"rates", "inflation", "fed", "treasury", "jobs", "cpi"},
    "filing": {"10-k", "10-q", "8-k", "form", "filed"},
}


def classify_document(document: dict[str, Any]) -> dict[str, Any]:
    text = f"{document.get('title', '')} {document.get('raw_text', '')}".lower()
    words = set(re.findall(r"[a-z0-9-]+", text))

    positive = sum(1 for term in POSITIVE_TERMS if term in text or term in words)
    negative = sum(1 for term in NEGATIVE_TERMS if term in text or term in words)
    total = max(positive + negative, 1)
    sentiment = (positive - negative) / total
    sentiment = max(-1.0, min(1.0, sentiment))

    event_type = "general"
    best_hits = 0
    for candidate, terms in EVENT_KEYWORDS.items():
        hits = sum(1 for term in terms if term in text)
        if hits > best_hits:
            best_hits = hits
            event_type = candidate

    confidence = min(0.95, 0.35 + 0.15 * total + 0.1 * best_hits)
    published = document.get("published_at")
    signal_date = _to_date(published) or date.today()
    source_url = document.get("url")
    summary = document.get("title") or f"{document.get('symbol')} market event"
    event_id = stable_event_id(document.get("symbol", ""), source_url or summary)

    return {
        "id": event_id,
        "symbol": document["symbol"],
        "signal_date": signal_date,
        "event_type": event_type,
        "sentiment": sentiment,
        "confidence": confidence,
        "source_url": source_url,
        "summary": summary,
    }


def document_id(symbol: str, url: str, title: str) -> str:
    digest = hashlib.sha256(f"{symbol}|{url}|{title}".encode("utf-8")).hexdigest()
    return digest[:24]


def stable_event_id(symbol: str, source: str) -> str:
    digest = hashlib.sha256(f"{symbol}|{source}".encode("utf-8")).hexdigest()
    return digest[:24]


def _to_date(value: Any) -> date | None:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    return None

