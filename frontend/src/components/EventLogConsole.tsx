import React, { useState, useRef, useEffect } from 'react';
import type { SimulationEvent } from '../types/navigation';

interface EventLogConsoleProps {
  events: SimulationEvent[];
  onClear: () => void;
}

export const EventLogConsole: React.FC<EventLogConsoleProps> = ({ events, onClear }) => {
  const [filter, setFilter] = useState<'ALL' | 'REPLAN' | 'WARN' | 'ERROR' | 'SUCCESS'>('ALL');
  const [autoScroll, setAutoScroll] = useState(true);
  const logEndRef = useRef<HTMLDivElement | null>(null);

  const filteredEvents = events.filter((e) => {
    if (filter === 'ALL') return true;
    return e.type === filter;
  });

  useEffect(() => {
    if (autoScroll) {
      logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [filteredEvents, autoScroll]);

  const getTagClass = (type: SimulationEvent['type']): string => {
    switch (type) {
      case 'REPLAN':
        return 'tag-replan';
      case 'SUCCESS':
        return 'tag-success';
      case 'WARN':
        return 'tag-warn';
      case 'ERROR':
        return 'tag-error';
      default:
        return 'tag-info';
    }
  };

  return (
    <div id="event-log-console-container" className="event-console-container">
      {/* Console Header & Filters */}
      <div className="console-header">
        <div className="console-title-group">
          <h3 className="section-title">Audit Log & Event Feed</h3>
          <span className="console-counter">{events.length} events</span>
        </div>

        <div className="console-controls">
          <div className="filter-chips">
            {(['ALL', 'REPLAN', 'SUCCESS', 'WARN', 'ERROR'] as const).map((f) => (
              <button
                key={f}
                className={`filter-chip ${filter === f ? 'active' : ''}`}
                onClick={() => setFilter(f)}
              >
                {f}
              </button>
            ))}
          </div>

          <label className="autoscroll-toggle">
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
            />
            <span>Auto-scroll</span>
          </label>

          <button className="btn-clear" onClick={onClear} title="Clear event feed">
            Clear
          </button>
        </div>
      </div>

      {/* Log Feed */}
      <div className="console-feed">
        {filteredEvents.length === 0 ? (
          <div className="empty-feed">No events recorded for current filter.</div>
        ) : (
          filteredEvents.map((evt) => (
            <div key={evt.id} className="feed-item">
              <span className="feed-time">
                {evt.timestamp.split('T')[1]?.slice(0, 8) || evt.timestamp}
              </span>
              <span className="feed-step">T+{evt.step}</span>
              <span className={`feed-tag ${getTagClass(evt.type)}`}>{evt.type}</span>
              <span className="feed-msg">{evt.message}</span>
            </div>
          ))
        )}
        <div ref={logEndRef} />
      </div>
    </div>
  );
};
