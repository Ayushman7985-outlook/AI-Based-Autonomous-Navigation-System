"""Configuration loader and validator for Autonomous Navigation System."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Tuple


def get_project_root() -> Path:
    """Return the absolute path to the project root directory."""
    # autonomous_navigation is at src/autonomous_navigation -> 2 levels up to root
    return Path(__file__).resolve().parent.parent.parent


@dataclass
class EnvironmentConfig:
    width: int
    height: int
    start: Tuple[int, int]
    goal: Tuple[int, int]
    static_obstacles: List[Tuple[int, int]]


@dataclass
class DynamicObstacleConfig:
    id: str
    initial_position: Tuple[int, int]
    trajectory: List[Tuple[int, int]]


@dataclass
class SimulationConfig:
    max_steps: int
    dynamic_obstacles: List[DynamicObstacleConfig] = field(default_factory=list)


@dataclass
class PlanningConfig:
    allow_diagonal: bool = False
    heuristic: str = "manhattan"


@dataclass
class ControlConfig:
    step_size: int = 1
    replan_on_block: bool = True


@dataclass
class VisualizationConfig:
    save_figure: bool = True
    figure_path: Path = field(default_factory=lambda: get_project_root() / "outputs" / "figures" / "simulation_trajectory.png")
    figure_title: str = "Autonomous Navigation Trajectory"


@dataclass
class EvaluationConfig:
    save_metrics: bool = True
    metrics_path: Path = field(default_factory=lambda: get_project_root() / "outputs" / "metrics" / "navigation_metrics.json")


@dataclass
class NavigationConfig:
    """Master configuration class."""
    environment: EnvironmentConfig
    simulation: SimulationConfig
    planning: PlanningConfig
    control: ControlConfig
    visualization: VisualizationConfig
    evaluation: EvaluationConfig

    @classmethod
    def load(cls, config_path: str | Path | None = None) -> "NavigationConfig":
        """Load and validate configuration from a JSON file.

        If config_path is None, defaults to `configs/default.json` relative to project root.
        """
        project_root = get_project_root()
        if config_path is None:
            resolved_path = project_root / "configs" / "default.json"
        else:
            resolved_path = Path(config_path)
            if not resolved_path.is_absolute():
                resolved_path = project_root / resolved_path

        if not resolved_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {resolved_path}")

        with open(resolved_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return cls.from_dict(data, project_root)

    @classmethod
    def from_dict(cls, data: Dict[str, Any], project_root: Path | None = None) -> "NavigationConfig":
        """Parse and validate configuration dictionary."""
        if project_root is None:
            project_root = get_project_root()

        env_raw = data.get("environment", {})
        cls._validate_environment_raw(env_raw)

        env_cfg = EnvironmentConfig(
            width=int(env_raw["width"]),
            height=int(env_raw["height"]),
            start=(int(env_raw["start"][0]), int(env_raw["start"][1])),
            goal=(int(env_raw["goal"][0]), int(env_raw["goal"][1])),
            static_obstacles=[(int(x), int(y)) for x, y in env_raw.get("static_obstacles", [])],
        )

        sim_raw = data.get("simulation", {})
        dyn_obs_list: List[DynamicObstacleConfig] = []
        for dyn in sim_raw.get("dynamic_obstacles", []):
            dyn_obs_list.append(
                DynamicObstacleConfig(
                    id=str(dyn.get("id", "dyn_obs")),
                    initial_position=(int(dyn["initial_position"][0]), int(dyn["initial_position"][1])),
                    trajectory=[(int(p[0]), int(p[1])) for p in dyn.get("trajectory", [])],
                )
            )

        sim_cfg = SimulationConfig(
            max_steps=int(sim_raw.get("max_steps", 100)),
            dynamic_obstacles=dyn_obs_list,
        )

        plan_raw = data.get("planning", {})
        plan_cfg = PlanningConfig(
            allow_diagonal=bool(plan_raw.get("allow_diagonal", False)),
            heuristic=str(plan_raw.get("heuristic", "manhattan")).lower(),
        )

        ctrl_raw = data.get("control", {})
        ctrl_cfg = ControlConfig(
            step_size=int(ctrl_raw.get("step_size", 1)),
            replan_on_block=bool(ctrl_raw.get("replan_on_block", True)),
        )

        vis_raw = data.get("visualization", {})
        fig_path = Path(vis_raw.get("figure_path", "outputs/figures/simulation_trajectory.png"))
        if not fig_path.is_absolute():
            fig_path = project_root / fig_path

        vis_cfg = VisualizationConfig(
            save_figure=bool(vis_raw.get("save_figure", True)),
            figure_path=fig_path,
            figure_title=str(vis_raw.get("figure_title", "Autonomous Navigation Trajectory")),
        )

        eval_raw = data.get("evaluation", {})
        metrics_path = Path(eval_raw.get("metrics_path", "outputs/metrics/navigation_metrics.json"))
        if not metrics_path.is_absolute():
            metrics_path = project_root / metrics_path

        eval_cfg = EvaluationConfig(
            save_metrics=bool(eval_raw.get("save_metrics", True)),
            metrics_path=metrics_path,
        )

        config = cls(
            environment=env_cfg,
            simulation=sim_cfg,
            planning=plan_cfg,
            control=ctrl_cfg,
            visualization=vis_cfg,
            evaluation=eval_cfg,
        )
        config.validate()
        return config

    @staticmethod
    def _validate_environment_raw(env_raw: Dict[str, Any]) -> None:
        required_fields = ["width", "height", "start", "goal"]
        for field_name in required_fields:
            if field_name not in env_raw:
                raise ValueError(f"Missing required environment field: '{field_name}'")

    def validate(self) -> None:
        """Validate logical constraints across configurations."""
        if self.environment.width <= 0 or self.environment.height <= 0:
            raise ValueError("Environment width and height must be strictly positive integers.")

        w, h = self.environment.width, self.environment.height
        sx, sy = self.environment.start
        gx, gy = self.environment.goal

        if not (0 <= sx < w and 0 <= sy < h):
            raise ValueError(f"Start position {self.environment.start} is out of bounds for grid {w}x{h}.")
        if not (0 <= gx < w and 0 <= gy < h):
            raise ValueError(f"Goal position {self.environment.goal} is out of bounds for grid {w}x{h}.")
        if self.environment.start == self.environment.goal:
            raise ValueError("Start and goal positions cannot be identical.")

        obs_set = set(self.environment.static_obstacles)
        if self.environment.start in obs_set:
            raise ValueError(f"Start position {self.environment.start} is placed on an obstacle.")
        if self.environment.goal in obs_set:
            raise ValueError(f"Goal position {self.environment.goal} is placed on an obstacle.")

        for ox, oy in obs_set:
            if not (0 <= ox < w and 0 <= oy < h):
                raise ValueError(f"Obstacle ({ox}, {oy}) is outside environment boundaries {w}x{h}.")

        if self.simulation.max_steps <= 0:
            raise ValueError("Simulation max_steps must be greater than zero.")

        if self.planning.heuristic not in ("manhattan", "euclidean"):
            raise ValueError(f"Unsupported heuristic '{self.planning.heuristic}'. Use 'manhattan' or 'euclidean'.")
