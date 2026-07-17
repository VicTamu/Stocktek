# StockTek V1 Production Plan

Goal: turn the working prototype into a production-ready V1 whose competitive
position is **trustworthiness** — every score explains itself, cites sources,
and shows its own measured track record. Phases are ordered so that each one
makes the honesty thesis more demonstrable; later phases depend on earlier ones.

Effort tags: (S) hours, (M) a day or two, (L) several days.

---

## Phase 0 — Data foundations

*Kills the silent-failure class and adds redundancy before anything is built on top.*

| # | Task | Effort | Notes |
|---|------|--------|-------|
| 0.1 | Free API keys in `.env`: FRED, Tiingo, Finnhub | S | User signups; adapters read from config. FRED adapter already built and dormant. |
| 0.2 | Real SEC user agent contact | S | SEC compliance requirement; replace `contact@example.com` default. |
| 0.3 | Tiingo price adapter + Stooq fallback | M | Same `(bars, warnings)` contract as `prices.py`. Config-selected primary. |
| 0.4 | Cross-source price reconciliation | M | Compare closes across sources; discrepancies > 0.5% become warnings and a health-panel flag. "We verify our data" is the feature. |
| 0.5 | Surface ingest warnings in the UI | S | API already returns them; TopBar shows only counts. The yfinance breakage was invisible for exactly this reason. |
| 0.6 | Mark demo events `is_demo` | S | Same fix already applied to signals; `get_ticker_events` fallback is still unlabeled. |
| 0.7 | `^VIX` via price adapter as a regime feature | S | Zero cost, feeds Phase 2 features. |

**Acceptance:** a broken data source is visible in the UI within one refresh;
prices agree across two independent sources or say why not.

## Phase 1 — Trust core: backfill + honest backtests

*The single most valuable phase. Unblocks everything measurable.*

| # | Task | Effort | Notes |
|---|------|--------|-------|
| 1.1 | Historical signal backfill | L | Reconstruct feature snapshots + signals for every cached bar date (~350/ticker). **Price features only** — news/sentiment excluded unless point-in-time correct. Store a `generated_by: backfill` marker. |
| 1.2 | Backtest rigor | L | Walk-forward train/test separation; non-overlapping or portfolio-aware position accounting; explicit small-sample warning below ~50 trades; fix `datetime.utcnow()`. |
| 1.3 | Calibration bucket visualization | M | Backend already computes buckets; BacktestPanel prints a string. This chart *is* the product thesis — predicted vs realized hit rate per bucket. |

**Acceptance:** a fresh install with one full ingest can run a backtest over a
year of signal dates and see calibration buckets with real counts.

## Phase 2 — Calibrated model

*Depends on Phase 1: backfilled signals are the training set.*

| # | Task | Effort | Notes |
|---|------|--------|-------|
| 2.1 | Walk-forward logistic regression + isotonic calibration | L | scikit-learn is already pinned and unused. Retrain on expanding window; never score a date with data from its future. |
| 2.2 | Driver attribution from coefficients | M | coefficient x feature value -> ranked drivers/risks; keeps the existing explainability UI intact. |
| 2.3 | Model-vs-heuristic comparison | S | Backtest both; show side by side. Honesty about whether the model earns its keep. |

**Acceptance:** stated probabilities match realized frequencies within bucket
noise on held-out dates; every score still lists human-readable drivers.

## Phase 3 — Automation + event awareness

| # | Task | Effort | Notes |
|---|------|--------|-------|
| 3.1 | Scheduled daily ingest | M | APScheduler in FastAPI lifespan (or launchd); runs after market close; retry with backoff. |
| 3.2 | Freshness UI | S | "Data as of / next refresh at" in TopBar + per-source age in health panel. |
| 3.3 | EDGAR 8-K near-real-time watch | M | EDGAR filing feed polled frequently; 8-K within minutes = free material-event detection. |
| 3.4 | Earnings calendar (Finnhub free) | M | "Earnings in N days" as displayed context **and** as an uncertainty-widening feature for Phase 2. |

**Acceptance:** app is current every trading evening with zero manual action;
upcoming earnings visibly widen stated uncertainty.

## Phase 4 — Product polish

| # | Task | Effort | Notes |
|---|------|--------|-------|
| 4.1 | Add-ticker UI | S | `POST /api/watchlist` exists; button is decorative. Cheapest real feature in the repo. |
| 4.2 | Real company metadata | S | Names from SEC `company_tickers.json` (already fetched in `sec.py`); kill "XYZ Corporation". |
| 4.3 | Sidebar routes or trim to Watchlist | M | Decorative nav erodes trust in a trust-positioned product. |
| 4.4 | Sortable/selectable columns | S | "Columns" button exists; wire or remove. |
| 4.5 | Frontend tests | M | vitest configured, zero tests. Start with format.ts, WatchlistTable ranking, demo-flag rendering. |
| 4.6 | Cross-platform README + dev scripts | S | Currently PowerShell-only; venv story changed to uv. |

---

## Sequencing rationale ("what I'd do first")

1. **Backfill (1.1)** — unblocks everything measurable.
2. **Second price source + reconciliation + visible warnings (0.3–0.5)** — kills silent failures. Do Phase 0 first since backfill trains on this data.
3. **Scheduled refresh (3.1)** — prototype -> tool.
4. **Calibrated model (2.1)** — the credibility core.
5. **8-K watch + earnings calendar (3.3–3.4)** — event edge from free primary sources.

Phase 0 -> 1 -> 2 is a strict dependency chain; 3 and 4 can interleave anywhere
after Phase 0.

## Deliberately out of scope for V1

Real-time streaming quotes, X/Twitter (cost/signal ratio), broker integration,
auto-trading (permanently out), LLM sentiment (revisit post-V1 with local Ollama
option to preserve the local-first story).
