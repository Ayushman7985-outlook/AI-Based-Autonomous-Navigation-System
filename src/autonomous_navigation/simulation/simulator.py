"""Simulator orchestrating dynamic obstacle updates, replanning, and agent execution."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from autonomous_navigation.control.controller import WaypointController
from autonomous_navigation.environment.world import Coordinate, GridWorld
from autonomous_navigation.perception.obstacle_map import ObstacleMap
from autonomous_navigation.planning.astar import AStarPlanner


@dataclass
class DynamicObstacle:
    """Represents an active dynamic obstacle moving along a trajectory."""
    id: str
    initial_position: Coordinate
    trajectory: List[Coordinate]
    _index: int = 0

    @property
    def current_position(self) -> Coordinate:
        if not self.trajectory:
            return self.initial_position
        return self.trajectory[self._index % len(self.trajectory)]

    def step(self) -> Coordinate:
        """Advance obstacle along its trajectory sequence."""
        if self.trajectory:
            self._index += 1
        return self.current_position

    def reset(self) -> None:
        """Reset obstacle position index to start."""
        self._index = 0


@dataclass
class SimulationHistoryStep:
    """Snapshot of a single simulation time step."""
    step: int
    robot_position: Coordinate
    dynamic_obstacles: Dict[str, Coordinate]
    replan_triggered: bool
    active_path: List[Coordinate]


@dataclass
class SimulationResult:
    """Result summary of a simulation run."""
    success: bool
    collision: bool
    total_steps: int
    replan_count: int
    trajectory: List[Coordinate]
    history: List[SimulationHistoryStep]
    message: str
    execution_time_seconds: float = 0.0


class NavigationSimulator:
    """Simulates agent navigation in a dynamic grid environment."""

    def __init__(
        self,
        world: GridWorld,
        obstacle_map: ObstacleMap,
        planner: AStarPlanner,
        controller: WaypointController,
        dynamic_obstacles: Optional[List[DynamicObstacle]] = None,
        max_steps: int = 100,
        replan_on_block: bool = True,
        lookahead_horizon: Optional[int] = None,
    ) -> None:
        self.world = world
        self.obstacle_map = obstacle_map
        self.planner = planner
        self.controller = controller
        self.dynamic_obstacles = dynamic_obstacles or []
        self.max_steps = max_steps
        self.replan_on_block = replan_on_block
        self.lookahead_horizon = lookahead_horizon

    def run(self) -> SimulationResult:
        """Execute the simulation loop until goal reached, collision, or timeout."""
        start_time = time.perf_counter()

        # Reset dynamic obstacles to initial state
        for dyn in self.dynamic_obstacles:
            dyn.reset()

        # Sync initial obstacle map
        dyn_positions = [dyn.current_position for dyn in self.dynamic_obstacles]
        self.obstacle_map.update_dynamic_obstacles(dyn_positions)

        # Initial plan
        current_pos = self.world.start
        planned_path = self.planner.plan(current_pos, self.world.goal)

        if not planned_path:
            elapsed = time.perf_counter() - start_time
            return SimulationResult(
                success=False,
                collision=False,
                total_steps=0,
                replan_count=0,
                trajectory=[current_pos],
                history=[],
                message="Initial path planning failed: goal unreachable or start/goal blocked.",
                execution_time_seconds=elapsed,
            )

        self.controller.set_path(planned_path, current_pos=current_pos)

        trajectory: List[Coordinate] = [current_pos]
        history: List[SimulationHistoryStep] = [
            SimulationHistoryStep(
                step=0,
                robot_position=current_pos,
                dynamic_obstacles={d.id: d.current_position for d in self.dynamic_obstacles},
                replan_triggered=False,
                active_path=list(planned_path),
            )
        ]

        replan_count = 0
        step_num = 0

        while step_num < self.max_steps:
            step_num += 1
            replan_this_step = False

            # 1. Advance dynamic obstacles
            for dyn in self.dynamic_obstacles:
                dyn.step()

            # 2. Update perception map with new obstacle positions
            current_dyn_positions = [dyn.current_position for dyn in self.dynamic_obstacles]
            self.obstacle_map.update_dynamic_obstacles(current_dyn_positions)

            # Check if dynamic obstacle moved onto robot's current position
            if self.obstacle_map.is_occupied(current_pos):
                elapsed = time.perf_counter() - start_time
                return SimulationResult(
                    success=False,
                    collision=True,
                    total_steps=step_num,
                    replan_count=replan_count,
                    trajectory=trajectory,
                    history=history,
                    message=f"Collision occurred: dynamic obstacle moved into agent position at {current_pos}.",
                    execution_time_seconds=elapsed,
                )

            # 3. Check if current path is blocked ahead
            if self.replan_on_block:
                remaining_path = self.controller.get_remaining_waypoints()
                if self.lookahead_horizon is not None and self.lookahead_horizon > 0:
                    checked_waypoints = remaining_path[: self.lookahead_horizon]
                else:
                    checked_waypoints = remaining_path

                is_path_blocked = any(self.obstacle_map.is_occupied(wp) for wp in checked_waypoints)

                if is_path_blocked:
                    # Trigger replanning from current agent position
                    new_path = self.planner.plan(current_pos, self.world.goal)
                    if new_path:
                        self.controller.set_path(new_path, current_pos=current_pos)
                        replan_count += 1
                        replan_this_step = True
                    else:
                        # Path is blocked and no alternative route currently exists; hold position
                        pass

            # 4. Controller selects next movement target
            target_pos = self.controller.step(current_pos)

            # 5. Safety governor: never enter an occupied cell
            if target_pos != current_pos and self.obstacle_map.is_occupied(target_pos):
                # Obstacle occupies the target cell; hold position safely
                target_pos = current_pos

            current_pos = target_pos
            trajectory.append(current_pos)

            history.append(
                SimulationHistoryStep(
                    step=step_num,
                    robot_position=current_pos,
                    dynamic_obstacles={d.id: d.current_position for d in self.dynamic_obstacles},
                    replan_triggered=replan_this_step,
                    active_path=self.controller.path,
                )
            )

            # 6. Check goal arrival
            if self.controller.is_goal_reached(current_pos, self.world.goal):
                elapsed = time.perf_counter() - start_time
                return SimulationResult(
                    success=True,
                    collision=False,
                    total_steps=step_num,
                    replan_count=replan_count,
                    trajectory=trajectory,
                    history=history,
                    message="Goal successfully reached.",
                    execution_time_seconds=elapsed,
                )

        # Max steps exceeded
        elapsed = time.perf_counter() - start_time
        return SimulationResult(
            success=False,
            collision=False,
            total_steps=step_num,
            replan_count=replan_count,
            trajectory=trajectory,
            history=history,
            message="Simulation exceeded maximum steps without reaching the goal.",
            execution_time_seconds=elapsed,
        )
