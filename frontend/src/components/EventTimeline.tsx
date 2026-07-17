import { ExternalLink, FileText, Newspaper } from "lucide-react";
import { formatPercent } from "../lib/format";
import type { EventSignal } from "../types/api";

interface EventTimelineProps {
  events: EventSignal[];
}

export function EventTimeline({ events }: EventTimelineProps) {
  return (
    <section className="panel timeline-panel" aria-labelledby="timeline-title">
      <div className="panel-heading">
        <div>
          <h2 id="timeline-title">Event timeline</h2>
          <p>Filing and news signals with source provenance.</p>
        </div>
      </div>

      <div className="timeline-list">
        {events.length === 0 ? (
          <div className="empty-state compact">Events will appear after ingestion.</div>
        ) : (
          events.slice(0, 8).map((event) => (
            <article className="timeline-item" key={event.id}>
              <div className="timeline-icon">
                {event.event_type === "filing" ? <FileText size={16} /> : <Newspaper size={16} />}
              </div>
              <div>
                <div className="timeline-meta">
                  <span>{event.event_type}</span>
                  <span>{event.signal_date}</span>
                  <span>{formatPercent(event.confidence, 0)} confidence</span>
                </div>
                <p>{event.summary}</p>
                {event.source_url && (
                  <a href={event.source_url} target="_blank">
                    Open source <ExternalLink size={13} />
                  </a>
                )}
              </div>
            </article>
          ))
        )}
      </div>
    </section>
  );
}

