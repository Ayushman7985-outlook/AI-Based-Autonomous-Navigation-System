"""Simulation management service coordinating the Python autonomous navigation engine and web clients."""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from starlette.websockets import WebSocket

from autonomous_navigation.config import NavigationConfig, get_project_root
from autonomous_navigation.control.controller import WaypointController
from autonomous_navigation.environment.world import Coordinate, GridWorld
from autonomous_navigation.evaluation.metrics import NavigationMetrics, calculate_metrics
from autonomous_navigation.perception.obstacle_map import ObstacleMap
from autonomous_navigation.planning.astar import AStarPlanner
from autonomous_navigation.simulation.simulator import DynamicObstacle, SimulationHistoryStep, SimulationResult
from backend.app.schemas.models import (
    NavigationConfigSchema,
    NavigationMetricsSchema,
    SimulationEvent,
    SimulationRunRecord,
    SimulationStatusType,
    SimulationStepState,
)

logger = logging.getLogger("autonomous_navigation.service")


class SimulationService:
    """Thread-safe orchestrator managing simulation lifecycle, step execution, and live event streaming."""

    def __init__(self, config: Optional[NavigationConfig] = None) -> None:
        self.lock = asyncio.Lock()
        self.config = config or NavigationConfig.load()
        self.speed_ms = 200  # Delay between steps in ms

        # Active components
        self.world: GridWorld
        self.obstacle_map: ObstacleMap
        self.planner: AStarPlanner
        self.controller: WaypointController
        self.dynamic_obstacles: List[DynamicObstacle] = []

        # State tracking
        self.status: SimulationStatusType = "IDLE"
        self.step_num: int = 0
        self.robot_position: Coordinate = (0, 0)
        self.planned_path: List[Coordinate] = []
        self.optimal_baseline_path: Optional[List[Coordinate]] = None
        self.trajectory: List[Coordinate] = []
        self.history: List[SimulationHistoryStep] = []
        self.events: List[SimulationEvent] = []
        self.replan_count: int = 0
        self.last_message: str = "System initialized and ready."
        self.current_metrics: Optional[NavigationMetricsSchema] = None
        self.run_history: List[SimulationRunRecord] = []

        # Background task & control flags
        self._is_running: bool = False
        self._is_paused: bool = False
        self._sim_task: Optional[asyncio.Task] = None
        self._start_perf_time: float = 0.0
        self._active_websockets: Set[WebSocket] = set()

        # Initialize simulation components
        self._build_components()
        self._init_state()

    def _build_components(self) -> None:
        """Instantiate world, obstacle map, planner, and controller from current configuration."""
        env = self.config.environment
        self.world = GridWorld(
            width=env.width,
            height=env.height,
            start=env.start,
            goal=env.goal,
            static_obstacles=env.static_obstacles,
        )
        self.obstacle_map = ObstacleMap(self.world)
        self.planner = AStarPlanner(
            obstacle_map=self.obstacle_map,
            allow_diagonal=self.config.planning.allow_diagonal,
            heuristic=self.config.planning.heuristic,
        )
        self.controller = WaypointController(
            step_size=self.config.control.step_size,
        )

        self.dynamic_obstacles = [
            DynamicObstacle(
                id=d.id,
                initial_position=d.initial_position,
                trajectory=d.trajectory,
            )
            for d in self.config.simulation.dynamic_obstacles
        ]

    def _init_state(self) -> None:
        """Reset simulation state to step 0."""
        for dyn in self.dynamic_obstacles:
            dyn.reset()

        dyn_positions = [dyn.current_position for dyn in self.dynamic_obstacles]
        self.obstacle_map.update_dynamic_obstacles(dyn_positions)

        self.step_num = 0
        self.robot_position = self.world.start
        self.replan_count = 0
        self.trajectory = [self.robot_position]

        # Calculate initial optimal baseline path
        initial_plan = self.planner.plan(self.world.start, self.world.goal)
        if initial_plan:
            self.planned_path = initial_plan
            self.optimal_baseline_path = list(initial_plan)
            self.controller.set_path(self.planned_path, current_pos=self.robot_position)
            self.status = "IDLE"
            self.last_message = f"Initial path computed with {len(initial_plan)} waypoints."
            self._log_event("INFO", 0, self.last_message)
        else:
            self.planned_path = []
            self.optimal_baseline_path = None
            self.status = "FAILED"
            self.last_message = "Initial path planning failed: goal unreachable or start/goal blocked."
            self._log_event("ERROR", 0, self.last_message)

        self.history = [
            SimulationHistoryStep(
                step=0,
                robot_position=self.robot_position,
                dynamic_obstacles={d.id: d.current_position for d in self.dynamic_obstacles},
                replan_triggered=False,
                active_path=list(self.planned_path),
            )
        ]
        self.current_metrics = None

    def _log_event(self, event_type: str, step: int, message: str) -> None:
        """Record an audit event."""
        event = SimulationEvent(
            id=str(uuid.uuid4())[:8],
            timestamp=datetime.now().strftime("%H:%M:%S.%f")[:-3],
            step=step,
            type=event_type,  # type: ignore
            message=message,
        )
        self.events.append(event)
        # Keep maximum 200 events in memory
        if len(self.events) > 200:
            self.events.pop(0)

    # ---------------- WebSocket Management ----------------

    async def register_websocket(self, websocket: WebSocket) -> None:
        """Add WebSocket client connection."""
        await websocket.accept()
        self._active_websockets.add(websocket)
        # Send current state immediately on connection
        await websocket.send_json({
            "type": "STATE_UPDATE",
            "data": self.get_state().model_dump(),
        })

    def unregister_websocket(self, websocket: WebSocket) -> None:
        """Remove WebSocket client connection."""
        self._active_websockets.discard(websocket)

    async def _broadcast_state(self) -> None:
        """Broadcast state snapshot to all connected WebSocket clients."""
        if not self._active_websockets:
            return
        state_data = {
            "type": "STATE_UPDATE",
            "data": self.get_state().model_dump(),
        }
        dead_sockets: List[WebSocket] = []
        for ws in self._active_websockets:
            try:
                await ws.send_json(state_data)
            except Exception:
                dead_sockets.append(ws)
        for ws in dead_sockets:
            self._active_websockets.discard(ws)

    async def _broadcast_event(self, event: SimulationEvent) -> None:
        """Broadcast a single event to connected WebSocket clients."""
        if not self._active_websockets:
            return
        event_data = {
            "type": "EVENT_LOG",
            "data": event.model_dump(),
        }
        dead_sockets: List[WebSocket] = []
        for ws in self._active_websockets:
            try:
                await ws.send_json(event_data)
            except Exception:
                dead_sockets.append(ws)
        for ws in dead_sockets:
            self._active_websockets.discard(ws)

    # ---------------- State and Query Methods ----------------

    def get_state(self) -> SimulationStepState:
        """Generate current state snapshot."""
        return SimulationStepState(
            step=self.step_num,
            status=self.status,
            robot_position=self.robot_position,
            start_position=self.world.start,
            goal_position=self.world.goal,
            grid_size=(self.world.width, self.world.height),
            static_obstacles=list(self.world.static_obstacles),
            dynamic_obstacles={d.id: d.current_position for d in self.dynamic_obstacles},
            active_path=list(self.planned_path),
            trajectory=list(self.trajectory),
            replan_triggered=self.history[-1].replan_triggered if self.history else False,
            replan_count=self.replan_count,
            message=self.last_message,
            metrics=self.current_metrics,
        )

    def get_metrics(self) -> Optional[NavigationMetricsSchema]:
        """Return latest metrics if available."""
        return self.current_metrics

    def get_runs(self) -> List[SimulationRunRecord]:
        """Return history of completed simulation runs."""
        return list(self.run_history)

    def get_events(self) -> List[SimulationEvent]:
        """Return event log list."""
        return list(self.events)

    def clear_events(self) -> None:
        """Clear event log."""
        self.events.clear()
        self._log_event("INFO", self.step_num, "Event log cleared by user.")

    def set_speed(self, speed_ms: int) -> None:
        """Adjust delay between simulation steps."""
        self.speed_ms = max(10, min(2000, speed_ms))

    # ---------------- Simulation Execution Controls ----------------

    async def start(self) -> SimulationStepState:
        """Start or resume continuous simulation execution."""
        async with self.lock:
            if self._is_running and not self._is_paused:
                return self.get_state()

            if self.status in ("GOAL_REACHED", "COLLISION", "MAX_STEPS_EXCEEDED", "FAILED"):
                # Reset if previously finished
                self._init_state()

            if not self.planned_path:
                self.status = "FAILED"
                self.last_message = "Cannot start simulation: initial path planning failed."
                return self.get_state()

            self._is_running = True
            self._is_paused = False
            self.status = "RUNNING"
            self._start_perf_time = time.perf_counter()
            self.last_message = f"Simulation started at step {self.step_num}."
            self._log_event("INFO", self.step_num, self.last_message)

            if self._sim_task is None or self._sim_task.done():
                self._sim_task = asyncio.create_task(self._run_loop())

            await self._broadcast_state()
            return self.get_state()

    async def pause(self) -> SimulationStepState:
        """Pause active simulation execution."""
        async with self.lock:
            if self._is_running and not self._is_paused:
                self._is_paused = True
                self.status = "PAUSED"
                self.last_message = f"Simulation paused at step {self.step_num}."
                self._log_event("INFO", self.step_num, self.last_message)
                await self._broadcast_state()
            return self.get_state()

    async def resume(self) -> SimulationStepState:
        """Resume paused simulation execution."""
        async with self.lock:
            if self._is_running and self._is_paused:
                self._is_paused = False
                self.status = "RUNNING"
                self.last_message = f"Simulation resumed at step {self.step_num}."
                self._log_event("INFO", self.step_num, self.last_message)
                await self._broadcast_state()
            return self.get_state()

    async def reset(self) -> SimulationStepState:
        """Reset simulation environment and agent to initial state."""
        async with self.lock:
            self._is_running = False
            self._is_paused = False
            if self._sim_task and not self._sim_task.done():
                self._sim_task.cancel()
                try:
                    await self._sim_task
                except asyncio.CancelledError:
                    pass
                self._sim_task = None

            self._build_components()
            self._init_state()
            if self.status != "FAILED":
                self.status = "IDLE"
            self.last_message = "Simulation reset to initial state."
            self._log_event("INFO", 0, self.last_message)
            await self._broadcast_state()
            return self.get_state()

    async def step(self) -> SimulationStepState:
        """Execute a single simulation step tick."""
        async with self.lock:
            if self.status in ("GOAL_REACHED", "COLLISION", "MAX_STEPS_EXCEEDED", "FAILED"):
                return self.get_state()

            if self._start_perf_time == 0.0:
                self._start_perf_time = time.perf_counter()

            self._execute_single_step()
            await self._broadcast_state()
            return self.get_state()

    # ---------------- Step Logic (Core Engine Integration) ----------------

    def _execute_single_step(self) -> None:
        """Perform one discrete simulation update cycle using the autonomous_navigation core."""
        self.step_num += 1
        replan_this_step = False

        # 1. Advance dynamic obstacles
        for dyn in self.dynamic_obstacles:
            dyn.step()

        # 2. Update perception obstacle map
        current_dyn_positions = [dyn.current_position for dyn in self.dynamic_obstacles]
        self.obstacle_map.update_dynamic_obstacles(current_dyn_positions)

        # 3. Collision check with robot's current cell
        if self.obstacle_map.is_occupied(self.robot_position):
            elapsed = time.perf_counter() - self._start_perf_time
            self.status = "COLLISION"
            self._is_running = False
            self.last_message = f"Collision! Dynamic obstacle entered agent cell at {self.robot_position}."
            self._log_event("ERROR", self.step_num, self.last_message)
            self._finalize_run(success=False, collision=True, elapsed_seconds=elapsed)
            return

        # 4. Path blockage detection & online replanning
        if self.config.control.replan_on_block:
            remaining_path = self.controller.get_remaining_waypoints()
            is_path_blocked = any(self.obstacle_map.is_occupied(wp) for wp in remaining_path)

            if is_path_blocked:
                # Trigger online A* replan
                new_path = self.planner.plan(self.robot_position, self.world.goal)
                if new_path:
                    self.controller.set_path(new_path, current_pos=self.robot_position)
                    self.planned_path = new_path
                    self.replan_count += 1
                    replan_this_step = True
                    self.status = "REPLANNING"
                    msg = f"Path obstructed ahead! Replanned new route ({len(new_path)} waypoints) from {self.robot_position}."
                    self.last_message = msg
                    self._log_event("REPLAN", self.step_num, msg)
                else:
                    msg = f"Path blocked at step {self.step_num} and no alternate route found; holding position."
                    self.last_message = msg
                    self._log_event("WARN", self.step_num, msg)

        # 5. Waypoint controller chooses target position
        target_pos = self.controller.step(self.robot_position)

        # 6. Safety governor: do not enter occupied cell
        if target_pos != self.robot_position and self.obstacle_map.is_occupied(target_pos):
            target_pos = self.robot_position
            msg = f"Safety governor prevented move into occupied cell at step {self.step_num}; holding position."
            self.last_message = msg
            self._log_event("WARN", self.step_num, msg)

        self.robot_position = target_pos
        self.trajectory.append(self.robot_position)
        self.planned_path = self.controller.path

        self.history.append(
            SimulationHistoryStep(
                step=self.step_num,
                robot_position=self.robot_position,
                dynamic_obstacles={d.id: d.current_position for d in self.dynamic_obstacles},
                replan_triggered=replan_this_step,
                active_path=list(self.planned_path),
            )
        )

        # 7. Check goal arrival
        if self.controller.is_goal_reached(self.robot_position, self.world.goal):
            elapsed = time.perf_counter() - self._start_perf_time
            self.status = "GOAL_REACHED"
            self._is_running = False
            self.last_message = f"Goal reached successfully at {self.world.goal} in {self.step_num} steps!"
            self._log_event("SUCCESS", self.step_num, self.last_message)
            self._finalize_run(success=True, collision=False, elapsed_seconds=elapsed)
            return

        # 8. Check max steps limit
        if self.step_num >= self.config.simulation.max_steps:
            elapsed = time.perf_counter() - self._start_perf_time
            self.status = "MAX_STEPS_EXCEEDED"
            self._is_running = False
            self.last_message = f"Simulation terminated: exceeded max steps limit ({self.config.simulation.max_steps})."
            self._log_event("WARN", self.step_num, self.last_message)
            self._finalize_run(success=False, collision=False, elapsed_seconds=elapsed)
            return

        # Normal running step
        if not replan_this_step and self.status != "PAUSED":
            self.status = "RUNNING"
            self.last_message = f"Step {self.step_num}: agent at {self.robot_position}."

    def _finalize_run(self, success: bool, collision: bool, elapsed_seconds: float) -> None:
        """Compute final metrics, update metrics state, and persist run summary."""
        sim_result = SimulationResult(
            success=success,
            collision=collision,
            total_steps=self.step_num,
            replan_count=self.replan_count,
            trajectory=self.trajectory,
            history=self.history,
            message=self.last_message,
            execution_time_seconds=elapsed_seconds,
        )

        raw_metrics = calculate_metrics(sim_result, optimal_path=self.optimal_baseline_path)
        self.current_metrics = NavigationMetricsSchema(
            success=raw_metrics.success,
            collision=raw_metrics.collision,
            total_steps=raw_metrics.total_steps,
            trajectory_length=raw_metrics.trajectory_length,
            optimal_path_length=raw_metrics.optimal_path_length,
            path_efficiency=raw_metrics.path_efficiency,
            replan_count=raw_metrics.replan_count,
            execution_time_seconds=raw_metrics.execution_time_seconds,
            message=raw_metrics.message,
        )

        # Create Run Record
        run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:4]}"
        record = SimulationRunRecord(
            run_id=run_id,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            success=raw_metrics.success,
            collision=raw_metrics.collision,
            total_steps=raw_metrics.total_steps,
            trajectory_length=raw_metrics.trajectory_length,
            optimal_path_length=raw_metrics.optimal_path_length,
            path_efficiency=raw_metrics.path_efficiency,
            replan_count=raw_metrics.replan_count,
            execution_time_seconds=raw_metrics.execution_time_seconds,
            config_summary={
                "grid_size": [self.world.width, self.world.height],
                "start": self.world.start,
                "goal": self.world.goal,
                "static_obstacles_count": len(self.world.static_obstacles),
                "dynamic_obstacles_count": len(self.dynamic_obstacles),
                "allow_diagonal": self.config.planning.allow_diagonal,
                "heuristic": self.config.planning.heuristic,
            },
            message=raw_metrics.message,
        )
        self.run_history.insert(0, record)
        # Keep maximum 50 runs
        if len(self.run_history) > 50:
            self.run_history.pop()

        # Save metrics to outputs/
        try:
            output_dir = get_project_root() / "outputs" / "runs"
            output_dir.mkdir(parents=True, exist_ok=True)
            run_file = output_dir / f"{run_id}.json"
            with open(run_file, "w", encoding="utf-8") as f:
                json.dump(record.model_dump(), f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to persist run summary to disk: {e}")

    # ---------------- Continuous Simulation Loop ----------------

    async def _run_loop(self) -> None:
        """Asynchronous execution loop ticking steps until paused, stopped, or completed."""
        try:
            while self._is_running:
                if self._is_paused:
                    await asyncio.sleep(0.1)
                    continue

                async with self.lock:
                    if not self._is_running:
                        break
                    self._execute_single_step()
                    await self._broadcast_state()

                    if self.status in ("GOAL_REACHED", "COLLISION", "MAX_STEPS_EXCEEDED", "FAILED"):
                        self._is_running = False
                        break

                # Sleep according to configured simulation speed
                await asyncio.sleep(self.speed_ms / 1000.0)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.exception("Unexpected exception in simulation loop")
            self.status = "FAILED"
            self.last_message = f"Simulation loop encountered error: {str(e)}"
            self._log_event("ERROR", self.step_num, self.last_message)
            self._is_running = False
            await self._broadcast_state()

    # ---------------- Configuration Updates ----------------

    async def update_config(self, new_config: NavigationConfigSchema) -> SimulationStepState:
        """Validate and apply a new configuration, resetting the simulation."""
        async with self.lock:
            if self._is_running:
                self._is_running = False
                if self._sim_task and not self._sim_task.done():
                    self._sim_task.cancel()
                    self._sim_task = None

            # Convert schema to internal NavigationConfig
            cfg_dict = new_config.model_dump()
            internal_cfg = NavigationConfig.from_dict(cfg_dict, get_project_root())
            internal_cfg.validate()

            self.config = internal_cfg
            self._build_components()
            self._init_state()
            if self.status != "FAILED":
                self.status = "IDLE"
                self.last_message = "Configuration updated and simulation re-initialized."
                self._log_event("INFO", 0, self.last_message)
            await self._broadcast_state()
            return self.get_state()

    async def reset_to_default_config(self) -> SimulationStepState:
        """Reset configuration back to configs/default.json."""
        default_cfg = NavigationConfig.load()
        default_schema = NavigationConfigSchema.model_validate(
            {
                "environment": {
                    "width": default_cfg.environment.width,
                    "height": default_cfg.environment.height,
                    "start": default_cfg.environment.start,
                    "goal": default_cfg.environment.goal,
                    "static_obstacles": default_cfg.environment.static_obstacles,
                },
                "simulation": {
                    "max_steps": default_cfg.simulation.max_steps,
                    "dynamic_obstacles": [
                        {
                            "id": d.id,
                            "initial_position": d.initial_position,
                            "trajectory": d.trajectory,
                        }
                        for d in default_cfg.simulation.dynamic_obstacles
                    ],
                },
                "planning": {
                    "allow_diagonal": default_cfg.planning.allow_diagonal,
                    "heuristic": default_cfg.planning.heuristic,
                },
                "control": {
                    "step_size": default_cfg.control.step_size,
                    "replan_on_block": default_cfg.control.replan_on_block,
                },
            }
        )
        return await self.update_config(default_schema)
