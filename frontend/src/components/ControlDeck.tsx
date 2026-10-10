import React from 'react';
import type {
  InteractiveTool,
  NavigationConfig,
  SimulationStatusType,
} from '../types/navigation';
import { PRESET_SCENARIOS } from '../utils/presets';
import type { PresetScenario } from '../utils/presets';

interface ControlDeckProps {
  status: SimulationStatusType;
  speedMs: number;
  activeTool: InteractiveTool;
  config: NavigationConfig | null;
  onStart: () => void;
  onPause: () => void;
  onResume: () => void;
  onStep: () => void;
  onReset: () => void;
  onSpeedChange: (speed: number) => void;
  onToolChange: (tool: InteractiveTool) => void;
  onConfigChange: (updater: (prev: NavigationConfig) => NavigationConfig) => void;
  onSelectPreset: (preset: PresetScenario) => void;
}

export const ControlDeck: React.FC<ControlDeckProps> = ({
  status,
  speedMs,
  activeTool,
  config,
  onStart,
  onPause,
  onResume,
  onStep,
  onReset,
  onSpeedChange,
  onToolChange,
  onConfigChange,
  onSelectPreset,
}) => {
  const isRunning = status === 'RUNNING' || status === 'REPLANNING';
  const isPaused = status === 'PAUSED';


  return (
    <div id="control-deck-container" className="deck-container">
      {/* 1. Simulation Playback Controls */}
      <div className="deck-section">
        <h3 className="section-title">Execution Controls</h3>
        <div className="button-group">
          {!isRunning && !isPaused && (
            <button
              id="btn-simulation-start"
              className="btn btn-primary"
              onClick={onStart}
              title="Start or restart simulation"
            >
              <span className="btn-icon">▶</span> Run
            </button>
          )}

          {isRunning && (
            <button
              id="btn-simulation-pause"
              className="btn btn-warning"
              onClick={onPause}
              title="Pause running simulation"
            >
              <span className="btn-icon">⏸</span> Pause
            </button>
          )}

          {isPaused && (
            <button
              id="btn-simulation-resume"
              className="btn btn-primary"
              onClick={onResume}
              title="Resume paused simulation"
            >
              <span className="btn-icon">▶</span> Resume
            </button>
          )}

          <button
            id="btn-simulation-step"
            className="btn btn-secondary"
            onClick={onStep}
            disabled={isRunning}
            title="Advance one discrete step"
          >
            <span className="btn-icon">⏭</span> Step
          </button>

          <button
            id="btn-simulation-reset"
            className="btn btn-danger"
            onClick={onReset}
            title="Reset simulation to step 0"
          >
            <span className="btn-icon">↺</span> Reset
          </button>
        </div>
      </div>

      {/* 2. Simulation Speed Control */}
      <div className="deck-section">
        <div className="section-header-row">
          <h3 className="section-title">Speed / Throttle</h3>
          <span className="badge-speed">{speedMs} ms / step</span>
        </div>
        <div className="speed-slider-row">
          <input
            id="slider-simulation-speed"
            type="range"
            min="30"
            max="800"
            step="10"
            value={speedMs}
            onChange={(e) => onSpeedChange(Number(e.target.value))}
            className="range-slider"
          />
        </div>
        <div className="speed-quick-buttons">
          <button
            className={`btn-tag ${speedMs === 400 ? 'active' : ''}`}
            onClick={() => onSpeedChange(400)}
          >
            0.5x
          </button>
          <button
            className={`btn-tag ${speedMs === 200 ? 'active' : ''}`}
            onClick={() => onSpeedChange(200)}
          >
            1.0x
          </button>
          <button
            className={`btn-tag ${speedMs === 100 ? 'active' : ''}`}
            onClick={() => onSpeedChange(100)}
          >
            2.0x
          </button>
          <button
            className={`btn-tag ${speedMs === 40 ? 'active' : ''}`}
            onClick={() => onSpeedChange(40)}
          >
            5.0x
          </button>
        </div>
      </div>

      {/* 3. Interactive Grid Tools */}
      <div className="deck-section">
        <h3 className="section-title">Interactive Grid Editor</h3>
        <p className="tool-hint">Select a tool and click or drag on the 2D grid to customize the scenario.</p>
        <div className="tool-grid">
          <button
            id="tool-select"
            className={`btn-tool ${activeTool === 'select' ? 'active' : ''}`}
            onClick={() => onToolChange('select')}
            title="Inspect cells"
          >
            <span className="tool-icon">🔍</span> Inspect
          </button>

          <button
            id="tool-add-obstacle"
            className={`btn-tool ${activeTool === 'add_obstacle' ? 'active' : ''}`}
            onClick={() => onToolChange('add_obstacle')}
            title="Click or drag to paint static obstacles"
          >
            <span className="tool-icon">🧱</span> Add Wall
          </button>

          <button
            id="tool-remove-obstacle"
            className={`btn-tool ${activeTool === 'remove_obstacle' ? 'active' : ''}`}
            onClick={() => onToolChange('remove_obstacle')}
            title="Click or drag to erase static obstacles"
          >
            <span className="tool-icon">🧹</span> Erase Wall
          </button>

          <button
            id="tool-set-start"
            className={`btn-tool ${activeTool === 'set_start' ? 'active' : ''}`}
            onClick={() => onToolChange('set_start')}
            title="Click grid cell to relocate start"
          >
            <span className="tool-icon">🟢</span> Set Start
          </button>

          <button
            id="tool-set-goal"
            className={`btn-tool ${activeTool === 'set_goal' ? 'active' : ''}`}
            onClick={() => onToolChange('set_goal')}
            title="Click grid cell to relocate goal"
          >
            <span className="tool-icon">🔴</span> Set Goal
          </button>
        </div>
      </div>

      {/* 4. Algorithm & Planning Configuration */}
      <div className="deck-section">
        <h3 className="section-title">A* Planning Algorithm</h3>
        <div className="form-group">
          <label htmlFor="select-heuristic" className="form-label">Distance Heuristic</label>
          <select
            id="select-heuristic"
            className="form-select"
            value={config?.planning?.heuristic || 'manhattan'}
            onChange={(e) => {
              const val = e.target.value as 'manhattan' | 'euclidean';
              onConfigChange((prev) => ({
                ...prev,
                planning: { ...prev.planning, heuristic: val },
              }));
            }}
          >
            <option value="manhattan">Manhattan (L1 Metric - Grid Cardinal)</option>
            <option value="euclidean">Euclidean (L2 Metric - Straight Line)</option>
          </select>
        </div>

        <div className="form-toggle-row">
          <label className="toggle-label" htmlFor="toggle-diagonal">
            <span>Allow 8-Way Diagonal Steps</span>
            <span className="toggle-sub">Corner-cutting safety enforced</span>
          </label>
          <input
            id="toggle-diagonal"
            type="checkbox"
            className="toggle-checkbox"
            checked={Boolean(config?.planning?.allow_diagonal)}
            onChange={(e) => {
              const checked = e.target.checked;
              onConfigChange((prev) => ({
                ...prev,
                planning: { ...prev.planning, allow_diagonal: checked },
              }));
            }}
          />
        </div>

        <div className="form-toggle-row">
          <label className="toggle-label" htmlFor="toggle-replan">
            <span>Online Replanning on Block</span>
            <span className="toggle-sub">Trigger dynamic A* path rerouting</span>
          </label>
          <input
            id="toggle-replan"
            type="checkbox"
            className="toggle-checkbox"
            checked={config?.control?.replan_on_block ?? true}
            onChange={(e) => {
              const checked = e.target.checked;
              onConfigChange((prev) => ({
                ...prev,
                control: { ...prev.control, replan_on_block: checked },
              }));
            }}
          />
        </div>
      </div>

      {/* 5. Benchmark Preset Scenarios */}
      <div className="deck-section">
        <h3 className="section-title">Benchmark Scenarios</h3>
        <div className="presets-list">
          {PRESET_SCENARIOS.map((preset) => (
            <button
              key={preset.id}
              id={`preset-${preset.id}`}
              className="btn-preset"
              onClick={() => onSelectPreset(preset)}
            >
              <span className="preset-icon">{preset.icon}</span>
              <div className="preset-text">
                <span className="preset-name">{preset.name}</span>
                <span className="preset-desc">{preset.description}</span>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
