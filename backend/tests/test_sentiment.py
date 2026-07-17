from __future__ import annotations

from app.analysis.sentiment import classify_document, document_id


def test_classify_document_extracts_event_and_sentiment():
    document = {
        "symbol": "MSFT",
        "title": "MSFT beats earnings expectations and raises guidance",
        "url": "https://example.com/msft",
        "source": "fixture",
        "raw_text": "Analysts call the quarter strong after revenue growth.",
    }

    event = classify_document(document)

    assert event["symbol"] == "MSFT"
    assert event["event_type"] == "earnings"
    assert event["sentiment"] > 0
    assert event["confidence"] > 0.5


def test_document_id_is_stable():
    first = document_id("AAPL", "https://example.com/aapl", "Apple news")
    second = document_id("AAPL", "https://example.com/aapl", "Apple news")

    assert first == second
    assert len(first) == 24

