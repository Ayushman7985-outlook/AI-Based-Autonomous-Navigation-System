"""Matplotlib-based renderer for 2D grid autonomous navigation simulation."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import matplotlib
matplotlib.use("Agg")  # Non-interactive headless backend
import matplotlib.patches as patches
import matplotlib.pyplot as plt

from autonomous_navigation.environment.world import Coordinate, GridWorld
from autonomous_navigation.simulation.simulator import SimulationResult


class SimulationRenderer:
    """Renders environment, obstacles, paths, and robot trajectories to image files."""

    def __init__(self, world: GridWorld) -> None:
        self.world = world

    def render(
        self,
        result: SimulationResult,
        output_path: str | Path,
        title: str = "Autonomous Navigation Simulation",
        initial_path: Optional[List[Coordinate]] = None,
    ) -> Path:
        """Render the complete simulation trajectory to a file."""
        target_path = Path(output_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        fig, ax = plt.subplots(figsize=(10, 10))

        # 1. Grid boundary and ticks
        ax.set_xlim(-0.5, self.world.width - 0.5)
        ax.set_ylim(-0.5, self.world.height - 0.5)
        ax.set_xticks(range(self.world.width))
        ax.set_yticks(range(self.world.height))
        ax.grid(True, which="both", color="#e0e0e0", linestyle="--", linewidth=0.5)
        ax.set_aspect("equal")

        # 2. Draw static obstacles
        static_patch = None
        for ox, oy in self.world.static_obstacles:
            rect = patches.Rectangle(
                (ox - 0.5, oy - 0.5), 1, 1,
                linewidth=0, facecolor="#2b2d42", alpha=0.9
            )
            static_patch = ax.add_patch(rect)

        # 3. Draw initial planned path if available
        if initial_path and len(initial_path) > 1:
            ix = [p[0] for p in initial_path]
            iy = [p[1] for p in initial_path]
            ax.plot(
                ix, iy,
                color="#00b4d8", linestyle="--", linewidth=1.8,
                alpha=0.7, label="Initial Planned Path"
            )

        # 4. Draw dynamic obstacle final/trajectory footprints
        dynamic_patch = None
        for step_data in result.history:
            for _, dyn_pos in step_data.dynamic_obstacles.items():
                circle = patches.Circle(
                    dyn_pos, 0.35,
                    facecolor="#ef233c", alpha=0.15, edgecolor="none"
                )
                ax.add_patch(circle)

        # Draw final positions of dynamic obstacles
        if result.history:
            last_step = result.history[-1]
            for dyn_id, dyn_pos in last_step.dynamic_obstacles.items():
                circle = patches.Circle(
                    dyn_pos, 0.4,
                    facecolor="#d90429", edgecolor="#8d99ae", linewidth=1.5,
                    label=f"Dynamic Obs ({dyn_id})"
                )
                dynamic_patch = ax.add_patch(circle)

        # 5. Draw actual robot trajectory
        if result.trajectory:
            rx = [p[0] for p in result.trajectory]
            ry = [p[1] for p in result.trajectory]
            ax.plot(
                rx, ry,
                color="#3a0ca3", linewidth=2.5, marker="o", markersize=3.5,
                alpha=0.9, label="Executed Trajectory"
            )

        # 6. Highlight replanning points
        replan_x = []
        replan_y = []
        for step_data in result.history:
            if step_data.replan_triggered:
                replan_x.append(step_data.robot_position[0])
                replan_y.append(step_data.robot_position[1])

        if replan_x:
            ax.scatter(
                replan_x, replan_y,
                color="#f72585", marker="x", s=100, linewidths=2.5,
                zorder=5, label=f"Replan Events ({len(replan_x)})"
            )

        # 7. Start and Goal Markers
        sx, sy = self.world.start
        gx, gy = self.world.goal
        ax.scatter(
            [sx], [sy],
            color="#2ec4b6", marker="s", s=140, edgecolors="#011627", linewidths=1.5,
            zorder=6, label=f"Start ({sx}, {sy})"
        )
        ax.scatter(
            [gx], [gy],
            color="#ffb703", marker="*", s=220, edgecolors="#fb8500", linewidths=1.5,
            zorder=6, label=f"Goal ({gx}, {gy})"
        )

        # 8. Titles & Legends
        status_text = "SUCCESS" if result.success else ("COLLISION" if result.collision else "TIMEOUT")
        ax.set_title(
            f"{title}\nStatus: {status_text} | Steps: {result.total_steps} | Replans: {result.replan_count}",
            fontsize=12, fontweight="bold", pad=12
        )
        ax.set_xlabel("X Coordinate", fontsize=10)
        ax.set_ylabel("Y Coordinate", fontsize=10)

        # Deduplicate legend items
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        if static_patch:
            by_label["Static Obstacle"] = patches.Patch(facecolor="#2b2d42")

        ax.legend(
            by_label.values(), by_label.keys(),
            loc="upper left", bbox_to_anchor=(1.02, 1),
            frameon=True, fontsize=9
        )

        plt.tight_layout()
        plt.savefig(target_path, dpi=200, bbox_inches="tight")
        plt.close(fig)

        return target_path
