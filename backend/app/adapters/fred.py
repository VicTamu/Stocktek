from __future__ import annotations

from datetime import date
from typing import Any

import httpx

from app.core.config import settings


FRED_OBSERVATIONS_URL = "https://api.stlouisfed.org/fred/series/observations"
DEFAULT_SERIES = {
    "DGS10": "10-year treasury yield",
    "DGS2": "2-year treasury yield",
    "CPIAUCSL": "consumer price index",
    "UNRATE": "unemployment rate",
}


def fetch_macro_snapshot(series: dict[str, str] | None = None) -> tuple[dict[str, Any], list[str]]:
    if not settings.fred_api_key:
        return {"macro_regime": "fred_api_key_missing", "series": {}}, [
            "FRED_API_KEY is not set; macro enrichment skipped"
        ]

    warnings: list[str] = []
    values: dict[str, Any] = {}
    selected = series or DEFAULT_SERIES

    with httpx.Client(timeout=settings.request_timeout_seconds) as client:
        for series_id, label in selected.items():
            params = {
                "series_id": series_id,
                "api_key": settings.fred_api_key,
                "file_type": "json",
                "sort_order": "desc",
                "limit": "2",
            }
            try:
                response = client.get(FRED_OBSERVATIONS_URL, params=params)
                response.raise_for_status()
                observations = response.json().get("observations", [])
            except Exception as exc:  # pragma: no cover - network/provider dependent
                warnings.append(f"FRED {series_id}: {exc}")
                continue

            current = _latest_value(observations)
            values[series_id] = {"label": label, "value": current}

    return {"macro_regime": _classify_regime(values), "series": values, "as_of": date.today()}, warnings


def _latest_value(observations: list[dict[str, str]]) -> float | None:
    for row in observations:
        value = row.get("value")
        if value and value != ".":
            try:
                return float(value)
            except ValueError:
                return None
    return None


def _classify_regime(values: dict[str, Any]) -> str:
    ten_year = values.get("DGS10", {}).get("value")
    two_year = values.get("DGS2", {}).get("value")
    if ten_year is None or two_year is None:
        return "macro_context_partial"
    if two_year > ten_year:
        return "yield_curve_inverted"
    return "yield_curve_normal"

