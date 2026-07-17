from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_health_and_watchlist_endpoints_start():
    with TestClient(app) as client:
        health = client.get("/api/health")
        watchlist = client.get("/api/watchlist")

    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert watchlist.status_code == 200
    assert any(row["symbol"] == "AAPL" for row in watchlist.json())


def test_signals_endpoint_returns_demo_when_no_cached_signals():
    with TestClient(app) as client:
        response = client.get("/api/signals")

    assert response.status_code == 200
    assert response.json()
    assert "probability_outperform_spy" in response.json()[0]

