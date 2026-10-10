import { useState, useEffect, useRef, useCallback } from 'react';
import type {
  Coordinate,
  InteractiveTool,
  NavigationConfig,
  NavigationMetrics,
  SimulationEvent,
  SimulationRunRecord,
  SimulationStepState,
} from './types/navigation';
import { NavigationApiClient, SimulationWebSocket } from './api/navigationApi';
import type { PresetScenario } from './utils/presets';

import { TopBar } from './components/TopBar';
import { NavigationCanvas } from './components/NavigationCanvas';
import { ControlDeck } from './components/ControlDeck';
import { TelemetryPanel } from './components/TelemetryPanel';
import { EventLogConsole } from './components/EventLogConsole';
import { HistoryTable } from './components/HistoryTable';
import './index.css';

export function App() {
  const [state, setState] = useState<SimulationStepState | null>(null);
  const [config, setConfig] = useState<NavigationConfig | null>(null);
  const [metrics, setMetrics] = useState<NavigationMetrics | null>(null);
  const [events, setEvents] = useState<SimulationEvent[]>([]);
  const [history, setHistory] = useState<SimulationRunRecord[]>([]);
  const [activeTool, setActiveTool] = useState<InteractiveTool>('select');
  const [speedMs, setSpeedMs] = useState<number>(200);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'simulation' | 'audit_log' | 'history'>('simulation');
  const [toastMessage, setToastMessage] = useState<{ text: string; type: 'info' | 'error' | 'success' } | null>(null);

  const wsClientRef = useRef<SimulationWebSocket | null>(null);
  const toastTimeoutRef = useRef<number | null>(null);

  const showToast = useCallback((text: string, type: 'info' | 'error' | 'success' = 'info') => {
    if (toastTimeoutRef.current) clearTimeout(toastTimeoutRef.current);
    setToastMessage({ text, type });
    toastTimeoutRef.current = window.setTimeout(() => {
      setToastMessage(null);
    }, 3500);
  }, []);

  // WebSocket Connection Lifecycle
  useEffect(() => {
    let isMounted = true;
    NavigationApiClient.getConfig().then((initialConfig) => {
      if (isMounted) setConfig(initialConfig);
    }).catch(() => {});

    NavigationApiClient.getState().then((initialState) => {
      if (isMounted) {
        setState(initialState);
        if (initialState.metrics) setMetrics(initialState.metrics);
      }
    }).catch(() => {});

    NavigationApiClient.getEvents(100).then((initialEvents) => {
      if (isMounted) setEvents(initialEvents);
    }).catch(() => {});

    NavigationApiClient.getHistory().then((initialHistory) => {
      if (isMounted) setHistory(initialHistory);
    }).catch(() => {});

    const ws = new SimulationWebSocket(
      (newState) => {
        if (isMounted) {
          setState(newState);
          if (newState.metrics) {
            setMetrics(newState.metrics);
          }
        }
      },
      (newEvent) => {
        if (isMounted) {
          setEvents((prev) => [...prev.slice(-200), newEvent]);
        }
      },
      (connected) => {
        if (isMounted) {
          setIsConnected(connected);
        }
      }
    );

    wsClientRef.current = ws;

    return () => {
      isMounted = false;
      ws.destroy();
    };
  }, []);

  // Simulation Controls
  const handleStart = async () => {
    try {
      if (wsClientRef.current && isConnected) {
        wsClientRef.current.sendAction('START');
      } else {
        const newState = await NavigationApiClient.startSimulation();
        setState(newState);
      }
      showToast('Simulation started', 'info');
    } catch (e: any) {
      showToast(e.message || 'Failed to start simulation', 'error');
    }
  };

  const handlePause = async () => {
    try {
      if (wsClientRef.current && isConnected) {
        wsClientRef.current.sendAction('PAUSE');
      } else {
        const newState = await NavigationApiClient.pauseSimulation();
        setState(newState);
      }
      showToast('Simulation paused', 'info');
    } catch (e: any) {
      showToast(e.message || 'Failed to pause simulation', 'error');
    }
  };

  const handleResume = async () => {
    try {
      if (wsClientRef.current && isConnected) {
        wsClientRef.current.sendAction('RESUME');
      } else {
        const newState = await NavigationApiClient.resumeSimulation();
        setState(newState);
      }
      showToast('Simulation resumed', 'info');
    } catch (e: any) {
      showToast(e.message || 'Failed to resume simulation', 'error');
    }
  };

  const handleStep = async () => {
    try {
      if (wsClientRef.current && isConnected) {
        wsClientRef.current.sendAction('STEP');
      } else {
        const newState = await NavigationApiClient.stepSimulation();
        setState(newState);
      }
    } catch (e: any) {
      showToast(e.message || 'Failed to step simulation', 'error');
    }
  };

  const handleReset = async () => {
    try {
      if (wsClientRef.current && isConnected) {
        wsClientRef.current.sendAction('RESET');
      } else {
        const newState = await NavigationApiClient.resetSimulation();
        setState(newState);
      }
      showToast('Simulation reset to initial step', 'info');
    } catch (e: any) {
      showToast(e.message || 'Failed to reset simulation', 'error');
    }
  };

  const handleSpeedChange = async (newSpeed: number) => {
    setSpeedMs(newSpeed);
    try {
      await NavigationApiClient.setSpeed(newSpeed);
    } catch (e: any) {
      console.error('Failed to update speed:', e);
    }
  };

  // Config Updates
  const handleConfigChange = async (updater: (prev: NavigationConfig) => NavigationConfig) => {
    if (!config) return;
    const updated = updater(config);
    setConfig(updated);
    try {
      const newState = await NavigationApiClient.updateConfig(updated);
      setState(newState);
      showToast('Configuration updated', 'success');
    } catch (e: any) {
      showToast(e.message || 'Failed to apply configuration', 'error');
    }
  };

  const handleResetDefaultConfig = async () => {
    try {
      const newState = await NavigationApiClient.resetConfigToDefault();
      setState(newState);
      const freshConfig = await NavigationApiClient.getConfig();
      setConfig(freshConfig);
      showToast('Configuration restored to default', 'success');
    } catch (e: any) {
      showToast(e.message || 'Failed to reset config', 'error');
    }
  };

  const handleSelectPreset = async (preset: PresetScenario) => {
    setConfig(preset.config);
    try {
      const newState = await NavigationApiClient.updateConfig(preset.config);
      setState(newState);
      showToast(`Loaded preset: ${preset.name}`, 'success');
    } catch (e: any) {
      showToast(e.message || 'Failed to load preset', 'error');
    }
  };

  // Interactive Grid Manipulation
  const handleCellClick = (coord: Coordinate) => {
    if (!config) return;
    const [x, y] = coord;

    if (activeTool === 'set_start') {
      if (config.environment.goal[0] === x && config.environment.goal[1] === y) {
        showToast('Start cannot overlap Goal', 'error');
        return;
      }
      handleConfigChange((prev) => ({
        ...prev,
        environment: {
          ...prev.environment,
          start: coord,
          static_obstacles: prev.environment.static_obstacles.filter(
            ([ox, oy]) => !(ox === x && oy === y)
          ),
        },
      }));
    } else if (activeTool === 'set_goal') {
      if (config.environment.start[0] === x && config.environment.start[1] === y) {
        showToast('Goal cannot overlap Start', 'error');
        return;
      }
      handleConfigChange((prev) => ({
        ...prev,
        environment: {
          ...prev.environment,
          goal: coord,
          static_obstacles: prev.environment.static_obstacles.filter(
            ([ox, oy]) => !(ox === x && oy === y)
          ),
        },
      }));
    } else if (activeTool === 'add_obstacle') {
      const isStart = config.environment.start[0] === x && config.environment.start[1] === y;
      const isGoal = config.environment.goal[0] === x && config.environment.goal[1] === y;
      if (isStart || isGoal) return;

      const exists = config.environment.static_obstacles.some(([ox, oy]) => ox === x && oy === y);
      if (!exists) {
        handleConfigChange((prev) => ({
          ...prev,
          environment: {
            ...prev.environment,
            static_obstacles: [...prev.environment.static_obstacles, coord],
          },
        }));
      }
    } else if (activeTool === 'remove_obstacle') {
      handleConfigChange((prev) => ({
        ...prev,
        environment: {
          ...prev.environment,
          static_obstacles: prev.environment.static_obstacles.filter(
            ([ox, oy]) => !(ox === x && oy === y)
          ),
        },
      }));
    }
  };

  const handleCellDrag = (coords: Coordinate[]) => {
    if (!config) return;
    if (activeTool === 'add_obstacle') {
      const [sx, sy] = config.environment.start;
      const [gx, gy] = config.environment.goal;

      handleConfigChange((prev) => {
        const obsSet = new Set(prev.environment.static_obstacles.map(([ox, oy]) => `${ox},${oy}`));
        coords.forEach(([cx, cy]) => {
          if ((cx === sx && cy === sy) || (cx === gx && cy === gy)) return;
          obsSet.add(`${cx},${cy}`);
        });

        const newObs: Coordinate[] = Array.from(obsSet).map((k) => {
          const parts = k.split(',');
          return [parseInt(parts[0], 10), parseInt(parts[1], 10)];
        });

        return {
          ...prev,
          environment: {
            ...prev.environment,
            static_obstacles: newObs,
          },
        };
      });
    } else if (activeTool === 'remove_obstacle') {
      const removeKeys = new Set(coords.map(([cx, cy]) => `${cx},${cy}`));
      handleConfigChange((prev) => ({
        ...prev,
        environment: {
          ...prev.environment,
          static_obstacles: prev.environment.static_obstacles.filter(
            ([ox, oy]) => !removeKeys.has(`${ox},${oy}`)
          ),
        },
      }));
    }
  };

  const refreshHistory = async () => {
    try {
      const records = await NavigationApiClient.getHistory();
      setHistory(records);
      showToast('Run history refreshed', 'info');
    } catch {
      showToast('Failed to refresh history', 'error');
    }
  };

  return (
    <div className="app-container">
      {/* Toast Notification */}
      {toastMessage && (
        <div className={`toast-popup toast-${toastMessage.type}`}>
          <span>{toastMessage.text}</span>
        </div>
      )}

      {/* Header */}
      <TopBar
        isConnected={isConnected}
        onResetDefaultConfig={handleResetDefaultConfig}
      />

      {/* Main Layout Grid */}
      <main className="main-content">
        {/* Left Column: Canvas View & Navigation Views */}
        <section className="viewport-column">
          {/* Navigation View Tabs */}
          <div className="tab-navigation">
            <button
              id="tab-btn-simulation"
              className={`tab-btn ${activeTab === 'simulation' ? 'active' : ''}`}
              onClick={() => setActiveTab('simulation')}
            >
              <span className="tab-icon">🗺</span> Live 2D Grid Simulator
            </button>
            <button
              id="tab-btn-audit-log"
              className={`tab-btn ${activeTab === 'audit_log' ? 'active' : ''}`}
              onClick={() => setActiveTab('audit_log')}
            >
              <span className="tab-icon">📋</span> Audit Feed ({events.length})
            </button>
            <button
              id="tab-btn-history"
              className={`tab-btn ${activeTab === 'history' ? 'active' : ''}`}
              onClick={() => {
                setActiveTab('history');
                refreshHistory();
              }}
            >
              <span className="tab-icon">📊</span> Historical Benchmark Runs ({history.length})
            </button>
          </div>

          {/* Active Tab View */}
          <div className="view-content-wrapper">
            {activeTab === 'simulation' && (
              <>
                <TelemetryPanel
                  state={state}
                  metrics={metrics}
                  maxSteps={config?.simulation?.max_steps || 100}
                />
                <NavigationCanvas
                  state={state}
                  activeTool={activeTool}
                  onCellClick={handleCellClick}
                  onCellDrag={handleCellDrag}
                />
              </>
            )}

            {activeTab === 'audit_log' && (
              <EventLogConsole
                events={events}
                onClear={() => setEvents([])}
              />
            )}

            {activeTab === 'history' && (
              <HistoryTable
                history={history}
                onRefresh={refreshHistory}
              />
            )}
          </div>
        </section>

        {/* Right Column: Interactive Controls & Configuration Deck */}
        <aside className="controls-column">
          <ControlDeck
            status={state?.status || 'IDLE'}
            speedMs={speedMs}
            activeTool={activeTool}
            config={config}
            onStart={handleStart}
            onPause={handlePause}
            onResume={handleResume}
            onStep={handleStep}
            onReset={handleReset}
            onSpeedChange={handleSpeedChange}
            onToolChange={setActiveTool}
            onConfigChange={handleConfigChange}
            onSelectPreset={handleSelectPreset}
          />
        </aside>
      </main>
    </div>
  );
}

export default App;
