import React from 'react';
import type { NavigationMetrics, SimulationStatusType, SimulationStepState } from '../types/navigation';

interface TelemetryPanelProps {
  state: SimulationStepState | null;
  metrics: NavigationMetrics | null;
  maxSteps: number;
}

export const TelemetryPanel: React.FC<TelemetryPanelProps> = ({
  state,
  metrics,
  maxSteps,
}) => {
  const status = state?.status || 'IDLE';
  const step = state?.step || 0;
  const replanCount = state?.replan_count || 0;
  const progressPercent = Math.min(100, Math.round((step / (maxSteps || 100)) * 100));

  const efficiency = metrics
    ? `${(metrics.path_efficiency * 100).toFixed(1)}%`
    : state?.active_path && state.trajectory
    ? `${Math.max(0, Math.min(100, Math.round((state.active_path.length / Math.max(1, state.trajectory.length)) * 100)))}%`
    : '--%';

  const getStatusColor = (st: SimulationStatusType): string => {
    switch (st) {
      case 'GOAL_REACHED':
        return '#10b981'; // Emerald
      case 'RUNNING':
        return '#00f0ff'; // Neon Cyan
      case 'REPLANNING':
        return '#f59e0b'; // Amber
      case 'PAUSED':
        return '#a855f7'; // Violet
      case 'COLLISION':
      case 'FAILED':
        return '#ef4444'; // Red
      case 'MAX_STEPS_EXCEEDED':
        return '#f97316'; // Orange
      default:
        return '#64748b'; // Slate
    }
  };

  return (
    <div id="telemetry-panel-container" className="telemetry-container">
      {/* 1. Status Bar */}
      <div className="status-header">
        <div className="status-badge-wrapper">
          <span
            className="status-dot"
            style={{
              backgroundColor: getStatusColor(status),
              boxShadow: `0 0 12px ${getStatusColor(status)}`,
            }}
          />
          <span className="status-text" style={{ color: getStatusColor(status) }}>
            {status.replace(/_/g, ' ')}
          </span>
        </div>
        <span className="step-counter">
          Step <strong className="highlight-text">{step}</strong> / {maxSteps}
        </span>
      </div>

      {/* 2. Step Progress Bar */}
      <div className="progress-bar-container">
        <div
          className="progress-bar-fill"
          style={{
            width: `${progressPercent}%`,
            backgroundColor: getStatusColor(status),
          }}
        />
      </div>

      {/* 3. Metric Cards Grid */}
      <div className="metrics-grid">
        <div className="metric-card">
          <span className="metric-label">Path Efficiency</span>
          <span className="metric-value efficiency-val">{efficiency}</span>
          <span className="metric-sub">Optimal / Trajectory Ratio</span>
        </div>

        <div className={`metric-card ${replanCount > 0 ? 'replan-active' : ''}`}>
          <span className="metric-label">Replan Events</span>
          <span className="metric-value replan-val">{replanCount}</span>
          <span className="metric-sub">Dynamic Obstacle Detours</span>
        </div>

        <div className="metric-card">
          <span className="metric-label">Robot Position</span>
          <span className="metric-value coord-val">
            {state?.robot_position ? `(${state.robot_position[0]}, ${state.robot_position[1]})` : '--'}
          </span>
          <span className="metric-sub">
            Target: {state?.goal_position ? `(${state.goal_position[0]}, ${state.goal_position[1]})` : '--'}
          </span>
        </div>

        <div className="metric-card">
          <span className="metric-label">Trajectory Length</span>
          <span className="metric-value">
            {metrics ? `${metrics.trajectory_length.toFixed(1)} u` : `${state?.trajectory?.length || 0} steps`}
          </span>
          <span className="metric-sub">
            Optimal: {metrics ? `${metrics.optimal_path_length.toFixed(1)} u` : `${state?.active_path?.length || 0} waypoints`}
          </span>
        </div>
      </div>

      {/* 4. Live Message Banner */}
      {state?.message && (
        <div className="status-message-banner">
          <span className="message-icon">ℹ</span>
          <span className="message-text">{state.message}</span>
        </div>
      )}
    </div>
  );
};
