export type Coordinate = [number, number];

export type SimulationStatusType =
  | 'IDLE'
  | 'RUNNING'
  | 'PAUSED'
  | 'REPLANNING'
  | 'GOAL_REACHED'
  | 'COLLISION'
  | 'MAX_STEPS_EXCEEDED'
  | 'FAILED';

export interface DynamicObstacleConfig {
  id: string;
  initial_position: Coordinate;
  trajectory: Coordinate[];
}

export interface EnvironmentConfig {
  width: number;
  height: number;
  start: Coordinate;
  goal: Coordinate;
  static_obstacles: Coordinate[];
}

export interface PlanningConfig {
  allow_diagonal: boolean;
  heuristic: 'manhattan' | 'euclidean';
}

export interface ControlConfig {
  step_size: number;
  replan_on_block: boolean;
}

export interface SimulationConfig {
  max_steps: number;
  dynamic_obstacles: DynamicObstacleConfig[];
}

export interface VisualizationConfig {
  save_figure: boolean;
  figure_path: string;
  figure_title: string;
}

export interface EvaluationConfig {
  save_metrics: boolean;
  metrics_path: string;
}

export interface NavigationConfig {
  environment: EnvironmentConfig;
  simulation: SimulationConfig;
  planning: PlanningConfig;
  control: ControlConfig;
  visualization?: VisualizationConfig;
  evaluation?: EvaluationConfig;
}

export interface NavigationMetrics {
  success: boolean;
  collision: boolean;
  total_steps: number;
  trajectory_length: number;
  optimal_path_length: number;
  path_efficiency: number;
  replan_count: number;
  execution_time_seconds: number;
  message: string;
}

export interface SimulationStepState {
  step: number;
  status: SimulationStatusType;
  robot_position: Coordinate;
  start_position: Coordinate;
  goal_position: Coordinate;
  grid_size: [number, number];
  static_obstacles: Coordinate[];
  dynamic_obstacles: Record<string, Coordinate>;
  active_path: Coordinate[];
  trajectory: Coordinate[];
  replan_triggered: boolean;
  replan_count: number;
  message: string;
  metrics?: NavigationMetrics | null;
}

export interface SimulationEvent {
  id: string;
  timestamp: string;
  step: number;
  type: 'INFO' | 'WARN' | 'SUCCESS' | 'ERROR' | 'REPLAN';
  message: string;
}

export interface SimulationRunRecord {
  run_id: string;
  timestamp: string;
  success: boolean;
  collision: boolean;
  total_steps: number;
  trajectory_length: number;
  optimal_path_length: number;
  path_efficiency: number;
  replan_count: number;
  execution_time_seconds: number;
  config_summary: Record<string, unknown>;
  message: string;
}

export type InteractiveTool = 'select' | 'add_obstacle' | 'remove_obstacle' | 'set_start' | 'set_goal';
