"""Unit tests for evaluation metrics calculation and serialization."""

import json
import tempfile
import unittest
from pathlib import Path

from autonomous_navigation.evaluation.metrics import (
    calculate_metrics,
    calculate_path_length,
    save_metrics,
)
from autonomous_navigation.simulation.simulator import SimulationResult


class TestNavigationMetrics(unittest.TestCase):
    """Tests for metric calculations, path lengths, and reporting across scenarios."""

    def test_calculate_path_length(self):
        # Empty and single-point paths have length 0.0
        self.assertEqual(calculate_path_length([]), 0.0)
        self.assertEqual(calculate_path_length([(0, 0)]), 0.0)

        # Straight line: (0,0) -> (0,3) -> length 3.0
        path = [(0, 0), (0, 1), (0, 2), (0, 3)]
        self.assertEqual(calculate_path_length(path), 3.0)

    def test_direct_route_efficiency(self):
        """Direct route matches optimal path -> 100% efficiency."""
        result = SimulationResult(
            success=True,
            collision=False,
            total_steps=5,
            replan_count=0,
            trajectory=[(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0)],
            history=[],
            message="Goal reached.",
        )
        optimal = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0)]
        metrics = calculate_metrics(result, optimal_path=optimal)
        self.assertTrue(metrics.success)
        self.assertEqual(metrics.total_steps, 5)
        self.assertEqual(metrics.trajectory_length, 5.0)
        self.assertEqual(metrics.optimal_path_length, 5.0)
        self.assertEqual(metrics.path_efficiency, 1.0)
        self.assertEqual(metrics.replan_count, 0)

    def test_detour_around_obstacles_efficiency(self):
        """Detour trajectory is longer than optimal direct baseline -> efficiency < 1.0."""
        # Optimal direct would be 4 units straight: (0,0) to (4,0)
        optimal = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)]  # length 4.0
        # Detour went up to avoid obstacle at (2,0): (0,0)->(1,0)->(1,1)->(2,1)->(3,1)->(3,0)->(4,0) -> length 6.0
        detour = [(0, 0), (1, 0), (1, 1), (2, 1), (3, 1), (3, 0), (4, 0)]
        result = SimulationResult(
            success=True,
            collision=False,
            total_steps=6,
            replan_count=0,
            trajectory=detour,
            history=[],
            message="Goal reached with detour.",
        )
        metrics = calculate_metrics(result, optimal_path=optimal)
        self.assertTrue(metrics.success)
        self.assertEqual(metrics.trajectory_length, 6.0)
        self.assertEqual(metrics.optimal_path_length, 4.0)
        self.assertAlmostEqual(metrics.path_efficiency, 4.0 / 6.0, places=4)

    def test_route_involving_replanning_efficiency(self):
        """Route with online replanning records replan count and accurately computes efficiency."""
        optimal = [(0, 0), (0, 1), (0, 2), (0, 3)]  # length 3.0
        executed = [(0, 0), (0, 1), (1, 1), (1, 2), (0, 2), (0, 3)]  # length 5.0
        result = SimulationResult(
            success=True,
            collision=False,
            total_steps=5,
            replan_count=2,
            trajectory=executed,
            history=[],
            message="Goal reached after replanning.",
        )
        metrics = calculate_metrics(result, optimal_path=optimal)
        self.assertEqual(metrics.replan_count, 2)
        self.assertEqual(metrics.trajectory_length, 5.0)
        self.assertEqual(metrics.optimal_path_length, 3.0)
        self.assertEqual(metrics.path_efficiency, 0.6)

    def test_zero_length_degenerate_trajectory(self):
        """Start == Goal: 0 distance needed and 0 distance traversed -> efficiency 1.0."""
        result = SimulationResult(
            success=True,
            collision=False,
            total_steps=0,
            replan_count=0,
            trajectory=[(0, 0)],
            history=[],
            message="Already at goal.",
        )
        optimal = [(0, 0)]
        metrics = calculate_metrics(result, optimal_path=optimal)
        self.assertTrue(metrics.success)
        self.assertEqual(metrics.trajectory_length, 0.0)
        self.assertEqual(metrics.optimal_path_length, 0.0)
        self.assertEqual(metrics.path_efficiency, 1.0)

        # But if agent wandered when start was goal:
        wandered_result = SimulationResult(
            success=True,
            collision=False,
            total_steps=4,
            replan_count=0,
            trajectory=[(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)],
            history=[],
            message="Returned to goal.",
        )
        metrics_wandered = calculate_metrics(wandered_result, optimal_path=optimal)
        self.assertEqual(metrics_wandered.path_efficiency, 0.0)

    def test_failed_or_unreachable_navigation(self):
        """Failed navigation yields efficiency 0.0."""
        result_collision = SimulationResult(
            success=False,
            collision=True,
            total_steps=3,
            replan_count=1,
            trajectory=[(0, 0), (0, 1), (0, 2)],
            history=[],
            message="Collision occurred.",
        )
        metrics = calculate_metrics(result_collision, optimal_path=[(0, 0), (0, 1), (0, 2), (0, 3)])
        self.assertFalse(metrics.success)
        self.assertTrue(metrics.collision)
        self.assertEqual(metrics.path_efficiency, 0.0)

        result_unreachable = SimulationResult(
            success=False,
            collision=False,
            total_steps=0,
            replan_count=0,
            trajectory=[(0, 0)],
            history=[],
            message="Goal unreachable.",
        )
        metrics_unreachable = calculate_metrics(result_unreachable, optimal_path=None)
        self.assertFalse(metrics_unreachable.success)
        self.assertEqual(metrics_unreachable.path_efficiency, 0.0)

    def test_save_metrics_json(self):
        result = SimulationResult(
            success=True,
            collision=False,
            total_steps=2,
            replan_count=0,
            trajectory=[(0, 0), (0, 1)],
            history=[],
            message="Goal reached.",
        )
        metrics = calculate_metrics(result)

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_metrics.json"
            save_metrics(metrics, file_path)
            self.assertTrue(file_path.exists())

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(data["success"], True)
            self.assertEqual(data["total_steps"], 2)


if __name__ == "__main__":
    unittest.main()
