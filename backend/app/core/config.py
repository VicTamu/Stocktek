from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


load_dotenv(_project_root() / ".env")


@dataclass(frozen=True)
class Settings:
    app_name: str = "StockTek"
    api_prefix: str = "/api"
    database_path: Path = Path(os.getenv("STOCKTEK_DB_PATH", "data/stocktek.duckdb"))
    sec_user_agent: str = os.getenv(
        "STOCKTEK_SEC_USER_AGENT",
        "StockTek/0.1 educational research contact@example.com",
    )
    fred_api_key: str | None = os.getenv("FRED_API_KEY") or None
    tiingo_api_key: str | None = os.getenv("TIINGO_API_KEY") or None
    finnhub_api_key: str | None = os.getenv("FINNHUB_API_KEY") or None
    price_source: str | None = os.getenv("STOCKTEK_PRICE_SOURCE") or None
    request_timeout_seconds: float = 12.0

    @property
    def root_dir(self) -> Path:
        return _project_root()

    @property
    def db_path(self) -> Path:
        if self.database_path.is_absolute():
            return self.database_path
        return self.root_dir / self.database_path

    @property
    def data_dir(self) -> Path:
        return self.db_path.parent


settings = Settings()
