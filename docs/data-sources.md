# StockTek Data Sources

StockTek V1 uses free or low-cost sources by default.

## Prices

The default adapter uses `yfinance` for personal educational research. The adapter lives behind a boundary so it can later be replaced with Polygon, Tiingo, Alpaca, Alpha Vantage, or another licensed source.

## SEC EDGAR

SEC EDGAR APIs provide company submissions and XBRL facts without an API key. StockTek uses a configurable user agent through `STOCKTEK_SEC_USER_AGENT`.

## FRED

FRED macro data requires a free API key. If `FRED_API_KEY` is absent, the app continues without macro enrichment and marks macro context as unavailable.

## News

GDELT is used for free/open news discovery. Results can be noisy, so StockTek stores source links and uses conservative confidence scoring.

## Important Limits

- Free APIs can rate-limit or change behavior.
- News search can return irrelevant articles.
- Historical data can have splits/dividend quirks.
- Backtests must include costs and avoid lookahead bias.

