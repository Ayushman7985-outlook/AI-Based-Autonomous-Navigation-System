import type {
  NavigationConfig,
  NavigationMetrics,
  SimulationEvent,
  SimulationRunRecord,
  SimulationStepState,
} from '../types/navigation';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

export class NavigationApiClient {
  static async checkHealth(): Promise<{ status: string; service: string; version: string }> {
    const res = await fetch(`${API_BASE_URL}/api/health`);
    if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
    return res.json();
  }

  static async getConfig(): Promise<NavigationConfig> {
    const res = await fetch(`${API_BASE_URL}/api/config`);
    if (!res.ok) throw new Error(`Failed to load config: ${res.statusText}`);
    return res.json();
  }

  static async updateConfig(config: NavigationConfig): Promise<SimulationStepState> {
    const res = await fetch(`${API_BASE_URL}/api/config`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Failed to update config');
    }
    return res.json();
  }

  static async resetConfigToDefault(): Promise<SimulationStepState> {
    const res = await fetch(`${API_BASE_URL}/api/config/reset`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error(`Failed to reset config: ${res.statusText}`);
    return res.json();
  }

  static async startSimulation(): Promise<SimulationStepState> {
    const res = await fetch(`${API_BASE_URL}/api/simulation/start`, { method: 'POST' });
    if (!res.ok) throw new Error(`Failed to start simulation: ${res.statusText}`);
    return res.json();
  }

  static async pauseSimulation(): Promise<SimulationStepState> {
    const res = await fetch(`${API_BASE_URL}/api/simulation/pause`, { method: 'POST' });
    if (!res.ok) throw new Error(`Failed to pause simulation: ${res.statusText}`);
    return res.json();
  }

  static async resumeSimulation(): Promise<SimulationStepState> {
    const res = await fetch(`${API_BASE_URL}/api/simulation/resume`, { method: 'POST' });
    if (!res.ok) throw new Error(`Failed to resume simulation: ${res.statusText}`);
    return res.json();
  }

  static async stepSimulation(): Promise<SimulationStepState> {
    const res = await fetch(`${API_BASE_URL}/api/simulation/step`, { method: 'POST' });
    if (!res.ok) throw new Error(`Failed to step simulation: ${res.statusText}`);
    return res.json();
  }

  static async resetSimulation(): Promise<SimulationStepState> {
    const res = await fetch(`${API_BASE_URL}/api/simulation/reset`, { method: 'POST' });
    if (!res.ok) throw new Error(`Failed to reset simulation: ${res.statusText}`);
    return res.json();
  }

  static async setSpeed(speedMs: number): Promise<{ speed_ms: number; status: string }> {
    const res = await fetch(`${API_BASE_URL}/api/simulation/speed`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ speed_ms: speedMs }),
    });
    if (!res.ok) throw new Error(`Failed to set speed: ${res.statusText}`);
    return res.json();
  }

  static async getState(): Promise<SimulationStepState> {
    const res = await fetch(`${API_BASE_URL}/api/simulation/state`);
    if (!res.ok) throw new Error(`Failed to get state: ${res.statusText}`);
    return res.json();
  }

  static async getMetrics(): Promise<NavigationMetrics | null> {
    const res = await fetch(`${API_BASE_URL}/api/metrics`);
    if (!res.ok) throw new Error(`Failed to get metrics: ${res.statusText}`);
    return res.json();
  }

  static async getEvents(limit = 100): Promise<SimulationEvent[]> {
    const res = await fetch(`${API_BASE_URL}/api/events?limit=${limit}`);
    if (!res.ok) throw new Error(`Failed to get events: ${res.statusText}`);
    return res.json();
  }

  static async getHistory(): Promise<SimulationRunRecord[]> {
    const res = await fetch(`${API_BASE_URL}/api/history`);
    if (!res.ok) throw new Error(`Failed to get history: ${res.statusText}`);
    return res.json();
  }
}

export class SimulationWebSocket {
  private ws: WebSocket | null = null;
  private reconnectTimer: number | null = null;
  private onStateCallback?: (state: SimulationStepState) => void;
  private onEventCallback?: (event: SimulationEvent) => void;
  private onConnectionChangeCallback?: (connected: boolean) => void;
  private isDestroyed = false;

  constructor(
    onState?: (state: SimulationStepState) => void,
    onEvent?: (event: SimulationEvent) => void,
    onConnectionChange?: (connected: boolean) => void
  ) {
    this.onStateCallback = onState;
    this.onEventCallback = onEvent;
    this.onConnectionChangeCallback = onConnectionChange;
    // Defer opening the socket until after React StrictMode's effect cleanup probe.
    queueMicrotask(() => this.connect());
  }

  public connect(): void {
    if (this.isDestroyed) return;
    try {
      this.ws = new WebSocket(`${WS_BASE_URL}/ws/simulation`);

      this.ws.onopen = () => {
        this.onConnectionChangeCallback?.(true);
      };

      this.ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          const payload = msg.data ?? msg.payload;
          if ((msg.type === 'STATE_UPDATE' || msg.type === 'STATE') && payload) {
            this.onStateCallback?.(payload as SimulationStepState);
          } else if ((msg.type === 'EVENT_LOG' || msg.type === 'EVENT') && payload) {
            this.onEventCallback?.(payload as SimulationEvent);
          }
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      this.ws.onclose = () => {
        this.onConnectionChangeCallback?.(false);
        this.scheduleReconnect();
      };

      this.ws.onerror = () => {
        this.onConnectionChangeCallback?.(false);
      };
    } catch {
      this.onConnectionChangeCallback?.(false);
      this.scheduleReconnect();
    }
  }

  private scheduleReconnect(): void {
    if (this.isDestroyed || this.reconnectTimer) return;
    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, 2000);
  }

  public sendAction(action: 'START' | 'PAUSE' | 'RESUME' | 'STEP' | 'RESET' | 'PING'): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ action }));
    }
  }

  public destroy(): void {
    this.isDestroyed = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}
