import React from 'react';
import type { SimulationRunRecord } from '../types/navigation';

interface HistoryTableProps {
  history: SimulationRunRecord[];
  onRefresh: () => void;
}

export const HistoryTable: React.FC<HistoryTableProps> = ({ history, onRefresh }) => {
  return (
    <div id="history-table-container" className="history-container">
      <div className="history-header">
        <div className="history-title-group">
          <h3 className="section-title">Historical Benchmark Runs</h3>
          <span className="history-counter">{history.length} runs</span>
        </div>
        <button className="btn-refresh" onClick={onRefresh} title="Refresh historical records">
          🔄 Refresh
        </button>
      </div>

      <div className="history-table-wrapper">
        {history.length === 0 ? (
          <div className="empty-history">
            No completed simulation runs recorded yet. Run a simulation to goal to view telemetry records here.
          </div>
        ) : (
          <table className="history-table">
            <thead>
              <tr>
                <th>Run ID</th>
                <th>Outcome</th>
                <th>Total Steps</th>
                <th>Efficiency</th>
                <th>Replans</th>
                <th>Duration</th>
                <th>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {history.map((record) => (
                <tr key={record.run_id}>
                  <td className="mono-cell">{record.run_id.slice(0, 8)}</td>
                  <td>
                    <span
                      className={`badge-outcome ${
                        record.success ? 'badge-success' : 'badge-failure'
                      }`}
                    >
                      {record.success ? '✓ SUCCESS' : record.collision ? '⚠ COLLISION' : '✕ FAILED'}
                    </span>
                  </td>
                  <td>{record.total_steps}</td>
                  <td className="efficiency-cell">
                    {(record.path_efficiency * 100).toFixed(1)}%
                  </td>
                  <td>
                    <span className={`replan-badge ${record.replan_count > 0 ? 'has-replans' : ''}`}>
                      {record.replan_count}
                    </span>
                  </td>
                  <td className="mono-cell">{record.execution_time_seconds.toFixed(3)}s</td>
                  <td className="timestamp-cell">
                    {record.timestamp.split('T')[1]?.slice(0, 8) || record.timestamp}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
