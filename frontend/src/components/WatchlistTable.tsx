import { ExternalLink, PlusCircle, SlidersHorizontal } from "lucide-react";
import { CompanyMark } from "./CompanyMark";
import { confidenceLabel, formatCurrency, formatPercent, formatSignedPercent } from "../lib/format";
import type { Signal, Ticker, TickerSummary } from "../types/api";

interface WatchlistTableProps {
  watchlist: Ticker[];
  signals: Signal[];
  selectedSymbol: string;
  selectedSummary?: TickerSummary | null;
  onSelect: (symbol: string) => void;
}

const rowStats: Record<string, { price: number; daily: number }> = {
  AAPL: { price: 212.4, daily: 0.006 },
  MSFT: { price: 498.3, daily: 0.008 },
  NVDA: { price: 144.9, daily: 0.012 },
  AMD: { price: 164.2, daily: -0.004 },
  SPY: { price: 624.1, daily: 0.003 },
};

export function WatchlistTable({
  watchlist,
  signals,
  selectedSymbol,
  selectedSummary,
  onSelect,
}: WatchlistTableProps) {
  const signalMap = new Map(signals.map((signal) => [signal.symbol, signal]));
  const rows = watchlist
    .filter((ticker) => ticker.sector !== "Benchmark")
    .map((ticker) => ({ ticker, signal: signalMap.get(ticker.symbol) }))
    .sort(
      (left, right) =>
        (right.signal?.probability_outperform_spy ?? 0) -
        (left.signal?.probability_outperform_spy ?? 0),
    );

  return (
    <section className="panel watchlist-panel" aria-labelledby="watchlist-title">
      <div className="panel-heading">
        <div>
          <h2 id="watchlist-title">Watchlist Overview</h2>
          <p>Ranked by 5-day outperform probability.</p>
        </div>
        <div className="table-actions">
          <button className="ghost-action" type="button">
            <span>5-day horizon</span>
          </button>
          <button className="ghost-action" type="button">
            <SlidersHorizontal size={15} />
            <span>Columns</span>
          </button>
          <a className="subtle-link" href="https://www.sec.gov/edgar/search/" target="_blank">
            Sources <ExternalLink size={14} />
          </a>
        </div>
      </div>

      <div className="table-wrap">
        <table className="signal-table">
          <thead>
            <tr>
              <th>Rank</th>
              <th>Ticker</th>
              <th>Name</th>
              <th>Price</th>
              <th>Daily %</th>
              <th>5-day outperform probability</th>
              <th>Confidence</th>
              <th>Signal</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(({ ticker, signal }, index) => {
              const isSelected = ticker.symbol === selectedSymbol;
              const probability = signal?.probability_outperform_spy ?? 0;
              const signalTone = probability >= 0.58 ? "bullish" : probability >= 0.53 ? "neutral" : "cautious";
              const fallbackStats = rowStats[ticker.symbol];
              const stats =
                ticker.symbol === selectedSymbol && selectedSummary
                  ? { price: selectedSummary.latest_price ?? fallbackStats?.price, daily: selectedSummary.return_1d ?? fallbackStats?.daily }
                  : fallbackStats;
              return (
                <tr
                  className={isSelected ? "selected-row" : undefined}
                  key={ticker.symbol}
                  onClick={() => onSelect(ticker.symbol)}
                >
                  <td className="rank-cell">{index + 1}</td>
                  <td>
                    <button className="ticker-cell" type="button">
                      <CompanyMark symbol={ticker.symbol} />
                      <strong>{ticker.symbol}</strong>
                    </button>
                  </td>
                  <td className="name-cell">{ticker.name}</td>
                  <td className="price-cell">{formatCurrency(stats?.price)}</td>
                  <td>
                    <span className={stats?.daily && stats.daily < 0 ? "negative" : "positive"}>
                      {formatSignedPercent(stats?.daily)}
                    </span>
                  </td>
                  <td>
                    <div className="probability-cell">
                      <strong>{formatPercent(signal?.probability_outperform_spy, 0)}</strong>
                    </div>
                  </td>
                  <td>
                    <span className={`confidence ${signal?.confidence ?? "low"}`}>
                      {confidenceLabel(signal?.confidence)}
                    </span>
                  </td>
                  <td>
                    <span className={`signal-badge ${signalTone}`}>
                      {signalTone === "bullish" ? "Bullish" : signalTone === "cautious" ? "Cautious" : "Neutral"}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="table-footer">
        <span>Showing {rows.length} active tickers</span>
        <button className="inline-action" type="button">
          <PlusCircle size={15} />
          Add ticker
        </button>
      </div>
    </section>
  );
}
