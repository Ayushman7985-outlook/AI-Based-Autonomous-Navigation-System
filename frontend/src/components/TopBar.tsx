import React from 'react';

interface TopBarProps {
  isConnected: boolean;
  onResetDefaultConfig: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({
  isConnected,
  onResetDefaultConfig,
}) => {
  return (
    <header id="app-topbar" className="topbar">
      <div className="topbar-brand">
        <div className="radar-icon-wrapper">
          <span className="radar-pulse"></span>
          <span className="radar-core">🧭</span>
        </div>
        <div className="brand-text">
          <h1 className="brand-title">AI Autonomous Navigation System</h1>
          <span className="brand-subtitle">
            2D Grid World • Dynamic Obstacle Avoidance • Online A* Replanning
          </span>
        </div>
      </div>

      <div className="topbar-actions">
        {/* Connection status indicator */}
        <div className="connection-badge">
          <span className={`conn-dot ${isConnected ? 'online' : 'offline'}`} />
          <span className="conn-label">
            {isConnected ? 'LIVE WS' : 'CONNECTING...'}
          </span>
        </div>

        <button
          id="btn-topbar-reset-defaults"
          className="btn-topbar-action"
          onClick={onResetDefaultConfig}
          title="Restore original default environment configuration"
        >
          <span>↺</span> Default Config
        </button>
      </div>
    </header>
  );
};
