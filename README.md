# StockTek

StockTek is a local-first stock market watchlist analysis assistant. V1 focuses on educational research: daily-close watchlist analysis, evidence-backed signals, source links, and backtesting. It does not auto-trade and it does not provide financial advice.

## What V1 Does

- Tracks a 25-100 ticker watchlist.
- Caches free market data locally with DuckDB.
- Pulls daily price bars through a replaceable `yfinance` adapter.
- Uses SEC EDGAR for filings and GDELT/RSS-style news discovery.
- Calculates transparent technical, sentiment, and evidence signals.
- Scores 5-day outperform probability against SPY.
- Runs simple backtests with benchmark, costs, drawdown, Sharpe, win rate, and calibration.
- Serves a React dashboard for watchlist ranking, ticker detail, events, and backtest status.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
cd frontend
npm install
cd ..
copy .env.example .env
```

Optional: add a free `FRED_API_KEY` to `.env` for macro data.

## Run

Start both apps in separate PowerShell windows:

```powershell
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

```powershell
cd frontend
npm run dev -- --host 127.0.0.1
```

Or run the helper:

```powershell
npm start
```

Frontend: `http://127.0.0.1:5173`

Backend API: `http://127.0.0.1:8000/docs`

## First Workflow

1. Open the dashboard.
2. Confirm the default watchlist.
3. Click `Refresh Daily Data`.
4. Review signals and source links.
5. Run a backtest before trusting any signal.

## Notes

- This project is for educational research only.
- Free data sources have limits and quality gaps.
- `yfinance` is unofficial and intended for personal research/prototyping.
- Real-time data, broker connections, and automated trading are intentionally out of scope for V1.

