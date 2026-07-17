import { AlertTriangle, Link2, Star, X } from "lucide-react";
import { CompanyMark } from "./CompanyMark";
import { confidenceLabel, formatCurrency, formatPercent, formatSignedPercent } from "../lib/format";
import type { TickerSummary } from "../types/api";

interface TickerDetailProps {
  summary: TickerSummary | null;
}

export function TickerDetail({ summary }: TickerDetailProps) {
  if (!summary) {
    return (
      <section className="panel detail-panel">
        <div className="empty-state">Select a ticker to review the analysis.</div>
      </section>
    );
  }

  const signal = summary.signal;
  const probability = signal?.probability_outperform_spy ?? 0.5;
  const probabilityArc = Math.max(8, Math.min(100, probability * 100));
  const drivers = signal?.drivers.length ? signal.drivers : summary.what_changed;
  const risks = summary.risks.length ? summary.risks : signal?.risks ?? [];
  const signalLabel = probability >= 0.58 ? "Bullish" : probability >= 0.53 ? "Neutral" : "Cautious";

  return (
    <section className="panel detail-panel" aria-labelledby="detail-title">
      <div className="detail-header">
        <div className="detail-title-block">
          <CompanyMark symbol={summary.symbol} />
          <div>
            <span className="exchange-label">{summary.exchange ?? "Watchlist"}</span>
            <h2 id="detail-title">
              {summary.symbol}
              <span>{summary.name}</span>
            </h2>
          </div>
        </div>
        <div className="detail-actions" aria-label="Ticker actions">
          <button aria-label="Watch ticker" className="icon-action" type="button">
            <Star size={15} />
          </button>
          <button aria-label="Close detail" className="icon-action" type="button">
            <X size={15} />
          </button>
        </div>
      </div>

      <div className="price-strip">
        <div className="price-block">
          <span>Latest close</span>
          <strong>{formatCurrency(summary.latest_price)}</strong>
        </div>
        <div className="price-move">
          <span className={summary.return_1d && summary.return_1d < 0 ? "negative" : "positive"}>
            {formatSignedPercent(summary.return_1d)}
          </span>
          <small>{summary.latest_date ?? "not cached"}</small>
        </div>
      </div>

      <div className="probability-summary">
        <div>
          <span>5-day outperform probability</span>
          <strong>{formatPercent(signal?.probability_outperform_spy, 0)}</strong>
        </div>
        <div className="gauge" aria-hidden="true">
          <svg viewBox="0 0 120 70">
            <path className="gauge-track" d="M 18 56 A 42 42 0 0 1 102 56" pathLength="100" />
            <path
              className="gauge-value"
              d="M 18 56 A 42 42 0 0 1 102 56"
              pathLength="100"
              style={{ strokeDasharray: `${probabilityArc} 100` }}
            />
          </svg>
        </div>
      </div>

      <div className="signal-summary-row">
        <MiniMetric label="Confidence" value={confidenceLabel(signal?.confidence)} />
        <MiniMetric label="Gauge" value={formatPercent(signal?.probability_outperform_spy, 0)} />
        <MiniMetric label="Signal" value={signalLabel} tone={signalLabel.toLowerCase()} />
      </div>

      <div className="analysis-grid">
        <div>
          <div className="section-label">Drivers</div>
          <ul className="bullet-list positive-list">
            {drivers.map((item) => (
              <li key={item}>
                <span className="research-dot" />
                <span>{item}</span>
                <small>(1w)</small>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <div className="section-label">Risks</div>
          <ul className="bullet-list negative-list">
            {risks.map((item) => (
              <li key={item}>
                <span className="research-dot" />
                <span>{item}</span>
                <small>(1w)</small>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="key-metrics">
        <h3>Key metrics</h3>
        <Metric label="1d return" value={formatSignedPercent(summary.return_1d)} context="Latest close" tone={summary.return_1d} />
        <Metric label="5d return" value={formatSignedPercent(summary.return_5d)} context="Signal horizon" tone={summary.return_5d} />
        <Metric label="20d return" value={formatSignedPercent(summary.return_20d)} context="Trend window" tone={summary.return_20d} />
        <Metric
          label="20d vs SPY"
          value={formatSignedPercent(summary.relative_strength_spy)}
          context="Benchmark"
          tone={summary.relative_strength_spy}
        />
        <Metric label="Evidence links" value={String(signal?.evidence.length ?? 0)} context="Sources" />
      </div>

      {signal?.evidence.length ? (
        <div className="source-list">
          <h3>Sources</h3>
          {signal.evidence.map((item) => (
            <a href={item.url ?? "#"} key={`${item.type}-${item.summary}`} target="_blank">
              <Link2 size={14} />
              <span>{item.summary ?? item.type}</span>
            </a>
          ))}
        </div>
      ) : null}

      {summary.is_demo && (
        <div className="data-health-note">
          <AlertTriangle size={16} />
          <span>Demo data is showing until a daily refresh successfully caches free market sources.</span>
        </div>
      )}
    </section>
  );
}

interface MiniMetricProps {
  label: string;
  value: string;
  tone?: string;
}

function MiniMetric({ label, value, tone }: MiniMetricProps) {
  return (
    <div className="mini-metric">
      <span>{label}</span>
      <strong className={tone}>{value}</strong>
    </div>
  );
}

interface MetricProps {
  label: string;
  value: string;
  context: string;
  tone?: number | null;
}

function Metric({ label, value, context, tone }: MetricProps) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong className={tone === null || tone === undefined ? undefined : tone >= 0 ? "positive" : "negative"}>
        {value}
      </strong>
      <small>{context}</small>
    </div>
  );
}
