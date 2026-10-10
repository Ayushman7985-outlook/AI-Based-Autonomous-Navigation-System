"""Pydantic schemas for API request and response validation."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Tuple
from pydantic import BaseModel, Field, field_validator


class DynamicObstacleSchema(BaseModel):
    """Configuration for a dynamic obstacle."""
    id: str = Field(..., description="Unique identifier for the dynamic obstacle")
    initial_position: Tuple[int, int] = Field(..., description="[x, y] initial coordinate")
    trajectory: List[Tuple[int, int]] = Field(default_factory=list, description="List of [x, y] coordinates in trajectory")

    @field_validator("initial_position", "trajectory", mode="before")
    @classmethod
    def convert_coords(cls, v: Any) -> Any:
        if isinstance(v, list):
            if len(v) == 2 and isinstance(v[0], (int, float)) and isinstance(v[1], (int, float)):
                return (int(v[0]), int(v[1]))
            return [(int(p[0]), int(p[1])) for p in v]
        return v


class EnvironmentConfigSchema(BaseModel):
    """Grid environment configuration schema."""
    width: int = Field(20, ge=3, le=100, description="Grid width in cells")
    height: int = Field(20, ge=3, le=100, description="Grid height in cells")
    start: Tuple[int, int] = Field((1, 1), description="[x, y] start position")
    goal: Tuple[int, int] = Field((18, 18), description="[x, y] goal position")
    static_obstacles: List[Tuple[int, int]] = Field(default_factory=list, description="List of [x, y] static obstacle cells")

    @field_validator("start", "goal", mode="before")
    @classmethod
    def convert_tuple(cls, v: Any) -> Tuple[int, int]:
        if isinstance(v, (list, tuple)) and len(v) == 2:
            return (int(v[0]), int(v[1]))
        raise ValueError(f"Expected [x, y] coordinate pair, got {v}")

    @field_validator("static_obstacles", mode="before")
    @classmethod
    def convert_obstacles(cls, v: Any) -> List[Tuple[int, int]]:
        if isinstance(v, list):
            return [(int(p[0]), int(p[1])) for p in v]
        return []


class PlanningConfigSchema(BaseModel):
    """Path planning algorithm settings."""
    allow_diagonal: bool = Field(False, description="Allow 8-directional diagonal movement")
    heuristic: Literal["manhattan", "euclidean"] = Field("manhattan", description="A* heuristic distance metric")


class ControlConfigSchema(BaseModel):
    """Controller configuration."""
    step_size: int = Field(1, ge=1, le=5, description="Waypoint controller step size")
    replan_on_block: bool = Field(True, description="Enable automatic online replanning when path is obstructed")


class SimulationConfigSchema(BaseModel):
    """Simulation run parameters."""
    max_steps: int = Field(100, ge=1, le=1000, description="Maximum simulation execution steps")
    dynamic_obstacles: List[DynamicObstacleSchema] = Field(default_factory=list, description="Dynamic obstacles list")


class VisualizationConfigSchema(BaseModel):
    save_figure: bool = Field(True)
    figure_path: str = Field("outputs/figures/simulation_trajectory.png")
    figure_title: str = Field("Autonomous Navigation Trajectory")


class EvaluationConfigSchema(BaseModel):
    save_metrics: bool = Field(True)
    metrics_path: str = Field("outputs/metrics/navigation_metrics.json")


class NavigationConfigSchema(BaseModel):
    """Master application configuration schema."""
    environment: EnvironmentConfigSchema = Field(default_factory=EnvironmentConfigSchema)
    simulation: SimulationConfigSchema = Field(default_factory=SimulationConfigSchema)
    planning: PlanningConfigSchema = Field(default_factory=PlanningConfigSchema)
    control: ControlConfigSchema = Field(default_factory=ControlConfigSchema)
    visualization: VisualizationConfigSchema = Field(default_factory=VisualizationConfigSchema)
    evaluation: EvaluationConfigSchema = Field(default_factory=EvaluationConfigSchema)


class NavigationMetricsSchema(BaseModel):
    """Quantitative performance metrics schema."""
    success: bool
    collision: bool
    total_steps: int
    trajectory_length: float
    optimal_path_length: float
    path_efficiency: float
    replan_count: int
    execution_time_seconds: float
    message: str


SimulationStatusType = Literal[
    "IDLE",
    "RUNNING",
    "PAUSED",
    "REPLANNING",
    "GOAL_REACHED",
    "COLLISION",
    "MAX_STEPS_EXCEEDED",
    "FAILED",
]


class SimulationStepState(BaseModel):
    """Real-time simulation state snapshot."""
    step: int
    status: SimulationStatusType
    robot_position: Tuple[int, int]
    start_position: Tuple[int, int]
    goal_position: Tuple[int, int]
    grid_size: Tuple[int, int]
    static_obstacles: List[Tuple[int, int]]
    dynamic_obstacles: Dict[str, Tuple[int, int]]
    active_path: List[Tuple[int, int]]
    trajectory: List[Tuple[int, int]]
    replan_triggered: bool
    replan_count: int
    message: str
    metrics: Optional[NavigationMetricsSchema] = None


class SimulationEvent(BaseModel):
    """Simulation audit event entry."""
    id: str
    timestamp: str
    step: int
    type: Literal["INFO", "WARN", "SUCCESS", "ERROR", "REPLAN"]
    message: str


class SimulationRunRecord(BaseModel):
    """Historical run summary."""
    run_id: str
    timestamp: str
    success: bool
    collision: bool
    total_steps: int
    trajectory_length: float
    optimal_path_length: float
    path_efficiency: float
    replan_count: int
    execution_time_seconds: float
    config_summary: Dict[str, Any]
    message: str


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str


class SimulationSpeedRequest(BaseModel):
    speed_ms: int = Field(200, ge=10, le=2000, description="Delay between steps in milliseconds")
