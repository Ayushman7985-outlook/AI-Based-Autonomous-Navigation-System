"""Performance metrics calculator and reporting for autonomous navigation.

Formulas & Definitions:
- total_steps: Integer count of simulation time steps executed.
- trajectory_length: Cumulative Euclidean distance traversed by the agent across consecutive
  coordinates: sum(hypot(x_{i+1} - x_i, y_{i+1} - y_i) for i in range(len(trajectory) - 1)).
- optimal_path_length: Cumulative Euclidean distance of the baseline collision-free path
  planned before dynamic obstacle interference.
- path_efficiency:
    - If navigation failed (collision or timeout): 0.0
    - If navigation succeeded with non-zero optimal and actual length:
        min(optimal_path_length / trajectory_length, 1.0)
    - If navigation succeeded with zero optimal length (start == goal):
        1.0 if trajectory_length == 0.0 else 0.0
- replan_count: Total number of online A* replanning operations triggered by path blockages.
- execution_time_seconds: CPU clock elapsed time of the simulation run.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from autonomous_navigation.environment.world import Coordinate
from autonomous_navigation.simulation.simulator import SimulationResult


@dataclass
class NavigationMetrics:
    """Quantitative performance metrics of a simulation execution."""
    success: bool
    collision: bool
    total_steps: int
    trajectory_length: float
    optimal_path_length: float
    path_efficiency: float
    replan_count: int
    execution_time_seconds: float
    message: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def calculate_path_length(path: List[Coordinate]) -> float:
    """Calculate Euclidean cumulative length of a coordinate sequence."""
    if len(path) < 2:
        return 0.0
    total = 0.0
    for i in range(len(path) - 1):
        x1, y1 = path[i]
        x2, y2 = path[i + 1]
        total += math.hypot(x2 - x1, y2 - y1)
    return round(total, 4)


def calculate_metrics(
    result: SimulationResult,
    optimal_path: Optional[List[Coordinate]] = None,
) -> NavigationMetrics:
    """Compute performance metrics from simulation outcome.

    Calculates trajectory length, baseline reference length, and path efficiency.
    Handles degenerate, failed, and detour scenarios explicitly.
    """
    traj_len = calculate_path_length(result.trajectory)
    opt_len = calculate_path_length(optimal_path) if optimal_path is not None else traj_len

    if not result.success:
        efficiency = 0.0
    elif opt_len == 0.0:
        efficiency = 1.0 if traj_len == 0.0 else 0.0
    elif traj_len > 0.0:
        efficiency = round(min(opt_len / traj_len, 1.0), 4)
    else:
        efficiency = 0.0

    return NavigationMetrics(
        success=result.success,
        collision=result.collision,
        total_steps=result.total_steps,
        trajectory_length=traj_len,
        optimal_path_length=opt_len,
        path_efficiency=efficiency,
        replan_count=result.replan_count,
        execution_time_seconds=round(result.execution_time_seconds, 6),
        message=result.message,
    )


def save_metrics(metrics: NavigationMetrics, output_path: str | Path) -> Path:
    """Save metrics to a JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metrics.to_dict(), f, indent=2)
    return path
