"""Main CLI application entry point orchestrating autonomous navigation simulation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from autonomous_navigation.config import NavigationConfig
from autonomous_navigation.control.controller import WaypointController
from autonomous_navigation.environment.world import GridWorld
from autonomous_navigation.evaluation.metrics import calculate_metrics, save_metrics
from autonomous_navigation.perception.obstacle_map import ObstacleMap
from autonomous_navigation.planning.astar import AStarPlanner
from autonomous_navigation.simulation.simulator import DynamicObstacle, NavigationSimulator
from autonomous_navigation.visualization.renderer import SimulationRenderer


def parse_args(args: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AI Autonomous Navigation System Simulation Runner"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to JSON configuration file (defaults to configs/default.json)",
    )
    return parser.parse_args(args)


def run_navigation(config_path: str | Path | None = None) -> int:
    """Run the complete navigation pipeline based on specified config."""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("=" * 60)
    print("  AI-Based Autonomous Navigation System")
    print("=" * 60)

    # 1. Load configuration
    try:
        config = NavigationConfig.load(config_path)
        print("[+] Configuration successfully loaded and validated.")
    except Exception as e:
        print(f"[!] Failed to load configuration: {e}", file=sys.stderr)
        return 1

    # 2. Initialize Environment
    world = GridWorld(
        width=config.environment.width,
        height=config.environment.height,
        start=config.environment.start,
        goal=config.environment.goal,
        static_obstacles=config.environment.static_obstacles,
    )
    print(f"[+] World initialized: {world.width}x{world.height} grid | Start: {world.start} | Goal: {world.goal}")

    # 3. Initialize Perception & Obstacle Map
    obstacle_map = ObstacleMap(world)

    # 4. Initialize Planner & Controller
    planner = AStarPlanner(
        obstacle_map=obstacle_map,
        allow_diagonal=config.planning.allow_diagonal,
        heuristic=config.planning.heuristic,
    )
    controller = WaypointController(step_size=config.control.step_size)

    # Compute optimal baseline path without dynamic obstacles
    initial_optimal_path = planner.plan(world.start, world.goal)

    # 5. Initialize Dynamic Obstacles
    dynamic_obstacles = [
        DynamicObstacle(
            id=d.id,
            initial_position=d.initial_position,
            trajectory=d.trajectory,
        )
        for d in config.simulation.dynamic_obstacles
    ]
    print(f"[+] Dynamic obstacles configured: {len(dynamic_obstacles)} active agent(s)")

    # 6. Initialize and run Simulator
    simulator = NavigationSimulator(
        world=world,
        obstacle_map=obstacle_map,
        planner=planner,
        controller=controller,
        dynamic_obstacles=dynamic_obstacles,
        max_steps=config.simulation.max_steps,
        replan_on_block=config.control.replan_on_block,
    )

    print("[*] Executing simulation run...")
    result = simulator.run()

    # 7. Calculate and Save Metrics
    metrics = calculate_metrics(result, optimal_path=initial_optimal_path)
    if config.evaluation.save_metrics:
        saved_metrics_file = save_metrics(metrics, config.evaluation.metrics_path)
        print(f"[+] Metrics saved to: {saved_metrics_file}")

    # 8. Render and Save Figure
    if config.visualization.save_figure:
        renderer = SimulationRenderer(world)
        saved_fig_file = renderer.render(
            result=result,
            output_path=config.visualization.figure_path,
            title=config.visualization.figure_title,
            initial_path=initial_optimal_path,
        )
        print(f"[+] Figure saved to: {saved_fig_file}")

    # 9. Output Summary
    print("-" * 60)
    print(f"Status           : {'SUCCESS' if metrics.success else ('COLLISION' if metrics.collision else 'FAILED')}")
    print(f"Message          : {metrics.message}")
    print(f"Total Steps      : {metrics.total_steps}")
    print(f"Replanning Events: {metrics.replan_count}")
    print(f"Path Efficiency  : {metrics.path_efficiency * 100:.1f}%")
    print(f"Execution Time   : {metrics.execution_time_seconds:.4f} s")
    print("=" * 60)

    return 0 if metrics.success else 2


def main() -> None:
    args = parse_args()
    exit_code = run_navigation(args.config)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
